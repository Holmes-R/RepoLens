from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.app.config import config
from backend.app.api.routes import analyze, diagrams, health, chat

app = FastAPI(
    title="RepoLens AI",
    description="Intelligent GitHub Repository Analyzer - Understand any repository in minutes",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze.router)
app.include_router(chat.router)
app.include_router(diagrams.router)
app.include_router(health.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "RepoLens AI"}


@app.get("/api/info")
async def api_info():
    return {
        "name": "RepoLens AI",
        "version": "1.0.0",
        "description": "Intelligent GitHub Repository Analyzer",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
