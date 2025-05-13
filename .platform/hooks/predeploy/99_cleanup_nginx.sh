#!/bin/bash

# Ensure staging proxy directory exists, then clear it
mkdir -p /var/proxy/staging/nginx/conf.d
rm -rf /var/proxy/staging/nginx/conf.d/*
# Remove any legacy EB application-specific configs
rm -rf /var/proxy/staging/nginx/conf.d/elasticbeanstalk*

# Write WebSocket and type settings into staging
cat > /var/proxy/staging/nginx/conf.d/websocket.conf << 'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
types_hash_max_size 2048;
types_hash_bucket_size 128;
EOF

# Write Streamlit proxy configuration into staging
cat > /var/proxy/staging/nginx/conf.d/01_streamlit.conf << 'EOF'
upstream streamlit_app {
  server 127.0.0.1:8000;
  keepalive 256;
}
server {
  listen 80;

  location / {
    proxy_pass http://streamlit_app;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
  }

  location /_stcore/stream {
    proxy_pass http://streamlit_app;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
    proxy_buffering off;
    proxy_cache off;
  }
}
EOF

exit 0