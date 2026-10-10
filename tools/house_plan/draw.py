# -*- coding: utf-8 -*-
"""Floor plans as data, drawn to SVG in the usual Israeli sketch-plan style.

A concept is a Plan: gross blocks (the outer faces of the exterior walls), rooms (net rectangles),
openings, furniture, garden items and roof areas. Walls are not drawn one by one: the blocks are
filled with the wall color and the rooms are drawn on top, so whatever is left between rooms is
wall, and gross minus net is the wall area. Coordinates are in meters in the plot frame of lot.py
(x from the shared wall, y from the street); the SVG is in centimeters.

Style: white rooms with black wall faces, gray walls, hatched concrete for the mamad, doors with
their swing, windows inside the walls, furniture and fixtures in thin lines, names and areas.

mirror=True draws the plan for the other unit of the pair (shared wall on the right). The page
orientation and the north arrow stay: the street is still up and north is still 17° left of up.
"""
import math
import re

import lot as S

PAPER, INK, WALL = "#ffffff", "#1d1d1b", "#9b9a95"
MUTED, FURN, GLASS = "#77756e", "#3a3936", "#3a3936"
FONT = 'font-family="Arial, Segoe UI, sans-serif"'
EPS = 1e-6


def c(v):
    """meters -> centimeters, rounded for compact SVG"""
    return round(v * 100, 1)


def area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


class Plan:
    def __init__(self, cid, name, blocks, floor="קומת קרקע"):
        self.cid, self.name, self.floor = cid, name, floor
        self.blocks = [tuple(b) for b in blocks]
        self.rooms, self.openings, self.furniture, self.garden = [], [], [], []
        self.roof, self.marks, self.dims, self.zones = [], [], [], []
        self.gaps = []               # openings in the roof terrace railing, where a stair arrives
        self.upper = None            # optional upper floor (another Plan, same frame)
        self.entry = None            # (x, y, direction) of the main entrance arrow
        self.routes = []             # walks for the checklist scenarios (route view)
        self.room_dims = False       # write the inner width × depth under the area (stage 3)

    # ---- building ---------------------------------------------------------------------------
    def room(self, rid, name, *rects, kind="room", at=None, area_label=True, small=False, count=True, dims=True):
        """dims=False: no width × depth line under the area, for a room too small for it."""
        self.rooms.append(dict(id=rid, name=name, rects=[tuple(r) for r in rects], kind=kind,
                               at=at, area_label=area_label, small=small, count=count, dims=dims))
        return self

    def door(self, x0, y0, x1, y1, hinge, into, kind="hinged"):
        """Cut through a wall. hinge: 'x0'/'x1' on a horizontal wall, 'y0'/'y1' on a vertical one;
        into: +1/-1, the side the leaf opens to (+y/-y or +x/-x). kind: hinged, steel (mamad)."""
        self.openings.append(dict(t=kind, r=(x0, y0, x1, y1), hinge=hinge, into=into))

    def slide(self, x0, y0, x1, y1):
        """Interior sliding / pocket door."""
        self.openings.append(dict(t="slide", r=(x0, y0, x1, y1)))

    def gap(self, x0, y0, x1, y1):
        """Open passage without a door."""
        self.openings.append(dict(t="gap", r=(x0, y0, x1, y1)))

    def window(self, x0, y0, x1, y1, kind="window"):
        """kind: window, high (high sill), glass (floor-to-ceiling sliding glass door)."""
        self.openings.append(dict(t=kind, r=(x0, y0, x1, y1)))

    def furn(self, kind, *r, **kw):
        self.furniture.append(dict(k=kind, r=tuple(r), **kw))

    def yard(self, kind, *r, label=None, **kw):
        self.garden.append(dict(k=kind, r=tuple(r), label=label, **kw))

    def zone(self, x0, y0, x1, y1):
        """Dashed outline of an open zone inside a bigger room (kitchen, entry lobby...)."""
        self.zones.append((x0, y0, x1, y1))

    def roof_area(self, kind, *r, slope=None):
        """kind: tile, flat, or terrace (a flat roof to walk on, with a railing around it);
        slope: direction the water runs ('+y', '-y', '+x', '-x', 'gable-x', 'gable-y')."""
        self.roof.append(dict(k=kind, r=tuple(r), slope=slope))

    def mark(self, x, y, text, size=0.22, color=MUTED, anchor="middle", bold=False, roof=False):
        self.marks.append(dict(x=x, y=y, text=text, size=size, color=color, anchor=anchor, bold=bold, roof=roof))

    def dim(self, x0, y0, x1, y1, off=0.6, text=None):
        self.dims.append(dict(p=(x0, y0, x1, y1), off=off, text=text))

    def route(self, kind, *pts, name="", at=None):
        """A walk through the house for the checklist scenarios. kind: alarm, groceries, guest, laundry.
        at: where to put the length label (default: just above the start)."""
        self.routes.append(dict(kind=kind, pts=[tuple(q) for q in pts], name=name, at=at))

    @staticmethod
    def route_length(rt):
        return sum(math.dist(a, b) for a, b in zip(rt["pts"], rt["pts"][1:]))

    # ---- numbers ----------------------------------------------------------------------------
    def gross(self):
        return sum(area(b) for b in self.blocks)

    def net(self):
        return sum(self.room_area(r) for r in self.rooms if r["count"])

    @staticmethod
    def room_area(r):
        return sum(area(x) for x in r["rects"])

    def roof_split(self):
        tile = sum(area(x["r"]) for x in self.roof if x["k"] == "tile")
        flat = sum(area(x["r"]) for x in self.roof if x["k"] in ("flat", "terrace"))
        return tile, flat

    def bbox(self):
        xs = [v for b in self.blocks for v in (b[0], b[2])]
        ys = [v for b in self.blocks for v in (b[1], b[3])]
        return min(xs), min(ys), max(xs), max(ys)

    def check(self):
        """Overlapping rooms or rooms outside the blocks are drawing errors."""
        errs = []
        rects = [(r["id"], x) for r in self.rooms for x in r["rects"]]
        inside = lambda px, py: any(b[0] - EPS <= px <= b[2] + EPS and b[1] - EPS <= py <= b[3] + EPS
                                    for b in self.blocks)
        for i, (a, ra) in enumerate(rects):
            if not all(inside(px, py) for px in (ra[0], ra[2]) for py in (ra[1], ra[3])):
                errs.append(f"{a} outside the blocks: {ra}")
            for b, rb in rects[i + 1:]:
                if min(ra[2], rb[2]) - max(ra[0], rb[0]) > EPS and min(ra[3], rb[3]) - max(ra[1], rb[1]) > EPS:
                    errs.append(f"{a} overlaps {b}")
        return errs


# ---- mirroring ------------------------------------------------------------------------------

def _mr(r, w):
    return (round(w - r[2], 4), r[1], round(w - r[0], 4), r[3])


def _flipx(v):
    return {"x0": "x1", "x1": "x0"}.get(v, v)


