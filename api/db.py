"""Read-only DuckDB access shared by the API endpoints."""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from decimal import Decimal
from typing import Annotated, Any

import duckdb
from fastapi import Depends, HTTPException

from api.config import database_path

logger = logging.getLogger(__name__)


def get_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    path = database_path()
    if not path.exists():
        logger.error("DuckDB file not found at %s", path)
        raise HTTPException(
            status_code=503,
            detail="Base de datos no disponible. Revisa la configuración del servidor.",
        )
    try:
        connection = duckdb.connect(str(path), read_only=True)
    except (duckdb.Error, OSError) as exc:
        logger.error("Could not open DuckDB read-only at %s: %s", path, exc)
        raise HTTPException(
            status_code=503,
            detail="No se pudo abrir la base de datos en modo de solo lectura.",
        ) from exc
    try:
        yield connection
    finally:
        connection.close()


Connection = Annotated[duckdb.DuckDBPyConnection, Depends(get_connection)]


def fetch_all(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    parameters: Sequence[Any] = (),
) -> list[dict[str, Any]]:
    cursor = connection.execute(query, list(parameters))
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def fetch_one(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    parameters: Sequence[Any] = (),
) -> dict[str, Any] | None:
    rows = fetch_all(connection, query, parameters)
    return rows[0] if rows else None


def money(value: Decimal | float | None) -> float | None:
    return float(value) if value is not None else None
