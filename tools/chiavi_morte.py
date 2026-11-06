"""Italian i18n keys that no code asks for: a dead key is a text nobody reads, and a translator
still pays for it.

A key is alive when the code writes it whole, or its base without the plural suffix, or a
template builds it: `t(`weather.verdict.${v}`)` keeps every `weather.verdict.*` (and
`t(`weather.wind700${forma}`)` every key starting so), and
`t(`${prefisso}.label`)` with `"settings.folders"` written somewhere keeps
`settings.folders.label`. The last rule can keep a dead key alive; it never kills a live one.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "frontend" / "src"

KEY = re.compile(r'^\s*"([\w.\-]+)":', re.M)
PLURAL = re.compile(r"\.(one|zero|ten)$")
PREFIX = re.compile(r"`([\w.\-]+)\$\{")
SUFFIX = re.compile(r"\}\.([\w.\-]+)`")
STRING = re.compile(r"""["'`]([\w.\-]+)["'`]""")


def _dictionary(p: Path) -> bool:
    """`it.ts`, `it-meteo.ts`, `en.ts`...: the words; `i18n/index.ts` is code that reads them."""
    return p.parent.name == "i18n" and re.fullmatch(r"(it|en)(-[\w-]+)?\.ts", p.name) is not None


def keys(src: Path) -> list[str]:
    found = []
    for f in sorted((src / "i18n").glob("it*.ts")):
        if _dictionary(f) and f.name.startswith("it"):
            found += KEY.findall(f.read_text(encoding="utf-8"))
    return found


def code_of(src: Path) -> str:
    return "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(src.rglob("*"))
        if p.suffix in {".ts", ".tsx"} and not _dictionary(p) and p.name != "schema.d.ts"
    )


def dead(all_keys: list[str], code: str) -> list[str]:
    strings = set(STRING.findall(code))
    prefixes = set(PREFIX.findall(code))
    suffixes = set(SUFFIX.findall(code))

    def alive(key: str) -> bool:
        base = PLURAL.sub("", key)
        if key in strings or base in strings:
            return True
        if any(key.startswith(p) for p in prefixes):
            return True
        parts = base.split(".")
        return any(
            ".".join(parts[:i]) in strings and ".".join(parts[i:]) in suffixes
            for i in range(2, len(parts))
        )

    return [k for k in all_keys if not alive(k)]


def main() -> int:
    found = dead(keys(SRC), code_of(SRC))
    for k in found:
        print(f"chiave i18n che nessuno legge: {k}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
