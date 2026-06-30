# RepoLens

Intelligent GitHub Repository Analyzer — Understand any codebase in minutes.

---

## Situation

Developers join new projects, review pull requests, or audit unfamiliar repositories every day. Understanding a codebase's architecture, dependencies, call flows, and data models requires manually reading dozens of files, switching between multiple tools, and piecing together context from scattered sources. This process is slow, error-prone, and lacks a centralized view — costing hours or days of productivity for each new codebase encountered.

## Task

Build a tool that, given any public GitHub repository URL, automatically:
- Clones and deeply analyzes the full codebase
- Detects architecture patterns (MVC, Clean Architecture, Microservices, Event-Driven, Hexagonal, Serverless, DDD) with confidence scoring
- Extracts dependencies from 7 package managers (npm, PyPI, Cargo, Go, RubyGems, Pub, Maven)
- Generates function-level call graphs via AST parsing across 8 languages (Python, JS, TS, Go, Rust, Java, PHP, Ruby)
- Discovers database schemas from SQL files, migration scripts, and ORM models (Django, SQLAlchemy, TypeORM, Prisma, Laravel, Alembic)
- Renders 5 types of interactive Mermaid diagrams (architecture, dependency, sequence, directory, layer)
- Provides natural-language AI chat for codebase Q&A powered by Groq or Gemini

All delivered through a flat dark-themed dashboard accessible from a single URL.

## Action

### Architecture
- **Backend:** Python/FastAPI service with a modular analysis pipeline — clones repos via GitPython, walks ASTs with tree-sitter, detects frameworks, computes cyclomatic complexity, and emits structured JSON. A pluggable AI service supports multiple providers (Ollama locally, Groq, Gemini) for context-aware codebase Q&A.
- **Frontend:** React/TypeScript SPA built with Vite and Tailwind CSS. Interactive dashboard with 7 tabs (Overview, Architecture, Dependencies, Database, Call Graph, Diagrams, Contributors). Mermaid diagrams use `theme: 'base'` with custom dark-mode theme variables. Sidebar navigation preserves repo context across Analysis, Diagrams, and Chat views via URL-based routing.
- **AI Chat:** Keyword-based file retrieval finds relevant source files from the analyzed codebase and passes them as context to the AI. Supports Ollama (local), Groq (`llama-3.3-70b`), or Gemini (`gemini-2.0-flash`) — configurable via a single environment variable.

### Deployment
- **Single-container Docker** — builds frontend (Node) and backend (Python) in one image. Backend serves the React SPA as static files and handles API routes under `/api/`.
- **Render-ready** — deployable as a Docker web service with persistent disk for cloned repositories.
- **Local development** — `docker compose up` or manual backend + frontend setup.

## Result

A fully containerized, self-hosted application that reduces codebase onboarding from hours to minutes. Paste any public GitHub URL and instantly see:

| Feature | Description |
|---|---|
| Architecture Detection | MVC, Clean Architecture, Layered, Microservices, Event-Driven, Hexagonal, Serverless, DDD — with confidence scoring |
| Dependency Graph | npm, PyPI, Cargo, Go, RubyGems, Pub, Maven — grouped by source with version info |
| Call Graph | Function-level call relationships across 8 languages |
| Schema Analysis | Detects DB schemas from SQL files, migrations, ORM models |
| Directory Tree | Interactive project structure diagram |
| Code Metrics | Files, lines, functions, classes, cyclomatic complexity |
| AI Chat | Q&A about the repo using Groq, Gemini, or local Ollama |
| Framework Detection | Identifies frameworks with version info |
| Language Breakdown | Per-file language detection with distribution |
| Diagrams | 5 types: architecture, dependency, sequence, directory, layer |

---

## Quick Start

### Docker (local)

```bash
docker compose up --build -d
```

Open [http://localhost/](http://localhost/).

### Manual

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Set your API keys
python -m backend.app.main

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) (Vite dev server proxies API to backend).

---

## Deployment on Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service → Connect your repo
3. Set **Runtime** to `Docker`, **Dockerfile Path** to `./Dockerfile`
4. Add environment variables:
   - `GEMINI_API_KEY` — from [aistudio.google.com](https://aistudio.google.com/apikey) (free)
   - *or* `GROQ_API_KEY` — from [console.groq.com](https://console.groq.com) (free tier)
   - *or* `OPENAI_API_KEY` — from [platform.openai.com](https://platform.openai.com)
   - `GITHUB_TOKEN` — from [github.com/settings/tokens](https://github.com/settings/tokens) (optional, for higher rate limits)
   - `CORS_ORIGINS` — set to `https://your-app.onrender.com`
5. Add a **Disk** → Name: `repolens-data`, Mount Path: `/data`, Size: `1 GB`
6. Deploy

---

## Configuration

Set via environment variables (`.env` file for local, Render dashboard for production):

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | auto | `gemini`, `groq`, `ollama`, or `openai` — auto-detected from API key presence |
| `GEMINI_API_KEY` | — | Google Gemini API key (free, 60 req/min) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `GROQ_API_KEY` | — | Groq API key (free tier, rate limited) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ollama model name |
| `GITHUB_TOKEN` | — | GitHub personal access token |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins |
| `REPO_STORAGE_PATH` | `./data/repos` | Where cloned repos are stored |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Tech Stack

- **Backend:** Python, FastAPI, GitPython, Tree-sitter, requests
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Mermaid, Lucide React, Axios
- **AI:** Ollama (local), Groq (cloud), Gemini (cloud)
- **Infrastructure:** Docker, Render
