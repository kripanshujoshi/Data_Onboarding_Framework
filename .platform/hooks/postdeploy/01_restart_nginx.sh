#!/bin/bash
# This script runs after the application is deployed

echo "Starting postdeploy hook script..."

# Stop any existing nginx processes to ensure a clean restart
echo "Stopping Nginx service..."
service nginx stop || true

# Sleep briefly to ensure all processes are terminated
sleep 2

# Start Nginx with the new configuration
echo "Starting Nginx service with new configuration..."
service nginx start

# Check if Nginx is running properly
if service nginx status | grep -q "is running"; then
  echo "Nginx successfully restarted and is running"
else
  echo "ERROR: Nginx failed to start properly. Checking logs..."
  tail -n 20 /var/log/nginx/error.log
  echo "Attempting one more restart..."
  service nginx restart
fi

# Final verification
if service nginx status | grep -q "is running"; then
  echo "Nginx is now running successfully"
else
  echo "CRITICAL ERROR: Nginx could not be started!"
fi

# Verify Nginx is running
if sudo service nginx status | grep -q "running"; then
  echo "Nginx successfully restarted and is running"
else
  echo "Warning: Nginx may not have restarted properly"
fi

echo "Postdeploy hook completed"
exit 0