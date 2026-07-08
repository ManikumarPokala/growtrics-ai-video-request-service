import queue
import asyncio
import threading
from concurrent.futures import ProcessPoolExecutor
from app.core.config import logger

class JobScheduler:
    def __init__(self) -> None:
        self._queue = queue.Queue()
        # ProcessPoolExecutor for CPU-heavy Pillow frame drawing tasks
        self._executor = ProcessPoolExecutor(max_workers=2)
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        logger.info("Background JobScheduler initialized and thread loop started.")

    def push_job(self, job_id: str) -> None:
        self._queue.put(job_id)
        logger.info(f"Scheduler: Enqueued job ID {job_id}.")

    def get_executor(self) -> ProcessPoolExecutor:
        return self._executor

    def _worker_loop(self) -> None:
        # Loop running inside background consumer thread
        while True:
            try:
                job_id = self._queue.get()
                if job_id is None:
                    break

                logger.info(f"Scheduler worker: dequeued job ID {job_id} for processing.")
                
                # Lazy import inside the loop to avoid circular import issues
                from app.repositories.database import repository
                from app.models.schemas import VideoJobStatus
                from app.services.llm import llm_provider
                from app.services.renderer import video_renderer

                job = repository.get_by_id(job_id)
                if not job:
                    logger.error(f"Scheduler: Job ID {job_id} not found in database.")
                    self._queue.task_done()
                    continue

                # Transition 1: pending -> generating (progress 10%)
                repository.update(job_id, {
                    "status": VideoJobStatus.GENERATING,
                    "progress": 10.0
                })

                # Step 1: Storyboard generation (async)
                try:
                    logger.info(f"Scheduler worker: generating storyboard for query '{job.query}'")
                    # Run async coroutine synchronously inside the background thread
                    storyboard = asyncio.run(llm_provider.generate_storyboard(job.query))
                    repository.update(job_id, {
                        "storyboard": storyboard,
                        "progress": 30.0
                    })
                except Exception as e:
                    import traceback
                    err_msg = f"Storyboard generation failed: {str(e)}\n{traceback.format_exc()}"
                    logger.error(f"Scheduler error for job {job_id}: {err_msg}")
                    repository.update(job_id, {
                        "status": VideoJobStatus.FAILED,
                        "error_message": err_msg,
                        "progress": 0.0
                    })
                    self._queue.task_done()
                    continue

                # Step 2: Visual and Audio rendering (delegates to ProcessPoolExecutor)
                try:
                    logger.info(f"Scheduler worker: rendering video for job {job_id}")
                    # Update progress to 60% as we begin frame generation
                    repository.update(job_id, {"progress": 60.0})
                    
                    video_url = video_renderer.render_job_video(job_id, storyboard)
                    
                    # Update progress to 100% and transition state
                    repository.update(job_id, {
                        "status": VideoJobStatus.COMPLETED,
                        "progress": 100.0,
                        "video_url": video_url
                    })
                    logger.info(f"Scheduler worker: job {job_id} completed successfully. URL: {video_url}")
                except Exception as e:
                    import traceback
                    err_msg = f"Video rendering failed: {str(e)}\n{traceback.format_exc()}"
                    logger.error(f"Scheduler error for job {job_id}: {err_msg}")
                    repository.update(job_id, {
                        "status": VideoJobStatus.FAILED,
                        "error_message": err_msg,
                        "progress": 0.0
                    })
                finally:
                    self._queue.task_done()

            except Exception as ex:
                logger.critical(f"Critical scheduler background loop exception: {str(ex)}")

# Global singleton scheduler instance
scheduler = JobScheduler()
