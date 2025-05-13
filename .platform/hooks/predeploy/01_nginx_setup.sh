#!/bin/bash
# This script runs before the application is deployed and helps configure Nginx properly

# Ensure the Nginx configuration directory exists
mkdir -p /etc/nginx/conf.d/elasticbeanstalk/

# Backup the problematic configuration file if it exists
if [ -f /etc/nginx/conf.d/elasticbeanstalk/00_application.conf ]; then
  echo "Backing up default Nginx configuration"
  mv /etc/nginx/conf.d/elasticbeanstalk/00_application.conf /etc/nginx/conf.d/elasticbeanstalk/00_application.conf.bak
fi

# Create a basic configuration for Nginx to test if it's valid
echo "Creating test configuration file"
cat > /tmp/nginx_test.conf << 'EOF'
server {
  listen 80;
  location / {
    proxy_pass http://127.0.0.1:8000;
  }
}
EOF

# Test if Nginx can start with the test configuration
echo "Testing Nginx configuration"
nginx -t -c /tmp/nginx_test.conf || echo "Nginx test failed but continuing"

echo "Predeploy hook completed"
exit 0