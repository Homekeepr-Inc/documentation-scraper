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

# Output git hash and first 20 chars of commit message
echo "Git hash: $(git rev-parse HEAD)"
echo "Commit message: $(git log -1 --pretty=%s | cut -c1-20)"

# Scale to 4 replicas for production
echo "🔄 Scaling to 4 app instances"
docker compose up --build --scale app=4 -d

# Clean up old images (optional)
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"