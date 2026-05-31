# Route Optimizer

Multi-stop route optimization (Traveling Salesperson Problem) with a **FastAPI** backend (OR-Tools + Mapbox or haversine fallback), a **Flutter** mobile app, and a **React** web UI.

## Project structure

```
route-optimizer/
├── backend/
│   └── app/
│       ├── api/          # HTTP routes
│       ├── core/         # Exceptions
│       ├── models/       # Pydantic schemas
│       ├── services/     # Matrix, solver, response builder
│       ├── config.py     # Environment settings
│       └── main.py       # FastAPI app
├── frontend/             # React + Leaflet web UI
├── mobile/               # Flutter app (android/, ios/, lib/)
└── README.md
```

## Prerequisites

- Python 3.9+
- Flutter SDK 3.10+ (for mobile)
- Node.js 18+ (optional, for web UI)
- Android Studio and/or Xcode (for mobile)

## Setup

### 1. Python virtual environment

```bash
cd /Users/suhani_garate/Desktop/route-optimizer
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Backend environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

- Set `USE_HAVERSINE=true` to run without a Mapbox token (straight-line estimates).
- Or set `USE_HAVERSINE=false` and add your `MAPBOX_ACCESS_TOKEN` for real road distances.

### 3. Mobile app

```bash
cd mobile
flutter pub get
```

See [mobile/README.md](mobile/README.md) for Android Studio setup and device-specific API URLs.

### 4. Web UI (optional)

```bash
cd frontend
npm install
```

## Run

**Terminal 1 — API**

```bash
cd /Users/suhani_garate/Desktop/route-optimizer
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Mobile — Android Studio or CLI**

Open `mobile/` in Android Studio and click Run, or:

```bash
cd mobile
flutter run
```

**Terminal 2 — Web UI (optional)**

```bash
cd /Users/suhani_garate/Desktop/route-optimizer/frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The dev server proxies `/api` to the backend.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/optimize-route` | Optimize stop order |

Example:

```bash
curl -X POST http://127.0.0.1:8000/optimize-route \
  -H "Content-Type: application/json" \
  -d '{"stops":[{"lat":19.076,"lng":72.8777},{"lat":19.117,"lng":72.906},{"lat":19.059,"lng":72.829}]}'
```

## Docker (backend only)

```bash
cd backend
docker build -t route-optimizer-api .
docker run -p 8000:8000 --env-file .env route-optimizer-api
```

## Notes

- Maximum **25 stops** (Mapbox matrix limit); configurable via `MAX_STOPS`.
- Mobile details: [mobile/README.md](mobile/README.md)
