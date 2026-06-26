from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.app.models.analysis import DiagramRequest
from backend.app.services.diagram_service import DiagramService
from backend.app.api.routes.analyze import analysis_cache

router = APIRouter(prefix="/api/diagrams", tags=["diagrams"])
diagram_service = DiagramService()


@router.post("/")
async def generate_diagram(request: DiagramRequest):
    """Generate a specific diagram type for an analysis."""
    result = analysis_cache.get(request.analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Use cached diagram if available
    if request.diagram_type in result.diagrams:
        mermaid_code = result.diagrams[request.diagram_type]
    else:
        # Generate on demand
        data = {
            "architecture": result.architecture.model_dump() if result.architecture else {},
            "language_stats": [ls.model_dump() for ls in result.language_stats],
            "dependencies": [d.model_dump() for d in result.dependencies],
            "modules": [m.model_dump() for m in result.modules],
        }
        mermaid_code = diagram_service.generate_mermaid_diagram(request.diagram_type, data)
        result.diagrams[request.diagram_type] = mermaid_code

    return {
        "diagram_type": request.diagram_type,
        "mermaid": mermaid_code,
        "repository": result.repository.name,
    }


@router.get("/types")
async def get_diagram_types():
    """Get available diagram types."""
    return {
        "types": [
            {"id": "architecture", "name": "Architecture Diagram", "description": "High-level system architecture"},
            {"id": "dependency", "name": "Dependency Graph", "description": "External and internal dependencies"},
            {"id": "sequence", "name": "Sequence Diagram", "description": "Request lifecycle flow"},
            {"id": "class", "name": "Class Diagram", "description": "Class hierarchy and relationships"},
            {"id": "layer", "name": "Layer Diagram", "description": "Architecture layer relationships"},
        ]
    }


@router.get("/{analysis_id}")
async def get_all_diagrams(analysis_id: str):
    """Get all diagrams for an analysis."""
    result = analysis_cache.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "repository": result.repository.name,
        "diagrams": result.diagrams,
    }
