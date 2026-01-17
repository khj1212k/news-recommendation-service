#!/bin/sh
set -e

docker compose up -d --build

echo "Waiting for services..."
sleep 15

BACKEND_PORT="${BACKEND_PORT:-8000}"
BACKEND_URL="http://localhost:${BACKEND_PORT}"
for attempt in 1 2 3; do
  if docker compose exec airflow airflow dags trigger news_pipeline_daily_4x; then
    break
  fi
  sleep 5
done

echo "Waiting for backend..."
for _ in $(seq 1 30); do
  if curl -sf "${BACKEND_URL}/health" >/dev/null; then
    break
  fi
  sleep 2
done
if ! curl -sf "${BACKEND_URL}/health" >/dev/null; then
  echo "backend not ready at ${BACKEND_URL}" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN=python
fi
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "python not found (set PYTHON_BIN or install python3)" >&2
  exit 1
fi
AUTH_PAYLOAD='{"email": "user@example.com", "password": "strongpassword"}'
SIGNUP_STATUS=$(curl -s -o /tmp/signup.json -w "%{http_code}" \
  -X POST "http://localhost:${BACKEND_PORT}/auth/signup" \
  -H 'Content-Type: application/json' \
  -d "${AUTH_PAYLOAD}")
if [ "${SIGNUP_STATUS}" -eq 200 ]; then
  TOKEN=$("${PYTHON_BIN}" -c "import json; print(json.load(open('/tmp/signup.json'))['access_token'])")
else
  LOGIN_STATUS=$(curl -s -o /tmp/login.json -w "%{http_code}" \
    -X POST "http://localhost:${BACKEND_PORT}/auth/login" \
    -H 'Content-Type: application/json' \
    -d "${AUTH_PAYLOAD}")
  if [ "${LOGIN_STATUS}" -ne 200 ]; then
    echo "auth failed (signup ${SIGNUP_STATUS}, login ${LOGIN_STATUS})" >&2
    cat /tmp/signup.json /tmp/login.json >&2 || true
    exit 1
  fi
  TOKEN=$("${PYTHON_BIN}" -c "import json; print(json.load(open('/tmp/login.json'))['access_token'])")
fi

curl -s "http://localhost:${BACKEND_PORT}/feed" -H "Authorization: Bearer ${TOKEN}" | head -c 300

echo "\nIntegration test completed."
