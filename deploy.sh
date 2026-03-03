#!/bin/bash

set -e

# Add deploy key to ssh agent
eval "$(ssh-agent -s)"
ssh-add /root/.ssh/scraper

# Get secret from .env
SCRAPER_SECRET=$(grep SCRAPER_SECRET .env | cut -d '=' -f2)

echo "🚀 Starting deployment..."

# Pull latest code
echo "📥 Pulling latest code..."
git pull

# Build new app image
echo "🔨 Building new app image..."
# Keep supply-chain attestations enabled (SBOM + provenance), but avoid
# the Compose metadata temp-file path that can fail on some VPS hosts.
APP_IMAGE=$(docker compose config --images | grep -m1 -E '(^|-)app$')
docker buildx build \
  --platform linux/amd64 \
  --pull \
  --provenance=true \
  --sbom=true \
  --tag "${APP_IMAGE}:latest" \
  --load \
  .

# Scale up to 8 replicas (4 old + 4 new) for zero downtime
echo "🔄 Scaling up to 8 app instances"
docker compose up --scale app=8 -d --no-build

# Wait for all app containers to be healthy
echo "⏳ Waiting for all app containers to be healthy..."
until [ $(docker compose ps app | grep -c "healthy") -eq 8 ]; do
  echo "Waiting for health checks..."
  sleep 10
done
echo "✅ All app containers are healthy"

# Scale down to 4 replicas (remove old ones)
echo "🔄 Scaling down to 4 app instances"
docker compose up --scale app=4 -d --no-deps --no-build app

# Clean up old images (optional)
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"
