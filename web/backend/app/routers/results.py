"""Results API router."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, func

from app.core.database import get_session
from app.core.security import create_token, verify_token
from app.models import (
    BenchmarkResult,
    EncodeResult,
    EncodeResultPayload,
    ResultSubmission,
    ResultResponse,
    SystemInfoPayload,
)

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/token")
def get_token():
    """Request an upload token."""
    token, expires_at = create_token()
    return {"token": token, "expires_at": expires_at.isoformat()}


@router.post("", status_code=201)
def submit_result(
    submission: ResultSubmission,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
):
    """Submit a benchmark result."""
    # Validate token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization[7:]
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Check for duplicate run_id
    existing = session.exec(
        select(BenchmarkResult).where(BenchmarkResult.run_id == submission.run_id)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Result with this run_id already exists")
    
    # Parse timestamp
    try:
        timestamp = datetime.fromisoformat(submission.timestamp.replace("Z", "+00:00"))
    except ValueError:
        timestamp = datetime.now(timezone.utc)
    
    # Create benchmark result
    result = BenchmarkResult(
        benchmark_version=submission.benchmark_version,
        run_id=submission.run_id,
        timestamp=timestamp,
        os=submission.system.os,
        os_version=submission.system.os_version,
        arch=submission.system.arch,
        cpu_model=submission.system.cpu_model,
        cpu_cores=submission.system.cpu_cores,
        cpu_threads=submission.system.cpu_threads,
        ram_gb=submission.system.ram_gb,
        is_virtualized=submission.system.is_virtualized,
        virtualization_platform=submission.system.virtualization_platform,
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    
    # Create encode results
    for er in submission.results:
        encode_result = EncodeResult(
            benchmark_result_id=result.id,
            video=er.video,
            codec=er.codec,
            preset=er.preset,
            crf=er.crf,
            encode_time_seconds=er.encode_time_seconds,
            fps=er.fps,
            output_size_mb=er.output_size_mb,
        )
        session.add(encode_result)
    
    session.commit()
    return {"id": result.id, "status": "accepted"}


@router.get("", response_model=List[ResultResponse])
def list_results(
    cpu_model: Optional[str] = Query(None),
    codec: Optional[str] = Query(None),
    is_virtualized: Optional[bool] = Query(None),
    os: Optional[str] = Query(None),
    arch: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """List benchmark results with filtering."""
    statement = (
        select(BenchmarkResult)
        .options(selectinload(BenchmarkResult.encode_results))
        .order_by(BenchmarkResult.timestamp.desc())
    )
    
    if cpu_model:
        statement = statement.where(BenchmarkResult.cpu_model.ilike(f"%{cpu_model}%"))
    if is_virtualized is not None:
        statement = statement.where(BenchmarkResult.is_virtualized == is_virtualized)
    if os:
        statement = statement.where(BenchmarkResult.os.ilike(f"%{os}%"))
    if arch:
        statement = statement.where(BenchmarkResult.arch == arch)
    
    results = session.exec(statement.offset(offset).limit(limit)).all()
    
    response = []
    for r in results:
        encode_results = r.encode_results
        
        if codec:
            encode_results = [er for er in encode_results if er.codec == codec]
            if not encode_results:
                continue
        
        response.append(
            ResultResponse(
                id=r.id,
                benchmark_version=r.benchmark_version,
                run_id=r.run_id,
                timestamp=r.timestamp,
                system=SystemInfoPayload(
                    os=r.os,
                    os_version=r.os_version,
                    arch=r.arch,
                    cpu_model=r.cpu_model,
                    cpu_cores=r.cpu_cores,
                    cpu_threads=r.cpu_threads,
                    ram_gb=r.ram_gb,
                    is_virtualized=r.is_virtualized,
                    virtualization_platform=r.virtualization_platform,
                ),
                results=[
                    EncodeResultPayload(
                        video=er.video,
                        codec=er.codec,
                        preset=er.preset,
                        crf=er.crf,
                        encode_time_seconds=er.encode_time_seconds,
                        fps=er.fps,
                        output_size_mb=er.output_size_mb,
                    )
                    for er in r.encode_results
                ],
            )
        )
    
    return response


@router.get("/{result_id}", response_model=ResultResponse)
def get_result(result_id: str, session: Session = Depends(get_session)):
    """Get a single benchmark result."""
    statement = (
        select(BenchmarkResult)
        .where(BenchmarkResult.id == result_id)
        .options(selectinload(BenchmarkResult.encode_results))
    )
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return ResultResponse(
        id=result.id,
        benchmark_version=result.benchmark_version,
        run_id=result.run_id,
        timestamp=result.timestamp,
        system=SystemInfoPayload(
            os=result.os,
            os_version=result.os_version,
            arch=result.arch,
            cpu_model=result.cpu_model,
            cpu_cores=result.cpu_cores,
            cpu_threads=result.cpu_threads,
            ram_gb=result.ram_gb,
            is_virtualized=result.is_virtualized,
            virtualization_platform=result.virtualization_platform,
        ),
        results=[
            EncodeResultPayload(
                video=er.video,
                codec=er.codec,
                preset=er.preset,
                crf=er.crf,
                encode_time_seconds=er.encode_time_seconds,
                fps=er.fps,
                output_size_mb=er.output_size_mb,
            )
            for er in result.encode_results
        ],
    )
