"""
Database/core.py — Pydantic-backed SQLite ORM.

Tables are defined by Pydantic models. The ORM maps Python types to SQLite
types, applies defaults (including `default_factory`) on insert, and returns
fully-validated Pydantic models via `Row.to_model()`.
"""

import pathlib
import datetime
import json
import sqlite3
from typing import Any, Optional, Union, Callable, get_args, get_origin
from enum import Enum

from pydantic import BaseModel
from pydantic.fields import FieldInfo


# ---------------------------------------------------------------------------
# Type mapping: Python/Pydantic -> SQLite
# ---------------------------------------------------------------------------

def python_type_to_sqlite(py_type: Any) -> str:
    """Map a Python type annotation to a SQLite column type."""
    origin = get_origin(py_type)

    # Handle Optional[X], Union[X, None]
    if origin is Union:
        args = [a for a in get_args(py_type) if a is not type(None)]
        if len(args) == 1:
            return python_type_to_sqlite(args[0])
        return "TEXT"  # multi-union -> JSON blob

    # Handle Literal[...] -> TEXT
    if origin is not None and str(origin).endswith("Literal"):
        return "TEXT"

    if py_type is int:
        return "INTEGER"
    if py_type is float:
        return "REAL"
    if py_type is bool:
        return "INTEGER"  # SQLite has no bool
    if py_type is bytes:
        return "BLOB"
    if py_type in (str, datetime.datetime, datetime.date, datetime.time):
        return "TEXT"
    if py_type is dict or py_type is list or origin in (dict, list, tuple, set):
        return "TEXT"  # stored as JSON
    if isinstance(py_type, type) and issubclass(py_type, Enum):
        return "TEXT"
    if isinstance(py_type, type) and issubclass(py_type, BaseModel):
        return "TEXT"  # nested -> JSON
    return "TEXT"


def is_nullable(py_type: Any, field_info: FieldInfo) -> bool:
    """Determine if a field allows NULL."""
    extra = field_info.json_schema_extra or {}
    if "nullable" in extra:
        return bool(extra["nullable"])

    origin = get_origin(py_type)
    if origin is Union and type(None) in get_args(py_type):
        return True

    return False


