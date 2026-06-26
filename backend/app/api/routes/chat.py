from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.app.models.analysis import ChatRequest, ChatResponse
from backend.app.services.vector_service import VectorService
from backend.app.services.llm_service import LLMService
from backend.app.config import config
from backend.app.api.routes.analyze import analysis_cache, analyzer

router = APIRouter(prefix="/api/chat", tags=["chat"])
vector_service = analyzer.vector_service
llm_service = LLMService(config.OPENAI_API_KEY, config.OPENAI_MODEL)


@router.post("/", response_model=ChatResponse)
async def chat_with_repository(request: ChatRequest):
    """Chat with a repository using AI."""
    result = analysis_cache.get(request.analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found. Please analyze the repository first.")

    # Search for relevant code (analyzer already indexed the repo)
    search_results = vector_service.search(request.analysis_id, request.message)

    # Build context from analysis data
    repo_info = {
        "name": result.repository.name,
        "description": result.repository.description,
        "architecture": result.architecture.model_dump() if result.architecture else {},
        "frameworks": [fw.model_dump() for fw in result.frameworks],
        "dependencies": [d.model_dump() for d in result.dependencies],
        "complexity": result.complexity.model_dump() if result.complexity else {},
        "health_score": result.health_score,
    }

    # Generate answer
    response_text = llm_service.answer_question(request.message, search_results, repo_info)

    # Extract sources
    sources = [r["file"] for r in search_results]

    return ChatResponse(
        response=response_text,
        sources=sources,
    )


@router.get("/sources/{analysis_id}")
async def get_indexed_sources(analysis_id: str):
    """Get list of indexed files for an analysis."""
    docs = vector_service.get_all_documents(analysis_id)
    return {"files": docs, "count": len(docs)}
