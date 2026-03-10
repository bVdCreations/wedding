# Database Access

## SSH Tunnel

Connect to the production database via an SSH tunnel.

### Prerequisites

- SSH access to the production server
- Database credentials (see `.env.prod` on server)

### Setup

1. Update the tunnel script with your server details:
   ```bash
   nano tunnel.sh
   ```
   Replace `user@your-server-ip` with your actual SSH user and server address.

2. Deploy the database port change to production:
   ```bash
   git push
   ssh user@your-server "cd /path/to/project && docker-compose -f docker-compose.prod.yml up -d db"
   ```

### Connect

```bash
./tunnel.sh
```

In your database client, connect to:
- **Host:** `localhost`
- **Port:** `54320`
- **Database:** Get from `POSTGRES_DB` in `.env.prod`
- **Username:** Get from `POSTGRES_USER` in `.env.prod`
- **Password:** Get from `POSTGRES_PASSWORD` in `.env.prod`

### Get Credentials

```bash
ssh user@your-server "grep POSTGRES_ /path/to/.env.prod"
```