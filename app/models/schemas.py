from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class VideoJobStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoRequest(BaseModel):
    query: str = Field(..., description="The learner's educational request topic.")
    source_language: str = Field(default="auto", description="Detected or specified input language.")
    target_language: str = Field(default="en", description="Target output explanation language.")
    locale: str = Field(default="en-US", description="Locale format for formatting outputs.")

    @field_validator("query")
    @classmethod
    def validate_query_length(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 10 or len(trimmed) > 200:
            raise ValueError("Query length must be between 10 and 200 characters.")
        return trimmed

class StoryboardScene(BaseModel):
    visual_type: str = Field(..., description="Identifies the drawingPrimitive/drawer strategy to use.")
    script: str = Field(..., description="Scene voiceover narration script.")
    duration: float = Field(..., description="Duration of the scene in seconds.")

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        if v <= 0.0 or v > 30.0:
            raise ValueError("Scene duration must be positive and under 30 seconds.")
        return v

class Storyboard(BaseModel):
    scenes: List[StoryboardScene]

class VideoJob(BaseModel):
    id: str
    query: str
    status: VideoJobStatus = VideoJobStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    video_url: Optional[str] = None
    retry_count: int = 0
    storyboard: Optional[Storyboard] = None
    source_language: str = "auto"
    target_language: str = "en"
    locale: str = "en-US"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
