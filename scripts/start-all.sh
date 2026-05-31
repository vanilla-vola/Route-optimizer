#!/usr/bin/env bash
# Start Route Optimizer: API + web UI + Android emulator + Flutter app
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FLUTTER="${FLUTTER:-$HOME/Desktop/flutter_sdk/bin/flutter}"
ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"

echo "==> Starting backend API on http://0.0.0.0:8000"
cd "$ROOT"
source .venv/bin/activate
cd backend
if lsof -i :8000 >/dev/null 2>&1; then
  echo "    (port 8000 already in use — skipping)"
else
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
  echo $! > /tmp/route-optimizer-api.pid
fi

echo "==> Starting web UI on http://localhost:5173"
cd "$ROOT/frontend"
if lsof -i :5173 >/dev/null 2>&1; then
  echo "    (port 5173 already in use — skipping)"
else
  npm run dev &
  echo $! > /tmp/route-optimizer-web.pid
fi

echo "==> Launching Android emulator (Medium_Phone)"
export PATH="$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools"
if ! adb devices | grep -q emulator; then
  "$ANDROID_HOME/emulator/emulator" -avd Medium_Phone &
fi

echo "==> Waiting for emulator..."
adb wait-for-device
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do
  sleep 2
done
echo "    Emulator ready."

echo "==> Running Flutter app on Android"
cd "$ROOT/mobile"
"$FLUTTER" pub get
"$FLUTTER" run -d emulator-5554
