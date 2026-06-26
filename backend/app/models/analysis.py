from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalyzeRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"
    deep_analysis: bool = False


class AnalyzeResponse(BaseModel):
    analysis_id: str
    status: str
    message: str


class ChatRequest(BaseModel):
    analysis_id: str
    message: str
    history: List[Dict[str, str]] = []


class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []


class DiagramRequest(BaseModel):
    analysis_id: str
    diagram_type: str  # architecture, dependency, sequence, database, deployment
    focus: Optional[str] = None


class HealthReport(BaseModel):
    overall_score: float
    security_score: float
    maintainability_score: float
    documentation_score: float
    testing_score: float
    architecture_score: float
    performance_score: float
    quality_score: float
    complexity_score: float
    dependency_score: float
    activity_score: float
    details: Dict[str, Any] = {}
