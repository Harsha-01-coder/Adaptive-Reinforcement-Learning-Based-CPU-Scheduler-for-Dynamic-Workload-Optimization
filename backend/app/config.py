"""
Application configuration via environment variables.
Loaded from .env file in development.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "RL CPU Scheduler API"
    app_version: str = "1.0.0"
    debug: bool = True

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/scheduler.db"

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    # RL
    rl_model_path: str = "rl_agent/models/ppo_cpu_scheduler"
    rl_training_timesteps: int = 500_000
    rl_n_envs: int = 4

    # Simulation
    max_processes: int = 50
    max_cores: int = 8
    default_time_quantum: float = 4.0

    # Export
    export_dir: str = "./exports"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
