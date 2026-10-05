"""Snapshots of what the program produces: a refactor that must not change behavior proves it
when these stay identical. Updating them is a decision, never an agent's (the guard hook)."""

import pytest
from syrupy.filters import props

from astrolog.fits.header_fields import extract_fields
from test_api_nights import archivio as nights_archive  # noqa: F401 - a fixture, used by name
from test_header_corpus import FILES, load

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
    assert extract_fields(load(path), path.name) == snapshot


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
