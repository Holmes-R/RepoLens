from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import re
import os
import logging

from backend.app.models.analysis import ChatRequest, ChatResponse
from backend.app.config import config
from backend.app.services.ollama_service import AIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])
ai_service = AIService(
    provider=config.AI_PROVIDER,
    ollama_url=config.OLLAMA_URL,
    ollama_model=config.OLLAMA_MODEL,
    groq_api_key=config.GROQ_API_KEY,
    groq_model=config.GROQ_MODEL,
)

from backend.app.api.routes.analyze import analysis_cache


def _find_relevant_files(
    question: str,
    file_contents: Dict[str, str],
    modules: List[Dict[str, Any]],
    max_files: int = 8,
) -> str:
    keywords = set(re.findall(r'\w+', question.lower()))
    keywords -= {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "do", "does", "did", "has", "have", "had", "can", "could",
        "will", "would", "shall", "should", "may", "might", "must",
        "this", "that", "these", "those", "it", "its", "they", "them",
        "what", "where", "when", "why", "how", "which", "who", "whom",
        "in", "on", "at", "to", "for", "of", "with", "by", "from",
        "and", "or", "but", "not", "if", "then", "else", "so",
        "explain", "describe", "tell", "show", "find", "locate",
        "how", "does", "work", "about", "please",
    }
    if not keywords:
        return ""

    scored: List[tuple[int, str, str]] = []
    for path, content in file_contents.items():
        content_lower = content.lower()
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scored.append((score, path, content))

    module_texts = {}
    for m in modules:
        text = f"{m.get('name', '')} {' '.join(m.get('classes', []))} {' '.join(m.get('functions', []))}"
        module_texts[m.get('path', m.get('name', ''))] = text.lower()

    seen_paths = {s[1] for s in scored}
    for path, text in module_texts.items():
        if path in seen_paths:
            continue
        score = sum(2 for kw in keywords if kw in text)
        if score > 0:
            scored.append((score, path, file_contents.get(path, f"// {path}")))

    scored.sort(key=lambda x: -x[0])

    parts = []
    for score, path, content in scored[:max_files]:
        snippet = content[:2000]
        parts.append(f"--- {path} ---\n{snippet}")

    return "\n\n".join(parts)


def _build_system_prompt(
    repo_name: str, description: str | None, readme: str | None,
    modules: List[Dict[str, Any]], architecture: Dict[str, Any] | None,
    dependencies: List[Dict[str, Any]], database_schema: List[Dict[str, Any]],
) -> str:
    parts = [f"You are a code analysis assistant for the repository '{repo_name}'."]
    if description:
        parts.append(f"\nDescription: {description}")
    if readme:
        parts.append(f"\nREADME:\n{readme[:2000]}")
    if architecture:
        parts.append(f"\nArchitecture: {architecture.get('pattern', 'Unknown')} ({architecture.get('confidence', 0)}%)")
        layers = architecture.get('layers', [])
        if layers:
            parts.append(f"Layers: {', '.join(layers)}")
    if modules:
        lines = [f"\nModules ({len(modules)}):"]
        for m in modules[:30]:
            cls = ', '.join(m.get('classes', [])[:5])
            funcs = ', '.join(m.get('functions', [])[:5])
            lines.append(f"  {m.get('path', m.get('name', ''))}: [{cls}] [{funcs}]")
        parts.append('\n'.join(lines))
    if database_schema:
        lines = [f"\nDatabase tables ({len(database_schema)}):"]
        for t in database_schema:
            cols = ', '.join(f"{c.get('name','')} {c.get('type','')}" for c in t.get('columns', [])[:8])
            lines.append(f"  {t.get('name')}: {cols}")
        parts.append('\n'.join(lines))
    if dependencies:
        top = sorted(dependencies, key=lambda d: d.get('name', ''))[:20]
        parts.append(f"\nDependencies: {', '.join(d.get('name','') for d in top)}")
    parts.append(
        "\n\nAnswer the user's question about this repository using the context and your knowledge."
        " Reference specific files and code. Be concise."
    )
    return '\n'.join(parts)


@router.post("/", response_model=ChatResponse)
async def chat_with_repo(request: ChatRequest):
    analysis_id = request.analysis_id
    result = analysis_cache.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    if not ai_service.is_available():
        provider = config.AI_PROVIDER
        detail = f"AI provider '{provider}' is not available."
        if provider == "ollama":
            detail += f" Cannot reach Ollama at {config.OLLAMA_URL}."
        elif provider == "groq":
            detail += " GROQ_API_KEY is missing or invalid."
        raise HTTPException(status_code=503, detail=detail)

    file_contents = getattr(result, 'file_contents', {}) or {}
    modules_dicts = [m.model_dump() for m in getattr(result, 'modules', [])]
    arch_dict = result.architecture.model_dump() if result.architecture else None
    dep_dicts = [d.model_dump() for d in getattr(result, 'dependencies', [])]
    db_schema_dicts = [t.model_dump() for t in getattr(result, 'database_schema', [])]

    repo_name = result.repository.name if result.repository else "unknown"
    repo_desc = getattr(result.repository, 'description', None)
    readme = getattr(result, 'readme_content', None)

    system_prompt = _build_system_prompt(
        repo_name, repo_desc, readme,
        modules_dicts, arch_dict, dep_dicts, db_schema_dicts,
    )

    relevant_files = _find_relevant_files(request.message, file_contents, modules_dicts)
    context = system_prompt
    if relevant_files:
        context += f"\n\nRelevant files:\n{relevant_files}"

    messages = [{"role": "system", "content": context}]

    for msg in request.history[-10:]:
        messages.append(msg)

    messages.append({"role": "user", "content": request.message})

    response = ai_service.chat(messages)

    if response is None:
        raise HTTPException(
            status_code=503,
            detail=f"AI provider '{config.AI_PROVIDER}' returned no response. Check the backend logs for details.",
        )

    sources = []
    for path in file_contents:
        if path in response or os.path.basename(path) in response:
            sources.append(path)
    for m in modules_dicts:
        path = m.get('path', '')
        if path and path not in sources and path in response:
            sources.append(path)

    return ChatResponse(response=response, sources=sources[:10])


@router.get("/test")
async def test_ai():
    """Test endpoint to verify the AI provider is working."""
    if not ai_service.is_available():
        return {
            "status": "error",
            "message": f"AI provider '{config.AI_PROVIDER}' is not available",
            "provider": config.AI_PROVIDER,
            "ollama_url": config.OLLAMA_URL,
            "model": config.OLLAMA_MODEL if config.AI_PROVIDER == "ollama" else config.GROQ_MODEL,
            "has_groq_key": bool(config.GROQ_API_KEY),
        }

    result = ai_service.test_chat()
    return {
        "status": "ok" if result and not result.startswith("ERROR") else "error",
        "message": f"AI provider '{config.AI_PROVIDER}' is available and responded",
        "provider": config.AI_PROVIDER,
        "model": config.OLLAMA_MODEL if config.AI_PROVIDER == "ollama" else config.GROQ_MODEL,
        "test_response": result,
    }
