"""Workload generation and upload API routes."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile

from workload_generator import WorkloadGenerator

router = APIRouter(prefix="/api/workload", tags=["Workload"])
_gen = WorkloadGenerator(seed=42)


def _process_to_dict(p) -> Dict[str, Any]:
    return {
        "pid": p.pid,
        "arrival_time": p.arrival_time,
        "burst_time": p.burst_time,
        "priority": p.priority,
        "process_type": p.process_type,
    }


@router.get("/generate")
async def generate_workload(
    mode: str = Query(default="medium", pattern="^(small|medium|large|random)$"),
    n: Optional[int] = Query(default=None, ge=2, le=200),
    seed: Optional[int] = Query(default=None),
) -> Dict[str, Any]:
    """
    Generate a synthetic workload.

    - **mode**: small (10), medium (30), large (100), or random
    - **n**: override process count
    - **seed**: reproducibility seed
    """
    try:
        processes = _gen.generate(mode=mode, n=n, seed=seed)
        return {
            "mode": mode,
            "n_processes": len(processes),
            "processes": [_process_to_dict(p) for p in processes],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_workload(file: UploadFile) -> Dict[str, Any]:
    """
    Upload a CSV file with custom workload.

    Expected CSV columns (case-insensitive):
        pid, arrival_time, burst_time, priority, process_type
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    try:
        content = await file.read()
        csv_text = content.decode("utf-8")
        processes = _gen.load_csv(csv_text)
        return {
            "mode": "custom",
            "filename": file.filename,
            "n_processes": len(processes),
            "processes": [_process_to_dict(p) for p in processes],
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/template")
async def download_template():
    """Download a CSV template for custom workload import."""
    from fastapi.responses import Response

    csv_content = (
        "pid,arrival_time,burst_time,priority,process_type\n"
        "1,0,10,3,cpu_bound\n"
        "2,2,5,1,io_bound\n"
        "3,4,8,5,cpu_bound\n"
        "4,1,3,2,io_bound\n"
        "5,6,15,4,cpu_bound\n"
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=workload_template.csv"},
    )
