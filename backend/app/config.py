from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mapbox_access_token: str = ""
    matrix_profile: str = "driving-traffic"
    use_haversine: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    max_stops: int = 25
    solver_time_limit_s: int = 5
    use_dcir: bool = True
    dcir_time_limit_s: int = 12
    dcir_robust_lambda: float = 0.3
    dcir_mapbox_profiles: bool = True
    dcir_timezone: str = "Asia/Kolkata"
    dcir_depart_hours: str = "8,13,18"
    dcir_refresh_legs: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
