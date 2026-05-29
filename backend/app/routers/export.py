"""Export API routes — CSV and PDF download."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models import SimulationRecord
from ..services.export_service import export_csv, export_pdf

router = APIRouter(prefix="/api/export", tags=["Export"])


async def _load_simulation(simulation_id: str) -> Dict[str, Any]:
    """Load simulation result from DB."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SimulationRecord).where(SimulationRecord.id == simulation_id)
        )
        record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id!r} not found")

    return record.result_json


@router.get("/{simulation_id}/csv")
async def download_csv(simulation_id: str) -> Response:
    """Download simulation results as CSV."""
    sim = await _load_simulation(simulation_id)
    csv_bytes = export_csv(sim)
    filename = f"simulation_{simulation_id[:8]}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{simulation_id}/pdf")
async def download_pdf(simulation_id: str) -> Response:
    """Download simulation results as PDF report."""
    sim = await _load_simulation(simulation_id)
    pdf_bytes = export_pdf(sim)
    filename = f"simulation_{simulation_id[:8]}.pdf"
    content_type = "application/pdf" if pdf_bytes[:4] == b"%PDF" else "text/plain"
    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/inline/csv")
async def export_inline_csv(simulation_result: Dict[str, Any]) -> Response:
    """Export a simulation result payload directly as CSV (no DB lookup)."""
    csv_bytes = export_csv(simulation_result)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=simulation.csv"},
    )


@router.post("/inline/pdf")
async def export_inline_pdf(simulation_result: Dict[str, Any]) -> Response:
    """Export a simulation result payload directly as PDF (no DB lookup)."""
    pdf_bytes = export_pdf(simulation_result)
    content_type = "application/pdf" if len(pdf_bytes) > 4 and pdf_bytes[:4] == b"%PDF" else "text/plain"
    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={"Content-Disposition": "attachment; filename=simulation.pdf"},
    )
