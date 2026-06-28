# RepoLens

Intelligent GitHub Repository Analyzer — Understand any codebase in minutes.

**Live deployment:** [http://repolens/](http://repolens/)

---

## Situation

Developers join new projects, review pull requests, or audit unfamiliar repositories and face a steep learning curve. Understanding a codebase's architecture, dependencies, call flows, and data models requires manually reading files, switching between tools, and piecing together context — a slow, error-prone process with no centralized view.

## Task

Build a tool that, given any public GitHub repository URL, automatically:
- Clones and analyzes the full codebase
- Detects architecture patterns (MVC, Clean Architecture, Microservices, etc.)
- Extracts dependencies by package manager (npm, PyPI, Cargo, Go, Pub, Maven, RubyGems)
- Generates call graphs and code metrics via AST parsing
- Discovers database schemas from SQL, ORM models, and migration files
- Renders interactive Mermaid diagrams (architecture, dependency, sequence, directory, layer)
- Provides a natural-language AI chat powered by local Ollama for codebase Q&A

All behind a flat dark-themed dashboard accessible from a single URL.

## Action

- **Backend:** Python/FastAPI service with a modular analysis pipeline — clones repos, walks ASTs, detects frameworks, and emits structured JSON. An Ollama service retrieves relevant source files and answers questions via `qwen2.5:7b`.
- **Frontend:** React/TypeScript SPA built with Vite and Tailwind CSS. An interactive dashboard (7 tabs: Overview, Architecture, Dependencies, Database, Call Graph, Diagrams, Contributors) displays results, renders Mermaid diagrams with a custom dark theme, and hosts the AI chat sidebar.
- **Diagrams:** All 5 diagram types (architecture, dependency, sequence, directory, layer) generated server-side as Mermaid definitions and rendered client-side. Uses `theme: 'base'` with custom theme variables for dark-mode compatibility.
- **Docker Deployment:** Two containers — `repolens-backend` (uvicorn on `:8000`) and `repolens-frontend` (nginx on `:80`). nginx proxies `/api` to the backend with a 300s timeout for long-running analysis and AI requests. Analysis data persists via a named volume.
- **AI Integration:** Ollama runs on the host and is accessed from the container via `host.docker.internal`. The chat uses keyword-based file retrieval (no vector DB) to find relevant source files and passes them as context in the system prompt.

## Result

A fully containerized, self-hosted application that reduces codebase onboarding from hours to minutes. Paste any public GitHub URL and instantly see:

| Feature | Description |
|---|---|
| Architecture Detection | MVC, Clean Architecture, Layered, Microservices, Event-Driven, Hexagonal, Serverless, DDD — with confidence scoring |
| Dependency Graph | npm, PyPI, Cargo, Go, RubyGems, Pub, Maven — grouped by source with version info |
| Call Graph | Function-level call relationships across Python, JS, TS, Go, Rust, Java, PHP, Ruby |
| Schema Analysis | SQL files, migrations, ORM models (Django, SQLAlchemy, TypeORM, Prisma, Laravel, Alembic) |
| Directory Tree | Interactive project structure diagram (depth-limited) |
| Code Metrics | Files, lines, functions, classes, cyclomatic complexity, average function length |
| AI Chat | Natural-language Q&A about the repository using local Ollama (`qwen2.5:7b`) |
| Framework Detection | Identifies frameworks and libraries with version info |
| Language Breakdown | Per-file language detection with percentage distribution |
| Diagrams | 5 types: architecture, dependency, sequence, directory, layer — all rendered as Mermaid |

---

## Quick Start

### Docker (recommended)

```bash
docker compose up --build -d
```

Then open [http://repolens/](http://repolens/) (requires hosts entry: `127.0.0.1 repolens`).

### Backend (manual)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your keys
python -m backend.app.main
```

### Frontend (manual)

```bash
cd frontend
npm install
npm run dev
```

## Prerequisites

- **Docker** (for containerized deployment) or **Python 3.12+** / **Node 20+** (for manual setup)
- **Ollama** running locally with `qwen2.5:7b` (or another model) for AI chat
- A **GitHub token** (optional, but increases API rate limits for public repos)

## Tech Stack

- **Backend:** Python, FastAPI, GitPython, tree-sitter, requests
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Mermaid, Lucide React
- **AI:** Ollama (`qwen2.5:7b`)
- **Infrastructure:** Docker, nginx, docker compose
