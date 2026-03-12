#!/bin/bash
set -e

BACKUP_DIR="$(dirname "$0")/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

source .env.prod

docker exec wedding_db pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f "$BACKUP_FILE"

gzip "$BACKUP_FILE"

echo "Backup created: ${BACKUP_FILE}.gz"
