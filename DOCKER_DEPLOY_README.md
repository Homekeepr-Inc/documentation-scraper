# Docker Deployment Guide

This guide explains how to deploy the documentation scraper using Docker Compose with zero-downtime updates.

## Prerequisites
- Docker and Docker Compose installed
- Git repository with deploy key set up for `git pull`

## Initial Setup
1. Clone the repository and navigate to the directory.
2. Update `.env` with your actual secrets (e.g., `SCRAPER_SECRET`).
3. Start Caddy reverse proxy:
   ```
   docker-compose up -d caddy
   ```
4. Run the initial deployment:
   ```
   ./deploy.sh
   ```
   This will build the image, start the app container, and configure Caddy to proxy traffic to it.

## Zero-Downtime Deployment
To deploy updates:
1. Ensure you're on the main branch.
2. Run:
   ```
   ./deploy.sh
   ```
   The script will:
   - Pull latest code
   - Build new image
   - Start new app container
   - Wait for health check
   - Switch Caddy to route traffic to new container
   - Wait 60 seconds for old container to drain
   - Stop old container
   - Clean up

## Accessing the App
- Web UI: http://localhost
- API: http://localhost/documents, etc.

## Troubleshooting
- If deployment fails, check logs: `docker logs <container_id>`
- To rollback, run `./deploy.sh` with the previous image tag (modify script temporarily).
- Ensure `.env` has correct secrets.

## Notes
- Scraping jobs are queued to prevent multiple instances.
- Temp files are ephemeral in containers.
- Persistent data (DB, files) is in `./data` volume.