# PlanetMind MVP

Software scaffold for the PlanetMind project — a cloud-native, explainable, multi-agent AI platform for global risk prediction:

- **Backend** (FastAPI): climate & pandemic ML modules (train/version/promote/predict), SHAP explainability, multi-agent orchestration, simulated federated learning, an in-process knowledge graph, and a generic risk-sandbox heuristic for health/cyber/economic domains.
- **Control-plane** (Django): authentication, organizations/teams, model governance (registry, promotion approvals, audit trail).
- **Frontend** (React + TypeScript): dashboard covering all of the above, with charts and a knowledge-graph visualization.
- **Local infra**: Dockerfiles, docker-compose (Postgres, Prometheus, Grafana), GitHub Actions CI.

## Structure

```text
planetmind/
  backend/
  control-plane/
  frontend/
  monitoring/
  .github/workflows/
  docker-compose.yml
```

## Run locally (without Docker)

### Backend

```powershell
cd c:\Desktop\Project\planetmind\backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd c:\Desktop\Project\planetmind\frontend
npm install
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm run dev
```

## Run with Docker

```powershell
cd c:\Desktop\Project\planetmind
docker compose up --build
```

Then open `http://localhost:5173`.

## One-command startup on Windows

From the project root:

```powershell
cd c:\Desktop\Project\planetmind
.\start-dev-windows.bat
```

This opens two terminal windows:
- Backend on `http://localhost:8000`
- Frontend on `http://localhost:5173`

## Module 1: Climate Analytics (Dataset -> Train -> Persisted Predictions)

The backend now includes a production-style Climate Analytics module with:
- CSV dataset ingestion
- Model training (scikit-learn RandomForest regressor)
- Persisted model metadata in PostgreSQL
- Persisted prediction history in PostgreSQL

### Start full stack with PostgreSQL

```powershell
cd c:\Desktop\Project\planetmind
docker compose up --build
```

### 1) Train a climate model from a CSV dataset

The CSV must include a target column (default: `risk_score`) and numeric feature columns.

```powershell
curl -X POST "http://localhost:8000/api/v1/climate/train" ^
  -F "dataset=@C:\path\to\climate_dataset.csv" ^
  -F "target_column=risk_score"
```

### 2) Run prediction (persisted to PostgreSQL)

```powershell
curl -X POST "http://localhost:8000/api/v1/climate/predict" ^
  -H "Content-Type: application/json" ^
  -d "{\"region\":\"East Africa\",\"features\":{\"temperature_anomaly\":0.73,\"rainfall_deficit\":0.62,\"soil_moisture_drop\":0.55,\"wildfire_index\":0.21}}"
```

### 3) View persisted prediction history

```powershell
curl "http://localhost:8000/api/v1/climate/predictions?limit=20"
```

### 4) List models and promote active model version

```powershell
curl "http://localhost:8000/api/v1/climate/models?limit=20"
curl -X POST "http://localhost:8000/api/v1/climate/models/1/promote"
```

## Database Migrations (Alembic)

Alembic is configured in `backend/alembic.ini` with migration scripts under `backend/alembic/versions`.

### Run migrations

```powershell
cd c:\Desktop\Project\planetmind\backend
python -m alembic upgrade head
```

### Create a new migration

```powershell
cd c:\Desktop\Project\planetmind\backend
python -m alembic revision --autogenerate -m "describe change"
```

### Roll back one migration

```powershell
cd c:\Desktop\Project\planetmind\backend
python -m alembic downgrade -1
```

## Frontend Climate & Pandemic Analytics UI

The React dashboard includes Climate Analytics and Pandemic Analytics views (same generic module workflow, mounted twice) with:
- Dataset CSV upload + model training
- Model version list with active model promotion
- Prediction execution using the active model, with a SHAP explanation chart
- Prediction history table sourced from PostgreSQL-backed API
- A federated learning subsection (see below)

Open `http://localhost:5173`, then use the `Climate Analytics` or `Pandemic Analytics` tab to run the full flow end-to-end.

## Explainable AI (SHAP)

Every prediction from `/api/v1/{module}/predict` is explained with SHAP (`shap.TreeExplainer`) against the trained RandomForest model, returning per-feature contributions and a base value. Explanations are persisted alongside each prediction and viewable in the dedicated `Explainability` tab, or via:

```powershell
curl "http://localhost:8000/api/v1/climate/predictions?limit=5"
```

## Multi-Agent Orchestration

A deterministic pipeline of five cooperating agents (ingestion → prediction → explainability → simulation → reporting) processes each request end-to-end, with the full execution trace persisted for auditability. No external LLM/API key required.

```powershell
curl -X POST "http://localhost:8000/api/v1/agents/pipeline/run" ^
  -H "Content-Type: application/json" ^
  -d "{\"module\":\"climate\",\"region\":\"Sahel Belt\",\"features\":{\"feature_a\":0.5,\"feature_b\":0.5}}"

curl "http://localhost:8000/api/v1/agents/pipeline/runs?limit=10"
```

Also available in the `Multi-Agent Console` tab.

## Federated Learning (Simulated)

Simulates multiple client organizations training a linear model locally on private data shards, aggregated via federated averaging (FedAvg), compared against a centralized baseline trained on pooled data (same held-out test split) — directly testing whether federated training can match centralized accuracy without any organization sharing raw data.

```powershell
curl -X POST "http://localhost:8000/api/v1/climate/federated/train" ^
  -F "dataset=@C:\path\to\climate_dataset.csv" ^
  -F "target_column=risk_score" ^
  -F "num_clients=3" ^
  -F "rounds=10"
```

## Knowledge Graph

`GET /api/v1/knowledge-graph` builds an in-process graph (via `networkx`) from existing modules, model runs, predictions, and regions, and returns it as `{nodes, edges}` for visualization. Viewable in the `Knowledge Graph` tab (a dependency-free SVG radial layout).

## Monitoring

The backend exposes Prometheus metrics at `/metrics` (via `prometheus-fastapi-instrumentator`), and the control-plane exposes its own at `/metrics` (via `django-prometheus`). `docker compose up` also starts Prometheus (`http://localhost:9090`, pre-configured to scrape both services) and Grafana (`http://localhost:3000`, default login `admin` / `admin`).

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs the backend (`pytest`), control-plane (`manage.py test`), and frontend (`npm run build` + `npm run test`) suites on every push/PR to `main`.
