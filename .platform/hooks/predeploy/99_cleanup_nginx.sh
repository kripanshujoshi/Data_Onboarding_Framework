#!/bin/bash
# This runs before deployment to clear old Nginx configs and write new WebSocket config
rm -rf /etc/nginx/conf.d/*

# Write WebSocket header mapping and type settings
cat > /etc/nginx/conf.d/websocket.conf << 'EOF'
# Map upgrade headers for WebSocket
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
# Increase types hash sizes to avoid warnings
types_hash_max_size 2048;
types_hash_bucket_size 128;
EOF

# Write Streamlit proxy configuration
cat > /etc/nginx/conf.d/01_streamlit.conf << 'EOF'
upstream streamlit_app {
  server 127.0.0.1:8000;
  keepalive 256;
}
server {
  listen 80;
  proxy_http_version 1.1;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;

  location / {
    proxy_pass http://streamlit_app;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_read_timeout 86400;
  }

  location /_stcore/stream {
    proxy_pass http://streamlit_app;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_read_timeout 86400;
    proxy_buffering off;
    proxy_cache off;
  }
}
EOF

exit 0