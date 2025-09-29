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

# Build and deploy with docker compose (scale to 2 for zero downtime)
echo "🚀 Building and deploying with docker compose"
docker compose up --scale app=2 --build -d

# Scale down to 1 (Docker waits for healthcheck automatically)
echo "🔄 Scaling down to 1 app instance"
docker compose up --scale app=1 -d

# Clean up old images (optional)
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"