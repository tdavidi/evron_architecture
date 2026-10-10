# -*- coding: utf-8 -*-
"""Pictures of the 3D model of one model: a page of the model in deliverables/preview/ (not in git), photographed by
Chrome without a window (headless). Optional: the page itself already has the 3D tab.

Usage (from the repo root, with a local server on port 8765 serving deliverables/:
  .venv/Scripts/python -m http.server 8765 --directory deliverables   in another terminal):
  .venv/Scripts/python tools/house_plan/shots3d.py <model function> garden patio
writes deliverables/preview/3d-<id>-<view>.png. Views: top, plan, garden, street, and the model's own (texts.py,
VIEWS3D). Append :on, :off or :shade to a view for the roof.
CHROME below is the usual path on Windows; on a Mac: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_page as B  # noqa: E402
import example_models  # noqa: E402
import example_texts  # noqa: E402
import house3d  # noqa: E402
import models  # noqa: E402
import texts  # noqa: E402

CHROME = (shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium")
          or r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PREVIEW = B.ROOT / "deliverables" / "preview"
PORT = int(os.environ.get("PORT", "8765"))   # the local server


def main():
    fn, views = sys.argv[1], sys.argv[2:] or ["top"]
    mine = hasattr(models, fn)
    M, T = (models, texts) if mine else (example_models, example_texts)
    p = getattr(M, fn)()
    PREVIEW.mkdir(parents=True, exist_ok=True)
    name = f"3d-{B.fid(p)}"
    (PREVIEW / f"{name}.html").write_text(house3d.page(B.data3d(T, p), B.buttons3d(T, p)), encoding="utf-8")
    for v in views:
        view, _, roof = v.partition(":")
        out = PREVIEW / f"{name}-{view}{'-' + roof if roof else ''}.png"
        url = f"http://127.0.0.1:{PORT}/preview/{name}.html#view={view}&shot=1" + (f"&roof={roof}" if roof else "")
        with tempfile.TemporaryDirectory() as prof:       # a profile of its own, or Chrome hands it to a running one
            subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--use-angle=swiftshader",
                            "--enable-unsafe-swiftshader", "--window-size=1400,900", "--virtual-time-budget=30000",
                            f"--screenshot={out}", url], capture_output=True, timeout=120)
        print("wrote", out)


if __name__ == "__main__":
    main()
