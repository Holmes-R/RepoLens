import os
import re
from typing import Dict, Any, List, Optional

COLUMN_RE = re.compile(r'^\s*`?(\w+)`?\s+(\w+(?:\s*\([^)]+\))?)', re.MULTILINE)
CREATE_TABLE_RE = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?\s*\((.*?)\);', re.DOTALL | re.IGNORECASE)
PK_RE = re.compile(r'PRIMARY\s+KEY\s*\(`?(\w+)`?\)', re.IGNORECASE)
FK_RE = re.compile(r'FOREIGN\s+KEY\s*\(`?(\w+)`?\)\s*REFERENCES\s+`?(\w+)`?\s*\(`?(\w+)`?\)', re.IGNORECASE)


class DatabaseSchemaDetector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def detect(self) -> Dict[str, Any]:
        tables = []
        seen = set()
        for method in [self._find_sql_schemas, self._find_migration_files, self._find_orm_models, self._find_prisma_schema]:
            for tbl in method():
                if tbl["name"] not in seen:
                    seen.add(tbl["name"])
                    tables.append(tbl)
        return {"tables": tables, "total_tables": len(tables)}

    def _find_migration_files(self) -> List[Dict[str, Any]]:
        tables = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", "__pycache__")]
            for f in files:
                if f.endswith(".php"):
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        parsed = self._parse_laravel_migration(content)
                        tables.extend(parsed)
                    except Exception:
                        continue
        return tables

    def _parse_laravel_migration(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        schema_re = re.compile(r'Schema::create\(\s*[\'"](\w+)[\'"]\s*,\s*function\s*\((?:Blueprint\s*)?\$table\)\s*\{(.*?)\}\)', re.DOTALL)
        for match in schema_re.finditer(content):
            table_name = match.group(1)
            body = match.group(2)
            columns = []

            NOARG_COLUMNS = {
                "id": "id",
                "bigIncrements": "id",
                "increments": "id",
                "timestamps": ("created_at", "updated_at"),
                "nullableTimestamps": ("created_at", "updated_at"),
                "softDeletes": "deleted_at",
                "rememberToken": "remember_token",
            }

            col_re = re.compile(r'\$table->(\w+)\s*\(\s*[\'"](\w+)[\'"]', re.DOTALL)
            seen_names = set()
            for col in col_re.finditer(body):
                col_type = col.group(1)
                col_name = col.group(2)
                pk = col_type in ("id", "bigIncrements", "increments")
                if col_name not in seen_names:
                    seen_names.add(col_name)
                    columns.append({"name": col_name, "type": col_type, "primary_key": pk})

            # Also detect no-arg column methods
            for col_type, default_names in NOARG_COLUMNS.items():
                if re.search(r'\$table->' + col_type + r'\s*\(\)', body):
                    names = default_names if isinstance(default_names, tuple) else (default_names,)
                    for name in names:
                        if name not in seen_names:
                            seen_names.add(name)
                            columns.append({"name": name, "type": col_type, "primary_key": col_type in ("id", "bigIncrements", "increments")})

            tables.append({"name": table_name, "columns": columns, "foreign_keys": []})
        return tables

    def _find_sql_schemas(self) -> List[Dict[str, Any]]:
        tables = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", "__pycache__")]
            for f in files:
                if f.endswith(".sql"):
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                            parsed = self._parse_sql(content)
                            tables.extend(parsed)
                    except Exception:
                        continue
        return tables

    def _parse_sql(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        for match in CREATE_TABLE_RE.finditer(content):
            table_name = match.group(1)
            body = match.group(2)
            columns = []
            foreign_keys = []
            pk_cols = set()
            pk_match = PK_RE.search(body)
            if pk_match:
                pk_cols.add(pk_match.group(1))
            for fk in FK_RE.finditer(body):
                foreign_keys.append({
                    "column": fk.group(1),
                    "references_table": fk.group(2),
                    "references_column": fk.group(3),
                })
            for col_match in COLUMN_RE.finditer(body):
                col_name = col_match.group(1)
                col_type = col_match.group(2).strip()
                if col_name.upper() in ("PRIMARY", "FOREIGN", "INDEX", "UNIQUE", "CONSTRAINT", "KEY"):
                    continue
                columns.append({
                    "name": col_name,
                    "type": col_type,
                    "primary_key": col_name in pk_cols,
                })
            tables.append({
                "name": table_name,
                "columns": columns,
                "foreign_keys": foreign_keys,
            })
        return tables

    def _find_orm_models(self) -> List[Dict[str, Any]]:
        tables = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", "__pycache__")]
            for f in files:
                if f == "models.py" or f == "models.ts":
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        parsed = self._parse_orm_models(content, f.endswith(".ts"))
                        tables.extend(parsed)
                    except Exception:
                        continue
                elif f == "schema.prisma":
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        parsed = self._parse_prisma(content)
                        tables.extend(parsed)
                    except Exception:
                        continue
        return tables

    def _parse_orm_models(self, content: str, is_typescript: bool) -> List[Dict[str, Any]]:
        tables = []
        if is_typescript:
            class_re = re.compile(r'@Entity\s*\n\s*class\s+(\w+).*?\{([^}]*)\}', re.DOTALL)
            for match in class_re.finditer(content):
                table_name = match.group(1)
                body = match.group(2)
                columns = []
                for prop in re.finditer(r'(\w+)\s*[:=]\s*(\w+)', body):
                    name, typ = prop.group(1), prop.group(2)
                    if name in ("export", "default", "class", "extends", "implements"):
                        continue
                    columns.append({"name": name, "type": typ, "primary_key": False})
                tables.append({"name": table_name, "columns": columns, "foreign_keys": []})
        else:
            class_re = re.compile(r'class\s+(\w+)\s*\(.*?models?\.\w+.*?\)\s*:\s*\n(.*?)(?=\nclass|\Z)', re.DOTALL)
            for match in class_re.finditer(content):
                table_name = match.group(1)
                body = match.group(2)
                columns = []
                field_re = re.compile(r'(\w+)\s*=\s*models\.(\w+)\(', re.DOTALL)
                for fld in field_re.finditer(body):
                    name, typ = fld.group(1), fld.group(2)
                    columns.append({"name": name, "type": typ, "primary_key": False})
                tables.append({"name": table_name, "columns": columns, "foreign_keys": []})
        return tables

    def _parse_prisma(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        model_re = re.compile(r'model\s+(\w+)\s*\{([^}]*)\}', re.DOTALL)
        for match in model_re.finditer(content):
            table_name = match.group(1)
            body = match.group(2)
            columns = []
            foreign_keys = []
            for field in re.finditer(r'^\s+(\w+)\s+(\w+(?:\s*\[\])?)\s*(@relation\([^)]*\))?\s*$', body, re.MULTILINE):
                name, typ = field.group(1), field.group(2)
                if typ in ("model", "enum"):
                    continue
                columns.append({"name": name, "type": typ, "primary_key": "@id" in (field.group(3) or "")})
            tables.append({"name": table_name, "columns": columns, "foreign_keys": foreign_keys})
        return tables

    def _find_prisma_schema(self) -> List[Dict[str, Any]]:
        tables = []
        for root, dirs, files in os.walk(self.repo_path):
            for f in files:
                if f == "schema.prisma":
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        parsed = self._parse_prisma(content)
                        tables.extend(parsed)
                    except Exception:
                        continue
        return tables
