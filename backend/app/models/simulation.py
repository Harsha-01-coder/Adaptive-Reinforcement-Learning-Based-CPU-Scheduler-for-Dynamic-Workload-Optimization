"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SimulationRecord(Base):
    """Persisted simulation result."""

    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    algorithm: Mapped[str] = mapped_column(String(64))
    workload_mode: Mapped[str] = mapped_column(String(32), default="custom")
    n_processes: Mapped[int] = mapped_column(Integer)
    num_cores: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Metrics (denormalized for quick queries)
    avg_waiting_time: Mapped[float] = mapped_column(Float, default=0.0)
    avg_turnaround_time: Mapped[float] = mapped_column(Float, default=0.0)
    avg_response_time: Mapped[float] = mapped_column(Float, default=0.0)
    cpu_utilization: Mapped[float] = mapped_column(Float, default=0.0)
    throughput: Mapped[float] = mapped_column(Float, default=0.0)
    context_switches: Mapped[int] = mapped_column(Integer, default=0)
    fairness_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Full result JSON
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)


class BenchmarkRecord(Base):
    """Persisted benchmark comparison run."""

    __tablename__ = "benchmarks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workload_mode: Mapped[str] = mapped_column(String(32))
    n_processes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    results_json: Mapped[dict] = mapped_column(JSON, default=dict)
