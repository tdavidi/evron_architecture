# -*- coding: utf-8 -*-
"""Builds the sketch board: a page where the family draws by hand, over the plot or over a model.

The board is Excalidraw (free drawing and shapes, a library of objects in real size: beds, sofas, doors, windows,
kitchen, bath, a car...) with a locked background: the empty plot, or one of the models. Scale: 1 m = 50 px, in the
plot's coordinates (x from the shared boundary, y from the street to the garden), so Claude can read a sketch back
in meters. The page is published as a private Artifact; drafts and versions live in its database (db).

  python tools/sketch/build_sketch.py            the empty plot and your models (models.py)  -> deliverables/sketch/index.html
  python tools/sketch/build_sketch.py example    the empty plot and the example's models     -> deliverables/example/sketch.html

The page is in the Artifact format (<title> and <style> first, no document tags). The texts.py LEAKS check runs on
the backgrounds, as on the shared page.
"""
import base64
import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "house_plan"))
import draw  # noqa: E402

PX = 50                     # px per meter, the board's scale


def clean(svg, leaks):
    if leaks:
        texts = " ".join(re.findall(r">([^<>]+)<", svg))
        found = sorted({m.group(0) for m in re.finditer(leaks, texts)})
        if found:
            raise SystemExit(f"sketch: left in a background: {found}")
    return svg


def background(key, label, svg, leaks):
    vb = [float(v) / 100 for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]   # cm -> m
    data = base64.b64encode(clean(svg, leaks).encode("utf-8")).decode("ascii")
    label = label.replace("\\", "").replace('"', "'")
    return (f'{key}:{{label:"{label}",dataURL:"data:image/svg+xml;base64,{data}",'
            f'x:{vb[0] * PX:.1f},y:{vb[1] * PX:.1f},w:{vb[2] * PX:.1f},h:{vb[3] * PX:.1f}}}')


def main():
    example = len(sys.argv) > 1 and sys.argv[1] == "example"
    M = importlib.import_module("example_models" if example else "models")
    T = importlib.import_module("example_texts" if example else "texts")
    leaks = getattr(T, "LEAKS", None)
    plans = [f() for f in (M.FORMS if example else M.MODELS)]
    bgs = [background("plot", "המגרש, ריק", draw.render(draw.Plan("empty", "", []), "site"), leaks)]
    bgs += [background(f"m{i}", f"דגם {p.cid}", draw.render(p, "plan"), leaks) for i, p in enumerate(plans)]
    html = (Path(__file__).parent / "template.html").read_text(encoding="utf-8")
    html = html.replace("/*__BACKGROUNDS__*/{}", "{" + ",".join(bgs) + "}")
    out = ROOT / "deliverables" / ("example/sketch.html" if example else "sketch/index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", out.relative_to(ROOT), f"{len(html) // 1024} KB, backgrounds: plot" +
          "".join(f", {p.cid}" for p in plans))


if __name__ == "__main__":
    main()
