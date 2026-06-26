import os
import re
from typing import Dict, Any, List


COLUMN_RE = re.compile(r'^\s*`?(\w+)`?\s+(\w+(?:\s*\([^)]+\))?)', re.MULTILINE)
CREATE_TABLE_RE = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?\s*\((.*?)\);',
    re.DOTALL | re.IGNORECASE,
)
PK_RE = re.compile(r'PRIMARY\s+KEY\s*\(`?(\w+)`?\)', re.IGNORECASE)
FK_RE = re.compile(
    r'FOREIGN\s+KEY\s*\(`?(\w+)`?\)\s*REFERENCES\s+`?(\w+)`?\s*\(`?(\w+)`?\)',
    re.IGNORECASE,
)

IGNORE_DIRS = frozenset({'.git', 'node_modules', 'venv', '__pycache__', '.venv', '.tox', 'dist', 'build', '.next'})


def _walk(repo_path: str):
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        yield root, dirs, files


class DatabaseSchemaDetector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def detect(self) -> Dict[str, Any]:
        tables = []
        seen = set()

        for method in [
            self._find_sql_schemas,
            self._find_laravel_migrations,
            self._find_alembic_migrations,
            self._find_raw_create_table_in_python,
            self._find_django_models,
            self._find_sqlalchemy_models,
            self._find_typeorm_entities,
            self._find_prisma_schema,
        ]:
            for tbl in method():
                if tbl["name"] not in seen:
                    seen.add(tbl["name"])
                    tables.append(tbl)
        return {"tables": tables, "total_tables": len(tables)}

    # ── Raw .sql files ──────────────────────────────────────────────
    def _find_sql_schemas(self) -> List[Dict[str, Any]]:
        tables = []
        for root, _dirs, files in _walk(self.repo_path):
            for f in files:
                if f.endswith(".sql"):
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                            tables.extend(self._parse_sql(fh.read()))
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
            tables.append({"name": table_name, "columns": columns, "foreign_keys": foreign_keys})
        return tables

    # ── Laravel PHP migrations ──────────────────────────────────────
    def _find_laravel_migrations(self) -> List[Dict[str, Any]]:
        tables = []
        for root, _dirs, files in _walk(self.repo_path):
            for f in files:
                if f.endswith(".php"):
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                            tables.extend(self._parse_laravel_migration(fh.read()))
                    except Exception:
                        continue
        return tables

    def _parse_laravel_migration(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        schema_re = re.compile(
            r'Schema::create\(\s*[\'"](\w+)[\'"]\s*,\s*function\s*\((?:Blueprint\s*)?\$table\)\s*\{(.*?)\}\)',
            re.DOTALL,
        )
        NOARG_COLUMNS = {
            "id": "id",
            "bigIncrements": "id",
            "increments": "id",
            "timestamps": ("created_at", "updated_at"),
            "nullableTimestamps": ("created_at", "updated_at"),
            "softDeletes": "deleted_at",
            "rememberToken": "remember_token",
        }

        for match in schema_re.finditer(content):
            table_name = match.group(1)
            body = match.group(2)
            columns = []
            seen_names = set()
            col_re = re.compile(r'\$table->(\w+)\s*\(\s*[\'"](\w+)[\'"]', re.DOTALL)
            for col in col_re.finditer(body):
                col_type = col.group(1)
                col_name = col.group(2)
                pk = col_type in ("id", "bigIncrements", "increments")
                if col_name not in seen_names:
                    seen_names.add(col_name)
                    columns.append({"name": col_name, "type": col_type, "primary_key": pk})
            for col_type, default_names in NOARG_COLUMNS.items():
                if re.search(r'\$table->' + col_type + r'\s*\(\)', body):
                    names = default_names if isinstance(default_names, tuple) else (default_names,)
                    for name in names:
                        if name not in seen_names:
                            seen_names.add(name)
                            columns.append({
                                "name": name,
                                "type": col_type,
                                "primary_key": col_type in ("id", "bigIncrements", "increments"),
                            })
            tables.append({"name": table_name, "columns": columns, "foreign_keys": []})
        return tables

    # ── Alembic / Aerich Python migrations ─────────────────────────
    def _find_alembic_migrations(self) -> List[Dict[str, Any]]:
        tables = []
        migration_dirs = set()
        for root, _dirs, files in _walk(self.repo_path):
            if "alembic" in root.split(os.sep) or "migrations" in root.split(os.sep):
                for f in files:
                    if f.endswith(".py") and f != "__init__.py":
                        migration_dirs.add(root)

        for mdir in migration_dirs:
            for root, _dirs, files in os.walk(mdir):
                for f in files:
                    if f.endswith(".py") and f != "__init__.py":
                        try:
                            with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                                content = fh.read()
                            tables.extend(self._parse_alembic_migration(content))
                        except Exception:
                            continue
        return tables

    def _parse_alembic_migration(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        op_re = re.compile(
            r'op\.create_table\(\s*[\'"](\w+)[\'"]\s*,\s*(.*?)(?=\)\s*\))',
            re.DOTALL,
        )
        for match in op_re.finditer(content):
            table_name = match.group(1)
            body = match.group(2)
            columns = []
            col_re = re.compile(
                r'sa\.Column\(\s*[\'"](\w+)[\'"]\s*,\s*sa\.(\w+)',
            )
            for col in col_re.finditer(body):
                columns.append({
                    "name": col.group(1),
                    "type": col.group(2),
                    "primary_key": "primary_key=True" in body or f"{col.group(1)}.*primary" in body,
                })
            tables.append({"name": table_name, "columns": columns, "foreign_keys": []})
        return tables

    # ── Raw CREATE TABLE in any Python file ────────────────────────
    def _find_raw_create_table_in_python(self) -> List[Dict[str, Any]]:
        tables = []
        for root, _dirs, files in _walk(self.repo_path):
            for f in files:
                if f.endswith(".py"):
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        tables.extend(self._parse_sql(content))
                    except Exception:
                        continue
        return tables

    # ── Django models ──────────────────────────────────────────────
    def _find_django_models(self) -> List[Dict[str, Any]]:
        tables = []
        for root, _dirs, files in _walk(self.repo_path):
            for f in files:
                path = os.path.join(root, f)
                if f == "models.py" or (f.endswith(".py") and "models" in root.split(os.sep)):
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        if "models.Model" in content or "models.ForeignKey" in content:
                            tables.extend(self._parse_django_models(content, root, f))
                    except Exception:
                        continue
        return tables

    def _parse_django_models(self, content: str, root: str, filename: str) -> List[Dict[str, Any]]:
        tables = []
        class_re = re.compile(r'class\s+(\w+)\s*\(.*?models\.\w+.*?\)\s*:\s*\n(.*?)(?=\nclass|\Z)', re.DOTALL)
        for match in class_re.finditer(content):
            table_name = match.group(1)
            body = match.group(2)
            columns = []
            field_re = re.compile(r'(\w+)\s*=\s*models\.(\w+)\(', re.DOTALL)
            for fld in field_re.finditer(body):
                name, typ = fld.group(1), fld.group(2)
                columns.append({"name": name, "type": typ, "primary_key": typ == "AutoField"})
            tables.append({"name": table_name, "columns": columns, "foreign_keys": []})
        return tables

    # ── SQLAlchemy models ──────────────────────────────────────────
    def _find_sqlalchemy_models(self) -> List[Dict[str, Any]]:
        tables = []
        for root, _dirs, files in _walk(self.repo_path):
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    if "declarative_base" in content or "Column(" in content or "Table(" in content:
                        tables.extend(self._parse_sqlalchemy(content, f))
                except Exception:
                    continue
        return tables

    def _parse_sqlalchemy(self, content: str, filename: str) -> List[Dict[str, Any]]:
        tables = []
        class_re = re.compile(r'class\s+(\w+)\s*\(.*?Base.*?\)\s*:\s*\n(.*?)(?=\nclass|\Z)', re.DOTALL)
        for match in class_re.finditer(content):
            table_name = match.group(1)
            body = match.group(2)
            columns = []
            col_re = re.compile(r'(\w+)\s*=\s*Column\(', re.DOTALL)
            for col in col_re.finditer(body):
                columns.append({"name": col.group(1), "type": "Column", "primary_key": False})
            tables.append({"name": table_name, "columns": columns, "foreign_keys": []})
        return tables

    # ── TypeORM entities ───────────────────────────────────────────
    def _find_typeorm_entities(self) -> List[Dict[str, Any]]:
        tables = []
        for root, _dirs, files in _walk(self.repo_path):
            for f in files:
                if f.endswith(".entity.ts") or f.endswith(".entity.js"):
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        tables.extend(self._parse_typeorm_entity(content))
                    except Exception:
                        continue
        return tables

    def _parse_typeorm_entity(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        class_re = re.compile(r'@Entity.*?\n\s*class\s+(\w+).*?\{([^}]*)\}', re.DOTALL)
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
        return tables

    # ── Prisma schema ──────────────────────────────────────────────
    def _find_prisma_schema(self) -> List[Dict[str, Any]]:
        tables = []
        for root, _dirs, files in _walk(self.repo_path):
            for f in files:
                if f == "schema.prisma":
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        tables.extend(self._parse_prisma(content))
                    except Exception:
                        continue
        return tables

    def _parse_prisma(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        model_re = re.compile(r'model\s+(\w+)\s*\{([^}]*)\}', re.DOTALL)
        for match in model_re.finditer(content):
            table_name = match.group(1)
            body = match.group(2)
            columns = []
            for field in re.finditer(r'^\s+(\w+)\s+(\w+(?:\s*\[\])?)\s*(@relation\([^)]*\))?\s*$', body, re.MULTILINE):
                name, typ = field.group(1), field.group(2)
                if typ in ("model", "enum"):
                    continue
                columns.append({
                    "name": name,
                    "type": typ,
                    "primary_key": "@id" in (field.group(3) or ""),
                })
            tables.append({"name": table_name, "columns": columns, "foreign_keys": []})
        return tables
