"""FastAPI runs the dependency and the route body on two threadpool threads: the connection
belongs to one request only, so `check_same_thread=False` is safe and avoids a 500 under load."""

import sqlite3
from collections.abc import Iterator

from fastapi import Request

from ..db.connect import connect


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.db_path, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()
