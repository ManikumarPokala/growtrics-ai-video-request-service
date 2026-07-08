# AI Educational Video Request Service (Chemistry Prototype)

An asynchronous, AI-native backend service that generates high-quality 720p HD educational video clips from learner queries. This prototype is configured with pre-crafted animation drawers and fallback storyboards for three key Chemistry topics.

---

## Technical Architecture Overview
This prototype is built using a **4-Tier Clean Architecture** layout to strictly separate API handlers, database access, background workers, and rendering engines. 

For a detailed review of the design, check the **[Architecture Design Note](docs/architecture.md)** and the complete **[Implementation Plan](IMPLEMENTATION_PLAN.md)**.

---

## Quick Start (Local Setup)

### 1. Prerequisites
Ensure you have Python 3.12+ and FFmpeg installed on your system.
```bash
# On macOS via Homebrew
brew install ffmpeg
```

### 2. Install Virtual Environment & Dependencies
Initialize the Python virtual environment and install the required libraries:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the configuration template and create your local environment file:
```bash
cp .env.example .env
```

### 4. Run Automated Tests
Verify project dependencies and event lifecycles by running the test suite:
```bash
pytest
```

---

## Running the Server

Start the FastAPI application using Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```
Once the server starts, navigate to **[http://localhost:8000/docs](http://localhost:8000/docs)** to view the auto-generated Swagger API documentation.

---

## Verification Walkthrough (API Endpoints)

Reviewers can verify the asynchronous video request lifecycle using the following three chemistry queries:
1. `"How does the pH scale work?"`
2. `"Why do atoms form covalent bonds?"`
3. `"What is the difference between ionic and covalent bonding?"`

### 1. Submit Request
```bash
curl -X POST http://localhost:8000/api/v1/videos \
     -H "Content-Type: application/json" \
     -d '{"query": "Why do atoms form covalent bonds?"}'
```
*Saves record to DB (`pending` state) and returns a unique `id` (UUID).*

### 2. Observe State Transitions (Status Polling)
Query the status endpoint to monitor progressive progress ticks (e.g. 10%, 30%, 60%, 80%, 100%):
```bash
curl http://localhost:8000/api/v1/videos/{job_id}
```

### 3. Stream & Play Completed Video
Once status is `completed` and progress is `100.0`, download or play the generated video:
```bash
# Download file directly
curl -o covalent_bonds.mp4 http://localhost:8000/static/{job_id}.mp4
```

*Note: The completed videos for the three topics are also compiled and pre-saved directly under the `static/` directory (`static/ph_scale.mp4`, `static/covalent_bonds.mp4`, and `static/ionic_vs_covalent.mp4`) for instant inspection.*

---

## Codebase Structure
```
growtrics-ai-video-request-service/
├── app/
│   ├── main.py                # App entrypoint & static config
│   ├── api/routes.py          # API endpoints & rate-limit check
│   ├── core/config.py         # Config validations & structured logs
│   ├── core/interfaces.py     # Decoupled service contracts
│   ├── models/schemas.py      # Pydantic state models & validations
│   ├── repositories/database.py # Thread-safe InMemoryJobRepository
│   ├── services/llm.py        # Ollama connector & self-repair loops
│   ├── services/renderer.py   # PIL drawing loop & FFmpeg compiler
│   ├── storyboards/content_registry.py # Storyboard registries & fallback lists
│   └── workers/scheduler.py   # Thread-safe consumer task queue
├── tests/test_api.py          # Pytest suite
├── static/                    # Outputs folder (contains compiled MP4s)
├── docs/architecture.md       # Architecture note
├── IMPLEMENTATION_PLAN.md     # Frozen architecture plan
├── requirements.txt           # Project dependencies
└── .env.example               # Config template
```
