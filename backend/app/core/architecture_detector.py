import os
import re
from typing import Dict, Any, Optional, List


ARCHITECTURE_PATTERNS = [
    {
        "name": "MVC",
        "indicators": [
            r"(?i)controllers?",
            r"(?i)views?",
            r"(?i)models?",
            r"(?i)routes?",
        ],
        "weight": 1,
    },
    {
        "name": "Layered Architecture",
        "indicators": [
            r"(?i)layers?",
            r"(?i)presentation",
            r"(?i)business(?:ness)?",
            r"(?i)persistence",
            r"(?i)repositor(?:y|ies)",
        ],
        "weight": 1,
    },
    {
        "name": "Microservices",
        "indicators": [
            r"(?i)microservice",
            r"(?i)service\s*-\s*\w+",
            r"(?i)api\s*gateway",
            r"(?i)docker-compose",
            r"(?i)kubernetes",
        ],
        "weight": 1,
    },
    {
        "name": "Clean Architecture",
        "indicators": [
            r"(?i)use\s*cases?",
            r"(?i)entities?",
            r"(?i)interfaces?\s*adapters?",
            r"(?i)infrastructure",
        ],
        "weight": 1,
    },
    {
        "name": "Event-Driven Architecture",
        "indicators": [
            r"(?i)event\s*(?:bus|sourcing|driven)",
            r"(?i)message\s*(?:queue|broker|bus)",
            r"(?i)publish",
            r"(?i)subscribe",
            r"(?i)rabbitmq|kafka|redis",
        ],
        "weight": 1,
    },
    {
        "name": "Hexagonal Architecture",
        "indicators": [
            r"(?i)ports?\s*and\s*adapters?",
            r"(?i)hexagonal",
            r"(?i)inbound",
            r"(?i)outbound",
            r"(?i)driven\s*ports?",
        ],
        "weight": 1,
    },
    {
        "name": "Serverless Architecture",
        "indicators": [
            r"(?i)serverless",
            r"(?i)lambda\s*function",
            r"(?i)cloud\s*function",
            r"(?i)faas",
        ],
        "weight": 1,
    },
    {
        "name": "Domain-Driven Design",
        "indicators": [
            r"(?i)domain\s*(?:model|service|event)",
            r"(?i)aggregate",
            r"(?i)bounded\s*context",
            r"(?i)value\s*object",
        ],
        "weight": 1,
    },
    {
        "name": "Client-Server",
        "indicators": [
            r"(?i)\bclient\b",
            r"(?i)\bserver\b",
            r"(?i)\bfrontend\b|front-end",
            r"(?i)\bbackend\b|back-end",
        ],
        "weight": 1,
    },
]


class ArchitectureDetector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def detect(self) -> Optional[Dict[str, Any]]:
        scores = {}
        evidence = {}

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "venv"]
            rel_path = os.path.relpath(root, self.repo_path)

            for pattern in ARCHITECTURE_PATTERNS:
                name = pattern["name"]
                if name not in scores:
                    scores[name] = 0
                    evidence[name] = []

                for indicator in pattern["indicators"]:
                    # Check directory names
                    if re.search(indicator, rel_path):
                        scores[name] += pattern["weight"]
                        evidence[name].append(f"directory:{rel_path}")

                    # Check file names
                    for f in files:
                        if re.search(indicator, f):
                            scores[name] += pattern["weight"] * 0.5
                            evidence[name].append(f"file:{f}")

            # Check file contents
            for f in files:
                if any(f.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".md", ".yaml", ".yml", ".json"]):
                    file_path = os.path.join(root, f)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read(5000)  # Read first 5KB
                            for pattern in ARCHITECTURE_PATTERNS:
                                name = pattern["name"]
                                for indicator in pattern["indicators"]:
                                    if re.search(indicator, content):
                                        scores[name] += pattern["weight"] * 0.3
                    except Exception:
                        continue

        if not scores:
            return None

        best = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = round(scores[best] / total * 100, 2) if total > 0 else 0

        # Sort and format evidence for the top pattern
        top_evidence = evidence.get(best, [])
        unique_evidence = list(dict.fromkeys(top_evidence))[:10]  # deduplicate, max 10

        return {
            "pattern": best,
            "confidence": min(confidence, 99.0),
            "description": self._get_description(best),
            "layers": self._get_layers(best),
            "scores": scores,
            "evidence": unique_evidence,
        }

    def _get_description(self, pattern: str) -> str:
        descriptions = {
            "MVC": "Model-View-Controller architecture with separation of data, UI, and logic",
            "Layered Architecture": "Organized into horizontal layers with strict dependency direction",
            "Microservices": "Distributed architecture with independently deployable services",
            "Clean Architecture": "Dependency inversion with concentric layers of abstraction",
            "Event-Driven Architecture": "Asynchronous communication through event production and consumption",
            "Hexagonal Architecture": "Ports and adapters pattern with core business logic isolation",
            "Serverless Architecture": "Cloud-native architecture with function-as-a-service components",
            "Domain-Driven Design": "Business domain centric design with bounded contexts",
            "Client-Server": "Traditional two-tier architecture with distinct client and server components",
        }
        return descriptions.get(pattern, f"{pattern} architecture pattern detected")

    def _get_layers(self, pattern: str) -> List[str]:
        layers = {
            "MVC": ["Model (Data Layer)", "View (Presentation Layer)", "Controller (Business Logic)"],
            "Layered Architecture": ["Presentation", "Business Logic", "Persistence", "Database"],
            "Microservices": ["API Gateway", "Individual Services", "Message Bus", "Data Stores"],
            "Clean Architecture": ["Frameworks & Drivers", "Interface Adapters", "Application Logic", "Domain Entities"],
            "Event-Driven Architecture": ["Event Producers", "Event Bus", "Event Consumers", "Event Store"],
            "Hexagonal Architecture": ["Inbound Adapters", "Ports", "Core Domain", "Outbound Adapters"],
            "Serverless Architecture": ["API Gateway", "Functions", "Event Sources", "Managed Services"],
            "Domain-Driven Design": ["Presentation", "Application", "Domain", "Infrastructure"],
            "Client-Server": ["Client Application", "Network", "Server Application", "Database"],
        }
        return layers.get(pattern, [])
