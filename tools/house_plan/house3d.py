# -*- coding: utf-8 -*-
"""A 3D model of a house, built from the same plan as the drawings (a Plan of draw.py).

build_page.py puts it in the page of the models (a "תלת-ממד" tab per model); page() below is a page of one model
(shots3d.py photographs it). The walls with the doors and windows cut out, the floors, sample furniture,
the garden, the roof, the neighbors' houses as light boxes, and the sun by season and hour. three.js loads from a CDN
when the page opens (like the 3D view of the ranking pages); the viewer is house3d.js, inlined here.

The walls come from the plan the way the drawing makes them: whatever is inside the blocks and not inside a room is
wall. The plan is rasterized on a 5 cm grid (every coordinate of a plan is a multiple of 5 cm). Each wall cell gets
the height profile of the opening it is in (a door leaves only the lintel, a window the sill and the lintel), and
cells with the same profile are merged into boxes. The furniture goes to the viewer as the plan has it, with the
side of each piece that stands against a wall.

Heights: the floor at ±0.00, the ceiling at 2.75, the roof slab 0.25, the parapet of the flat roof 0.4. Doors 2.1,
windows 0.9-2.1, high windows 1.6-2.1, the glass to the garden 2.3. The tiles: 50% (the maximum in the rules), the
ridge along y as in the roof plan. The parking 0.7 below the house (4 steps), the garden 0.1 below.

"""
import json
import math
from collections import deque
from pathlib import Path

import draw
import lot as S

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

G = 0.05                                   # the grid, meters
CEIL = 2.75
DOOR, SILL, HEAD, HIGH, GLASS = 2.1, 0.9, 2.1, 1.6, 2.3
SOLID = {"full": [(0, CEIL)],              # the parts of the wall that stay, per opening kind
         "hinged": [(DOOR, CEIL)], "steel": [(DOOR, CEIL)], "slide": [(DOOR, CEIL)], "gap": [(DOOR, CEIL)],
         "window": [(0, SILL), (HEAD, CEIL)], "high": [(0, HIGH), (HEAD, CEIL)], "glass": [(GLASS, CEIL)]}
OPP = {"x0": "x1", "x1": "x0", "y0": "y1", "y1": "y0"}
LABEL_AT = {}             # where a bold mark's label goes, if not where the plan puts it: {text: (x, y)}


def ix(v):
    return int(round(v / G))


