"""Re-measure highlight boxes on the saved live notebook (no re-run)."""
import json, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]; REC = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "recording"); NB = sys.argv[2] if len(sys.argv) > 2 else "01_live.ipynb"; PORT = 8899
src = (ROOT / "recording/record_run.py").read_text(); find = src[src.index('find = """') + 10: src.index('"""', src.index('find = """') + 10)]
server = subprocess.Popen([str(ROOT / ".venv/bin/jupyter"), "lab", "--no-browser", f"--port={PORT}", f"--ServerApp.root_dir={ROOT}",
    "--IdentityProvider.token=", "--ServerApp.password=", f"--LabApp.user_settings_dir={REC / 'lab-settings'}"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
try:
    for _ in range(60):
        try: urllib.request.urlopen(f"http://localhost:{PORT}/api", timeout=1); break
        except Exception: time.sleep(1)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); ctx = b.new_context(viewport={"width": 1600, "height": 900}, device_scale_factor=2); p = ctx.new_page()
        p.goto(f"http://localhost:{PORT}/lab/tree/notebooks/{NB}?reset"); p.wait_for_selector(".jp-Notebook .jp-Cell", timeout=60000)
        p.keyboard.press("Meta+b"); time.sleep(3)
        targets = json.loads((REC / "highlight_targets.json").read_text()); boxes = {}
        cells = p.locator(".jp-Notebook .jp-Cell").all()
        for i, strs in targets.items():
            cells[int(i)].scroll_into_view_if_needed(); time.sleep(0.3)
            for s in strs: boxes.setdefault(i, {})[s] = p.evaluate(find, [int(i), s])
        (REC / "boxes.json").write_text(json.dumps(boxes, indent=1)); b.close()
        print("missing:", [(i, s) for i, d in boxes.items() for s, v in d.items() if v is None])
finally:
    server.terminate()
