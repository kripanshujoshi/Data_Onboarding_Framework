#!/bin/bash
# This script runs after the application is deployed

echo "Starting postdeploy hook script..."

# Restart Nginx to apply our custom configuration
if [ -f "/etc/init.d/nginx" ]; then
  echo "Restarting Nginx service"
  sudo /etc/init.d/nginx restart || sudo service nginx restart || sudo systemctl restart nginx
fi

# Create a marker file to indicate our hook ran successfully
echo "$(date) - Postdeploy hook executed successfully" > /tmp/eb_nginx_postdeploy_success

echo "Postdeploy hook completed"
exit 0