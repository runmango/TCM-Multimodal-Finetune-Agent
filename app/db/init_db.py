from __future__ import annotations

from app.db.models import CREATE_TABLES
from app.db.session import get_connection


def init_db() -> None:
    with get_connection() as connection:
        for statement in CREATE_TABLES:
            connection.execute(statement)
