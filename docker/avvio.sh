#!/bin/sh
# Container start: ASTAP and its D50 catalog live side by side in /data/astap (ASTAP reads the
# catalog next to itself), the catalog downloaded once with its checksum (ADR 0003).
set -eu

astap_dir=/data/astap
catalog_url=https://sourceforge.net/projects/astap-program/files/star_databases/d50_star_database.zip/download
# md5 as published on SourceForge for d50_star_database.zip (901308858 bytes).
catalog_md5=81bcce6ddc05c661eb276d05c7459bef

mkdir -p "$astap_dir"
cp -f /opt/astap/astap_cli "$astap_dir/astap_cli"

fetch_catalog() {
    tmp="$astap_dir/d50.zip.part"
    curl -fL --retry 3 -o "$tmp" "$catalog_url" &&
        echo "$catalog_md5  $tmp" | md5sum -c - &&
        unzip -q -o "$tmp" -d "$astap_dir"
    status=$?
    rm -f "$tmp"
    return $status
}

# A failed download does not stop the app: it starts and says the catalog is missing.
# Any ASTAP catalog already there (`<code>_0101.<ext>`, as astap.py reads them) counts.
if ! ls "$astap_dir"/*_0101.* >/dev/null 2>&1; then
    echo "AstroLog: downloading the D50 star catalog (900 MB, once)..."
    if fetch_catalog; then
        echo "AstroLog: star catalog ready."
    else
        echo "AstroLog: star catalog download failed; it is retried at the next start." >&2
    fi
fi

# The app runs as PUID:PGID, never root: the NAS user who owns the photos (linuxserver.io convention).
uid=${PUID:-1000}
gid=${PGID:-1000}
# Libraries (astropy) keep config and cache under HOME: root's is not theirs.
export HOME=/data/home
mkdir -p "$HOME"
find /data \( ! -user "$uid" -o ! -group "$gid" \) -exec chown "$uid:$gid" {} +
exec setpriv --reuid="$uid" --regid="$gid" --clear-groups python -m astrolog
