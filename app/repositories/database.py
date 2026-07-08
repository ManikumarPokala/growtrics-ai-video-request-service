import threading
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime, timezone
from app.models.schemas import VideoJob
from app.core.config import logger

class BaseRepository(ABC):
    @abstractmethod
    def create(self, job: VideoJob) -> VideoJob:
        pass

    @abstractmethod
    def get_by_id(self, job_id: str) -> Optional[VideoJob]:
        pass

    @abstractmethod
    def get_all(self) -> List[VideoJob]:
        pass

    @abstractmethod
    def update(self, job_id: str, updates: dict) -> Optional[VideoJob]:
        pass

class InMemoryJobRepository(BaseRepository):
    def __init__(self) -> None:
        self._jobs: Dict[str, VideoJob] = {}
        self._lock = threading.Lock()
        logger.info("Initialized thread-safe InMemoryJobRepository.")

    def create(self, job: VideoJob) -> VideoJob:
        with self._lock:
            # Prevent duplicate UUID insertion
            if job.id in self._jobs:
                logger.warning(f"Job ID {job.id} already exists in database. Overwriting.")
            self._jobs[job.id] = job
            logger.info(f"DB: Created job record {job.id}.")
            return job

    def get_by_id(self, job_id: str) -> Optional[VideoJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def get_all(self) -> List[VideoJob]:
        with self._lock:
            # Return copies to prevent caller mutation outside the lock context
            return list(self._jobs.values())

    def update(self, job_id: str, updates: dict) -> Optional[VideoJob]:
        with self._lock:
            if job_id not in self._jobs:
                logger.error(f"DB Update failed: Job ID {job_id} not found.")
                return None
            
            current_job = self._jobs[job_id]
            # Convert job to dictionary to modify and validate
            job_dict = current_job.model_dump()
            
            for key, value in updates.items():
                if key in job_dict:
                    job_dict[key] = value
            
            # Auto-update timestamp
            job_dict["updated_at"] = datetime.now(timezone.utc)
            
            # Re-parse into validated VideoJob entity
            updated_job = VideoJob(**job_dict)
            self._jobs[job_id] = updated_job
            
            logger.info(f"DB: Updated job {job_id} successfully. Fields: {list(updates.keys())}")
            return updated_job

# Global singleton repository instance
repository = InMemoryJobRepository()
