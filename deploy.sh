#!/bin/bash

set -e

# Configuration
IMAGE_NAME="documentation-scraper-app"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NEW_TAG="${IMAGE_NAME}:${TIMESTAMP}"
OLD_TAG="${IMAGE_NAME}:latest"
NETWORK="documentation-scraper_app_network"
NEW_PORT=8001
DRAIN_TIME=60  # seconds

# Add deploy key to ssh agent
eval "$(ssh-agent -s)"
ssh-add /root/.ssh/scraper

echo "🚀 Starting deployment..."

# Pull latest code
echo "📥 Pulling latest code..."
git pull

# Build new image
echo "🔨 Building new image: $NEW_TAG"
docker build -t "$NEW_TAG" .

# Ensure Caddy is running (creates network)
if ! docker ps -q -f ancestor=caddy:2 | grep -q .; then
    echo "🏁 Starting Caddy..."
    docker network rm "$NETWORK" || true
    docker compose up -d caddy
fi

# Start new container
echo "▶️  Starting new container"
NEW_CONTAINER_ID=$(docker run -d --network "$NETWORK" --env-file .env -v "$(pwd)/data:/app/data" "$NEW_TAG")

# Get new container IP
NEW_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$NEW_CONTAINER_ID")
echo "📍 New container IP: $NEW_IP"

# Wait for health check
echo "🏥 Waiting for new container to be healthy..."
for i in {1..30}; do
    if curl -f "http://$NEW_IP:8000/health" > /dev/null 2>&1; then
        echo "✅ New container is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ New container failed health check"
        docker stop "$NEW_CONTAINER_ID"
        docker rm "$NEW_CONTAINER_ID"
        exit 1
    fi
    sleep 5
done

# Update Caddyfile to point to new IP
echo "🔄 Updating Caddyfile to new IP"
sed -i "s/reverse_proxy .*/reverse_proxy $NEW_IP:8000/" Caddyfile

# Reload Caddy
echo "🔄 Reloading Caddy"
docker exec documentation-scraper_caddy_1 caddy reload

# Wait for drain
echo "⏳ Waiting $DRAIN_TIME seconds for old container to drain..."
sleep $DRAIN_TIME

# Stop old container if exists
OLD_CONTAINER_ID=$(docker ps -q -f ancestor="$OLD_TAG" | head -n1)
if [ -n "$OLD_CONTAINER_ID" ]; then
    echo "🛑 Stopping old container"
    docker stop "$OLD_CONTAINER_ID"
    docker rm "$OLD_CONTAINER_ID"
fi

# Tag new as latest
echo "🏷️  Tagging new image as latest"
docker tag "$NEW_TAG" "$OLD_TAG"

# Clean up old images (optional)
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"