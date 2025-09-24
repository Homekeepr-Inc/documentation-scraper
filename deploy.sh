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

# Wait for health check
echo "🏥 Waiting for app to be healthy..."
for i in {1..30}; do
    if curl -f -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost/health > /dev/null 2>&1; then
        echo "✅ App is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ App failed health check"
        exit 1
    fi
    sleep 5
done

# Scale down to 1
echo "🔄 Scaling down to 1 app instance"
docker compose up --scale app=1 -d

# Clean up old images (optional)
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"