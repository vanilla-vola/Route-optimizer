"""Benchmark instance catalog for paper experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        manifest = parent / "benchmarks" / "instances" / "manifest.json"
        if manifest.is_file():
            return parent
    raise HTTPException(
        status_code=500,
        detail="Benchmark instances directory not found in project tree.",
    )


def _instances_dir() -> Path:
    return _repo_root() / "benchmarks" / "instances"


class BenchmarkInstanceSummary(BaseModel):
    id: str
    description: str
    city: str
    region: str
    pattern: str
    stop_count: int
    mode: str
    round_trip: bool


class BenchmarkInstanceStop(BaseModel):
    name: str
    lat: float
    lng: float


class BenchmarkInstanceDetail(BaseModel):
    id: str
    description: str
    city: str
    region: str
    pattern: str
    mode: str
    round_trip: bool
    stops: list[BenchmarkInstanceStop]


class BenchmarkInstanceListResponse(BaseModel):
    count: int
    instances: list[BenchmarkInstanceSummary]


def _load_manifest() -> dict[str, Any]:
    manifest_path = _instances_dir() / "manifest.json"
    if not manifest_path.is_file():
        raise HTTPException(
            status_code=500,
            detail="Benchmark manifest not found. Run scripts/generate_benchmark_instances.py.",
        )
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _load_instance(instance_id: str) -> dict[str, Any]:
    path = _instances_dir() / f"{instance_id}.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Instance '{instance_id}' not found.")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/benchmark-instances", response_model=BenchmarkInstanceListResponse)
async def list_benchmark_instances() -> BenchmarkInstanceListResponse:
    manifest = _load_manifest()
    items = [BenchmarkInstanceSummary(**row) for row in manifest.get("instances", [])]
    return BenchmarkInstanceListResponse(count=len(items), instances=items)


@router.get("/benchmark-instances/{instance_id}", response_model=BenchmarkInstanceDetail)
async def get_benchmark_instance(instance_id: str) -> BenchmarkInstanceDetail:
    data = _load_instance(instance_id)
    return BenchmarkInstanceDetail(
        id=data["id"],
        description=data["description"],
        city=data["city"],
        region=data["region"],
        pattern=data["pattern"],
        mode=data["mode"],
        round_trip=data["round_trip"],
        stops=[BenchmarkInstanceStop(**stop) for stop in data["stops"]],
    )
