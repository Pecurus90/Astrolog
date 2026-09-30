"""Le rotte FastAPI sotto `/api/v1`: leggono, mettono in fila, rispondono. Non calcolano e
non aprono FITS. La forma di ogni risposta e' un modello Pydantic (`models.py`), da cui
l'OpenAPI e i tipi TypeScript del frontend."""
