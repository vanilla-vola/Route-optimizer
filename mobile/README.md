# Route Optimizer

Multi-stop route optimization (Traveling Salesperson Problem) with a **FastAPI** backend (OR-Tools + Mapbox or haversine fallback), a **Flutter** mobile app, and a **React** web UI.

## Project structure

```
route-optimizer/
├── backend/          # FastAPI + OR-Tools API
├── mobile/           # Flutter app (Android Studio / Xcode)
│   ├── android/
│   ├── ios/
│   └── lib/
├── frontend/         # React + Leaflet web UI
└── README.md
```

## Prerequisites

- Python 3.9+
- Flutter SDK 3.10+ (for mobile)
- Node.js 18+ (for web UI, optional)
- Android Studio and/or Xcode (for mobile emulators)

## Setup

### Backend

```bash
cd /Users/suhani_garate/Desktop/route-optimizer
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Edit `backend/.env` — set `USE_HAVERSINE=true` for offline testing, or add `MAPBOX_ACCESS_TOKEN` for real road distances.

### Mobile

```bash
cd mobile
flutter pub get
```

## Run

### 1. Start the API (required for mobile & web)

```bash
cd /Users/suhani_garate/Desktop/route-optimizer
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Use `--host 0.0.0.0` so physical devices on your Wi‑Fi can reach the API.

### 2. Mobile app (Flutter)

**Option A — Android Studio**

1. Open Android Studio → **Open** → select the `mobile/` folder
2. Wait for Gradle sync
3. Start an Android emulator (Device Manager)
4. Click **Run** ▶

**Option B — CLI**

```bash
cd mobile
flutter run
```

**API URL by device**

| Device | Default API URL |
|--------|-----------------|
| Android emulator | `http://10.0.2.2:8000` |
| iOS simulator | `http://127.0.0.1:8000` |
| Physical phone | Your computer's LAN IP, e.g. `http://192.168.1.10:8000` |

For a physical device:

```bash
flutter run --dart-define=API_BASE=http://YOUR_LAN_IP:8000
```

### 3. Web UI (optional)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Mobile app features

- Tap map to add stops
- Optimize route via backend API
- View ordered stop list and route polyline
- Toggle round-trip vs one-way
- OpenStreetMap tiles (no Mapbox token required on device)

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/optimize-route` | Optimize stop order |

## Notes

- Maximum **25 stops** (Mapbox matrix limit); configurable via `MAX_STOPS`.
- Android cleartext HTTP is enabled for local dev (`usesCleartextTraffic`).