def mirrored(p, w=S.W):
    q = Plan(p.cid, p.name, [_mr(b, w) for b in p.blocks], p.floor)
    q.room_dims = p.room_dims
    for r in p.rooms:
        q.rooms.append(dict(r, rects=[_mr(x, w) for x in r["rects"]],
                            at=(w - r["at"][0], r["at"][1]) if r["at"] else None))
    for o in p.openings:
        o2 = dict(o, r=_mr(o["r"], w))
        if o["t"] in ("hinged", "steel"):
            if o["hinge"] in ("x0", "x1"):
                o2["hinge"] = _flipx(o["hinge"])
            else:
                o2["into"] = -o["into"]
        q.openings.append(o2)
    for f in p.furniture:
        f2 = dict(f, r=_mr(f["r"], w) if len(f["r"]) == 4 else (w - f["r"][0],) + f["r"][1:])
        for key in ("head", "back", "face", "side", "open"):
            if key in f2:
                f2[key] = _flipx(f2[key])
        for key in ("sink", "hob", "chair"):
            if f2.get(key):
                f2[key] = (w - f2[key][0], f2[key][1])
        if f2.get("extend"):
            f2["extend"] = _mr(f2["extend"], w)
        q.furniture.append(f2)
    for g in p.garden:
        g2 = dict(g, r=_mr(g["r"], w) if len(g["r"]) == 4 else (w - g["r"][0],) + g["r"][1:])
        if g2.get("at"):
            g2["at"] = (w - g2["at"][0], g2["at"][1])
        for key in ("poly", "walk", "rail"):                 # a stair's points
            if g2.get(key):
                g2[key] = [(w - x, y) for x, y in g2[key]]
        if g2.get("rails"):
            g2["rails"] = [[(w - x, y) for x, y in rl] for rl in g2["rails"]]
        if g2.get("lines"):
            g2["lines"] = [(w - xa, ya, w - xb, yb) for xa, ya, xb, yb in g2["lines"]]
        q.garden.append(g2)
    for x in p.roof:
        sl = {"+x": "-x", "-x": "+x"}.get(x["slope"], x["slope"])
        q.roof.append(dict(x, r=_mr(x["r"], w), slope=sl))
    for rt in p.routes:
        q.routes.append(dict(rt, pts=[(w - x, y) for x, y in rt["pts"]],
                             at=(w - rt["at"][0], rt["at"][1]) if rt.get("at") else None))
    for m in p.marks:
        q.marks.append(dict(m, x=w - m["x"], anchor={"start": "end", "end": "start"}.get(m["anchor"], m["anchor"])))
    for d in p.dims:
        x0, y0, x1, y1 = d["p"]
        if abs(y0 - y1) < EPS:
            q.dims.append(dict(d, p=(w - x1, y0, w - x0, y1)))
        else:
            q.dims.append(dict(d, p=(w - x0, y0, w - x1, y1), off=-d["off"]))
    q.zones = [_mr(z, w) for z in p.zones]
    q.gaps = [_mr(z, w) for z in p.gaps]
    if p.entry:
        x, y, dr = p.entry
        q.entry = (w - x, y, {"+x": "-x", "-x": "+x"}.get(dr, dr))
    if p.upper:
        q.upper = mirrored(p.upper, w)
    return q


# ---- SVG primitives -------------------------------------------------------------------------

def visual(s):
    """Logical RTL text -> visual order, for renderers without bidi (the PNG export via MuPDF).
    Browsers get the logical text."""
    if not re.search("[֐-׿]", s):
        return s
    tok = r"[0-9A-Za-z.,:×/%²+±=\-–]"
    runs = re.findall(rf"{tok}+(?:\s+{tok}+)*|[^0-9A-Za-z.,:×/%²+±=\-–]+", s)
    flip = str.maketrans("()[]", ")(][")
    out = [run if re.search(r"[0-9A-Za-z±]", run) else run[::-1].translate(flip) for run in runs]
    return "".join(reversed(out))


