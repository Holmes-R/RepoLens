from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.app.core.health_score import HealthScoreCalculator
from backend.app.api.routes.analyze import analysis_cache

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/{analysis_id}")
async def get_health_score(analysis_id: str):
    """Get health score report for a repository."""
    result = analysis_cache.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Build analysis data for health calculator
    analysis_data = {
        "dependencies": [d.model_dump() for d in result.dependencies],
        "frameworks": [fw.model_dump() for fw in result.frameworks],
        "architecture": result.architecture.model_dump() if result.architecture else {},
        "complexity": result.complexity.model_dump() if result.complexity else {},
        "modules": [m.model_dump() for m in result.modules],
        "contributors": result.contributors,
        "readme_content": result.readme_content,
    }

    calculator = HealthScoreCalculator(analysis_data)
    scores = calculator.calculate()

    return {
        "repository": result.repository.name,
        "scores": scores,
    }
