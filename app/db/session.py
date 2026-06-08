from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.core.paths import APP_DB_PATH, DATA_DIR


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(APP_DB_PATH))
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