class Svg:
    def __init__(self, bidi=False):
        self.parts, self.bidi = [], bidi

    def add(self, s):
        self.parts.append(s)

    def rect(self, r, fill="none", stroke="none", sw=0, extra=""):
        x0, y0, x1, y1 = r
        self.add(f'<rect x="{c(x0)}" y="{c(y0)}" width="{c(x1 - x0)}" height="{c(y1 - y0)}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def line(self, x0, y0, x1, y1, stroke=FURN, sw=1.4, extra=""):
        self.add(f'<line x1="{c(x0)}" y1="{c(y0)}" x2="{c(x1)}" y2="{c(y1)}" stroke="{stroke}" '
                 f'stroke-width="{sw}" {extra}/>')

    def path(self, d, fill="none", stroke=FURN, sw=1.4, extra=""):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def circle(self, x, y, r, fill="none", stroke=FURN, sw=1.4, extra=""):
        self.add(f'<circle cx="{c(x)}" cy="{c(y)}" r="{c(r)}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" {extra}/>')

    def ellipse(self, x, y, rx, ry, fill="#fff", stroke=FURN, sw=1.4):
        self.add(f'<ellipse cx="{c(x)}" cy="{c(y)}" rx="{c(rx)}" ry="{c(ry)}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=0.26, color=INK, anchor="middle", bold=False, rotate=None):
        s = (visual(s) if self.bidi else s).replace("&", "&amp;").replace("<", "&lt;")
        rot = f' transform="rotate({rotate} {c(x)} {c(y)})"' if rotate else ""
        w = ' font-weight="700"' if bold else ""
        self.add(f'<text x="{c(x)}" y="{c(y)}" font-size="{c(size)}" fill="{color}" '
                 f'text-anchor="{anchor}" {FONT}{w}{rot}>{s}</text>')

    def hatch(self, r, step=0.09, stroke="#4b4a46", sw=1.0):
        """45° hatch clipped to a rectangle (concrete)."""
        x0, y0, x1, y1 = r
        w, h = x1 - x0, y1 - y0
        k = 0.0
        while k < w + h:
            # line x - y = const, from the bottom-left family: points (x0 + k - t, y0 + t)
            ax, ay = x0 + min(k, w), y0 + max(0.0, k - w)
            bx, by = x0 + max(0.0, k - h), y0 + min(k, h)
            self.line(ax, ay, bx, by, stroke=stroke, sw=sw)
            k += step


# ---- furniture --------------------------------------------------------------------------------

def _bed(g, r, head, pillows=None):
    x0, y0, x1, y1 = r
    g.rect(r, fill="#fff", stroke=FURN, sw=1.4)
    along_y = head in ("y0", "y1")
    width = (x1 - x0) if along_y else (y1 - y0)
    n = pillows or (2 if width > 1.25 else 1)
    pw = (width - 0.16 - 0.08 * (n - 1)) / n
    for i in range(n):
        o = 0.08 + i * (pw + 0.08)
        if along_y:
            py = y0 + 0.07 if head == "y0" else y1 - 0.37
            g.rect((x0 + o, py, x0 + o + pw, py + 0.3), fill="#fff", stroke=FURN, sw=1.1, extra='rx="5"')
        else:
            px = x0 + 0.07 if head == "x0" else x1 - 0.37
            g.rect((px, y0 + o, px + 0.3, y0 + o + pw), fill="#fff", stroke=FURN, sw=1.1, extra='rx="5"')
    # folded sheet: a diagonal line across the foot end
    if along_y:
        fy = y0 + 0.55 if head == "y0" else y1 - 0.55
        g.line(x0, fy, x1, fy, sw=1.0)
        ty = y1 - 0.45 if head == "y0" else y0 + 0.45
        g.line(x0 + 0.1, fy + (0.35 if head == "y0" else -0.35), x1 - 0.1, ty, sw=0.8)
    else:
        fx = x0 + 0.55 if head == "x0" else x1 - 0.55
        g.line(fx, y0, fx, y1, sw=1.0)
        tx = x1 - 0.45 if head == "x0" else x0 + 0.45
        g.line(fx + (0.35 if head == "x0" else -0.35), y0 + 0.1, tx, y1 - 0.1, sw=0.8)


def _chair(g, cx, cy, face, w=0.44, d=0.42):
    """A chair seen from above; face: the side the sitter faces ('x0','x1','y0','y1')."""
    if face in ("y0", "y1"):
        r = (cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2)
        g.rect(r, fill="#fff", stroke=FURN, sw=1.1, extra='rx="4"')
        by = r[3] - 0.07 if face == "y0" else r[1] + 0.07
        g.line(r[0] + 0.04, by, r[2] - 0.04, by, sw=1.6)
    else:
        r = (cx - d / 2, cy - w / 2, cx + d / 2, cy + w / 2)
        g.rect(r, fill="#fff", stroke=FURN, sw=1.1, extra='rx="4"')
        bx = r[2] - 0.07 if face == "x0" else r[0] + 0.07
        g.line(bx, r[1] + 0.04, bx, r[3] - 0.04, sw=1.6)


def _furniture(g, f):
    k, r = f["k"], f["r"]
    if k in ("bed", "crib"):
        _bed(g, r, f.get("head", "y0"), 1 if k == "crib" else None)
        if k == "crib":
            x0, y0, x1, y1 = r
            for i in range(1, 6):
                if f.get("head", "y0") in ("y0", "y1"):
                    yy = y0 + i * (y1 - y0) / 6
                    g.line(x0, yy, x0 + 0.06, yy, sw=0.8)
                    g.line(x1 - 0.06, yy, x1, yy, sw=0.8)
    elif k == "sofa":
        x0, y0, x1, y1 = r
        b = f.get("back", "y0")
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4, extra='rx="6"')
        t, a = 0.2, 0.18      # back and arm thickness
        seat = {"y0": (x0 + a, y0 + t, x1 - a, y1), "y1": (x0 + a, y0, x1 - a, y1 - t),
                "x0": (x0 + t, y0 + a, x1, y1 - a), "x1": (x0, y0 + a, x1 - t, y1 - a)}[b]
        g.rect(seat, fill="#fff", stroke=FURN, sw=1.1)
        n = f.get("seats", 3)
        if b in ("y0", "y1"):
            for i in range(1, n):
                xx = seat[0] + i * (seat[2] - seat[0]) / n
                g.line(xx, seat[1], xx, seat[3], sw=0.9)
        else:
            for i in range(1, n):
                yy = seat[1] + i * (seat[3] - seat[1]) / n
                g.line(seat[0], yy, seat[2], yy, sw=0.9)
        if f.get("open"):     # a sofa bed: dashed, the bed when open
            g.rect(f["open"], fill="none", stroke=FURN, sw=1.0, extra='stroke-dasharray="8 6"')
    elif k == "armchair":
        x0, y0, x1, y1 = r
        b = f.get("back", "y0")
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4, extra='rx="6"')
        t = 0.16
        seat = {"y0": (x0 + t, y0 + t, x1 - t, y1), "y1": (x0 + t, y0, x1 - t, y1 - t),
                "x0": (x0 + t, y0 + t, x1, y1 - t), "x1": (x0, y0 + t, x1 - t, y1 - t)}[b]
        g.rect(seat, fill="#fff", stroke=FURN, sw=1.0)
    elif k == "table":
        x0, y0, x1, y1 = r
        n = f.get("seats", 0)
        long_x = (x1 - x0) >= (y1 - y0)
        if n:
            per = n // 2 - (1 if f.get("ends") else 0)
            for i in range(per):
                if long_x:
                    cx = x0 + (i + 0.5) * (x1 - x0) / per
                    _chair(g, cx, y0 - 0.2, "y1")
                    _chair(g, cx, y1 + 0.2, "y0")
                else:
                    cy = y0 + (i + 0.5) * (y1 - y0) / per
                    _chair(g, x0 - 0.2, cy, "x1")
                    _chair(g, x1 + 0.2, cy, "x0")
            if f.get("ends"):
                if long_x:
                    _chair(g, x0 - 0.2, (y0 + y1) / 2, "x1")
                    _chair(g, x1 + 0.2, (y0 + y1) / 2, "x0")
                else:
                    _chair(g, (x0 + x1) / 2, y0 - 0.2, "y1")
                    _chair(g, (x0 + x1) / 2, y1 + 0.2, "y0")
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4)
        if f.get("extend"):  # dashed extension for holidays
            g.rect(f["extend"], fill="none", stroke=FURN, sw=1.0, extra='stroke-dasharray="8 6"')
    elif k == "round":   # round table
        x, y, rr = r
        n = f.get("seats", 4)
        for i in range(n):
            a = 2 * math.pi * i / n
            cx, cy = x + (rr + 0.2) * math.cos(a), y + (rr + 0.2) * math.sin(a)
            g.circle(cx, cy, 0.2, fill="#fff", sw=1.1)
        g.circle(x, y, rr, fill="#fff", sw=1.4)
    elif k in ("counter", "island"):
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4)
        if k == "counter":    # the front edge of the worktop
            fr = f.get("front")
            if fr:
                d = 0.04
                seg = {"y1": (x0, y1 - d, x1, y1 - d), "y0": (x0, y0 + d, x1, y0 + d),
                       "x1": (x1 - d, y0, x1 - d, y1), "x0": (x0 + d, y0, x0 + d, y1)}[fr]
                g.line(*seg, sw=0.8)
        if f.get("sink"):
            sx, sy = f["sink"]
            vert = f.get("sinkdir", "x") == "y"
            if vert:
                for dy in (-0.21, 0.21):
                    g.rect((sx - 0.19, sy + dy - 0.18, sx + 0.19, sy + dy + 0.18), fill="#fff", stroke=FURN, sw=1.1,
                           extra='rx="4"')
            else:
                for dx in (-0.21, 0.21):
                    g.rect((sx + dx - 0.18, sy - 0.19, sx + dx + 0.18, sy + 0.19), fill="#fff", stroke=FURN, sw=1.1,
                           extra='rx="4"')
        if f.get("hob"):
            hx, hy = f["hob"]
            g.rect((hx - 0.3, hy - 0.26, hx + 0.3, hy + 0.26), fill="#fff", sw=1.0)
            for dx in (-0.14, 0.14):
                for dy in (-0.12, 0.12):
                    g.circle(hx + dx, hy + dy, 0.08 if (dx < 0) == (dy < 0) else 0.06, sw=1.0)
        if k == "island" and f.get("overhang"):   # the counter overhangs the seating side: knee space past the line
            side, d = f.get("stools", "y1"), f["overhang"]
            line = {"y1": (x0, y1 - d, x1, y1 - d), "y0": (x0, y0 + d, x1, y0 + d),
                    "x1": (x1 - d, y0, x1 - d, y1), "x0": (x0 + d, y0, x0 + d, y1)}[side]
            g.line(*line, sw=0.8, extra='stroke-dasharray="6 5"')
        if k == "island" and f.get("stools"):
            side = f.get("stools")
            n = f.get("n", 3)
            for i in range(n):
                if side in ("y0", "y1"):
                    cx = x0 + (i + 0.5) * (x1 - x0) / n
                    cy = y1 + 0.25 if side == "y1" else y0 - 0.25
                else:
                    cy = y0 + (i + 0.5) * (y1 - y0) / n
                    cx = x1 + 0.25 if side == "x1" else x0 - 0.25
                g.circle(cx, cy, 0.17, fill="#fff", sw=1.1)
    elif k == "tall":   # tall cabinets / pantry wall
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4)
        g.line(x0, y0, x1, y1, sw=0.8)
        g.line(x0, y1, x1, y0, sw=0.8)
        if f.get("label"):
            g.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.06, f["label"], size=0.15, color=MUTED,
                   rotate=-90 if (y1 - y0) > (x1 - x0) else None)
    elif k == "fridge":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4)
        g.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.05, "מקרר", size=0.13, color=MUTED)
    elif k == "wardrobe":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4)
        if (x1 - x0) >= (y1 - y0):      # hanging rail along x with hanger ticks
            ym = (y0 + y1) / 2
            g.line(x0 + 0.05, ym, x1 - 0.05, ym, sw=0.8)
            n = int((x1 - x0) / 0.12)
            for i in range(1, n):
                xx = x0 + i * (x1 - x0) / n
                g.line(xx, ym - 0.17, xx, ym + 0.17, sw=0.6)
        else:
            xm = (x0 + x1) / 2
            g.line(xm, y0 + 0.05, xm, y1 - 0.05, sw=0.8)
            n = int((y1 - y0) / 0.12)
            for i in range(1, n):
                yy = y0 + i * (y1 - y0) / n
                g.line(xm - 0.17, yy, xm + 0.17, yy, sw=0.6)
    elif k == "shelf":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.2)
        if (x1 - x0) >= (y1 - y0):
            g.line(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, sw=0.6, extra='stroke-dasharray="4 4"')
        else:
            g.line((x0 + x1) / 2, y0, (x0 + x1) / 2, y1, sw=0.6, extra='stroke-dasharray="4 4"')
    elif k == "wc":
        x, y = r[0], r[1]
        face = f.get("face", "y1")    # direction of the bowl from the cistern
        tank = {"y1": (x - 0.22, y - 0.09, x + 0.22, y + 0.09), "y0": (x - 0.22, y - 0.09, x + 0.22, y + 0.09),
                "x1": (x - 0.09, y - 0.22, x + 0.09, y + 0.22), "x0": (x - 0.09, y - 0.22, x + 0.09, y + 0.22)}[face]
        bowl = {"y1": (x, y + 0.36), "y0": (x, y - 0.36), "x1": (x + 0.36, y), "x0": (x - 0.36, y)}[face]
        rx, ry = (0.18, 0.25) if face in ("y0", "y1") else (0.25, 0.18)
        g.ellipse(bowl[0], bowl[1], rx, ry)
        g.rect(tank, fill="#fff", stroke=FURN, sw=1.3)
    elif k == "basin":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.3)
        n = f.get("n", 1)             # n=2: a double vanity, basins along the long side
        for i in range(n):
            if x1 - x0 >= y1 - y0:
                cx, cy, rx, ry = x0 + (i + 0.5) * (x1 - x0) / n, (y0 + y1) / 2, (x1 - x0) * 0.32 / n, (y1 - y0) * 0.3
            else:
                cx, cy, rx, ry = (x0 + x1) / 2, y0 + (i + 0.5) * (y1 - y0) / n, (x1 - x0) * 0.32, (y1 - y0) * 0.3 / n
            g.ellipse(cx, cy, rx, ry, fill="none", sw=1.0)
    elif k == "shower":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.3)
        g.line(x0, y0, x1, y1, sw=0.8)
        g.line(x0, y1, x1, y0, sw=0.8)
        g.circle((x0 + x1) / 2, (y0 + y1) / 2, 0.04, fill=FURN, sw=0)
    elif k == "bath":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.3)
        g.rect((x0 + 0.07, y0 + 0.07, x1 - 0.07, y1 - 0.07), fill="none", stroke=FURN, sw=1.0, extra='rx="16"')
    elif k == "washer":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.3)
        g.circle((x0 + x1) / 2, (y0 + y1) / 2, min(x1 - x0, y1 - y0) * 0.32, sw=1.0)
    elif k == "desk":
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4)
        if f.get("chair"):
            cx, cy = f["chair"]
            _chair(g, cx, cy, f.get("face", "y0"), w=0.46, d=0.44)
    elif k == "chair":
        _chair(g, r[0], r[1], f.get("face", "y0"))
    elif k == "stool":   # a single stool, like the ones drawn along an island
        g.circle(r[0], r[1], 0.17, fill="#fff", sw=1.1)
    elif k == "low":     # coffee table, TV unit, bench, sideboard
        g.rect(r, fill="#fff", stroke=FURN, sw=1.3)
    elif k == "tv":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.3)
        if (x1 - x0) >= (y1 - y0):
            g.line(x0 + 0.25, (y0 + y1) / 2, x1 - 0.25, (y0 + y1) / 2, sw=2.4)
        else:
            g.line((x0 + x1) / 2, y0 + 0.25, (x0 + x1) / 2, y1 - 0.25, sw=2.4)
    elif k == "skylight":  # roof window, seen from below: dashed outline with an X
        x0, y0, x1, y1 = r
        g.rect(r, fill="none", stroke=MUTED, sw=1.0, extra='stroke-dasharray="6 4"')
        g.line(x0, y0, x1, y1, stroke=MUTED, sw=0.7, extra='stroke-dasharray="6 4"')
        g.line(x0, y1, x1, y0, stroke=MUTED, sw=0.7, extra='stroke-dasharray="6 4"')
    elif k == "wallbed":   # fold-down bed in a cabinet; dashed: the bed when open
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=FURN, sw=1.4)
        g.line(x0, y0, x1, y1, sw=0.7)
        if f.get("open"):
            g.rect(f["open"], fill="none", stroke=FURN, sw=1.0, extra='stroke-dasharray="8 6"')
    elif k == "rug":
        g.rect(r, fill="none", stroke=MUTED, sw=0.9, extra='stroke-dasharray="3 5"')
    elif k == "stairs":  # reserved stair (future): dashed treads
        x0, y0, x1, y1 = r
        g.rect(r, fill="none", stroke=MUTED, sw=1.6, extra='stroke-dasharray="10 7"')
        n = f.get("treads", 12)
        if f.get("along", "y") == "y":
            for i in range(1, n):
                yy = y0 + i * (y1 - y0) / n
                g.line(x0, yy, x1, yy, stroke=MUTED, sw=0.9, extra='stroke-dasharray="6 6"')
        else:
            for i in range(1, n):
                xx = x0 + i * (x1 - x0) / n
                g.line(xx, y0, xx, y1, stroke=MUTED, sw=0.9, extra='stroke-dasharray="6 6"')
    elif k == "plant":
        x, y, rr = r
        g.circle(x, y, rr, fill="#fff", sw=1.0)
        for a in range(0, 360, 45):
            ar = math.radians(a)
            g.line(x, y, x + rr * 0.8 * math.cos(ar), y + rr * 0.8 * math.sin(ar), sw=0.7)


