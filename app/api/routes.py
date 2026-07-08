import time
import uuid
import hashlib
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Request
from app.models.schemas import VideoRequest, VideoJob, VideoJobStatus
from app.repositories.database import repository
from app.workers.scheduler import scheduler
from app.core.config import logger

router = APIRouter(prefix="/api/v1")

# Slide window rate-limit memory map
CLIENT_REQUESTS = {}

def check_rate_limit(client_ip: str, limit: int = 5, window_seconds: int = 60):
    now = time.time()
    timestamps = CLIENT_REQUESTS.get(client_ip, [])
    # Keep only timestamps in the current window
    timestamps = [t for t in timestamps if now - t < window_seconds]
    CLIENT_REQUESTS[client_ip] = timestamps

    if len(timestamps) >= limit:
        logger.warning(f"Rate limit hit for client IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 5 video requests per minute allowed."
        )
    CLIENT_REQUESTS[client_ip].append(now)

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/videos", status_code=status.HTTP_202_ACCEPTED, response_model=VideoJob)
def create_video_job(payload: VideoRequest, request: Request):
    # Retrieve client IP for rate-limiting
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    normalized_query = payload.query.lower().strip()
    logger.info(f"Received video request query: '{payload.query}' from IP: {client_ip}")

    # Idempotency check: search for existing completed jobs with matching normalized query
    existing_job = next(
        (j for j in repository.get_all() 
         if j.query.lower().strip() == normalized_query and j.status == VideoJobStatus.COMPLETED),
        None
    )
    if existing_job:
        logger.info(f"Idempotency hit: returning existing completed job {existing_job.id} for query '{normalized_query}'")
        return existing_job

    # Create new asynchronous job
    job_id = str(uuid.uuid4())
    job = VideoJob(
        id=job_id,
        query=payload.query,
        status=VideoJobStatus.PENDING,
        progress=0.0,
        source_language=payload.source_language,
        target_language=payload.target_language,
        locale=payload.locale,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    repository.create(job)
    
    # Enqueue job for background processing
    scheduler.push_job(job_id)
    
    return job

@router.get("/videos", response_model=List[VideoJob])
def list_video_jobs():
    return repository.get_all()

@router.get("/videos/{job_id}", response_model=VideoJob)
def get_video_job(job_id: str):
    job = repository.get_by_id(job_id)
    if not job:
        logger.warning(f"Requested job ID {job_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested video job not found."
        )
    return job
