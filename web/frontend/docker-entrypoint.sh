#!/bin/sh
# Runtime env injection for frontend container.
# Allows configuring the API URL at container startup rather than build time.

set -e

API_URL="${API_URL:-/api/v1}"
echo "window.ENV = { API_URL: '${API_URL}' };" > /usr/share/nginx/html/env.js

echo "Frontend starting with API_URL: ${API_URL}"

# Inject Docker's internal DNS resolver into nginx config so variable-based
# proxy_pass can resolve the backend hostname at request time.
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
  echo "Waiting for backend (http://backend:8000) to be available..."
  for i in $(seq 1 30); do
    if curl -sf http://backend:8000/health >/dev/null 2>&1; then
      echo "Backend is up."
      break
    fi
    sleep 1
  done
fi

exec nginx -g 'daemon off;'