# ---- garden -------------------------------------------------------------------------------------

def _dashed(g, x0, y0, x1, y1, stroke, sw, on=0.1, off=0.06):
    """A dashed line drawn as short segments, so the PNGs show it too (PyMuPDF ignores stroke-dasharray)."""
    n = math.hypot(x1 - x0, y1 - y0)
    if n < EPS:
        return
    ux, uy = (x1 - x0) / n, (y1 - y0) / n
    t = 0.0
    while t < n - EPS:
        t1 = min(t + on, n)
        g.line(x0 + ux * t, y0 + uy * t, x0 + ux * t1, y0 + uy * t1, stroke=stroke, sw=sw)
        t = t1 + off


def _garden(g, it):
    k, r = it["k"], it["r"]
    if k == "lawn":
        g.rect(r, fill="#eef5e6")
    elif k == "deck":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#f6f1e6", stroke="#8c7f66", sw=1.4)
        step = 0.25
        n = int((y1 - y0) / step)
        for i in range(1, n + 1):
            yy = y0 + i * step
            if yy < y1 - 0.02:
                g.line(x0, yy, x1, yy, stroke="#cdbf9f", sw=0.8)
    elif k == "pergola":
        x0, y0, x1, y1 = r
        g.rect(r, fill="none", stroke="#5b5242", sw=1.8, extra='stroke-dasharray="16 6 3 6"')
        n = max(2, int(round((x1 - x0) / 0.55)))
        for i in range(1, n):
            xx = x0 + i * (x1 - x0) / n
            g.line(xx, y0, xx, y1, stroke="#9a8d73", sw=0.9)
    elif k == "canopy":     # solid entrance canopy / white beam
        g.rect(r, fill="none", stroke="#5b5242", sw=1.8, extra='stroke-dasharray="16 6 3 6"')
    elif k == "column":     # a concrete column, cut like the walls
        g.rect(r, fill=WALL, stroke=INK, sw=1.0)
    elif k == "beam":       # a concrete beam overhead: dashed, like everything above the cut
        x0, y0, x1, y1 = r
        for a in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
            _dashed(g, *a, stroke="#5b5242", sw=1.4)
    elif k == "beds":       # vegetable beds
        x0, y0, x1, y1 = r
        g.rect(r, fill="#f3ead8", stroke="#9b8a66", sw=1.3)
        for i in range(1, 4):
            g.line(x0, y0 + i * (y1 - y0) / 4, x1, y0 + i * (y1 - y0) / 4, stroke="#c2b08a", sw=0.8, extra='stroke-dasharray="5 5"')
    elif k == "paving":
        g.rect(r, fill="#f0eee9", stroke="#b9b5aa", sw=1.0)
    elif k == "service":
        g.rect(r, fill="#f1f0eb", stroke="#8f8b80", sw=1.3, extra='stroke-dasharray="8 5"')
    elif k == "tree":
        x, y, rr = r
        g.circle(x, y, rr, fill="#e3eedb", stroke="#7d9a6b", sw=1.3, extra='fill-opacity="0.9"')
        g.circle(x, y, rr * 0.55, fill="none", stroke="#a7bd98", sw=0.8, extra='stroke-dasharray="4 4"')
        g.circle(x, y, 0.06, fill="#7d9a6b", stroke="none", sw=0)
    elif k == "hedge":
        g.rect(r, fill="#dfeccf", stroke="#86a473", sw=1.1, extra='rx="16"')
    elif k == "steps":
        x0, y0, x1, y1 = r
        g.rect(r, fill="#fff", stroke=INK, sw=1.3)
        along = it.get("along", "y")
        n = it.get("n", 4)
        for i in range(1, n):
            if along == "y":
                yy = y0 + i * (y1 - y0) / n
                g.line(x0, yy, x1, yy, stroke=INK, sw=1.0)
            else:
                xx = x0 + i * (x1 - x0) / n
                g.line(xx, y0, xx, y1, stroke=INK, sw=1.0)
        if it.get("up"):         # arrow toward the top of the steps
            ux, uy = {"+y": (0, 1), "-y": (0, -1), "+x": (1, 0), "-x": (-1, 0)}[it["up"]]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            ln = 0.42
            g.line(cx - ux * ln, cy - uy * ln, cx + ux * ln, cy + uy * ln, stroke=INK, sw=1.2)
            g.path(f"M {c(cx + ux * ln)} {c(cy + uy * ln)} l {c(-ux * 0.12 - uy * 0.08)} {c(-uy * 0.12 - ux * 0.08)} "
                   f"M {c(cx + ux * ln)} {c(cy + uy * ln)} l {c(-ux * 0.12 + uy * 0.08)} {c(-uy * 0.12 + ux * 0.08)}",
                   stroke=INK, sw=1.2)
    elif k == "stair":      # a stair: its outline, the risers, the rail on its open side, and the walking line
        pts = " L ".join(f"{c(x)} {c(y)}" for x, y in it["poly"])
        g.path(f"M {pts} Z", fill="#fff", stroke=INK, sw=1.3)
        for a in it["lines"]:
            g.line(*a, stroke=INK, sw=1.0)
        for rl in ([it["rail"]] if it.get("rail") else []) + it.get("rails", []):   # rails: several polylines
            g.path("M " + " L ".join(f"{c(x)} {c(y)}" for x, y in rl), stroke=INK, sw=2.0)
        w = it["walk"]           # from a dot on the first step to an arrow at the top
        g.path("M " + " L ".join(f"{c(x)} {c(y)}" for x, y in w), stroke=INK, sw=1.0)
        g.circle(*w[0], 0.05, fill=INK, stroke="none", sw=0)
        (ax, ay), (bx, by) = w[-2], w[-1]
        ln = math.hypot(bx - ax, by - ay) or 1.0
        ux, uy = (bx - ax) / ln, (by - ay) / ln
        g.path(f"M {c(bx)} {c(by)} l {c(-ux * 0.14 - uy * 0.08)} {c(-uy * 0.14 + ux * 0.08)} "
               f"M {c(bx)} {c(by)} l {c(-ux * 0.14 + uy * 0.08)} {c(-uy * 0.14 - ux * 0.08)}", stroke=INK, sw=1.0)
    elif k == "outkitchen":
        g.rect(r, fill="#fff", stroke=INK, sw=1.3)
    elif k == "wall":       # low garden wall / retaining wall
        g.rect(r, fill="#cfccc4", stroke="#77746b", sw=1.0)
    if it.get("label"):
        if len(r) == 4:
            lx, ly = it.get("at") or ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2 + 0.07)
        else:
            lx, ly = it.get("at") or (r[0], r[1] + r[2] + 0.3)
        g.text(lx, ly, it["label"], size=it.get("size", 0.2), color="#57554e")


