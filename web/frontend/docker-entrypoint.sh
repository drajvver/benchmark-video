#!/bin/sh
# Runtime env injection for frontend container.
# Allows configuring the API URL at container startup rather than build time.
#
# Environment variables:
#   API_URL        - Where the frontend JS calls the API (default: /api/v1)
#   BACKEND_HOST   - Hostname nginx proxies /api/ to (default: backend)

set -e

API_URL="${API_URL:-/api/v1}"
BACKEND_HOST="${BACKEND_HOST:-backend}"

# Generate env.js for runtime frontend config
echo "window.ENV = { API_URL: '${API_URL}' };" > /usr/share/nginx/html/env.js
echo "Frontend starting with API_URL: ${API_URL}, BACKEND_HOST: ${BACKEND_HOST}"

# Substitute backend host in nginx config
sed -i "s|__BACKEND_HOST__|${BACKEND_HOST}|g" /etc/nginx/conf.d/default.conf

# Inject Docker's internal DNS resolver into nginx config so variable-based
# proxy_pass can resolve hostnames at request time.
NAMESERVER=$(awk '/^nameserver/ {print $2; exit}' /etc/resolv.conf)
if [ -n "$NAMESERVER" ]; then
    sed -i "s|__NAMESERVER__|${NAMESERVER}|g" /etc/nginx/conf.d/default.conf
    echo "Using DNS resolver: ${NAMESERVER}"
else
    echo "WARNING: Could not find nameserver in /etc/resolv.conf"
fi

# If proxying to an internal backend service, wait for it to be reachable
# so the first API requests don't fail.
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

exec nginx -g 'daemon off;'
