"""Read-only DuckDB access shared by the API endpoints."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from decimal import Decimal
from typing import Annotated, Any

import duckdb
from fastapi import Depends, HTTPException

from api.config import database_path


def get_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    path = database_path()
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Base de datos no disponible: {path}",
        )
    try:
        connection = duckdb.connect(str(path), read_only=True)
    except (duckdb.Error, OSError) as exc:
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
