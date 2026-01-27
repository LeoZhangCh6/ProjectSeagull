# ProjectSeagull Backend

FastAPI backend for the ProjectSeagull simulation dashboard.

## Prerequisites

- Python 3.10+
- PostgreSQL running with initialized database (run `Scripts/init_db.py` first)
- Dependencies from project root `requirements.txt`

## Setup

```bash
# Install backend-specific dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

The API will be available at http://localhost:8000

## API Documentation

Once running, visit:
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc

## Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/signals` | List all signals |
| POST | `/api/signals` | Create/update signal |
| DELETE | `/api/signals/{id}` | Delete signal |
| GET | `/api/tests` | List test definitions |
| POST | `/api/tests` | Create/update test |
| DELETE | `/api/tests/{name}` | Delete test |
| GET | `/api/jobs` | List jobs |
| POST | `/api/jobs` | Create job |
| DELETE | `/api/jobs/{test}/{agent}` | Delete job |
| GET | `/api/agents` | List agents |
| POST | `/api/agents/clone` | Clone agent |
| POST | `/api/simulation/start` | Start simulation session |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/simulation/{session_id}` | Real-time simulation streaming |

## WebSocket Protocol

### Client Messages

```json
// Start simulation
{"action": "start", "test_names": ["quick"]}

// Stop simulation
{"action": "stop"}

// Ping
{"action": "ping"}
```

### Server Messages

```json
// Status update
{"type": "status", "status": "started", "jobs_total": 3}

// Job started
{"type": "job_start", "job_id": "quick_my_agent", "job_index": 0, ...}

// Bar update (real-time)
{"type": "bar_update", "job_id": "...", "bar": {...}, "equity": 100500, ...}

// Job completed
{"type": "job_complete", "job_id": "...", "result": {...}}

// Error
{"type": "error", "message": "..."}
```

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app entry
│   ├── routers/         # API route handlers
│   │   ├── signals.py
│   │   ├── tests.py
│   │   ├── jobs.py
│   │   ├── agents.py
│   │   └── simulation.py
│   ├── websocket/
│   │   └── handler.py   # WebSocket endpoint
│   ├── services/
│   │   ├── simulation_runner.py  # Backtest engine wrapper
│   │   └── job_manager.py        # Concurrent job execution
│   └── models/
│       └── schemas.py   # Pydantic models
├── requirements.txt
├── run.py               # Dev server launcher
└── README.md
```
