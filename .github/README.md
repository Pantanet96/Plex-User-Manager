# GitHub Actions Setup

This repository uses GitHub Actions to automatically build and publish Docker images.

## Required Secrets

You need to configure the following secrets in your GitHub repository:

### 1. Docker Hub Secrets

Go to: `https://github.com/Pantanet96/Plex-User-Manager/settings/secrets/actions`

Add these secrets:

- **DOCKERHUB_USERNAME**: Your Docker Hub username (e.g., `pantanet96`)
- **DOCKERHUB_TOKEN**: Docker Hub Access Token
  - Create at: https://hub.docker.com/settings/security
  - Click "New Access Token"
  - Description: "GitHub Actions"
  - Permissions: "Read, Write, Delete"
  - Copy the token and save it as secret

### 2. GitHub Token (Automatic)

- **GITHUB_TOKEN**: Automatically provided by GitHub Actions
  - No configuration needed
  - Used for GitHub Container Registry (GHCR)

## How It Works

The workflow (`.github/workflows/docker-build.yml`) automatically:

1. **Triggers on**:
   - Push to `main` branch
   - New tags starting with `v` (e.g., `v0.1.0-alpha`)
   - Manual workflow dispatch

2. **Builds**:
   - Multi-platform images (linux/amd64, linux/arm64)
   - Uses Docker Buildx for efficient builds
   - Caches layers for faster subsequent builds

3. **Publishes to**:
   - Docker Hub: `docker.io/pantanet96/plex-user-manager`
   - GitHub Container Registry: `ghcr.io/pantanet96/plex-user-manager`

4. **Tags**:
   - `latest` - Latest build from main branch
   - `v0.1.0-alpha` - Specific version tag
   - `v0.1.0` - Semver version
   - `v0.1` - Minor version
   - `v0` - Major version

## Testing the Workflow

After configuring secrets:

1. **Test with manual trigger**:
   - Go to: https://github.com/Pantanet96/Plex-User-Manager/actions
   - Click "Docker Build and Push"
   - Click "Run workflow"
   - Select branch: `main`
   - Click "Run workflow"

2. **Test with tag**:
   ```bash
   git tag -a v0.1.1-alpha -m "Test release"
   git push origin v0.1.1-alpha
   ```

3. **Check results**:
   - GitHub Actions: https://github.com/Pantanet96/Plex-User-Manager/actions
   - Docker Hub: https://hub.docker.com/r/pantanet96/plex-user-manager
   - GHCR: https://github.com/Pantanet96/plex-user-manager/pkgs/container/plex-user-manager

## Troubleshooting

### Build fails with "unauthorized"
- Check DOCKERHUB_USERNAME and DOCKERHUB_TOKEN secrets
- Verify Docker Hub token has write permissions

### GHCR push fails
- Check repository settings → Actions → General
- Ensure "Read and write permissions" is enabled for GITHUB_TOKEN

### Multi-platform build fails
- This is normal for first build (QEMU setup)
- Retry the workflow

## Workflow Features

- ✅ Multi-platform builds (amd64, arm64)
- ✅ Layer caching for faster builds
- ✅ Automatic tagging based on git tags
- ✅ Publishes to both Docker Hub and GHCR
- ✅ Updates Docker Hub description automatically
- ✅ Supports manual workflow dispatch
