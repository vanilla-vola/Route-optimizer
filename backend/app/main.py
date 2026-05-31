from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Route Optimizer API",
    version=__version__,
    description="Multi-stop route optimization using OR-Tools and Mapbox (or haversine fallback).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
