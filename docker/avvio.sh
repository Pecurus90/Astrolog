#!/bin/sh
# Container start: ASTAP and its D50 catalog live side by side in /data/astap (ASTAP reads the
# catalog next to itself), the catalog downloaded once with its checksum (ADR 0003).
set -eu

# As root only one step: hand /data itself to PUID:PGID (linuxserver.io convention), then rerun
# this script as that user. Nothing else runs as root, so no link in /data is ever followed by it.
if [ "$(id -u)" = 0 ]; then
    uid=${PUID:-1000}
    gid=${PGID:-1000}
    chown -h "$uid:$gid" /data
    exec setpriv --reuid="$uid" --regid="$gid" --clear-groups "$0"
fi

# Libraries (astropy) keep config and cache under HOME: root's is not theirs.
export HOME=/data/home
mkdir -p "$HOME"

astap_dir=/data/astap
catalog_url=https://sourceforge.net/projects/astap-program/files/star_databases/d50_star_database.zip/download
# md5 as published on SourceForge for d50_star_database.zip (901308858 bytes).
catalog_md5=81bcce6ddc05c661eb276d05c7459bef

mkdir -p "$astap_dir"
cp -f /opt/astap/astap_cli "$astap_dir/astap_cli"

fetch_catalog() {
    tmp="$astap_dir/d50.zip.part"
    unpacked="$astap_dir/.d50"
    # Unpacked aside, then moved in: the solver never sees half a catalog.
    rm -rf "$unpacked"
    # A cut download resumes at the next start (-C -); only a wrong checksum starts it over.
    curl -fsSL --retry 3 -C - -o "$tmp" "$catalog_url" || return 1
    if ! echo "$catalog_md5  $tmp" | md5sum -c -; then
        rm -f "$tmp"
        return 1
    fi
    unzip -q -o "$tmp" -d "$unpacked" &&
        find "$unpacked" -type f -exec mv -f {} "$astap_dir/" \;
    status=$?
    rm -rf "$tmp" "$unpacked"
    return $status
}

# The download runs beside the app, which starts at once and says the catalog is missing until
# it lands. Any ASTAP catalog already there (`<code>_0101.<ext>`, as astap.py reads them) counts.
if ! ls "$astap_dir"/*_0101.* >/dev/null 2>&1; then
    (
        echo "AstroLog: downloading the D50 star catalog (900 MB, once)..."
        if fetch_catalog; then
            echo "AstroLog: star catalog ready."
        else
            echo "AstroLog: star catalog download failed; it is retried at the next start." >&2
        fi
    ) &
fi

exec python -m astrolog
