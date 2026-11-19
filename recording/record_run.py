"""Real-time screen recording of the notebook running cell by cell in JupyterLab, plus a crisp still of every cell.

Outputs (recording/):
  run.webm            the live session (1600x900)
  cells.json          per cell: index, type, video start/end seconds, text
  cells/cell_XX.png   2x screenshot of each executed cell (input + output)
"""
import json, shutil, subprocess, time, urllib.request
from pathlib import Path

import nbformat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
import sys
REC = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "recording")
SRC = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "notebooks/01_scamguard.ipynb")
LIVE = ROOT / ("notebooks/" + SRC.stem + "_live.ipynb")
PORT = 8899
URL = f"http://localhost:{PORT}/lab/tree/notebooks/{LIVE.name}?reset"

# Start from a clean notebook so every output on screen is produced live.
nb = nbformat.read(SRC, 4)
for c in nb.cells:
    if c.cell_type == "code":
        c.outputs, c.execution_count = [], None
nbformat.write(nb, LIVE)

settings = REC / "lab-settings/@jupyterlab/apputils-extension"
settings.mkdir(parents=True, exist_ok=True)
(settings / "themes.jupyterlab-settings").write_text(json.dumps(
    {"overrides": {"code-font-size": "18px", "content-font-size1": "18px", "ui-font-size1": "14px"}}))
(settings / "notification.jupyterlab-settings").write_text(json.dumps({"fetchNews": "false", "checkForUpdates": False}))

server = subprocess.Popen(
    [str(ROOT / ".venv/bin/jupyter"), "lab", "--no-browser", f"--port={PORT}", f"--ServerApp.root_dir={ROOT}",
     "--IdentityProvider.token=", "--ServerApp.password=", "--ServerApp.disable_check_xsrf=True",
     f"--LabApp.user_settings_dir={REC / 'lab-settings'}"],
    stdout=open(REC / "jupyter.log", "w"), stderr=subprocess.STDOUT)
try:
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}/api", timeout=1); break
        except Exception:
            time.sleep(1)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1600, "height": 900},
                                  record_video_dir=str(REC / "_video"), record_video_size={"width": 1600, "height": 900})
        t0 = time.monotonic()
        page = ctx.new_page()
        page.goto(URL)
        page.wait_for_selector(".jp-Notebook .jp-Cell", timeout=60000)
        page.wait_for_function("() => document.querySelector('.jp-Notebook-ExecutionIndicator')?.getAttribute('data-status') === 'idle'", timeout=60000)
        page.keyboard.press("Meta+b")  # hide the file browser
        time.sleep(2)
        for _ in range(3):  # dismiss any startup dialog (kernel picker, news) before starting
            if page.locator(".jp-Dialog").count():
                btn = page.locator(".jp-Dialog .jp-mod-accept")
                (btn.first.click() if btn.count() else page.keyboard.press("Escape")); time.sleep(1)
        page.locator(".jp-Notebook .jp-Cell").first.click(force=True)
        page.keyboard.press("Escape")  # command mode

        log = []
        cells = nb.cells
        for i, c in enumerate(cells):
            start = time.monotonic() - t0
            page.keyboard.press("Shift+Enter")
            if c.cell_type == "code":
                page.wait_for_function(
                    """i => { const p = document.querySelectorAll('.jp-Notebook .jp-Cell')[i].querySelector('.jp-InputPrompt');
                             return p && /\\[\\d+\\]/.test(p.textContent); }""", arg=i, timeout=10800000)
            time.sleep(1.5)  # let the output settle on screen
            log.append({"i": i, "type": c.cell_type, "start": round(start, 2), "end": round(time.monotonic() - t0, 2),
                        "text": c.source[:200]})
            print(f"cell {i:2d} {c.cell_type:8s} {log[-1]['start']:7.1f}s -> {log[-1]['end']:7.1f}s", flush=True)
        time.sleep(2)
        page.keyboard.press("Meta+s")  # save the live outputs so the stills below show them
        page.wait_for_function("() => !document.title.startsWith('*') && !document.querySelector('.jp-mod-dirty')", timeout=30000)
        time.sleep(2)
        video = page.video
        page.close(); ctx.close()
        shutil.move(video.path(), REC / "run.webm")
        (REC / "cells.json").write_text(json.dumps(log, indent=1))
        page.context if False else None

        # Crisp stills of the executed live notebook.
        ctx2 = browser.new_context(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
        p2 = ctx2.new_page(); p2.goto(URL)
        p2.wait_for_selector(".jp-Notebook .jp-Cell", timeout=60000)
        p2.keyboard.press("Meta+b"); time.sleep(3)
        out = REC / "cells"; out.mkdir(exist_ok=True)
        targets = json.loads((REC / "highlight_targets.json").read_text())
        boxes = {}
        find = """([i, s]) => {
            const cell = document.querySelectorAll('.jp-Notebook .jp-Cell')[i], base = cell.getBoundingClientRect();
            const w = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT);
            for (let n; (n = w.nextNode());) {
                const k = n.textContent.indexOf(s); if (k < 0) continue;
                const r = document.createRange(); r.setStart(n, k); r.setEnd(n, k + s.length);
                const b = r.getBoundingClientRect();
                return [b.left - base.left, b.top - base.top, b.width, b.height].map(v => Math.round(v * 2));
            } return null; }"""
        for i, el in enumerate(p2.locator(".jp-Notebook .jp-Cell").all()):
            el.scroll_into_view_if_needed(); time.sleep(0.4)
            el.screenshot(path=str(out / f"cell_{i:02d}.png"))
            for s in targets.get(str(i), []):
                boxes.setdefault(str(i), {})[s] = p2.evaluate(find, [i, s])
        (REC / "boxes.json").write_text(json.dumps(boxes, indent=1))
        missing = [(i, s) for i, d in boxes.items() for s, b in d.items() if b is None]
        print("highlight boxes missing:", missing)
        ctx2.close(); browser.close()
finally:
    server.terminate()
print("done")
