"""Database models."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel


class BenchmarkResult(SQLModel, table=True):
    """Top-level benchmark result."""
    
    __tablename__ = "benchmark_results"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    benchmark_version: str = Field(default="1.0.0")
    run_id: str = Field(index=True, unique=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # System info
    os: str
    os_version: str
    arch: str
    cpu_model: str = Field(index=True)
    cpu_cores: int
    cpu_threads: int
    ram_gb: int
    is_virtualized: bool = Field(index=True, default=False)
    virtualization_platform: Optional[str] = None
    
    # Relationships
    encode_results: List["EncodeResult"] = Relationship(
        back_populates="benchmark_result",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class EncodeResult(SQLModel, table=True):
    """Individual encode run result."""
    
    __tablename__ = "encode_results"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    benchmark_result_id: Optional[str] = Field(
        default=None, foreign_key="benchmark_results.id", index=True
    )
    video: str
    codec: str = Field(index=True)
    preset: str
    crf: int
    encode_time_seconds: float
    fps: float = Field(index=True)
    output_size_mb: float
    
    # Relationship
    benchmark_result: Optional[BenchmarkResult] = Relationship(back_populates="encode_results")


# API request/response models

class EncodeResultPayload(SQLModel):
    video: str
    codec: str
    preset: str
    crf: int
    encode_time_seconds: float
    fps: float
    output_size_mb: float


class SystemInfoPayload(SQLModel):
    os: str
    os_version: str
    arch: str
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    ram_gb: int
    is_virtualized: bool = False
    virtualization_platform: Optional[str] = None


class ResultSubmission(SQLModel):
    benchmark_version: str
    run_id: str
    timestamp: str
    system: SystemInfoPayload
    results: List[EncodeResultPayload]


class ResultResponse(SQLModel):
    id: str
    benchmark_version: str
    run_id: str
    timestamp: datetime
    system: SystemInfoPayload
    results: List[EncodeResultPayload]


class LeaderboardEntry(SQLModel):
    cpu_model: str
    codec: str
    avg_fps: float
    best_fps: float
    run_count: int
    is_virtualized: bool


class CPUStats(SQLModel):
    cpu_model: str
    avg_fps: float
    best_fps: float
    run_count: int
    bare_metal_count: int
    virtualized_count: int
