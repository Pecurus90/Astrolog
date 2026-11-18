# AstroLog for a NAS: one multi-arch image (amd64, arm64), ASTAP inside, star catalog on first run.
# Built and published by .github/workflows/immagine.yml; installed from compose.yaml.

FROM node:24-bookworm-slim AS page
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS wheel
WORKDIR /src
COPY backend/ backend/
COPY --from=page /src/backend/astrolog/web/ backend/astrolog/web/
RUN pip install --no-cache-dir build && python -m build --wheel --outdir /wheel backend

FROM python:3.12-slim-bookworm
ARG TARGETARCH
# ASTAP command-line 2026.11.12, md5 as published on SourceForge (linux_installer).
ARG ASTAP_URL=https://sourceforge.net/projects/astap-program/files/linux_installer
ARG ASTAP_MD5_amd64=82eaeea5020dfc787ebc9cfe8fabbcf3
ARG ASTAP_MD5_arm64=d7f725d736d4c23615806871b46ccf42
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl unzip \
    && rm -rf /var/lib/apt/lists/*
RUN set -eu; \
    case "$TARGETARCH" in amd64) a=amd64; m=$ASTAP_MD5_amd64 ;; arm64) a=aarch64; m=$ASTAP_MD5_arm64 ;; \
      *) echo "no ASTAP for $TARGETARCH" >&2; exit 1 ;; esac; \
    curl -fsSL -o /tmp/astap.zip "$ASTAP_URL/astap_command-line_version_Linux_$a.zip/download"; \
    echo "$m  /tmp/astap.zip" | md5sum -c -; \
    mkdir -p /opt/astap && unzip -q /tmp/astap.zip -d /opt/astap && rm /tmp/astap.zip; \
    chmod +x /opt/astap/astap_cli
COPY --from=wheel /wheel/ /wheel/
RUN pip install --no-cache-dir /wheel/*.whl && rm -rf /wheel
COPY docker/avvio.sh /usr/local/bin/avvio.sh
RUN chmod +x /usr/local/bin/avvio.sh

ENV ASTROLOG_HOST=0.0.0.0 \
    ASTROLOG_PORT=8765 \
    ASTROLOG_DATA_DIR=/data \
    ASTROLOG_DATA_ROOT=/archivio \
    ASTROLOG_ASTAP=/data/astap/astap_cli
VOLUME ["/data"]
EXPOSE 8765
LABEL org.opencontainers.image.source=https://github.com/Pecurus90/Astrolog \
      org.opencontainers.image.description="AstroLog, preview: catalog and plan astrophotography sessions" \
      org.opencontainers.image.licenses=GPL-3.0-or-later
ENTRYPOINT ["/usr/local/bin/avvio.sh"]
