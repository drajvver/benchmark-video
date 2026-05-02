"""Leaderboard API router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import BenchmarkResult, EncodeResult, LeaderboardEntry, CPUStats

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(
    codec: Optional[str] = Query(None),
    video: Optional[str] = Query(None),
    is_virtualized: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    """Get leaderboard aggregated by CPU model and codec."""
    # Build subquery for encode results
    subq = select(
        BenchmarkResult.cpu_model,
        EncodeResult.codec,
        BenchmarkResult.is_virtualized,
        func.avg(EncodeResult.fps).label("avg_fps"),
        func.max(EncodeResult.fps).label("best_fps"),
        func.count(EncodeResult.id).label("run_count"),
    ).join(
        EncodeResult, BenchmarkResult.id == EncodeResult.benchmark_result_id
    ).group_by(
        BenchmarkResult.cpu_model,
        EncodeResult.codec,
        BenchmarkResult.is_virtualized,
    )
    
    if codec:
        subq = subq.where(EncodeResult.codec == codec)
    if video:
        subq = subq.where(EncodeResult.video == video)
    if is_virtualized is not None:
        subq = subq.where(BenchmarkResult.is_virtualized == is_virtualized)
    
    subq = subq.order_by(func.avg(EncodeResult.fps).desc())
    
    results = session.exec(subq.limit(limit)).all()
    
    return [
        LeaderboardEntry(
            cpu_model=r.cpu_model,
            codec=r.codec,
            avg_fps=round(r.avg_fps, 2) if r.avg_fps else 0.0,
            best_fps=round(r.best_fps, 2) if r.best_fps else 0.0,
            run_count=r.run_count,
            is_virtualized=r.is_virtualized,
        )
        for r in results
    ]


@router.get("/cpus", response_model=List[CPUStats])
def get_cpu_stats(
    codec: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    """Get aggregated stats per CPU model."""
    subq = select(
        BenchmarkResult.cpu_model,
        func.avg(EncodeResult.fps).label("avg_fps"),
        func.max(EncodeResult.fps).label("best_fps"),
        func.count(EncodeResult.id).label("run_count"),
        func.sum(case((BenchmarkResult.is_virtualized == False, 1), else_=0)).label("bare_metal_count"),
        func.sum(case((BenchmarkResult.is_virtualized == True, 1), else_=0)).label("virtualized_count"),
    ).join(
        EncodeResult, BenchmarkResult.id == EncodeResult.benchmark_result_id
    ).group_by(
        BenchmarkResult.cpu_model,
    )
    
    if codec:
        subq = subq.where(EncodeResult.codec == codec)
    
    subq = subq.order_by(func.avg(EncodeResult.fps).desc())
    
    results = session.exec(subq).all()
    
    return [
        CPUStats(
            cpu_model=r.cpu_model,
            avg_fps=round(r.avg_fps, 2) if r.avg_fps else 0.0,
            best_fps=round(r.best_fps, 2) if r.best_fps else 0.0,
            run_count=r.run_count,
            bare_metal_count=r.bare_metal_count or 0,
            virtualized_count=r.virtualized_count or 0,
        )
        for r in results
    ]
