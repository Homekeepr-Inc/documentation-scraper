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
docker compose build app

# Scale up to 8 replicas (4 old + 4 new) for zero downtime
echo "🔄 Scaling up to 8 app instances"
docker compose up --scale app=8 -d

# Wait for all app containers to be healthy
echo "⏳ Waiting for all app containers to be healthy..."
until [ $(docker compose ps app | grep -c "healthy") -eq 8 ]; do
  echo "Waiting for health checks..."
  sleep 10
done
echo "✅ All app containers are healthy"

# Scale down to 4 replicas (remove old ones)
echo "🔄 Scaling down to 4 app instances"
docker compose up --scale app=4 -d --no-deps app

# Clean up old images (optional)
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"