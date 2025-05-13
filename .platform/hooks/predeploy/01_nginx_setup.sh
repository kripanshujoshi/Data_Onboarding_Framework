#!/bin/bash
# This script runs before the application is deployed

echo "Starting predeploy hook script..."

# Remove any existing Elastic Beanstalk Nginx configurations to prevent conflicts
if [ -d "/etc/nginx/conf.d/elasticbeanstalk" ]; then
  echo "Removing existing Elastic Beanstalk Nginx configurations"
  sudo rm -rf /etc/nginx/conf.d/elasticbeanstalk/*.conf
fi

# Create a temporary Nginx server block that includes our location configs
cat > /tmp/nginx_server_block.conf << 'EOF'
server {
  listen 80;
  
  # Include our Streamlit location configurations
  include /tmp/streamlit_location.conf;
}
EOF

# Add this server block to the Elastic Beanstalk configuration directory
if [ -d "/etc/nginx/conf.d/elasticbeanstalk" ]; then
  echo "Adding Streamlit server configuration to Elastic Beanstalk Nginx"
  sudo cp /tmp/nginx_server_block.conf /etc/nginx/conf.d/elasticbeanstalk/00_streamlit_app.conf
fi

# Create a marker file to indicate our hook ran successfully
echo "$(date) - Predeploy hook executed successfully" > /tmp/eb_nginx_predeploy_success

echo "Predeploy hook completed"
exit 0