from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.database import init_db, get_db, engine
from app import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield
    # Cleanup (if needed)
    engine.dispose()


app = FastAPI(
    title="Industry Mood Prospecting MVP",
    description="Sistema semi-autónomo de prospección B2B para Industry Mood",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Industry Mood Prospecting MVP API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# TODO: Import and include routers
# from app.routers import leads, campaigns, sequences, analytics
# app.include_router(leads.router, prefix="/leads", tags=["leads"])
# app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
# app.include_router(sequences.router, prefix="/sequences", tags=["sequences"])
# app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)