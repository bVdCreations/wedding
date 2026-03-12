# Database Backup Plan: PostgreSQL to Cloudflare R2

## Overview

- **Database**: PostgreSQL 16-alpine (running in Docker)
- **Destination**: Cloudflare R2 (S3-compatible storage)
- **Schedule**: Daily via cron at 2:00 AM
- **Retention**: 7 days (auto-delete older backups)

---

## Prerequisites

### 1. Create Cloudflare R2 Bucket

1. Log into [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Go to **R2** → **Create bucket**
3. Bucket name: `wedding-backups`
4. Optionally enable "Protect this bucket" to block public access

### 2. Create R2 API Token

1. Go to **Profile** → **API Tokens**
2. Create token with permissions:
   - `Object Read & Write` on the wedding-backups bucket
3. Note the following credentials:
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`
   - `R2_ENDPOINT` (format: `https://<account-id>.r2.cloudflarestorage.com`)

---

## Implementation

### Step 1: Install AWS CLI on Ubuntu Server

```bash
# Update package list and install
sudo apt update
sudo apt install awscli -y

# Verify
aws --version
```

Or install AWS CLI v2 (recommended for R2):

```bash
cd /tmp
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
sudo ./aws/install
aws --version
```

### Step 2: Add Environment Variables

Add to `.env.prod`:

```bash
# R2 Backup
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=wedding-backups
```

### Step 3: Create Backup Script

Create `deploy/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/tmp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-wedding_rsvp}"
DB_USER="${POSTGRES_USER:-postgres}"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# Create compressed PostgreSQL dump
docker exec wedding_db pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_DIR/db_$DATE.dump"

# Upload to R2
aws s3 cp "$BACKUP_DIR/db_$DATE.dump" "s3://${R2_BUCKET_NAME}/db_$DATE.dump" \
  --endpoint-url="$R2_ENDPOINT" \
  --storage-class=STANDARD_IA

# Clean up local file
rm "$BACKUP_DIR/db_$DATE.dump"

# Delete backups older than 7 days
aws s3 ls "s3://${R2_BUCKET_NAME}/" --endpoint-url="$R2_ENDPOINT" | while read -r line; do
  backup_date=$(echo "$line" | awk '{print $1}')
  days_old=$(( ( $(date +%s) - $(date -d "$backup_date" +%s) ) / 86400 ))
  if [ "$days_old" -gt 7 ]; then
    backup_name=$(echo "$line" | awk '{print $4}')
    aws s3 rm "s3://${R2_BUCKET_NAME}/$backup_name" --endpoint-url="$R2_ENDPOINT"
    echo "[$(date)] Deleted old backup: $backup_name"
  fi
done

echo "[$(date)] Backup completed: db_$DATE.dump"
```

Make executable:
```bash
chmod +x deploy/backup.sh
```

### Step 4: Test Backup Script

```bash
# Run manually to verify
./deploy/backup.sh

# Check R2 bucket for uploaded file
aws s3 ls s3://wedding-backups/ --endpoint-url=https://<account-id>.r2.cloudflarestorage.com
```

### Step 5: Setup Cron Job

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 2:00 AM):
0 2 * * * /home/bvd/Projects/wedding/site/deploy/backup.sh >> /var/log/backup.log 2>&1
```

---

## Restore from Backup

To restore a backup:

```bash
# Download from R2
aws s3 cp "s3://wedding-backups/db_YYYYMMDD_HHMMSS.dump" /tmp/restore.dump \
  --endpoint-url="$R2_ENDPOINT"

# Restore to database
docker exec -i wedding_db pg_restore -U postgres -d wedding_rsvp < /tmp/restore.dump

# Clean up
rm /tmp/restore.dump
```

---

## Files

| File | Description |
|------|-------------|
| `deploy/backup.sh` | Backup script |
| `.env.prod` | Environment variables (add R2 credentials) |
| `/var/log/backup.log` | Backup logs (created by cron) |

---

## Monitoring

- Check cron logs: `grep CRON /var/log/syslog`
- Check backup logs: `tail -f /var/log/backup.log`
- Monitor R2 bucket for daily uploads
