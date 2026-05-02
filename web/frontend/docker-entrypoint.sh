#!/bin/sh
# Runtime env injection for frontend container.
#
# Environment variables:
#   API_URL        - Where the frontend JS calls the API (default: /api/v1)
#   BACKEND_HOST   - Hostname/IP nginx proxies /api/ to (default: backend)

set -e

API_URL="${API_URL:-/api/v1}"
BACKEND_HOST="${BACKEND_HOST:-backend}"

echo "Frontend starting with API_URL: ${API_URL}, BACKEND_HOST: ${BACKEND_HOST}"

# Generate env.js for runtime frontend JS config
if ! echo "window.ENV = { API_URL: '${API_URL}' };" > /usr/share/nginx/html/env.js 2>/dev/null; then
    echo "WARNING: Could not write env.js (read-only filesystem?)"
fi

# Determine if BACKEND_HOST is an IP address or localhost.
# IP addresses and localhost don't need DNS resolution — they use /etc/hosts.
# Hostnames like 'backend' need the resolver + variable-based proxy_pass.
IS_IP_OR_LOCALHOST=false
if echo "$BACKEND_HOST" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    IS_IP_OR_LOCALHOST=true
elif [ "$BACKEND_HOST" = "localhost" ] || [ "$BACKEND_HOST" = "127.0.0.1" ]; then
    IS_IP_OR_LOCALHOST=true
fi

if [ "$IS_IP_OR_LOCALHOST" = "true" ]; then
    # Literal proxy_pass — resolves via /etc/hosts at startup, no resolver needed
    cat > /etc/nginx/conf.d/default.conf <<EOF
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://${BACKEND_HOST}:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    echo "Using literal proxy_pass to ${BACKEND_HOST}:8000 (no DNS resolver)"
else
    # Variable-based proxy_pass with DNS resolver for hostname-based backends
    NAMESERVER=$(awk '/^nameserver/ {print $2; exit}' /etc/resolv.conf)
    if [ -n "$NAMESERVER" ]; then
        sed -i "s|__NAMESERVER__|${NAMESERVER}|g" /etc/nginx/conf.d/default.conf
        echo "Using DNS resolver: ${NAMESERVER}"
    else
        echo "WARNING: Could not find nameserver in /etc/resolv.conf"
    fi
    sed -i "s|__BACKEND_HOST__|${BACKEND_HOST}|g" /etc/nginx/conf.d/default.conf

    # Wait for backend health if proxying internally
    if echo "$API_URL" | grep -qE '^/api'; then
      echo "Waiting for backend (http://${BACKEND_HOST}:8000) to be available..."
      for i in $(seq 1 30); do
        if curl -sf "http://${BACKEND_HOST}:8000/health" >/dev/null 2>&1; then
          echo "Backend is up."
          break
        fi
        sleep 1
      done
    fi
fi

exec nginx -g 'daemon off;'