def serialize_value(value: Any, annotation: Any = None) -> Any:
    """Convert a Python value into something SQLite can store."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, BaseModel):
        return value.model_dump_json()
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(list(value) if isinstance(value, (tuple, set)) else value)
    if isinstance(value, bytes):
        return value
    return value


def deserialize_value(value: Any, annotation: Any) -> Any:
    """Convert a stored SQLite value back to the annotated Python type."""
    if value is None:
        return None

    origin = get_origin(annotation)
    if origin is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        annotation = args[0] if len(args) == 1 else str
        origin = get_origin(annotation)

    if annotation is bool:
        return bool(value)
    if annotation is datetime.datetime:
        return datetime.datetime.fromisoformat(value)
    if annotation is datetime.date:
        return datetime.date.fromisoformat(value)
    if annotation is datetime.time:
        return datetime.time.fromisoformat(value)
    if annotation is dict or origin is dict:
        return json.loads(value)
    if annotation is list or origin is list:
        return json.loads(value)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation(value)
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.model_validate_json(value)
    return value


# ---------------------------------------------------------------------------
# Column descriptor derived from Pydantic FieldInfo
# ---------------------------------------------------------------------------

class Column:
    def __init__(self, name: str, annotation: Any, field_info: FieldInfo):
        self.name = name
        self.annotation = annotation
        self.field_info = field_info
        self.sqlite_type = python_type_to_sqlite(annotation)
        self.nullable = is_nullable(annotation, field_info)

        extra = field_info.json_schema_extra or {}
        self.primary_key = bool(extra.get("primary_key"))
        self.autoincrement = bool(extra.get("autoincrement"))
        self.unique = bool(extra.get("unique"))
        self.references: Optional[str] = extra.get("references")

        # default may be a callable (default_factory) or a plain value
        if field_info.default_factory is not None:
            self.default_factory: Optional[Callable] = field_info.default_factory
            self.default = None
        else:
            self.default_factory = None
            self.default = field_info.default

    def has_default(self) -> bool:
        return (
            self.default_factory is not None
            or (self.default is not None and self.default is not ...)
            or self.nullable
        )

    def resolve_default(self) -> Any:
        """Return the default value (calling factory if needed)."""
        if self.default_factory is not None:
            return self.default_factory()
        if self.default is not ... and self.default is not None:
            return self.default
        return None

    def to_sql(self) -> str:
        parts = [f'"{self.name}"', self.sqlite_type]
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if self.autoincrement:
            parts.append("AUTOINCREMENT")
        if not self.nullable:
            parts.append("NOT NULL")
        if self.unique:
            parts.append("UNIQUE")
        if self.references:
            parts.append(f"REFERENCES {self.references}")

        # Skip SQL DEFAULT for callables — Python evaluates them per-row.
        if (
            self.default_factory is None
            and self.default is not None
            and self.default is not ...
        ):
            d = self.default
            if isinstance(d, bool):
                parts.append(f"DEFAULT {int(d)}")
            elif isinstance(d, (int, float)):
                parts.append(f"DEFAULT {d}")
            else:
                escaped = str(d).replace("'", "''")
                parts.append(f"DEFAULT '{escaped}'")
        return " ".join(parts)

    def __repr__(self):
        return f"Column({self.name}: {self.sqlite_type}, nullable={self.nullable})"


# ---------------------------------------------------------------------------
# Row wrapper
# ---------------------------------------------------------------------------

class Row:
    """Attribute-accessible row with Pydantic model reconstruction."""

    def __init__(self, data: dict, model: type = None, columns: dict = None):
        self._data = data
        self._model = model
        self._columns = columns or {}
        for k, v in data.items():
            setattr(self, k, v)

    def to_dict(self) -> dict:
        return dict(self._data)

    def to_model(self) -> BaseModel:
        """Return a fully-validated Pydantic instance."""
        if self._model is None:
            raise ValueError("No Pydantic model bound to this row")
        converted = {}
        for name, value in self._data.items():
            col = self._columns.get(name)
            if col:
                converted[name] = deserialize_value(value, col.annotation)
            else:
                converted[name] = value
        return self._model(**converted)

    def __getitem__(self, key):
        return self._data[key]

    def __repr__(self):
        return f"Row({self._data})"


# ---------------------------------------------------------------------------
# QueryBuilder
# ---------------------------------------------------------------------------

class QueryBuilder:
    def __init__(self, table: "Table"):
        self._table = table
        self._db = table._db
        self._where_clauses: list = []
        self._params: list = []
        self._order_by: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None

    # ---- Filtering ---------------------------------------------------------
    def where(self, **conditions) -> "QueryBuilder":
        for col, val in conditions.items():
            if val is None:
                self._where_clauses.append(f'"{col}" IS NULL')
            elif isinstance(val, (list, tuple, set)):
                placeholders = ",".join("?" * len(val))
                self._where_clauses.append(f'"{col}" IN ({placeholders})')
                self._params.extend(serialize_value(v) for v in val)
            else:
                self._where_clauses.append(f'"{col}" = ?')
                self._params.append(serialize_value(val))
        return self

    def where_gt(self, col: str, val) -> "QueryBuilder":
        self._where_clauses.append(f'"{col}" > ?')
        self._params.append(serialize_value(val))
        return self

    def where_gte(self, col: str, val) -> "QueryBuilder":
        self._where_clauses.append(f'"{col}" >= ?')
        self._params.append(serialize_value(val))
        return self

    def where_lt(self, col: str, val) -> "QueryBuilder":
        self._where_clauses.append(f'"{col}" < ?')
        self._params.append(serialize_value(val))
        return self

    def where_lte(self, col: str, val) -> "QueryBuilder":
        self._where_clauses.append(f'"{col}" <= ?')
        self._params.append(serialize_value(val))
        return self

    def where_like(self, col: str, pattern: str) -> "QueryBuilder":
        self._where_clauses.append(f'"{col}" LIKE ?')
        self._params.append(pattern)
        return self

    def order_by(self, col: str, desc: bool = False) -> "QueryBuilder":
        self._order_by = f'"{col}" {"DESC" if desc else "ASC"}'
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._limit = n
        return self

    def offset(self, n: int) -> "QueryBuilder":
        self._offset = n
        return self

    # ---- Execution ---------------------------------------------------------
    def _build_select(self) -> str:
        sql = f'SELECT * FROM "{self._table.name}"'
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        if self._offset is not None:
            sql += f" OFFSET {self._offset}"
        return sql

    def _wrap(self, db_rows) -> list:
        return [
            Row(dict(r), model=self._table.model, columns=self._table.columns_map)
            for r in db_rows
        ]

    def all(self) -> list:
        rows = self._db._execute(self._build_select(), self._params).fetchall()
        return self._wrap(rows)

    def first(self) -> Optional[Row]:
        self._limit = 1
        results = self.all()
        return results[0] if results else None

    def count(self) -> int:
        sql = f'SELECT COUNT(*) AS cnt FROM "{self._table.name}"'
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        row = self._db._execute(sql, self._params).fetchone()
        return row["cnt"]

    # ---- Defaults helper ---------------------------------------------------
    def _apply_defaults(self, data: dict) -> dict:
        """
        Fill missing values using column defaults.

        - Auto-increment primary keys are skipped when None/absent.
        - Fields with `default_factory` get a fresh value per row.
        - Fields with a plain default get that default.
        - Nullable fields are left absent (SQLite stores NULL).
        """
        row = dict(data)

        for name, col in self._table.columns_map.items():
            if col.autoincrement and col.primary_key:
                if row.get(name) is None:
                    row.pop(name, None)
                continue

            if name not in row or row[name] is None:
                if name in row and row[name] is None and col.nullable:
                    continue
                if col.default_factory is not None:
                    row[name] = col.resolve_default()
                elif col.default is not None and col.default is not ...:
                    row[name] = col.default

        return row

    # ---- Mutations ---------------------------------------------------------
    def insert(self, instance: Union[BaseModel, dict, None] = None, **values) -> int:
        """Insert a row. Accepts a Pydantic instance, dict, or kwargs."""
        if instance is not None and isinstance(instance, BaseModel):
            data = instance.model_dump()
        elif isinstance(instance, dict):
            data = dict(instance)
            data.update(values)
        else:
            data = dict(values)

        cleaned = self._apply_defaults(data)

        cols = ", ".join(f'"{k}"' for k in cleaned)
        placeholders = ", ".join("?" * len(cleaned))
        sql = f'INSERT INTO "{self._table.name}" ({cols}) VALUES ({placeholders})'
        params = [serialize_value(v) for v in cleaned.values()]
        cursor = self._db._execute(sql, params)
        self._db._conn.commit()
        return cursor.lastrowid

    def insert_many(self, instances: list) -> None:
        if not instances:
            return

        normalized = []
        for item in instances:
            if isinstance(item, BaseModel):
                normalized.append(item.model_dump())
            else:
                normalized.append(dict(item))

        filled = [self._apply_defaults(d) for d in normalized]

        all_keys = set()
        for d in filled:
            all_keys.update(d.keys())

        cols_order = [n for n in self._table.columns_map.keys() if n in all_keys]
        cols = ", ".join(f'"{k}"' for k in cols_order)
        placeholders = ", ".join("?" * len(cols_order))
        sql = f'INSERT INTO "{self._table.name}" ({cols}) VALUES ({placeholders})'

        rows = [[serialize_value(d.get(k)) for k in cols_order] for d in filled]

        self._db._conn.executemany(sql, rows)
        self._db._conn.commit()

    def update(self, instance: Union[BaseModel, None] = None, **values) -> int:
        """
        Update rows matching the current WHERE clause.

        Accepts either a Pydantic instance (only explicitly-set fields are used,
        and the primary key is always excluded) or keyword values.
        """
        if instance is not None and isinstance(instance, BaseModel):
            pk_name = (
                self._table.primary_key.name if self._table.primary_key else None
            )
            dumped = instance.model_dump(exclude_unset=True)
            values = {k: v for k, v in dumped.items() if k != pk_name}

        if not values:
            return 0

        set_clause = ", ".join(f'"{k}" = ?' for k in values.keys())
        sql = f'UPDATE "{self._table.name}" SET {set_clause}'
        params = [serialize_value(v) for v in values.values()]

        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
            params.extend(self._params)

        cursor = self._db._execute(sql, params)
        self._db._conn.commit()
        return cursor.rowcount

    def delete(self) -> int:
        sql = f'DELETE FROM "{self._table.name}"'
        params = []
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
            params = list(self._params)
        cursor = self._db._execute(sql, params)
        self._db._conn.commit()
        return cursor.rowcount


# ---------------------------------------------------------------------------
# Table — built from a Pydantic model
# ---------------------------------------------------------------------------

class Table:
    """
    A table backed by a Pydantic model.

    Example
    -------
    >>> class User(BaseModel):
    ...     id: Optional[int] = Field(default=None,
    ...         json_schema_extra={"primary_key": True, "autoincrement": True})
    ...     name: str
    ...     age: Optional[int] = None
    ...     created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    >>> users = Table(User)
    """

    def __init__(self, model: type, name: Optional[str] = None):
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            raise TypeError("Table requires a Pydantic BaseModel subclass")
        self.model = model
        self.name = name or model.__name__.lower() + "s"
        self.columns: dict[str, Column] = {}
        self._db: Optional["Database"] = None
        self._build_columns()
        self._create = self._create_table
        self._delete = self._delete_table

    # -- schema discovery ----------------------------------------------------
    def _build_columns(self):
        for fname, finfo in self.model.model_fields.items():
            self.columns[fname] = Column(fname, finfo.annotation, finfo)

    @property
    def columns_map(self) -> dict:
        return self.columns

    @property
    def primary_key(self) -> Optional[Column]:
        for c in self.columns.values():
            if c.primary_key:
                return c
        return None

    # -- DDL -----------------------------------------------------------------
    def _create_table(self):
        col_defs = ", ".join(c.to_sql() for c in self.columns.values())
        sql = f'CREATE TABLE IF NOT EXISTS "{self.name}" ({col_defs})'
        self._db._execute(sql)
        self._db._conn.commit()

    def _delete_table(self):
        self._db._execute(f'DROP TABLE IF EXISTS "{self.name}"')
        self._db._conn.commit()
        if self.name in self._db.tables:
            del self._db.tables[self.name]

    # -- queries -------------------------------------------------------------
    def query(self) -> QueryBuilder:
        return QueryBuilder(self)

    def all(self) -> list:
        return self.query().all()

    def first(self) -> Optional[Row]:
        return self.query().first()

    def count(self) -> int:
        return self.query().count()

    def insert(self, instance=None, **values) -> int:
        return self.query().insert(instance, **values)

    def insert_many(self, instances: list):
        return self.query().insert_many(instances)

    def update(self, instance=None, **values) -> int:
        return self.query().update(instance, **values)

    def delete(self) -> int:
        return self.query().delete()

    def get(self, pk_value) -> Optional[Row]:
        pk = self.primary_key
        if pk is None:
            raise ValueError(f"Table {self.name} has no primary key")
        return self.query().where(**{pk.name: pk_value}).first()

    def __repr__(self):
        return f"Table({self.name}, model={self.model.__name__})"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class Database:
    def __init__(self, fname) -> None:
        self._f: pathlib.Path = pathlib.Path(fname).absolute()
        self._f.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection = sqlite3.connect(
            str(self._f), check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self.tables: dict[str, Table] = {}

    def _execute(self, sql: str, params: list = None) -> sqlite3.Cursor:
        cursor = self._conn.cursor()
        cursor.execute(sql, params or [])
        return cursor

    def create(self, *tables: Table) -> None:
        for t in tables:
            if t.name in self.tables:
                if self.tables[t.name].model is not t.model:
                    raise ValueError(f"The table name {t.name} is already registered to another model.")
                continue
            t._db = self
            t._create()
            self.tables[t.name] = t

    def use(self, table: str) -> Table:
        if table not in self.tables:
            raise KeyError(f"Table {table} does not exist!")
        return self.tables[table]

    def delete(self, *tables: Union[Table, str]) -> None:
        for t in tables:
            if isinstance(t, str):
                if t in self.tables:
                    self.tables[t]._delete()
                else:
                    self._execute(f'DROP TABLE IF EXISTS "{t}"')
                    self._conn.commit()
            else:
                t._delete()

    def exists(self, table: str) -> bool:
        row = self._execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [table],
        ).fetchone()
        return row is not None

    def load(self, model: type, name: Optional[str] = None) -> Table:
        """Register an existing table using a Pydantic model for schema."""
        t = Table(model, name=name)
        if not self.exists(t.name):
            raise KeyError(f"Table {t.name} does not exist in the database")
        t._db = self
        self.tables[t.name] = t
        return t

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()