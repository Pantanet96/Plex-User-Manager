# Docker Deployment Guide

This guide explains how to deploy Plex User Manager using Docker.

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Pantanet96/Plex-User-Manager.git
   cd Plex-User-Manager
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file** with your configuration
   ```bash
   nano .env  # or use your preferred editor
   ```

4. **Start the container**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - Open browser: `http://localhost:5000`
   - Login: `admin` / `admin`
   - **Change the password immediately!**

## Environment Variables

### Required Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me-in-production` | Flask secret key (MUST change for production) |
| `SERVER_PORT` | `5000` | Port the server listens on |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HTTPS_ENABLED` | `false` | Enable HTTPS |
| `PLEX_URL` | - | Plex server URL (can be set via UI) |
| `PLEX_TOKEN` | - | Plex authentication token (can be set via UI) |
| `SCHEDULER_TYPE` | `interval` | Scheduler type: `interval` or `daily` |
| `SCHEDULER_INTERVAL_MINUTES` | `60` | Minutes between scheduler runs (5-1440) |
| `SCHEDULER_DAILY_TIME` | `03:00` | Daily execution time (HH:MM format) |
| `TZ` | `Europe/Rome` | Timezone for scheduler and logs |

## Persistent Data

The following directories are mounted as volumes to persist data across container restarts:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data/instance` | `/app/instance` | SQLite database |
| `./data/certs` | `/app/certs` | SSL certificates |
| `./data/logs` | `/app/logs` | Application logs |

**Important**: These directories will be created automatically on first run.

## Docker Commands

### Start the container
```bash
docker-compose up -d
```

### Stop the container
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Restart the container
```bash
docker-compose restart
```

### Rebuild the image
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Update to latest version
```bash
git pull
docker-compose build
docker-compose up -d
```

## HTTPS Configuration

### Using Self-Signed Certificates

1. Enable HTTPS in `.env`:
   ```env
   HTTPS_ENABLED=true
   ```

2. Restart container:
   ```bash
   docker-compose restart
   ```

3. Certificates will be auto-generated in `./data/certs/`

### Using Custom Certificates

1. Place your certificates in `./data/certs/`:
   - `server.crt` - Certificate file
   - `server.key` - Private key file

2. Enable HTTPS in `.env`:
   ```env
   HTTPS_ENABLED=true
   ```

3. Restart container:
   ```bash
   docker-compose restart
   ```

## Port Configuration

To change the port, edit `.env`:
```env
SERVER_PORT=8080
```

Then update `docker-compose.yml` ports mapping:
```yaml
ports:
  - "8080:8080"
```

Restart the container:
```bash
docker-compose up -d
```

## Backup and Restore

### Backup

```bash
# Backup database
cp ./data/instance/plex_manager.db ./backup/plex_manager_$(date +%Y%m%d).db

# Backup entire data directory
tar -czf plex-manager-backup-$(date +%Y%m%d).tar.gz ./data
```

### Restore

```bash
# Stop container
docker-compose down

# Restore database
cp ./backup/plex_manager_YYYYMMDD.db ./data/instance/plex_manager.db

# Or restore entire data directory
tar -xzf plex-manager-backup-YYYYMMDD.tar.gz

# Start container
docker-compose up -d
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs
```

### Permission issues

Fix ownership:
```bash
sudo chown -R 1000:1000 ./data
```

### Database locked

Stop container and check for stale lock files:
```bash
docker-compose down
rm ./data/instance/*.db-journal
docker-compose up -d
```

### Reset to defaults

```bash
docker-compose down
rm -rf ./data
docker-compose up -d
```

## Resource Limits

To limit container resources, uncomment the `deploy` section in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## Health Checks

The container includes a health check that runs every 30 seconds. Check status:

```bash
docker ps
```

Look for `healthy` in the STATUS column.

## Security Recommendations

1. **Change SECRET_KEY**: Generate a secure random key
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Change default password**: Login and change admin password immediately

3. **Use HTTPS**: Enable HTTPS for production deployments

4. **Firewall**: Restrict access to the port using firewall rules

5. **Regular updates**: Keep the container image updated
   ```bash
   git pull && docker-compose build && docker-compose up -d
   ```

## Docker Hub (Coming Soon)

Pre-built images will be available on Docker Hub:
```bash
docker pull pantanet96/plex-user-manager:latest
```
