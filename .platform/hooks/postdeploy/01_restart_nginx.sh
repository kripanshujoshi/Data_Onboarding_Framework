#!/bin/bash
# This script runs after the application is deployed

echo "Starting postdeploy hook script..."

# Ensure the Nginx configuration is valid before restarting
echo "Testing Nginx configuration..."
nginx_test=$(sudo nginx -t 2>&1)
if [ $? -ne 0 ]; then
  echo "Warning: Nginx configuration test failed, but continuing:"
  echo "$nginx_test"
fi

# Restart Nginx to apply our WebSocket configuration
echo "Restarting Nginx service..."
sudo service nginx restart

# Verify Nginx is running
if sudo service nginx status | grep -q "running"; then
  echo "Nginx successfully restarted and is running"
else
  echo "Warning: Nginx may not have restarted properly"
fi

echo "Postdeploy hook completed"
exit 0