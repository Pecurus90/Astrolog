#!/bin/sh
# Container start: ASTAP and its catalogs live side by side in /data/astap (ASTAP reads them next
# to itself): D05 from the image, D50 downloaded once with its checksum (ADR 0003).
set -eu

# As root only one step: hand /data itself to PUID:PGID (linuxserver.io convention), then rerun
# this script as that user. Nothing else runs as root, so no link in /data is ever followed by it.
if [ "$(id -u)" = 0 ]; then
    uid=${PUID:-1000}
    gid=${PGID:-1000}
    chown -h "$uid:$gid" /data
    exec setpriv --reuid="$uid" --regid="$gid" --clear-groups "$0"
fi

# Libraries (numba) keep their cache under HOME when the package dir is read-only: root's is not theirs.
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
    curl -fsSL --retry 5 --retry-all-errors -C - -o "$tmp" "$catalog_url" || return 1
    if ! echo "$catalog_md5  $tmp" | md5sum -c -; then
        rm -f "$tmp"
        return 2
    fi
    unzip -q -o "$tmp" -d "$unpacked" &&
        find "$unpacked" -type f -exec mv -f {} "$astap_dir/" \;
    status=$?
    rm -rf "$tmp" "$unpacked"
    return $status
}

# A catalog is `<code>_0101.<ext>`, as astap.py reads them. With none, the D05 of the image goes in:
# the app solves at once while D50 downloads beside it, unless a catalog other than D05 is there.
if ! ls "$astap_dir"/*_0101.* >/dev/null 2>&1; then
    cp /opt/astap/d05/* "$astap_dir/"
fi
if ! ls "$astap_dir"/*_0101.* | grep -qv '/d05_0101\.'; then
    (
        echo "AstroLog: downloading the D50 star catalog (900 MB, once)..."
        # A dropped line or a busy mirror is retried every ten minutes, resuming where it stopped.
        # A wrong checksum is not retried: 900 MB again every ten minutes would not change it.
        until fetch_catalog; do
            if [ $? = 2 ]; then
                echo "AstroLog: star catalog checksum does not match; D05 stays in use." >&2
                exit 0
            fi
            echo "AstroLog: star catalog download failed; retrying in 10 minutes." >&2
            sleep 600
        done
        echo "AstroLog: star catalog ready."
    ) &
fi

exec python -m astrolog
