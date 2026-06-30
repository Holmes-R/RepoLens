import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    REPO_STORAGE_PATH: str = os.getenv("REPO_STORAGE_PATH", "./data/repos")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    MAX_FILE_SIZE_KB: int = int(os.getenv("MAX_FILE_SIZE_KB", "500"))
    MAX_REPO_SIZE_MB: int = int(os.getenv("MAX_REPO_SIZE_MB", "100"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER",
        "gemini" if os.getenv("GEMINI_API_KEY") else
        "groq" if os.getenv("GROQ_API_KEY") else
        "ollama")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

config = Config()
