from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.agents import router as agents_router
from app.api.federated import climate_federated_router, pandemic_federated_router
from app.api.health import router as health_router
from app.api.knowledge_graph import router as knowledge_graph_router
from app.api.ml_modules import climate_router, pandemic_router
from app.api.risk import router as risk_router
from app.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="PlanetMind API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(risk_router)
app.include_router(climate_router)
app.include_router(pandemic_router)
app.include_router(climate_federated_router)
app.include_router(pandemic_federated_router)
app.include_router(agents_router)
app.include_router(knowledge_graph_router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root_status() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PlanetMind API</title>
  <style>
    body { margin: 0; min-height: 100vh; display: grid; place-items: center;
           font-family: "Segoe UI", sans-serif; background: #f2f6fd; color: #142033; }
    .card { background: #fff; border: 1px solid #d7e2f5; border-radius: 16px;
            padding: 2rem 2.5rem; box-shadow: 0 10px 30px rgba(11,42,92,.08); max-width: 520px; }
    .status { display: inline-flex; align-items: center; gap: .5rem; font-weight: 700;
              color: #17633d; background: #ddf5e8; border-radius: 999px; padding: .35rem .9rem; }
    .dot { width: 10px; height: 10px; border-radius: 50%; background: #22a06b; }
    a { color: #125ecf; font-weight: 600; text-decoration: none; }
    ul { padding-left: 1.1rem; line-height: 2; }
  </style>
</head>
<body>
  <div class="card">
    <p><span class="status"><span class="dot"></span> PlanetMind Backend is running</span></p>
    <p>FastAPI intelligence plane &middot; version 0.2.0</p>
    <ul>
      <li><a href="/api/v1/health">Health check</a> &mdash; /api/v1/health</li>
      <li><a href="/docs">Interactive API docs</a> &mdash; /docs</li>
      <li><a href="/metrics">Prometheus metrics</a> &mdash; /metrics</li>
      <li><a href="http://localhost:5173">Frontend app</a> &mdash; http://localhost:5173</li>
      <li><a href="http://localhost:8100">Control plane</a> &mdash; http://localhost:8100</li>
    </ul>
  </div>
</body>
</html>"""


Instrumentator().instrument(app).expose(app)
