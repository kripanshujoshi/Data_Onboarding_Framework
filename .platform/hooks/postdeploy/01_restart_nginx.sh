#!/bin/bash
# This script runs after the application is deployed

echo "Starting postdeploy hook script..."

# Restart Nginx to apply our WebSocket configuration
sudo service nginx restart

echo "Postdeploy hook completed"
exit 0