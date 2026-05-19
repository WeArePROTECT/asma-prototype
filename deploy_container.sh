#!/bin/bash
# Deployment script for ASMA prototype container
# Ensures all required volume mounts and environment variables are set

set -e

IMAGE_NAME="${1:-localhost/asma-prototype:main-latest}"
CONTAINER_NAME="${2:-asma-proto-v10}"
PORT="${3:-8765}"

echo "Deploying ASMA prototype container..."
echo "  Image: $IMAGE_NAME"
echo "  Container: $CONTAINER_NAME"
echo "  Port: $PORT"

# Stop and remove existing container if it exists
if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping existing container..."
    podman stop "$CONTAINER_NAME" || true
    podman rm "$CONTAINER_NAME" || true
fi

# Start new container with all required configuration
echo "Starting container with required volume mounts and environment variables..."
podman run -d \
  --name "$CONTAINER_NAME" \
  -p "${PORT}:5000" \
  -v /opt/shared/spencerlong/asma-prototype/real_data:/app/real_data:ro \
  -v /usr2/people/alex.styer/public_html:/app/alex_public_html:ro \
  -e ASMA_DATA_DIR=/app/real_data \
  -e ALEX_PUBLIC_HTML_DIR=/app/alex_public_html \
  --restart unless-stopped \
  "$IMAGE_NAME"

echo ""
echo "Container started. Checking logs for configuration warnings..."
sleep 2
podman logs "$CONTAINER_NAME" | grep -E "(WARNING|ASMA|taxonomy)" | tail -10

echo ""
echo "✅ Deployment complete!"
echo "Check container status: podman ps --filter name=$CONTAINER_NAME"
echo "View logs: podman logs -f $CONTAINER_NAME"

