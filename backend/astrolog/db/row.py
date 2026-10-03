"""A row read by name: a query's `sqlite3.Row` or the dict a page or a test builds."""

import sqlite3
from collections.abc import Mapping
from typing import Any

type Row = sqlite3.Row | Mapping[str, Any]
