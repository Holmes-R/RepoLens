from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from backend.app.models.analysis import AnalyzeRequest, AnalyzeResponse
from backend.app.core.analyzer import RepositoryAnalyzer
from backend.app.config import config

router = APIRouter(prefix="/api/analyze", tags=["analysis"])
analyzer = RepositoryAnalyzer(config)
analysis_cache: Dict[str, Any] = {}


@router.post("/", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Start analysis of a GitHub repository."""
    try:
        result = analyzer.analyze(request.repo_url, request.branch, request.deep_analysis)
        analysis_cache[result.repository.id] = result
        return AnalyzeResponse(
            analysis_id=result.repository.id,
            status=result.repository.status,
            message="Analysis completed successfully" if result.repository.status == "completed"
                    else f"Analysis failed: {result.repository.error_message}",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get analysis results by ID."""
    result = analysis_cache.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/{analysis_id}/summary")
async def get_analysis_summary(analysis_id: str):
    """Get a summary of the analysis results."""
    result = analysis_cache.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "repository": {
            "name": result.repository.name,
            "url": result.repository.url,
            "status": result.repository.status,
        },
        "languages": [ls.model_dump() for ls in result.language_stats],
        "frameworks": [fw.model_dump() for fw in result.frameworks],
        "architecture": result.architecture.model_dump() if result.architecture else None,
        "complexity": result.complexity.model_dump() if result.complexity else None,
        "health_score": result.health_score,
        "dependencies_count": len(result.dependencies),
        "modules_count": len(result.modules),
        "contributors_count": len(result.contributors),
    }


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete an analysis from cache."""
    if analysis_id in analysis_cache:
        del analysis_cache[analysis_id]
    return {"status": "deleted"}
