import re
from typing import Dict, Any, List, Optional


class DiagramService:
    def _sanitize_mermaid_id(self, name: str) -> str:
        safe = name.replace(".", "_").replace("-", "_").replace("/", "_").replace("[", "_").replace("]", "_")
        safe = safe.replace("(", "_").replace(")", "_").replace(" ", "_").replace("+", "_plus_")
        return safe

    def _sanitize_mermaid_label(self, name: str) -> str:
        # Remove characters Mermaid interprets as shape syntax
        return re.sub(r"[\[\](){}<>]", "", name)

    def generate_mermaid_diagram(self, diagram_type: str, data: Dict[str, Any]) -> str:
        generators = {
            "architecture": self._generate_architecture_diagram,
            "dependency": self._generate_dependency_diagram,
            "sequence": self._generate_sequence_diagram,
            "class": self._generate_class_diagram,
            "layer": self._generate_layer_diagram,
        }
        generator = generators.get(diagram_type, self._generate_architecture_diagram)
        return generator(data)

    def _generate_architecture_diagram(self, data: Dict[str, Any]) -> str:
        arch = data.get("architecture", {})
        pattern = arch.get("pattern", "Unknown")
        layers = arch.get("layers", [])
        components = arch.get("components", [])

        mermaid = ["graph TD"]
        mermaid.append(f"    subgraph {pattern.replace(' ', '_')}[{pattern} Architecture]")

        if layers:
            for i, layer in enumerate(layers):
                safe_name = layer.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
                mermaid.append(f"        {safe_name}[{layer}]")
                if i > 0:
                    prev = layers[i-1].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
                    mermaid.append(f"        {prev} -->|communicates| {safe_name}")

        # Add language stats
        lang_stats = data.get("language_stats", [])
        mermaid.append("    end")
        if lang_stats:
            mermaid.append("    subgraph Languages[Languages]")
            for lang in lang_stats[:5]:
                safe = lang["language"].replace(" ", "_")
                mermaid.append(f"        {safe}[{lang['language']}: {lang['percentage']}%]")
            mermaid.append("    end")

        # Connect architecture to languages
        if layers and lang_stats:
            first = layers[0].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
            first_lang = lang_stats[0]["language"].replace(" ", "_")
            mermaid.append(f"    {first} -->|built with| {first_lang}")

        return "\n".join(mermaid)

    def _generate_dependency_diagram(self, data: Dict[str, Any]) -> str:
        deps = data.get("dependencies", [])
        lang_stats = data.get("language_stats", [])

        mermaid = ["graph LR"]
        mermaid.append("    subgraph Project[Project Dependencies]")

        # Group dependencies by source
        source_groups = {}
        for d in deps:
            source = d.get("source", "unknown")
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(d)

        colors = {
            "npm": "#4FC3F7",
            "pypi": "#FFD54F",
            "cargo": "#FF8A65",
            "go": "#81C784",
            "rubygems": "#CE93D8",
            "pub": "#4DD0E1",
            "maven": "#FF8A65",
        }

        for source, sdeps in source_groups.items():
            safe_source = self._sanitize_mermaid_id(source)
            color = colors.get(source, "#90CAF9")
            mermaid.append(f"        subgraph {safe_source}[{source.upper()} - {len(sdeps)} deps]")
            for d in sdeps:
                safe_name = self._sanitize_mermaid_id(d["name"])
                label = self._sanitize_mermaid_label(d["name"])
                mermaid.append(f"            {safe_name}[{label}]")
            mermaid.append("        end")

        mermaid.append("    end")

        # Show languages
        if lang_stats:
            mermaid.append("    subgraph Lang[Languages]")
            for lang in lang_stats[:3]:
                safe = lang["language"].replace(" ", "_")
                mermaid.append(f"        {safe}[{lang['language']}]")
            mermaid.append("    end")

        return "\n".join(mermaid)

    def _generate_sequence_diagram(self, data: Dict[str, Any]) -> str:
        arch = data.get("architecture", {})
        pattern = arch.get("pattern", "Unknown")
        layers = arch.get("layers", [])

        if not layers:
            layers = ["Client", "Server", "Database"]

        mermaid = ["sequenceDiagram"]
        mermaid.append("    participant Client as Client")
        mermaid.append("    participant Server as Server")

        if len(layers) > 2:
            for layer in layers[1:-1]:
                safe = layer.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
                mermaid.append(f"    participant {safe} as {layer}")

        mermaid.append("    participant DB as Database")

        mermaid.append("")
        mermaid.append("    Client->>Server: HTTP Request")
        mermaid.append(f"    Server->>Server: Process ({pattern})")

        for i, layer in enumerate(layers[1:-1], 1):
            prev = layers[i].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
            safe = layer.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
            mermaid.append(f"    Server->>{safe}: Delegate")
            mermaid.append(f"    {safe}-->>Server: Response")

        mermaid.append("    Server->>DB: Query")
        mermaid.append("    DB-->>Server: Result")
        mermaid.append("    Server-->>Client: HTTP Response")

        return "\n".join(mermaid)

    def _generate_class_diagram(self, data: Dict[str, Any]) -> str:
        db_schema = data.get("database_schema", [])
        modules = data.get("modules", [])
        mermaid = ["classDiagram"]

        if db_schema:
            tables_rendered = set()
            for tbl in db_schema:
                name = tbl["name"]
                if name in tables_rendered:
                    continue
                tables_rendered.add(name)
                mermaid.append(f"    class {name} {{")
                for col in tbl.get("columns", []):
                    pk_flag = "PK " if col.get("primary_key") else ""
                    mermaid.append(f"        +{pk_flag}{col['type']} {col['name']}")
                mermaid.append("    }")
                for fk in tbl.get("foreign_keys", []):
                    ref = fk.get("references_table", "")
                    if ref in tables_rendered or any(t["name"] == ref for t in db_schema):
                        mermaid.append(f"    {name} --> {ref}")
        else:
            classes_seen = set()
            for m in modules:
                for cls in m.get("classes", []):
                    name = cls if isinstance(cls, str) else cls.get("name", "")
                    if name and name not in classes_seen:
                        classes_seen.add(name)

            if classes_seen:
                for name in classes_seen:
                    mermaid.append(f"    class {name}")
            else:
                langs = [ls["language"] for ls in data.get("language_stats", [])[:3]]
                mermaid.append("    class RepoLensAnalysis {")
                mermaid.append("        +analyzeRepository()")
                mermaid.append("        +detectLanguages()")
                mermaid.append("        +buildCallGraph()")
                mermaid.append("    }")
                mermaid.append("    class Languages {")
                for lang in langs:
                    mermaid.append(f"        +{lang}")
                mermaid.append("    }")

        return "\n".join(mermaid)

    def _generate_layer_diagram(self, data: Dict[str, Any]) -> str:
        arch = data.get("architecture", {})
        layers = arch.get("layers", [])

        if not layers:
            layers = ["Presentation", "Application", "Domain", "Infrastructure"]

        mermaid = ["flowchart LR"]
        for i, layer in enumerate(layers):
            safe = f"L{i}"
            mermaid.append(f"    {safe}[{layer}]")
            if i > 0:
                mermaid.append(f"    L{i-1} --> L{i}")

        return "\n".join(mermaid)
