"""Snapshots of what the program produces: a refactor that must not change behavior proves it
when these stay identical. Updating them is a decision, never an agent's (the guard hook)."""

from dataclasses import asdict
from enum import StrEnum

import pytest
from syrupy.filters import props

from test_api_nights import archivio as nights_archive  # noqa: F401 - a fixture, used by name
from test_header_corpus import FILES, card_of

# what changes between two runs on the same input: clocks and temporary paths
VOLATILE = props(
    "created_at",
    "started_at",
    "ended_at",
    "updated_at",
    "declared_at",
    "duration_s",
    "root_path",
    "folder_path",
    "path",
    "rel_path",
)

# nights are left out: the synthetic archive stops before `group`, so its night page is empty
PAGES = ("archive", "review", "gear", "folders", "scan-runs")


@pytest.mark.parametrize("path", FILES, ids=[f.stem for f in FILES])
def test_the_fields_read_from_real_headers(path, snapshot):
    """The card the pipeline reads (`pipeline/card.py`, Marco 28/11/2026): enums as their words,
    the start as ISO text."""
    card = asdict(card_of(path))
    words = {k: str(v) if isinstance(v, StrEnum) else v for k, v in card.items()}
    start = card["start_utc"]
    assert {**words, "start_utc": start.isoformat() if start else None} == snapshot


@pytest.mark.parametrize("page", PAGES)
def test_the_pages_of_the_synthetic_archive(client, page, snapshot):
    response = client.get(f"/api/v1/{page}")
    assert response.status_code == 200
    assert response.json() == snapshot(exclude=VOLATILE)


def test_the_nights_page_of_two_grouped_nights(nights_archive, snapshot):  # noqa: F811 - fixture
    response = nights_archive.get("/api/v1/nights")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json() == snapshot(exclude=VOLATILE)