# ---- openings -----------------------------------------------------------------------------------

def _opening(g, o):
    x0, y0, x1, y1 = o["r"]
    horiz = (x1 - x0) >= (y1 - y0)       # opening in a horizontal wall
    t = o["t"]
    e = 0.025                            # cover the wall-face strokes on both sides
    cut = (x0, y0 - e, x1, y1 + e) if horiz else (x0 - e, y0, x1 + e, y1)
    g.rect(cut, fill="#ffffff")
    jamb = 1.6
    if horiz:
        g.line(x0, y0, x0, y1, stroke=INK, sw=jamb)
        g.line(x1, y0, x1, y1, stroke=INK, sw=jamb)
    else:
        g.line(x0, y0, x1, y0, stroke=INK, sw=jamb)
        g.line(x0, y1, x1, y1, stroke=INK, sw=jamb)
    if t in ("window", "high"):
        if horiz:
            g.line(x0, y0, x1, y0, stroke=INK, sw=1.0)
            g.line(x0, y1, x1, y1, stroke=INK, sw=1.0)
            ym = (y0 + y1) / 2
            g.line(x0, ym - 0.025, x1, ym - 0.025, stroke=GLASS, sw=1.0)
            g.line(x0, ym + 0.025, x1, ym + 0.025, stroke=GLASS, sw=1.0)
        else:
            g.line(x0, y0, x0, y1, stroke=INK, sw=1.0)
            g.line(x1, y0, x1, y1, stroke=INK, sw=1.0)
            xm = (x0 + x1) / 2
            g.line(xm - 0.025, y0, xm - 0.025, y1, stroke=GLASS, sw=1.0)
            g.line(xm + 0.025, y0, xm + 0.025, y1, stroke=GLASS, sw=1.0)
        if t == "high":   # high sill: dashed outline on the room side
            if horiz:
                g.line(x0, y1 + 0.06, x1, y1 + 0.06, stroke=MUTED, sw=0.8, extra='stroke-dasharray="5 4"')
            else:
                g.line(x1 + 0.06, y0, x1 + 0.06, y1, stroke=MUTED, sw=0.8, extra='stroke-dasharray="5 4"')
        return
    if t == "glass":      # sliding glass door: two overlapping panels
        if horiz:
            ym = (y0 + y1) / 2
            mid = (x0 + x1) / 2
            g.line(x0, ym - 0.035, mid + 0.06, ym - 0.035, stroke=INK, sw=3.2)
            g.line(mid - 0.06, ym + 0.035, x1, ym + 0.035, stroke=INK, sw=3.2)
        else:
            xm = (x0 + x1) / 2
            mid = (y0 + y1) / 2
            g.line(xm - 0.035, y0, xm - 0.035, mid + 0.06, stroke=INK, sw=3.2)
            g.line(xm + 0.035, mid - 0.06, xm + 0.035, y1, stroke=INK, sw=3.2)
        return
    if t == "gap":
        return
    if t == "slide":
        if horiz:
            ym = (y0 + y1) / 2
            g.rect((x0, ym - 0.025, x1, ym + 0.025), fill="#fff", stroke=INK, sw=1.2)
            g.line(x0 - (x1 - x0) * 0.0, ym, x1, ym, stroke=INK, sw=0.6)
        else:
            xm = (x0 + x1) / 2
            g.rect((xm - 0.025, y0, xm + 0.025, y1), fill="#fff", stroke=INK, sw=1.2)
        return
    # hinged door: leaf drawn open at 90°, with the swing arc
    heavy = t == "steel"
    sw = 4.0 if heavy else 1.8
    if horiz:
        w = x1 - x0
        hx, ox = (x0, x1) if o["hinge"] == "x0" else (x1, x0)
        face = y1 if o["into"] > 0 else y0
        ey = face + o["into"] * w
        g.line(hx, face, hx, ey, stroke=INK, sw=sw)
        sweep = 1 if (o["into"] > 0) == (o["hinge"] == "x1") else 0
        g.path(f"M {c(hx)} {c(ey)} A {c(w)} {c(w)} 0 0 {sweep} {c(ox)} {c(face)}", stroke=INK, sw=0.9)
    else:
        w = y1 - y0
        hy, oy = (y0, y1) if o["hinge"] == "y0" else (y1, y0)
        face = x1 if o["into"] > 0 else x0
        ex = face + o["into"] * w
        g.line(face, hy, ex, hy, stroke=INK, sw=sw)
        sweep = 0 if (o["into"] > 0) == (o["hinge"] == "y1") else 1
        g.path(f"M {c(ex)} {c(hy)} A {c(w)} {c(w)} 0 0 {sweep} {c(face)} {c(oy)}", stroke=INK, sw=0.9)


# ---- dimensions ---------------------------------------------------------------------------------

def _dim(g, d, size=0.2):
    x0, y0, x1, y1 = d["p"]
    off = d["off"]
    col = "#55534d"
    if abs(y0 - y1) < EPS:   # horizontal dimension
        y = y0 + off
        g.line(x0, y, x1, y, stroke=col, sw=0.9)
        for x in (x0, x1):
            g.line(x, y - 0.1, x, y + 0.1, stroke=col, sw=0.8)
            g.line(x - 0.06, y + 0.06, x + 0.06, y - 0.06, stroke=col, sw=1.6)
        txt = d["text"] or f"{x1 - x0:.2f}"
        g.text((x0 + x1) / 2, y - 0.07, txt, size=size, color=col)
    else:                     # vertical dimension
        x = x0 + off
        g.line(x, y0, x, y1, stroke=col, sw=0.9)
        for y in (y0, y1):
            g.line(x - 0.1, y, x + 0.1, y, stroke=col, sw=0.8)
            g.line(x - 0.06, y + 0.06, x + 0.06, y - 0.06, stroke=col, sw=1.6)
        txt = d["text"] or f"{y1 - y0:.2f}"
        g.text(x - 0.07, (y0 + y1) / 2, txt, size=size, color=col, rotate=-90)


# ---- site context -------------------------------------------------------------------------------

