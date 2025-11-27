# Docker Deployment Guide

This guide explains how to deploy Plex User Manager using Docker.

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Pantanet96/Plex-User-Manager.git
   cd Plex-User-Manager
   ```

2. **Copy configuration templates**
   ```bash
   cp docker-compose.example.yml docker-compose.yml
   cp .env.example .env
   ```

3. **Edit configuration files**
   ```bash
   nano .env  # Edit with your settings
   nano docker-compose.yml  # Optional: customize volumes, ports, network mode
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

### Flask & Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me-in-production` | Flask secret key for session encryption. **MUST change for production!** Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SERVER_PORT` | `5000` | Port the server listens on inside the container |
| `FLASK_APP` | `app.py` | Flask application entry point (usually no need to change) |

### HTTPS Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HTTPS_ENABLED` | `false` | Enable HTTPS (`true` or `false`) |

### Plex Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PLEX_URL` | - | Plex server URL (e.g., `http://192.168.1.100:32400`). Can also be set via web UI |
| `PLEX_TOKEN` | - | Plex authentication token. Can also be set via web UI. [How to find your token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) |

### Scheduler Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SCHEDULER_TYPE` | `interval` | Scheduler execution type: `interval` (periodic) or `daily` (once per day) |
| `SCHEDULER_INTERVAL_MINUTES` | `60` | Minutes between scheduler runs when using `interval` type (range: 5-1440) |
| `SCHEDULER_DAILY_TIME` | `03:00` | Daily execution time when using `daily` type (24-hour format: HH:MM) |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `/app/instance/plex_manager.db` | Full path to SQLite database file inside container |

### System Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `Europe/Rome` | Timezone for scheduler and logs (e.g., `America/New_York`, `Asia/Tokyo`) |
| `PYTHONUNBUFFERED` | `1` | Python output buffering (keep as `1` for real-time logs) |

## Persistent Data

The following directories should be mounted as volumes to persist data across container restarts:

| Host Path | Container Path | Purpose | Required |
|-----------|----------------|---------|----------|
| `./data/instance` | `/app/instance` | SQLite database | **Yes** |
| `./data/certs` | `/app/certs` | SSL certificates (self-signed and custom) | Recommended |
| `./data/logs` | `/app/logs` | Application logs (app.log, error.log) | Optional |

**Important**: These directories will be created automatically on first run.

## Deployment Methods

### Method 1: Docker Compose (Recommended)

This is the easiest method with all configurations in one place.

1. **Create environment file**:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your settings
   ```

2. **Start the container**:
   ```bash
   docker-compose up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f
   ```

### Method 2: Docker Run

For manual control or custom setups.

**Basic usage**:
```bash
docker run -d \
  --name plex-user-manager \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /path/to/data/instance:/app/instance \
  -v /path/to/data/certs:/app/certs \
  -v /path/to/data/logs:/app/logs \
  -e SECRET_KEY=your-secret-key-here \
  -e TZ=Europe/Rome \
  plex-user-manager
```

**Windows example**:
```powershell
docker run -d `
  --name plex-user-manager `
  --restart unless-stopped `
  -p 5000:5000 `
  -v "C:/docker/plex-user/instance:/app/instance" `
  -v "C:/docker/plex-user/certs:/app/certs" `
  -v "C:/docker/plex-user/logs:/app/logs" `
  -e SECRET_KEY=your-secret-key-here `
  -e TZ=Europe/Rome `
  plex-user-manager
```

**With all environment variables**:
```bash
docker run -d \
  --name plex-user-manager \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /path/to/data/instance:/app/instance \
  -v /path/to/data/certs:/app/certs \
  -v /path/to/data/logs:/app/logs \
  -e SECRET_KEY=your-secret-key-here \
  -e SERVER_PORT=5000 \
  -e HTTPS_ENABLED=false \
  -e PLEX_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your-plex-token \
  -e SCHEDULER_TYPE=interval \
  -e SCHEDULER_INTERVAL_MINUTES=60 \
  -e TZ=Europe/Rome \
  plex-user-manager
```

## Restart Behavior

### Application Restart Button

When you click the "Restart Server" button in the web UI:
- The application exits with code 1
- Docker will automatically restart the container **only if** you used `--restart` policy or docker-compose with `restart: unless-stopped`

**Important**: If you use `docker run` with `--rm` flag, the container will be **removed** instead of restarted. Remove `--rm` if you want automatic restarts.

### Restart Policies

| Policy | Description |
|--------|-------------|
| `no` | Do not automatically restart (default) |
| `on-failure` | Restart only if container exits with error |
| `always` | Always restart, even after manual stop |
| `unless-stopped` | Always restart unless manually stopped (recommended) |



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