class Grid:
    """The plan on a 5 cm grid: None outside the walls, else (wall kind, opening kind)."""

    def __init__(self, p):
        x0, y0, x1, y1 = p.bbox()
        self.i0, self.j0 = ix(x0), ix(y0)
        self.ni, self.nj = ix(x1) - self.i0, ix(y1) - self.j0
        self.c = [[None] * self.nj for _ in range(self.ni)]
        for b in p.blocks:
            self.fill(b, ("wall", "full"))
        for r in p.rooms:
            for rc in r["rects"]:
                self.fill(rc, None)
        for r in p.rooms:                  # the mamad's walls: reinforced concrete
            if r["kind"] == "mamad":
                for rc in r["rects"]:
                    self.fill((rc[0] - 0.35, rc[1] - 0.35, rc[2] + 0.35, rc[3] + 0.35), ("mamad", "full"), True)
        for o in p.openings:
            self.fill(o["r"], o["t"], True)
        self.outer(p)

    def outer(self, p, t=5):
        """The outer 25 cm (t cells) of the outside walls get their own kind ("ext"), so an inner wall that meets
        them does not cut them into pieces: each outside face is one box from a corner to an opening, with no
        seams in the facades."""
        inside = [[False] * self.nj for _ in range(self.ni)]
        for b in p.blocks:
            si, sj = self.span(b)
            for i in si:
                for j in sj:
                    inside[i][j] = True
        steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
        near = lambda i, j: [(i + a, j + b) for a, b in steps]
        valid = lambda i, j: 0 <= i < self.ni and 0 <= j < self.nj
        is_wall = lambda i, j: valid(i, j) and self.c[i][j] is not None and self.c[i][j][0] == "wall"
        dist, q = {}, deque()
        for i in range(self.ni):
            for j in range(self.nj):
                if is_wall(i, j) and any(not valid(a, b) or not inside[a][b] for a, b in near(i, j)):
                    dist[i, j] = 1
                    q.append((i, j))
        while q:
            i, j = q.popleft()
            if dist[i, j] < t:
                for a, b in near(i, j):
                    if is_wall(a, b) and (a, b) not in dist:
                        dist[a, b] = dist[i, j] + 1
                        q.append((a, b))
        for i, j in dist:
            self.c[i][j] = ("ext", self.c[i][j][1])

    def span(self, r):
        return (range(max(ix(r[0]) - self.i0, 0), min(ix(r[2]) - self.i0, self.ni)),
                range(max(ix(r[1]) - self.j0, 0), min(ix(r[3]) - self.j0, self.nj)))

    def fill(self, r, v, walls_only=False):
        si, sj = self.span(r)
        for i in si:
            for j in sj:
                if walls_only:
                    if self.c[i][j] is None:
                        continue
                    v2 = (self.c[i][j][0], v) if isinstance(v, str) else v
                    self.c[i][j] = v2
                else:
                    self.c[i][j] = v

    def wall(self, x, y):
        i, j = int(math.floor(x / G + 1e-9)) - self.i0, int(math.floor(y / G + 1e-9)) - self.j0
        return 0 <= i < self.ni and 0 <= j < self.nj and self.c[i][j] is not None

    def boxes(self):
        """Greedy merge of cells with the same value into rectangles: (x0, x1, y0, y1, value)."""
        used = [[False] * self.nj for _ in range(self.ni)]
        out = []
        for j in range(self.nj):
            for i in range(self.ni):
                v = self.c[i][j]
                if v is None or used[i][j]:
                    continue
                i1 = i
                while i1 + 1 < self.ni and self.c[i1 + 1][j] == v and not used[i1 + 1][j]:
                    i1 += 1
                j1 = j
                while j1 + 1 < self.nj and all(self.c[k][j1 + 1] == v and not used[k][j1 + 1] for k in range(i, i1 + 1)):
                    j1 += 1
                for k in range(i, i1 + 1):
                    for m in range(j, j1 + 1):
                        used[k][m] = True
                out.append((round((self.i0 + i) * G, 3), round((self.i0 + i1 + 1) * G, 3),
                            round((self.j0 + j) * G, 3), round((self.j0 + j1 + 1) * G, 3), v))
        return out


def walls(grid):
    out = []
    for x0, x1, y0, y1, (kind, prof) in grid.boxes():
        for z0, z1 in SOLID[prof]:
            out.append([x0, x1, y0, y1, z0, z1, "wall" if kind == "ext" else kind])
    return out


def slab(p, holes):
    """The roof slab over the blocks, with the skylights cut out."""
    g = Grid.__new__(Grid)
    x0, y0, x1, y1 = p.bbox()
    g.i0, g.j0, g.ni, g.nj = ix(x0), ix(y0), ix(x1) - ix(x0), ix(y1) - ix(y0)
    g.c = [[None] * g.nj for _ in range(g.ni)]
    for b in p.blocks:
        g.fill(b, "slab")
    for h in holes:
        g.fill(h, None)
    return [b[:4] for b in g.boxes()]


def sides(grid, r):
    """How much of each side of a piece of furniture stands against a wall (0-1)."""
    x0, y0, x1, y1 = r
    out = {}
    for s in ("x0", "x1", "y0", "y1"):
        if s in ("x0", "x1"):
            x = x0 - 0.03 if s == "x0" else x1 + 0.03
            pts = [(x, y0 + (k + 0.5) * (y1 - y0) / 8) for k in range(8)]
        else:
            y = y0 - 0.03 if s == "y0" else y1 + 0.03
            pts = [(x0 + (k + 0.5) * (x1 - x0) / 8, y) for k in range(8)]
        out[s] = sum(grid.wall(x, y) for x, y in pts) / 8
    return out


