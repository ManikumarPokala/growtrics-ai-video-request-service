import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    
    ollama_host: str = Field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    ollama_model: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
    
    video_resolution_w: int = Field(default_factory=lambda: int(os.getenv("VIDEO_RESOLUTION_W", "1280")))
    video_resolution_h: int = Field(default_factory=lambda: int(os.getenv("VIDEO_RESOLUTION_H", "720")))
    video_fps: int = Field(default_factory=lambda: int(os.getenv("VIDEO_FPS", "24")))
    
    rate_limit_per_min: int = Field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MIN", "5")))
    max_retries: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))

    # Base Directories
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    static_dir: Path = Path(__file__).resolve().parent.parent.parent / "static"
    temp_dir: Path = Path(__file__).resolve().parent.parent.parent / "temp"
    assets_dir: Path = Path(__file__).resolve().parent.parent.parent / "assets"
    font_path: Path = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts" / "Roboto-Regular.ttf"

# Instantiate settings
settings = Settings()

# Setup structured logger
def setup_logger() -> logging.Logger:
    log = logging.getLogger("growtrics")
    log.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not log.handlers:
        handler = logging.StreamHandler()
        # Clean structured JSON-like format
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.propagate = False
    return log

logger = setup_logger()
