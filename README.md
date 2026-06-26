# RepoLens AI

Intelligent GitHub Repository Analyzer - Understand any repository in minutes.

## Architecture

```
repo-lens/
├── backend/          # Python FastAPI server
│   ├── app/
│   │   ├── api/      # REST API routes
│   │   ├── core/     # Analysis engine
│   │   ├── services/ # Git, Vector, LLM, Diagram services
│   │   └── models/   # Pydantic data models
│   └── requirements.txt
├── frontend/         # React + TypeScript + Vite
│   └── src/
│       ├── pages/    # Home, Analysis, Diagrams, Chat
│       ├── components/
│       └── api/      # API client
└── README.md
```

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your keys
python -m backend.app.main
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Features

- Repository cloning and analysis
- Language and framework detection
- Dependency graph extraction
- AST parsing and call graph construction
- Architecture pattern detection (MVC, Microservices, etc.)
- Complexity metrics and health scoring
- Mermaid diagram generation (architecture, dependency, sequence, component, layer)
- AI-powered repository chat