def room_of(p, x, y):
    for r in p.rooms:
        if any(rc[0] - 1e-6 <= x <= rc[2] + 1e-6 and rc[1] - 1e-6 <= y <= rc[3] + 1e-6 for rc in r["rects"]):
            return r["id"]
    return None


def furniture(p, grid):
    out = []
    stacks = [(m["x"], m["y"]) for m in p.marks if m["text"] == "×2"]
    for f in p.furniture:
        f = dict(f)
        r = f["r"]
        if len(r) == 4:
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            f["walls"] = sides(grid, r)
            # the back: the side with the most wall along it (the longer side wins a tie, as in a corner)
            lens = {s: f["walls"][s] * ((r[3] - r[1]) if s in ("x0", "x1") else (r[2] - r[0])) for s in f["walls"]}
            back = max(lens, key=lens.get)
            f["back_wall"] = back if f["walls"][back] >= 0.5 else None
        else:
            cx, cy = r[0], r[1]
        f["room"] = room_of(p, cx, cy)
        if f["k"] == "washer":
            f["stack"] = any(r[0] - 0.4 <= sx <= r[2] + 0.4 and r[1] <= sy <= r[3] for sx, sy in stacks)
        f.pop("label", None)
        out.append(f)
    return out


def _exterior(p, o):
    """Which way an opening faces, if one of its sides is outside the house (the forms page)."""
    x0, y0, x1, y1 = o["r"]
    cx, cy, d = (x0 + x1) / 2, (y0 + y1) / 2, 0.12
    out = lambda x, y: not any(b[0] < x < b[2] and b[1] < y < b[3] for b in p.blocks)
    if (x1 - x0) >= (y1 - y0):
        return "north" if out(cx, y0 - d) else "south" if out(cx, y1 + d) else None
    return "west" if out(x0 - d, cy) else "east" if out(x1 + d, cy) else None


def data(p, label_at=None, extras=None, sides_out=False):
    """label_at: where the bold labels go. extras: views, rugs, plants and the neighbors' labels of a model (the
    page of the models). sides_out: an opening is outside if one of its sides is."""
    label_at = LABEL_AT if label_at is None else label_at
    grid = Grid(p)
    x0, y0, x1, y1 = p.bbox()
    skylights = [f["r"] for f in p.furniture if f["k"] == "skylight"]
    rooms = []
    for r in p.rooms:
        big = max(r["rects"], key=lambda rc: (rc[2] - rc[0]) * (rc[3] - rc[1]))
        rooms.append(dict(id=r["id"], kind=r["kind"], rects=r["rects"], name=r["name"],
                          at=((big[0] + big[2]) / 2, (big[1] + big[3]) / 2)))
    labels = [dict(text=r["name"], x=r["at"][0], y=r["at"][1]) for r in rooms if r["name"]]
    labels += [dict(text=m["text"], x=label_at.get(m["text"], (m["x"], m["y"]))[0],
                    y=label_at.get(m["text"], (m["x"], m["y"]))[1]) for m in p.marks if m["bold"] and not m.get("roof")]
    glabels = [dict(text=m["text"], x=m["x"], y=m["y"], z=0.6) for m in p.marks
               if not m["bold"] and not m.get("roof") and m["text"].startswith("דשא")]
    glabels.append(dict(text="חניה", x=(S.PARKING[0] + S.PARKING[2]) / 2, y=2.2, z=0.4))
    openings = []
    for o in p.openings:
        r = o["r"]
        ext = r[1] <= y0 + 1e-6 and "north" or r[3] >= y1 - 1e-6 and "south" or r[0] <= x0 + 1e-6 and "west" \
            or r[2] >= x1 - 1e-6 and "east" or None
        if sides_out:
            ext = _exterior(p, o)
        openings.append(dict(o, ext=ext))
    garden = [{k: v for k, v in g.items() if k != "near"} for g in p.garden]
    terrace = [x["r"] for x in p.roof if x["k"] == "terrace"]   # the railing all around, open where the stair arrives
    rails = [a for seg in draw._inset_outline(terrace, 0.1) for a in draw._cut(seg, p.gaps)] if terrace else []
    return dict(**(extras or {}), blocks=p.blocks, rails=rails,
        bbox=[x0, y0, x1, y1], ceil=CEIL, door=DOOR, sill=SILL, head=HEAD, high=HIGH, glass=GLASS,
        walls=walls(grid), slab=slab(p, skylights), skylights=skylights, rooms=rooms, labels=labels, glabels=glabels,
        openings=openings, furniture=furniture(p, grid), garden=garden, roof=p.roof,
        plot=[S.W, S.D], parking=S.PARKING, stalls=S.STALLS, path=S.PATH,
        tx=0.0, entry_x=7.15)


