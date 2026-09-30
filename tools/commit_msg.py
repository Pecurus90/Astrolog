"""commit-msg hook: one ASCII line. At commit time editor `#` lines and scissors are dropped
(so a `-m "#..."` line slips through, as the ADR says); `--final` judges a stored message whole."""

import sys

SCISSORS = "------------------------ >8 ------------------------"


def message_lines(raw, final=False):
    lines = []
    for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not final and SCISSORS in line:
            break
        if not line.strip() or (not final and line.startswith("#")):
            continue
        lines.append(line)
    return lines


def problems(raw, final=False):
    lines = message_lines(raw, final)
    out = []
    if len(lines) != 1:
        out.append(f"one line expected, found {len(lines)}")
    if any(not line.isascii() for line in lines):
        out.append("non-ASCII characters")
    return out


def main(argv):
    final = "--final" in argv
    path = [a for a in argv[1:] if a != "--final"][0]
    with open(path, encoding="utf-8", errors="replace") as h:
        found = problems(h.read(), final)
    for p in found:
        print(f"commit message: {p}", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