def _north(g, x, y, size=0.9):
    a = math.radians(-S.AZ_UP)            # north is AZ_UP degrees left of up
    dx, dy = math.sin(a), -math.cos(a)
    px, py = -dy, dx
    tip = (x + dx * size, y + dy * size)
    l = (x - dx * size * 0.45 + px * size * 0.35, y - dy * size * 0.45 + py * size * 0.35)
    r = (x - dx * size * 0.45 - px * size * 0.35, y - dy * size * 0.45 - py * size * 0.35)
    m = (x - dx * size * 0.15, y - dy * size * 0.15)
    g.circle(x, y, size * 0.75, fill="none", stroke=INK, sw=1.0)
    g.path(f"M {c(tip[0])} {c(tip[1])} L {c(l[0])} {c(l[1])} L {c(m[0])} {c(m[1])} Z", fill=INK, stroke=INK, sw=1)
    g.path(f"M {c(tip[0])} {c(tip[1])} L {c(r[0])} {c(r[1])} L {c(m[0])} {c(m[1])} Z", fill="#fff", stroke=INK, sw=1.2)
    g.text(x + dx * (size + 0.28), y + dy * (size + 0.28) + 0.09, "N", size=0.28, bold=True)


def _sun(g, x, y):
    """Sun directions: winter (orange) and summer (red) sunrise/sunset, winter noon."""
    def at(az, ln):
        a = math.radians(az - S.AZ_UP)     # angle from "up", clockwise
        return x + math.sin(a) * ln, y - math.cos(a) * ln
    for az, lab, col in ((118, "זריחה בחורף", "#c27a1c"), (180, "צהרי חורף", "#c27a1c"),
                         (242, "שקיעה בחורף", "#c27a1c"), (62, "זריחה בקיץ", "#b8403b"),
                         (298, "שקיעה בקיץ", "#b8403b")):
        ex, ey = at(az, 1.1)
        g.line(x, y, ex, ey, stroke=col, sw=2.0)
        g.circle(ex, ey, 0.08, fill=col, stroke="none", sw=0)
        tx, ty = at(az, 1.5)
        g.text(tx, ty + 0.06, lab, size=0.17, color=col)
    g.circle(x, y, 0.05, fill=INK, stroke="none", sw=0)


def _site(g, mirror, p):
    W, Dp = S.W, S.D
    mx = (lambda r: _mr(r, W)) if mirror else (lambda r: r)
    g.rect((-3.0, -4.6, W + 3.0, 0.0), fill="#f1f0ec")
    g.rect((-3.0, -4.6, W + 3.0, -1.6), fill="#e2e0da")
    g.text(W / 2, -2.85, "הרחוב (ללא מוצא)", size=0.34, color="#6d6a62")
    g.text(W / 2, -0.62, "מדרכה", size=0.2, color="#8a877f")
    g.rect((-3.0, Dp, W + 3.0, Dp + 4.2), fill="#eaf2e3")
    g.text(W / 2, Dp + 1.55, "רצועה ירוקה, כ-12 מ' (עצים, שביל, ספסלים)", size=0.3, color="#55704a")
    g.text(W / 2, Dp + 2.15, "ומעבר לה בתים, גבוהים בכ-1 מ'", size=0.22, color="#55704a")
    g.rect(mx((-3.0, 0.0, 0.0, Dp)), fill="#f4f3ef")
    g.rect(mx((W, 0.0, W + 3.0, Dp)), fill="#f7f7f4")
    lx_partner = -1.5 if not mirror else W + 1.5
    lx_neigh = W + 1.5 if not mirror else -1.5
    g.text(lx_partner, Dp / 2 - 0.45, "השותפים", size=0.3, color="#7f7c74", bold=True)
    g.text(lx_partner, Dp / 2 + 0.05, "הבית השני בזוג", size=0.22, color="#7f7c74")
    g.text(lx_partner, Dp / 2 + 0.4, "קיר משותף", size=0.2, color="#7f7c74")
    g.text(lx_neigh, Dp / 2 - 0.45, "השכנים", size=0.3, color="#98958d", bold=True)
    g.text(lx_neigh, Dp / 2 + 0.05, "כ-6 מ' בין הבתים", size=0.2, color="#98958d")
    g.rect((0, 0, W, Dp), fill="#fcfcfa")
    for it in p.garden:
        if it["k"] == "lawn":
            _garden(g, it)
    g.rect(mx(S.ENVELOPE), fill="none", stroke="#c94a4a", sw=1.6, extra='stroke-dasharray="22 8 4 8"')
    for st in S.STALLS:
        g.rect(mx(st), fill="#f2f1ee", stroke="#77746b", sw=1.3)
    pr = mx(S.PARKING)
    g.text((pr[0] + pr[2]) / 2, 2.55, "חניה", size=0.26, color="#55534d")
    g.text((pr[0] + pr[2]) / 2, 2.9, "(מיקום מחייב)", size=0.19, color="#77746b")
    g.rect((0, 0, W, Dp), fill="none", stroke="#2f5d9b", sw=2.6, extra='stroke-dasharray="30 8"')
    sb = 0 if not mirror else W
    g.line(sb, -0.3, sb, Dp + 0.3, stroke="#2f5d9b", sw=5)


def render(p, view="plan", mirror=False, bidi=False, show_upper=False, title=None):
    """view: 'plan' (house only, detailed), 'site' (the whole plot with the garden), 'roof',
    'routes' (the plan with the checklist walks drawn on it)."""
    if mirror:
        p = mirrored(p)
    q = p.upper if show_upper and p.upper else p
    g = Svg(bidi)
    if view == "site":
        vb = (-3.0, -4.6, S.W + 6.0, S.D + 4.2 + 4.6)
    else:
        x0, y0, x1, y1 = p.bbox()
        if view in ("plan", "routes"):   # the plot edge, the parking and the near garden items
            for it in p.garden:
                if it.get("near") and len(it["r"]) == 4:
                    x0, y0 = min(x0, it["r"][0]), min(y0, it["r"][1])
                    x1, y1 = max(x1, it["r"][2]), max(y1, it["r"][3])
            y0 = min(y0, 0.0)
        vb = (x0 - 1.3, y0 - 1.5, x1 - x0 + 2.6 + 0.6, y1 - y0 + 3.0)
    g.add(f'<rect x="{c(vb[0])}" y="{c(vb[1])}" width="{c(vb[2])}" height="{c(vb[3])}" fill="{PAPER}"/>')
    if view in ("plan", "routes"):
        _plan_context(g, mirror, vb)
    if view == "site":
        _site(g, mirror, p)
    if view in ("site", "plan", "routes"):
        for it in p.garden:
            if it["k"] != "lawn" and (view == "site" or it.get("near")):
                _garden(g, it)
    if view == "roof":
        _roof(g, q)
    else:
        _house(g, q, small=(view == "site"))
        if show_upper and q is not p:
            for b in p.blocks:
                g.rect(b, fill="none", stroke=MUTED, sw=1.6, extra='stroke-dasharray="10 8"')
        if q.entry and not show_upper:
            _entry_arrow(g, *q.entry)
        if view == "routes":
            _routes(g, q)
    if view == "site":
        _north(g, S.W + 1.6, -3.3)
        _sun(g, S.W + 1.6 if not mirror else -1.6, S.D + 1.5)
        _scale(g, 0.0, S.D + 3.5)
    else:
        if view == "plan":
            for d in q.dims:
                _dim(g, d)
        _north(g, vb[0] + vb[2] - 0.9, vb[1] + 0.95, size=0.5)
        _scale(g, vb[0] + 0.5, vb[1] + vb[3] - 0.6, n=5)
        if title:
            g.text(vb[0] + vb[2] / 2, vb[1] + vb[3] - 0.35, title, size=0.3, bold=True)
    vbs = " ".join(str(c(v)) for v in vb)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vbs}" width="{c(vb[2]) * 0.4:.0f}" '
            f'height="{c(vb[3]) * 0.4:.0f}">' + "".join(g.parts) + "</svg>")