# A page of one model (shots3d.py): the title and the style, the bar of buttons and the stage. The viewer is
# house3d.js; HOUSE is the data of the model, and the page mounts itself when it loads.
TOP = """<title>הבית בתלת-ממד</title>
<style>
:root{--bg:#faf9f6;--card:#fff;--text:#22221f;--muted:#6b6a65;--line:#e4e2da;--accent:#0f6e56;--accent-bg:#e1f5ee}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 "Segoe UI",Arial,sans-serif}
main{max-width:1280px;margin:0 auto;padding:18px 16px 40px}
.bar{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;margin:0 0 10px}
.grp{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.bar button{font:inherit;font-size:14px;padding:4px 12px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--text);cursor:pointer}
.bar button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
#stage{position:relative;height:min(76vh,860px);min-height:380px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#dfe9f2;touch-action:none}
#stage canvas{display:block;width:100%;height:100%}
.msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#3a3833;font-size:15px;pointer-events:none;text-align:center;padding:16px}
.shot main{padding:0;max-width:none}.shot .bar{display:none}.shot #stage{height:100vh;border:0;border-radius:0}
</style>"""

BODY = """<main lang="he" dir="rtl">
<div class="bar">
  <div class="grp" role="group" aria-label="מבט">__VIEWS__</div>
  <div class="grp" role="group" aria-label="הגג">
    <button data-roof="off" aria-pressed="true">בלי גג</button><button data-roof="on">עם גג</button>
    <button data-roof="shade">בלי, עם הצל שלו</button></div>
  <div class="grp"><label><input type="checkbox" class="labels" checked> שמות החדרים</label>
    <label><input type="checkbox" class="neighbors" checked> השכנים</label></div>
  <div class="grp" role="group" aria-label="שמש">
    <button data-season="winter" aria-pressed="true">חורף</button><button data-season="summer">קיץ</button>
    <input type="range" class="hour" min="7" max="17" step="0.25" value="12" aria-label="שעה">
    <output class="sunread"></output></div>
</div>
<div id="stage"><canvas></canvas><div class="msg">טוען את ההדמיה...</div></div>
</main>
<script>const HOUSE = __DATA__;</script>
<script>
__JS__
</script>"""

PAGE = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
__TOP__
</head>
<body>
__BODY__
</body>
</html>
"""


def page(d, buttons):
    """A page of one model: d is data(p, ...) and buttons a list of (view, label)."""
    views = "".join(f'<button data-view="{v}"{" aria-pressed=true" if v == "top" else ""}>{t}</button>'
                    for v, t in buttons)
    js = (HERE / "house3d.js").read_text(encoding="utf-8")
    body = BODY.replace("__VIEWS__", views).replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    return PAGE.replace("__TOP__", TOP).replace("__BODY__", body.replace("__JS__", js))
