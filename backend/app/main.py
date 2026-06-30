from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import HTTPException
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


frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

if os.path.exists(frontend_dist):
    assets_path = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