def _plan_context(g, mirror, vb):
    """Around the house in the plan view: the plot boundaries, the building line, the parking."""
    W = S.W
    mx = (lambda r: _mr(r, W)) if mirror else (lambda r: r)
    for st in S.STALLS:
        g.rect(mx(st), fill="#f6f6f3", stroke="#8b887f", sw=1.1)
    pr = mx(S.PARKING)
    g.text((pr[0] + pr[2]) / 2, 2.3, "חניה", size=0.24, color="#6c6a62")
    g.text((pr[0] + pr[2]) / 2, 2.62, "בגובה הרחוב", size=0.17, color="#8b887f")
    g.rect(mx(S.PATH), fill="#f0eee9", stroke="#b9b5aa", sw=1.0)
    g.line(vb[0], 0, vb[0] + vb[2], 0, stroke="#2f5d9b", sw=1.6, extra='stroke-dasharray="30 8"')
    sb = 0 if not mirror else W
    g.line(sb, vb[1], sb, vb[1] + vb[3], stroke="#2f5d9b", sw=3.2)
    g.text(sb + (-0.15 if not mirror else 0.15), vb[1] + 2.2, "גבול משותף", size=0.17, color="#2f5d9b",
           anchor="end" if not mirror else "start")
    fs = W if not mirror else 0
    if vb[0] <= fs <= vb[0] + vb[2]:
        g.line(fs, vb[1], fs, vb[1] + vb[3], stroke="#2f5d9b", sw=1.6, extra='stroke-dasharray="30 8"')
    g.text(vb[0] + vb[2] / 2, -0.5, "גבול המגרש · מדרכה ורחוב", size=0.17, color="#2f5d9b")


def _entry_arrow(g, x, y, d):
    """The usual 'כניסה' triangle outside the main door, pointing in."""
    ux, uy = {"+y": (0, 1), "-y": (0, -1), "+x": (1, 0), "-x": (-1, 0)}[d]
    px, py = -uy, ux
    tip = (x, y)
    b1 = (x - ux * 0.32 + px * 0.2, y - uy * 0.32 + py * 0.2)
    b2 = (x - ux * 0.32 - px * 0.2, y - uy * 0.32 - py * 0.2)
    g.path(f"M {c(tip[0])} {c(tip[1])} L {c(b1[0])} {c(b1[1])} L {c(b2[0])} {c(b2[1])} Z", fill=INK, stroke=INK, sw=1)
    g.text(x - ux * 0.55, y - uy * 0.55 + 0.08, "כניסה", size=0.2, bold=True)


ROUTE_COLORS = {"alarm": "#c0392b", "groceries": "#2f6db5", "guest": "#2e8b57", "laundry": "#8e44ad"}


def _routes(g, p):
    """Each walk as a dashed colored line from a dot to an arrow, with its length in meters."""
    for rt in p.routes:
        col = ROUTE_COLORS.get(rt["kind"], INK)
        pts = rt["pts"]
        d = "M " + " L ".join(f"{c(x)} {c(y)}" for x, y in pts)
        g.path(d, fill="none", stroke="#ffffff", sw=9, extra='stroke-linejoin="round" stroke-linecap="round" opacity="0.8"')
        g.path(d, fill="none", stroke=col, sw=5, extra='stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="22 11"')
        g.circle(*pts[0], 0.09, fill=col, stroke="#ffffff", sw=1.5)
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        ln = math.hypot(bx - ax, by - ay) or 1.0
        ux, uy = (bx - ax) / ln, (by - ay) / ln
        b1 = (bx - ux * 0.3 - uy * 0.15, by - uy * 0.3 + ux * 0.15)
        b2 = (bx - ux * 0.3 + uy * 0.15, by - uy * 0.3 - ux * 0.15)
        g.path(f"M {c(bx)} {c(by)} L {c(b1[0])} {c(b1[1])} L {c(b2[0])} {c(b2[1])} Z", fill=col, stroke=col, sw=1)
        txt = f"{Plan.route_length(rt):.1f} מ'"
        lx, ly = rt.get("at") or (pts[0][0], pts[0][1] - 0.22)
        w = 0.105 * len(txt) + 0.12
        g.rect((lx - w / 2, ly - 0.2, lx + w / 2, ly + 0.07), fill="#ffffff", stroke=col, sw=1.2, extra='rx="5"')
        g.text(lx, ly, txt, size=0.18, color=col, bold=True)


def _scale(g, x, y, n=5):
    for i in range(n):
        g.rect((x + i, y, x + i + 1, y + 0.1), fill=INK if i % 2 == 0 else "#fff", stroke=INK, sw=1.0)
    g.text(x, y + 0.36, "0", size=0.17, color=MUTED)
    g.text(x + n, y + 0.36, f"{n} מ'", size=0.17, color=MUTED)


def _mamad_walls(r, t_ext, t_int, blocks):
    """The concrete band around the mamad: thicker toward the outside."""
    x0 = min(x[0] for x in r["rects"]); y0 = min(x[1] for x in r["rects"])
    x1 = max(x[2] for x in r["rects"]); y1 = max(x[3] for x in r["rects"])
    bx0 = min(b[0] for b in blocks); by0 = min(b[1] for b in blocks)
    bx1 = max(b[2] for b in blocks); by1 = max(b[3] for b in blocks)
    def t(side_coord, outer):
        return t_ext if abs(side_coord - outer) < 0.45 else t_int
    tw, te = t(x0, bx0), t(x1, bx1)
    tn, ts = t(y0, by0), t(y1, by1)
    return [(x0 - tw, y0 - tn, x1 + te, y0), (x0 - tw, y1, x1 + te, y1 + ts),
            (x0 - tw, y0, x0, y1), (x1, y0, x1 + te, y1)]


def _house(g, p, small=False):
    for b in p.blocks:
        g.rect(b, fill=WALL)
    for r in p.rooms:
        if r["kind"] == "mamad":     # concrete walls: hatched band around the room
            for band in _mamad_walls(r, 0.30, 0.25, p.blocks):
                g.rect(band, fill="#d9d8d3")
                g.hatch(band)
    for r in p.rooms:
        for x in r["rects"]:
            g.rect(x, fill="#ffffff")
    # wall faces: outline every room, then remove the shared edges of rects in the same room
    for r in p.rooms:
        _room_outline(g, r)
    for x0, y0, x1, y1 in _outline(p.blocks):
        g.line(x0, y0, x1, y1, stroke=INK, sw=2.2, extra='stroke-linecap="square"')
    for z in p.zones:
        g.rect(z, fill="none", stroke=MUTED, sw=0.9, extra='stroke-dasharray="9 6"')
    for f in p.furniture:
        _furniture(g, f)
    for o in p.openings:
        _opening(g, o)
    for r in p.rooms:
        if not r["name"]:
            continue
        rr = max(r["rects"], key=area)
        lx, ly = r["at"] or ((rr[0] + rr[2]) / 2, (rr[1] + rr[3]) / 2)
        sz = 0.19 if small else (0.19 if r["small"] else 0.25)
        for i, line in enumerate(r["name"].split("\n")):
            g.text(lx, ly + i * sz * 1.15, line, size=sz, bold=not small)
        nl = r["name"].count("\n")
        if r["area_label"] and not small:
            g.text(lx, ly + (nl + 1) * sz * 1.15, f"{Plan.room_area(r):.1f} מ\"ר", size=sz * 0.8, color="#55534d")
            if p.room_dims and r.get("dims", True) and len(r["rects"]) == 1 and r["kind"] not in ("circ", "public"):
                w, d = rr[2] - rr[0], rr[3] - rr[1]
                g.text(lx, ly + (nl + 1.95) * sz * 1.15, f"{w:.2f} × {d:.2f}", size=sz * 0.68, color=MUTED)
    for m in p.marks:
        if not m.get("roof"):
            g.text(m["x"], m["y"], m["text"], size=m["size"], color=m["color"], anchor=m["anchor"], bold=m["bold"])


def _outline(blocks):
    """The outer edges of the union of the blocks, so a house made of several blocks has no seams inside it."""
    def inside(x, y):
        return any(b[0] < x < b[2] and b[1] < y < b[3] for b in blocks)
    xs = sorted({v for b in blocks for v in (b[0], b[2])})
    ys = sorted({v for b in blocks for v in (b[1], b[3])})
    e = 1e-4
    segs = []
    for b in blocks:
        for k in (b[1], b[3]):                       # horizontal edges, split at every block corner
            cuts = [b[0]] + [x for x in xs if b[0] < x < b[2]] + [b[2]]
            segs += [(a, k, c, k) for a, c in zip(cuts, cuts[1:])
                     if inside((a + c) / 2, k - e) != inside((a + c) / 2, k + e)]
        for k in (b[0], b[2]):                       # vertical edges
            cuts = [b[1]] + [y for y in ys if b[1] < y < b[3]] + [b[3]]
            segs += [(k, a, k, c) for a, c in zip(cuts, cuts[1:])
                     if inside(k - e, (a + c) / 2) != inside(k + e, (a + c) / 2)]
    return sorted(set(segs))


