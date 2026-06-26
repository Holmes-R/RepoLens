from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RepoStatus(str, Enum):
    PENDING = "pending"
    CLONING = "cloning"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class LanguageStats(BaseModel):
    language: str
    percentage: float
    files: int
    lines: int


class Dependency(BaseModel):
    name: str
    version: str
    type: str  # internal, external
    source: str  # npm, pypi, cargo, etc.


class ModuleInfo(BaseModel):
    name: str
    path: str
    type: str  # file, directory
    language: Optional[str] = None
    imports: List[str] = []
    exports: List[str] = []
    classes: List[str] = []
    functions: List[str] = []
    dependencies: List[Dict[str, str]] = []


class ArchitectureInfo(BaseModel):
    pattern: str
    confidence: float
    description: str
    layers: List[str] = []
    scores: Dict[str, float] = {}
    evidence: List[str] = []
    components: List[Dict[str, Any]] = []


class Framework(BaseModel):
    name: str
    version: Optional[str] = None
    category: str  # frontend, backend, testing, database, etc.


class ComplexityMetrics(BaseModel):
    total_files: int
    total_lines: int
    total_functions: int
    total_classes: int
    avg_function_length: float
    avg_complexity: float
    max_complexity: float
    max_complexity_file: Optional[str] = None


class Repository(BaseModel):
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    url: str
    name: str
    full_name: str
    default_branch: str = "main"
    description: Optional[str] = None
    status: RepoStatus = RepoStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    local_path: Optional[str] = None
    error_message: Optional[str] = None


class AnalysisResult(BaseModel):
    repository: Repository
    language_stats: List[LanguageStats] = []
    frameworks: List[Framework] = []
    dependencies: List[Dependency] = []
    modules: List[ModuleInfo] = []
    architecture: Optional[ArchitectureInfo] = None
    call_graph: Dict[str, List[str]] = {}
    complexity: Optional[ComplexityMetrics] = None
    health_score: Optional[float] = None
    contributors: List[Dict[str, Any]] = []
    readme_content: Optional[str] = None
    diagrams: Dict[str, str] = {}  # type -> mermaid/markup string
    analyzed_at: datetime = Field(default_factory=datetime.now)
