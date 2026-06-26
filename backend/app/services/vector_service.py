import os
import uuid
from typing import List, Dict, Any, Optional


class VectorService:
    def __init__(self, persist_directory: str = "./data/vector_db"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._embeddings_file = os.path.join(persist_directory, "documents.json")
        self._load_documents()

    def index_repository(self, repo_path: str, analysis_id: str):
        """Index source code files into the vector store."""
        documents = []

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "venv" and d != "__pycache__"]
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                ext = os.path.splitext(file)[1].lower()

                if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
                           ".go", ".rs", ".cs", ".php", ".rb", ".kt", ".swift", ".dart", ".scala",
                           ".lua", ".sh", ".r", ".sql", ".yaml", ".yml", ".json", ".xml", ".toml",
                           ".md", ".html", ".css", ".scss", ".less"):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        if content.strip():
                            doc_id = str(uuid.uuid4())
                            documents.append({
                                "id": doc_id,
                                "text": content,
                                "metadata": {
                                    "file": rel_path,
                                    "extension": ext,
                                    "analysis_id": analysis_id,
                                    "size": len(content),
                                }
                            })
                    except Exception:
                        continue

        self._documents[analysis_id] = documents

        # Persist to JSON file
        self._save_documents()

    def search(self, analysis_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword-based search (in production would use embeddings)."""
        documents = self._documents.get(analysis_id, [])
        if not documents:
            return []

        query_terms = query.lower().split()
        scored = []

        for doc in documents:
            text = doc["text"].lower()
            score = sum(1 for term in query_terms if term in text)

            # Boost score for matches in metadata
            meta = doc.get("metadata", {})
            for term in query_terms:
                if term in meta.get("file", "").lower():
                    score += 3
                if term in meta.get("extension", "").lower():
                    score += 1

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scored[:top_k]:
            text = doc["text"]
            results.append({
                "file": doc["metadata"]["file"],
                "text": text[:1000],
                "score": score,
                "extension": doc["metadata"]["extension"],
            })

        return results

    def get_all_documents(self, analysis_id: str) -> List[Dict[str, Any]]:
        docs = self._documents.get(analysis_id, [])
        results = []
        for doc in docs:
            results.append({
                "file": doc["metadata"]["file"],
                "size": doc["metadata"]["size"],
                "extension": doc["metadata"]["extension"],
            })
        return results

    def delete_analysis(self, analysis_id: str):
        if analysis_id in self._documents:
            del self._documents[analysis_id]
            self._save_documents()

    def _save_documents(self):
        try:
            import json
            with open(self._embeddings_file, "w", encoding="utf-8") as f:
                json.dump(self._documents, f, default=str)
        except Exception:
            pass

    def _load_documents(self):
        try:
            import json
            if os.path.exists(self._embeddings_file):
                with open(self._embeddings_file, "r", encoding="utf-8") as f:
                    self._documents = json.load(f)
        except Exception:
            self._documents = {}
