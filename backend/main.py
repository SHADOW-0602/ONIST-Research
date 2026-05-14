import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Add project root to sys.path for absolute imports
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

import asyncio
from contextlib import asynccontextmanager
from backend.pipeline.notebook_client import notebook_client

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database schema on startup
    await notebook_client.initialize_schema()
    
    # Start the Portfolio Performance Monitor
    from backend.pipeline.portfolio_monitor import portfolio_monitor
    asyncio.create_task(portfolio_monitor.start_monitoring(interval_seconds=3600))
    
    yield
    # Shutdown logic if any

app = FastAPI(
    title="ONIST Research Intelligence Platform",
    description="Multi-Agent RAG — Equity Research Intelligence System",
    version="1.0",
    lifespan=lifespan
)

# Allow CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3050"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "ONIST Platform API is running"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the ONIST Research Intelligence Platform"}

from backend.api import router as pipeline_router

# Include the API router
app.include_router(pipeline_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
