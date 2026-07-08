import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import VideoJobStatus
from app.storyboards.content_registry import get_fallback_storyboard, PH_SCALE_STORYBOARD, COVALENT_BOND_STORYBOARD, IONIC_VS_COVALENT_STORYBOARD
from app.repositories.database import repository
from app.api.routes import CLIENT_REQUESTS

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    # Reset internal repo map before each test to maintain isolation
    repository._jobs.clear()
    CLIENT_REQUESTS.clear()

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_fallback_storyboard_lookup():
    sb_ph = get_fallback_storyboard("How does the pH scale work?")
    assert len(sb_ph.scenes) == 3
    assert sb_ph.scenes[0].visual_type == "ph_scale_overview"

    sb_cov = get_fallback_storyboard("Why do atoms form covalent bonds?")
    assert len(sb_cov.scenes) == 3
    assert sb_cov.scenes[1].visual_type == "electron_sharing"

    sb_diff = get_fallback_storyboard("What is the difference between ionic and covalent bonding?")
    assert len(sb_diff.scenes) == 3
    assert sb_diff.scenes[2].visual_type == "covalent_interaction"

def test_create_video_job_validation():
    # Query too short (< 10 chars)
    response = client.post("/api/v1/videos", json={"query": "short"})
    assert response.status_code == 422 # FastAPI Pydantic validation error

    # Query too long (> 200 chars)
    long_query = "a" * 205
    response = client.post("/api/v1/videos", json={"query": long_query})
    assert response.status_code == 422

def test_video_job_lifecycle():
    # Create video job
    query = "Why do atoms form covalent bonds?"
    response = client.post("/api/v1/videos", json={"query": query})
    assert response.status_code == 202
    
    data = response.json()
    job_id = data["id"]
    assert job_id is not None
    assert data["query"] == query
    assert data["status"] in (VideoJobStatus.PENDING, VideoJobStatus.GENERATING)

    # Get specific job
    response = client.get(f"/api/v1/videos/{job_id}")
    assert response.status_code == 200
    assert response.json()["id"] == job_id

    # List all jobs
    response = client.get("/api/v1/videos")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == job_id

def test_job_not_found():
    response = client.get("/api/v1/videos/non-existent-uuid")
    assert response.status_code == 404

def test_rate_limiting():
    query = "Testing rate limiter trigger query topic"
    # Trigger 5 requests successfully
    for _ in range(5):
        response = client.post("/api/v1/videos", json={"query": query})
        assert response.status_code == 202
        
    # The 6th request must trigger rate-limit
    response = client.post("/api/v1/videos", json={"query": query})
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