def _room_outline(g, r):
    """Outline a room made of several rects without drawing the seams between them."""
    rects = r["rects"]
    segs = []
    for x0, y0, x1, y1 in rects:
        segs += [("h", y0, x0, x1), ("h", y1, x0, x1), ("v", x0, y0, y1), ("v", x1, y0, y1)]
    out = []
    for kind, k, a, b in segs:
        pieces = [(a, b)]
        for x0, y0, x1, y1 in rects:      # remove parts that lie inside another rect of the room
            if kind == "h":
                inside = y0 - EPS < k < y1 + EPS and not (abs(k - y0) < EPS and abs(k - y1) < EPS)
                lo, hi = x0, x1
                touching = (abs(k - y0) < EPS or abs(k - y1) < EPS)
            else:
                inside = x0 - EPS < k < x1 + EPS
                lo, hi = y0, y1
                touching = (abs(k - x0) < EPS or abs(k - x1) < EPS)
            if not inside or not touching:
                continue
            # the segment lies on this rect's edge: keep it only where this rect is on one side only
            new = []
            for pa, pb in pieces:
                if pb <= lo + EPS or pa >= hi - EPS:
                    new.append((pa, pb))
                    continue
                if pa < lo:
                    new.append((pa, lo))
                if pb > hi:
                    new.append((hi, pb))
            pieces = new
        out += [(kind, k, pa, pb) for pa, pb in pieces]
    # an edge shared by two rects of the same room appears twice; the loop above removed it from both,
    # while the room's own outer edges survive because their only "touching" rect is their own.
    for kind, k, a, b in out:
        if b - a < EPS:
            continue
        if kind == "h":
            g.line(a, k, b, k, stroke=INK, sw=1.6)
        else:
            g.line(k, a, k, b, stroke=INK, sw=1.6)


def _inset_outline(rects, d):
    """The edges of the union of the rects, moved d into it, so that they meet at the corners (a railing)."""
    def inside(x, y):
        return any(r[0] < x < r[2] and r[1] < y < r[3] for r in rects)
    e = 1e-3
    out = []
    for x0, y0, x1, y1 in _outline(rects):
        ux, uy = (1.0, 0.0) if abs(y0 - y1) < EPS else (0.0, 1.0)
        nx, ny = -uy, ux                     # the normal that points into the union
        if not inside((x0 + x1) / 2 + nx * e, (y0 + y1) / 2 + ny * e):
            nx, ny = -nx, -ny

        def end(px, py, sx, sy):             # (sx, sy): from this end into the edge
            if not inside(px - sx * e + nx * e, py - sy * e + ny * e):
                return px + sx * d, py + sy * d          # an outer corner: stop short
            if inside(px - sx * e - nx * e, py - sy * e - ny * e):
                return px - sx * d, py - sy * d          # an inner corner: reach into it
            return px, py                                # the edge goes on straight
        ax, ay = end(x0, y0, ux, uy)
        bx, by = end(x1, y1, -ux, -uy)
        out.append((ax + nx * d, ay + ny * d, bx + nx * d, by + ny * d))
    return out


def _cut(seg, gaps):
    """An axis-parallel segment without the parts inside the gap rects."""
    pieces = [seg]
    for gx0, gy0, gx1, gy1 in gaps:
        new = []
        for x0, y0, x1, y1 in pieces:
            horiz = abs(y0 - y1) < EPS
            if horiz and gy0 <= y0 <= gy1:
                lo, hi = max(x0, gx0), min(x1, gx1)
            elif not horiz and gx0 <= x0 <= gx1:
                lo, hi = max(y0, gy0), min(y1, gy1)
            else:
                lo = hi = None
            if lo is None or hi <= lo:
                new.append((x0, y0, x1, y1))
                continue
            a, b = (x0, x1) if horiz else (y0, y1)
            for s, t in ((a, lo), (hi, b)):
                if t - s > EPS:
                    new.append((s, y0, t, y1) if horiz else (x0, s, x1, t))
        pieces = new
    return pieces


def _roof(g, p):
    for b in p.blocks:
        g.rect(b, fill="#fafaf8")
    for it in p.garden:                      # seen from above, inside a patio: its floor, its tree, its stair
        if it.get("roof"):
            _garden(g, dict(it, label=None))
    edge = _outline(p.blocks)
    for x0, y0, x1, y1 in edge:
        g.line(x0, y0, x1, y1, stroke=INK, sw=2, extra='stroke-linecap="square"')
    for x in p.roof:
        x0, y0, x1, y1 = x["r"]
        if x["k"] == "terrace":              # a flat roof to walk on: paving in 50 cm tiles
            g.rect(x["r"], fill="#f5f1e8")
            for i in range(math.floor(x0 / 0.5) + 1, math.ceil(x1 / 0.5)):
                g.line(i * 0.5, y0, i * 0.5, y1, stroke="#e2dac9", sw=0.6)
            for i in range(math.floor(y0 / 0.5) + 1, math.ceil(y1 / 0.5)):
                g.line(x0, i * 0.5, x1, i * 0.5, stroke="#e2dac9", sw=0.6)
            continue
        if x["k"] == "tile":
            g.rect(x["r"], fill="#f3dccf", stroke="#8a4e33", sw=1.6)
            vertical = x["slope"] in ("+y", "-y", "gable-y")
            n = int(((x1 - x0) if vertical else (y1 - y0)) / 0.3)
            for i in range(1, max(n, 1)):
                if vertical:
                    xx = x0 + i * (x1 - x0) / n
                    g.line(xx, y0, xx, y1, stroke="#cf9f86", sw=0.7)
                else:
                    yy = y0 + i * (y1 - y0) / n
                    g.line(x0, yy, x1, yy, stroke="#cf9f86", sw=0.7)
            if x["slope"] == "gable-y":      # ridge along y
                g.line((x0 + x1) / 2, y0, (x0 + x1) / 2, y1, stroke="#8a4e33", sw=2.2)
            elif x["slope"] == "gable-x":
                g.line(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, stroke="#8a4e33", sw=2.2)
        else:
            g.rect(x["r"], fill="#eceeef", stroke="#6f7a82", sw=1.6)
        sl = x["slope"]
        arrows = []
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if sl in ("+y", "-y", "+x", "-x"):
            arrows = [(cx, cy, sl)]
        elif sl == "gable-y":
            arrows = [((x0 + cx) / 2, cy, "-x"), ((x1 + cx) / 2, cy, "+x")]
        elif sl == "gable-x":
            arrows = [(cx, (y0 + cy) / 2, "-y"), (cx, (y1 + cy) / 2, "+y")]
        for ax, ay, d in arrows:
            dx, dy = {"+y": (0, 1), "-y": (0, -1), "+x": (1, 0), "-x": (-1, 0)}[d]
            g.line(ax - dx * 0.6, ay - dy * 0.6, ax + dx * 0.6, ay + dy * 0.6, stroke=INK, sw=2)
            g.path(f"M {c(ax + dx * 0.6)} {c(ay + dy * 0.6)} l {c(-dx * 0.2 - dy * 0.12)} {c(-dy * 0.2 - dx * 0.12)} "
                   f"M {c(ax + dx * 0.6)} {c(ay + dy * 0.6)} l {c(-dx * 0.2 + dy * 0.12)} {c(-dy * 0.2 + dx * 0.12)}",
                   stroke=INK, sw=2)
        lab = "רעפים" if x["k"] == "tile" else "גג שטוח"
        lx = (x0 + cx) / 2 if sl == "gable-y" else cx
        g.text(lx, cy - 0.85, f"{lab} · {area(x['r']):.0f} מ\"ר", size=0.26, bold=True)
    terrace = [x["r"] for x in p.roof if x["k"] == "terrace"]
    if terrace:                              # the railing all around the terrace, open where the stair arrives
        for s in _inset_outline(terrace, 0.1):
            for a in _cut(s, p.gaps):
                g.line(*a, stroke="#3d3b36", sw=5, extra='stroke-linecap="square"')
        for x0, y0, x1, y1 in edge:          # the paving covered half of the house edge
            g.line(x0, y0, x1, y1, stroke=INK, sw=2, extra='stroke-linecap="square"')
    for m in p.marks:
        if m.get("roof"):
            g.text(m["x"], m["y"], m["text"], size=m["size"], color=m["color"], bold=m["bold"])
