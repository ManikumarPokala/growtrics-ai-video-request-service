import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.core.config import settings, logger
from app.api.routes import router as api_router

# Initialize directories on startup
os.makedirs(settings.static_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)
logger.info(f"Initialized application folders. Static: {settings.static_dir}, Temp: {settings.temp_dir}")

app = FastAPI(
    title="AI Educational Video Request Service",
    description="Chemistry Prototype backend providing async educational video generation.",
    version="1.0.0",
)

# Mount static directory for video downloads
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
logger.info("Mounted static directories for serving MP4 artifacts.")

# Redirect root to Swagger API documentation
@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")

# Include api v1 router
app.include_router(api_router)
logger.info("Mounted API V1 routes successfully.")
