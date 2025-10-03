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

# Scale to 4 replicas for production
echo "🔄 Scaling to 4 app instances"
docker compose up --scale app=4 -d

# Clean up old images (optional)
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"