#!/bin/bash
# This script runs before the application is deployed

echo "Starting predeploy hook script..."

# Remove any existing Elastic Beanstalk Nginx configuration to prevent conflicts
if [ -d "/etc/nginx/conf.d/elasticbeanstalk" ]; then
  echo "Removing existing Elastic Beanstalk Nginx configurations"
  sudo rm -rf /etc/nginx/conf.d/elasticbeanstalk/*.conf
fi

# Create a marker file to indicate our hook ran successfully
echo "$(date) - Predeploy hook executed successfully" > /tmp/eb_nginx_predeploy_success

echo "Predeploy hook completed"
exit 0