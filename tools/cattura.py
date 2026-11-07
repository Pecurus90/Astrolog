"""Board and app captured alike by headless Chrome over CDP: real size, steps, console, screens.
Usage: python tools/cattura.py <url> <out.png> [--formato F] [--altezza N] | --piano <piano.json>"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

from websockets.sync.client import connect

# control sizes of the boards: handoff/design/docs/DECISIONI.md, v57, line "Controlli"
SIZES = {"desktop": (1440, 900), "stretto": (1280, 800), "telefono": (390, 844)}
LOAD_S = 3.0  # after navigate: the page's scripts and first fetches
STEP_MS = 800  # after a step's script, before its shot
START_S = 15.0
START_TRIES = 2  # a CI runner's Chrome at times dies or hangs at start, Issue #51
CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
# every screen of a board of states, as Design labels it
SCREENS_JS = "[...document.querySelectorAll('[data-screen-label]')].map(e => e.dataset.screenLabel)"
SCREEN_BOX_JS = """(() => {
  const all = [...document.querySelectorAll('[data-screen-label]')];
  const e = all.find(x => x.dataset.screenLabel === %s);
  const body = e.lastElementChild || e;
  body.scrollIntoView({block: 'start', inline: 'start'});
  const r = body.getBoundingClientRect();
  return [r.x + scrollX, r.y + scrollY, r.width, r.height];
})()"""
FULL_HEIGHT_JS = "Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)"


def find_chrome() -> str | None:
    """The Chrome to drive, or None when there is none."""
    named = os.environ.get("ASTROLOG_CHROME")
    if named:
        return named
    for path in CANDIDATES:
        if os.path.exists(path):
            return path
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def window(formato: str, height: int | None = None) -> tuple[int, int]:
    """Width and height of a format, taller on request; an unknown format raises KeyError."""
    width, base_height = SIZES[formato]
    return width, height or base_height


def chrome_command(chrome: str, size: tuple[int, int], profile: str) -> list[str]:
    """Headless Chrome on a free debugging port, in a throwaway profile."""
    width, height = size
    return [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--hide-scrollbars",
        f"--user-data-dir={profile}",
        "--remote-debugging-port=0",
        f"--window-size={width},{height}",
        "about:blank",
    ]


def event_line(message: dict) -> str | None:
    """A console call, an uncaught exception or a browser log entry (network errors) as a line."""
    params = message.get("params", {})
    method = message.get("method")
    if method == "Runtime.consoleAPICalled":
        words = [str(a.get("value", a.get("description", ""))) for a in params["args"]]
        return f"{params['type']}: {' '.join(words)}"
    if method == "Runtime.exceptionThrown":
        details = params["exceptionDetails"]
        return f"exception: {details.get('exception', {}).get('description', details.get('text'))}"
    if method == "Log.entryAdded":
        entry = params["entry"]
        source = f" -- {entry['url']}" if entry.get("url") else ""
        return f"{entry['level']}: {entry['text']}{source}"
    return None


def slug(label: str) -> str:
    """A screen label of the board as a file name."""
    for sep in (" " + chr(0xB7) + " ", ": ", " ", "/"):
        label = label.replace(sep, "-")
    return label.lower()


class Page:
    """One CDP connection to one tab; events seen while waiting go to the console."""

    def __init__(self, ws) -> None:
        self.ws = ws
        self.count = 0
        self.console: list[str] = []

    def call(self, method: str, params: dict | None = None) -> dict:
        self.count += 1
        self.ws.send(json.dumps({"id": self.count, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.count:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})
            line = event_line(message)
            if line:
                self.console.append(line)

    def evaluate(self, js: str):
        params = {"expression": js, "awaitPromise": True, "returnByValue": True}
        result = self.call("Runtime.evaluate", params)
        if "exceptionDetails" in result:
            raise RuntimeError(f"script: {result['exceptionDetails'].get('text')}: {js[:80]}")
        return result["result"].get("value")

    def shot(self, out: str, clip: list[float] | None = None) -> None:
        params: dict = {"format": "png"}
        if clip:
            x, y, width, height = clip
            params["clip"] = {"x": x, "y": y, "width": width, "height": height, "scale": 1}
            params["captureBeyondViewport"] = True
        data = self.call("Page.captureScreenshot", params)["data"]
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "wb") as f:
            f.write(base64.b64decode(data))


class ChromeStartError(RuntimeError):
    """Chrome exited or never opened its debugging port."""


def _debugger_url(profile: str, proc: subprocess.Popen) -> str:
    deadline = time.monotonic() + START_S
    port_file = os.path.join(profile, "DevToolsActivePort")
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise ChromeStartError(f"Chrome uscito all'avvio con codice {proc.returncode}")
        try:
            with open(port_file, encoding="utf-8") as f:
                port = f.readline().strip()
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list") as r:
                tabs = json.load(r)
            return next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
        except (OSError, ValueError, StopIteration):
            time.sleep(0.2)
    raise ChromeStartError("Chrome non ha aperto la porta di debug")


def _start(chrome: str, size: tuple[int, int], profile: str) -> tuple[subprocess.Popen, str]:
    """Chrome and its page's debugger URL; a failed start is tried again in a clean profile."""
    attempt = 0
    while True:
        folder = os.path.join(profile, str(attempt))
        proc = subprocess.Popen(
            chrome_command(chrome, size, folder),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            return proc, _debugger_url(folder, proc)
        except ChromeStartError:
            _kill_tree(proc)
            attempt += 1
            if attempt == START_TRIES:
                raise
        except BaseException:
            _kill_tree(proc)
            raise


def _kill_tree(proc: subprocess.Popen) -> None:
    # by PID only: a kill by name closes the user's own Chrome too
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        proc.kill()
    proc.wait()


def _open(page: Page, plan: dict, size: tuple[int, int]) -> None:
    width, height = size
    for domain in ("Runtime", "Log", "Page"):
        page.call(f"{domain}.enable")
    metrics = {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False}
    page.call("Emulation.setDeviceMetricsOverride", metrics)
    if plan.get("prima"):
        page.call("Page.addScriptToEvaluateOnNewDocument", {"source": plan["prima"]})
    page.call("Page.navigate", {"url": plan["url"]})
    time.sleep(plan.get("carica", LOAD_S))


def _steps(page: Page, plan: dict, width: int) -> list:
    values = []
    for step in plan.get("passi", []):
        values.append(page.evaluate(step["js"]) if step.get("js") else None)
        time.sleep(step.get("attesa", STEP_MS) / 1000)
        page.evaluate("1")  # collects the console of the wait
        if step.get("out"):
            clip = [0, 0, width, page.evaluate(FULL_HEIGHT_JS)] if step.get("intera") else None
            page.shot(step["out"], clip)
    return values


def _screens(page: Page, folder: str) -> list[str]:
    written = []
    for label in page.evaluate(SCREENS_JS):
        clip = page.evaluate(SCREEN_BOX_JS % json.dumps(label))
        out = os.path.join(folder, f"{slug(label)}.png")
        page.shot(out, clip)
        written.append(out)
    return written


def run(plan: dict) -> dict:
    """Open plan['url'] at plan['formato'], run the steps, shoot; returns values, console, screens.
    Plan keys: url, formato, altezza, prima (script before the page), carica (s), passi, schermi."""
    chrome = find_chrome()
    if chrome is None:
        raise FileNotFoundError("Chrome non trovato: installalo o indica ASTROLOG_CHROME")
    size = window(plan.get("formato", "desktop"), plan.get("altezza"))
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        proc, url = _start(chrome, size, profile)
        try:
            with connect(url, max_size=2**27) as ws:
                page = Page(ws)
                _open(page, plan, size)
                values = _steps(page, plan, size[0])
                screens = _screens(page, plan["schermi"]) if plan.get("schermi") else []
                page.evaluate("1")
        finally:
            _kill_tree(proc)
    return {"values": values, "console": page.console, "screens": screens}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Capture a page with headless Chrome")
    parser.add_argument("url", nargs="?")
    parser.add_argument("out", nargs="?")
    parser.add_argument("--formato", choices=sorted(SIZES), default="desktop")
    parser.add_argument("--altezza", type=int, help="taller window, same width")
    parser.add_argument("--piano", help="JSON plan: url, formato, prima, passi, schermi")
    args = parser.parse_args(argv)
    if args.piano:
        with open(args.piano, encoding="utf-8") as f:
            plan = json.load(f)
    elif args.url and args.out:
        plan = {"url": args.url, "formato": args.formato, "altezza": args.altezza}
        plan["passi"] = [{"out": args.out}]
    else:
        parser.error("serve <url> <out.png> oppure --piano")
    result = run(plan)
    for value in result["values"]:
        sys.stdout.write(f"valore: {json.dumps(value, ensure_ascii=False)}\n")
    for screen in result["screens"]:
        sys.stdout.write(f"schermo: {screen}\n")
    sys.stdout.write(f"console: {len(result['console'])} righe\n")
    for line in result["console"]:
        sys.stdout.write(f"  {line}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
