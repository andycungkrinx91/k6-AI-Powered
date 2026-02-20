#!/usr/bin/env bash
set -u

print_check() {
  local label="$1"
  local url="$2"
  local code

  code="$(curl -sS -L --max-time 20 -o /dev/null -w "%{http_code}" "$url" || true)"
  if [ -z "$code" ]; then
    code="000"
  fi

  printf "%-48s %s\n" "$label" "$code"
}

echo "== Smoke checks =="
echo "Note: cf-tunnel localhost workaround requires Linux host networking (network_mode: host)."
print_check "Local frontend (http://localhost:3000)" "http://localhost:3000"
print_check "Frontend proxy -> backend (/api/backend/api/captcha)" "http://localhost:3000/api/backend/api/captcha"
print_check "Public domain (https://k6.liveplay.me)" "https://k6.liveplay.me"

echo
echo "== Cloudflare tunnel config (latest) =="
updated_line="$(docker compose logs --no-color cf-tunnel 2>/dev/null | grep "Updated to new configuration" | tail -n 1 || true)"

if [ -n "$updated_line" ]; then
  printf "%s\n" "$updated_line"
else
  echo "No 'Updated to new configuration' log line found for cf-tunnel."
fi

if printf "%s" "$updated_line" | grep -q "http://localhost"; then
  echo
  echo "Cloudflare dashboard still points this remote-managed tunnel to localhost."
  echo "Update tunnel ingress services in Cloudflare Zero Trust -> Networks -> Tunnels -> Public Hostnames:"
  echo "- k6.liveplay.me -> http://frontend:3000"
  echo "- backend-test.liveplay.me -> http://backend:8000"
  echo "Then restart connector: docker compose restart cf-tunnel"
fi
