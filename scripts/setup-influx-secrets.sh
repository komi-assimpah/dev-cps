#!/usr/bin/env bash
set -euo pipefail

SECRETS_DIR="/home/louis"
USER_FILE="$SECRETS_DIR/.env.influxdb2-admin-username"
PASS_FILE="$SECRETS_DIR/.env.influxdb2-admin-password"
TOKEN_FILE="$SECRETS_DIR/.env.influxdb2-admin-token"

# Generate safe defaults if not present
if [[ ! -f "$USER_FILE" ]]; then
  echo "admin" > "$USER_FILE"
  echo "Created $USER_FILE"
else
  echo "Found $USER_FILE"
fi

if [[ ! -f "$PASS_FILE" ]]; then
  # 20-char random password
  head -c 32 /dev/urandom | base64 | tr -d '\n' | head -c 20 > "$PASS_FILE"
  echo "Created $PASS_FILE"
else
  echo "Found $PASS_FILE"
fi

if [[ ! -f "$TOKEN_FILE" ]]; then
  # 48-char random token
  head -c 64 /dev/urandom | base64 | tr -d '\n' | head -c 48 > "$TOKEN_FILE"
  echo "Created $TOKEN_FILE"
else
  echo "Found $TOKEN_FILE"
fi

chmod 600 "$USER_FILE" "$PASS_FILE" "$TOKEN_FILE"

echo "Secrets ready:"
echo "  username: $USER_FILE"
echo "  password: $PASS_FILE"
echo "  token:    $TOKEN_FILE"
