from abc import ABC, abstractmethod
from app.models.schemas import Storyboard, StoryboardScene, VideoJob

class ILLMProvider(ABC):
    @abstractmethod
    async def generate_storyboard(self, query: str, retry_count: int = 0) -> Storyboard:
        """
        Request storyboard from LLM, perform Pydantic schema validation, and handle retries.
        """
        pass

class ILocalizationProvider(ABC):
    @abstractmethod
    async def localize_storyboard(self, storyboard: Storyboard, target_lang: str, locale: str) -> Storyboard:
        """
        Translate and adapt storyboard scripts and parameters based on target locale.
        """
        pass

class ITTSProvider(ABC):
    @abstractmethod
    async def synthesize_speech(self, text: str, output_path: str, locale: str) -> str:
        """
        Generate audio speech file for the scene matching the locale. Return file path.
        """
        pass

class IVideoRendererProvider(ABC):
    @abstractmethod
    def draw_scene_frames(self, scene: StoryboardScene, audio_path: str, temp_dir: str) -> str:
        """
        Calculate animation frames, render images, and stitch into scene MP4. Return scene file path.
        """
        pass

class IStorageProvider(ABC):
    @abstractmethod
    def upload_artifact(self, local_path: str, filename: str) -> str:
        """
        Upload final video to artifact storage (GCS/S3) and return public URL.
        """
        pass

class IQueueProvider(ABC):
    @abstractmethod
    def push_job(self, job_id: str) -> None:
        """
        Queue job execution.
        """
        pass
