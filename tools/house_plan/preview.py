# -*- coding: utf-8 -*-
"""A quick preview of one model and one view, without building the whole page (deliverables/preview/, not in git).

Usage (from the repo root):
  .venv/Scripts/python tools/house_plan/preview.py <model function> <view> [x0 y0 x1 y1 [scale]]
<model function>: a function of models.py, or of example_models.py (e.g. form_patio_swap). <view>: plan, routes,
site or roof. x0 y0 x1 y1 (meters): also a crop of that part, enlarged by scale (approximate: the scale is measured on
the plan view, 64.7 px per meter at zoom 1.6).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import draw  # noqa: E402
import example_models  # noqa: E402
import models  # noqa: E402
from build_page import png  # noqa: E402
from PIL import Image  # noqa: E402

SP = Path(__file__).resolve().parents[2] / "deliverables" / "preview"
SP.mkdir(parents=True, exist_ok=True)
fn, view = sys.argv[1], sys.argv[2]
p = getattr(models if hasattr(models, fn) else example_models, fn)()
errs = p.check()
if errs:
    print("CHECK:", errs)
out = SP / f"pv-{fn}-{view}.png"
zoom = {"plan": 1.6, "routes": 1.6, "roof": 0.8, "site": 0.9}.get(view, 1.6)
png(draw.render(p, view, bidi=True), out, zoom)
if len(sys.argv) >= 7:
    x0, y0, x1, y1 = map(float, sys.argv[3:7])
    scale = float(sys.argv[7]) if len(sys.argv) > 7 else 2.0
    im = Image.open(out)
    K, X0, Y0 = 64.7 * zoom / 1.6, 79.5 * zoom / 1.6, 96.0 * zoom / 1.6
    box = tuple(int(v) for v in (X0 + x0 * K, Y0 + y0 * K, X0 + x1 * K, Y0 + y1 * K))
    c = im.crop(box)
    c = c.resize((int(c.width * scale), int(c.height * scale)))
    c.save(SP / f"pv-{fn}-{view}-crop.png")
    print("crop", box)
print("wrote", out)
