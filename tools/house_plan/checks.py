# -*- coding: utf-8 -*-
"""Automatic checks of a plan (written in the planning of the other house of the pair, 5.10.2026).

What can be measured is measured, so that a stair that breaks the regulations or a label over a tree is caught
before the user sees the drawing. Each finding is (level, code, message):
  error  a regulation, a hard rule of the checklist, or a drawing mistake
  warn   below what is common, or worth a look
A plan can accept a finding on purpose: p.waive = {code: reason}; the finding is then reported as waived.
The thresholds and their sources: docs/07-design-research.md, sections 4 (regulations) and 5 (what is common).

Usage: findings(p) -> list; report(p) -> printable lines. build_forms.py runs it for every model.
"""
import math
import re

import draw

BEDROOMS = {"kid", "kid2", "mamad", "parents"}       # the mamad is a child's room (rule 18)


def is_bedroom(r):
    """A bedroom, by the room's id: parents, mamad, or any id that starts with "kid" (kid, kid2, kid3...)."""
    return r["id"] in BEDROOMS or r["id"].startswith("kid")
OBSTACLES = {"bed", "crib", "sofa", "armchair", "table", "round", "counter", "island", "tall", "fridge", "wardrobe",
             "shelf", "wc", "basin", "shower", "bath", "washer", "desk", "low", "tv", "wallbed", "stairs", "plant"}
GARDEN_SHAPES = {"tree", "stair", "steps", "outkitchen", "column", "beds", "wall"}
EPS = 1e-6


# ---- geometry ----------------------------------------------------------------------------------------------------

def inside(x, y, r, e=0.0):
    return r[0] - e <= x <= r[2] + e and r[1] - e <= y <= r[3] + e


def overlap(a, b, e=0.0):
    return min(a[2], b[2]) - max(a[0], b[0]) > e and min(a[3], b[3]) - max(a[1], b[1]) > e


def contains(a, b, e=0.0):
    """b lies inside a."""
    return a[0] - e <= b[0] and a[1] - e <= b[1] and b[2] <= a[2] + e and b[3] <= a[3] + e


def grid(r, step=0.05):
    x0, y0, x1, y1 = r
    nx, ny = max(1, int((x1 - x0) / step)), max(1, int((y1 - y0) / step))
    return [(x0 + (x1 - x0) * (i + 0.5) / nx, y0 + (y1 - y0) * (j + 0.5) / ny) for i in range(nx) for j in range(ny)]


def in_poly(x, y, poly):
    n, hit = len(poly), False
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            hit = not hit
    return hit


def furn_rect(f):
    """The footprint of a piece of furniture, or None for what moves (chairs, stools) or is not an obstacle."""
    k, r = f["k"], f["r"]
    if k not in OBSTACLES:
        return None
    if k == "wc":                                     # the cistern and the bowl, as draw.py draws them
        x, y = r[0], r[1]
        return {"y1": (x - 0.22, y - 0.09, x + 0.22, y + 0.61), "y0": (x - 0.22, y - 0.61, x + 0.22, y + 0.09),
                "x1": (x - 0.09, y - 0.22, x + 0.61, y + 0.22),
                "x0": (x - 0.61, y - 0.22, x + 0.09, y + 0.22)}[f.get("face", "y1")]
    if len(r) == 3:                                   # round things: (x, y, radius)
        return (r[0] - r[2], r[1] - r[2], r[0] + r[2], r[1] + r[2])
    return r


def room_at(p, x, y):
    for r in p.rooms:
        if any(inside(x, y, q) for q in r["rects"]):
            return r
    return None


def in_wall(p, x, y):
    """Inside the house but in no room and no opening: in a wall."""
    return (any(inside(x, y, b) for b in p.blocks) and room_at(p, x, y) is None
            and not any(inside(x, y, o["r"], 0.01) for o in p.openings))


def swing(o, step=0.04, shrink=0.02):
    """Points in the quarter circle a hinged door sweeps (as draw.py draws it)."""
    x0, y0, x1, y1 = o["r"]
    pts = []
    if (x1 - x0) >= (y1 - y0):                        # in a horizontal wall
        w = x1 - x0
        hx, ox = (x0, x1) if o["hinge"] == "x0" else (x1, x0)
        face = y1 if o["into"] > 0 else y0
        sx, sy = (1 if ox > hx else -1), o["into"]
        n = int(w / step)
        pts = [(hx + sx * i * step, face + sy * j * step) for i in range(1, n + 1) for j in range(1, n + 1)
               if math.hypot(i * step, j * step) <= w - shrink]
    else:
        w = y1 - y0
        hy, oy = (y0, y1) if o["hinge"] == "y0" else (y1, y0)
        face = x1 if o["into"] > 0 else x0
        sx, sy = o["into"], (1 if oy > hy else -1)
        n = int(w / step)
        pts = [(face + sx * i * step, hy + sy * j * step) for i in range(1, n + 1) for j in range(1, n + 1)
               if math.hypot(i * step, j * step) <= w - shrink]
    return pts


def sides(o, d=0.12):
    """The two points just outside an opening, one on each side of its wall."""
    x0, y0, x1, y1 = o["r"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if (x1 - x0) >= (y1 - y0):
        return (cx, y0 - d), (cx, y1 + d)
    return (x0 - d, cy), (x1 + d, cy)


# ---- labels: read them from the drawing itself, so every label is checked the way it is drawn --------------------

def _width(s, size, bold):
    w = 0.0
    for ch in s:
        if ch == " ":
            w += 0.28
        elif ch in ".,:;·'|!":
            w += 0.28
        elif ch in "()[]-–/":
            w += 0.33
        elif ch == '"':
            w += 0.36
        elif ch.isdigit():
            w += 0.56
        elif ch == "×":
            w += 0.58
        elif "֐" <= ch <= "׿":
            w += 0.25 if ch in "וין" else (0.37 if ch in "גזנ" else 0.55)
        else:
            w += 0.6
    return w * size * (1.06 if bold else 1.0)


_TEXT = re.compile(r"<text ([^>]*)>([^<]*)</text>")
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def labels(svg):
    """(text, box) for every label in an SVG drawn by draw.py, in meters."""
    out = []
    for attrs, txt in _TEXT.findall(svg):
        a = dict(_ATTR.findall(attrs))
        x, y, s = float(a["x"]) / 100, float(a["y"]) / 100, float(a["font-size"]) / 100
        txt = txt.replace("&amp;", "&").replace("&lt;", "<")
        w = _width(txt, s, a.get("font-weight") == "700")
        anchor = a.get("text-anchor", "middle")
        lx = x - w / 2 if anchor == "middle" else (x if anchor == "start" else x - w)
        box = (lx, y - 0.72 * s, lx + w, y + 0.15 * s)
        rot = re.search(r"rotate\(([-\d.]+)", a.get("transform", ""))
        if rot and abs(abs(float(rot.group(1))) - 90) < 1:   # turned on its side, around (x, y)
            dx0, dy0, dx1, dy1 = box[0] - x, box[1] - y, box[2] - x, box[3] - y
            box = (x + dy0, y - dx1, x + dy1, y - dx0) if float(rot.group(1)) < 0 else (x - dy1, y + dx0, x - dy0, y + dx1)
        out.append(dict(text=txt, box=box, size=s))
    return out


def _crosses_rect(box, r):
    return overlap(box, r, 0.01) and not contains(r, box, 0.01) and not contains(box, r)


def _crosses_circle(box, x, y, rr):
    nx, ny = min(max(x, box[0]), box[2]), min(max(y, box[1]), box[3])
    touches = math.hypot(nx - x, ny - y) < rr - 0.01
    corners = [(box[0], box[1]), (box[2], box[1]), (box[0], box[3]), (box[2], box[3])]
    within = all(math.hypot(cx - x, cy - y) <= rr for cx, cy in corners)
    return touches and not within


def _crosses_poly(box, poly):
    pts = [(box[0] + (box[2] - box[0]) * i / 4, box[1] + (box[3] - box[1]) * j / 2) for i in range(5) for j in range(3)]
    ins = sum(in_poly(x, y, poly) for x, y in pts)
    if 0 < ins < len(pts):
        return True
    return ins == 0 and any(inside(x, y, box) for x, y in poly)


def label_findings(p):
    out = []
    plan = labels(draw.render(p, "plan"))
    for view, labs in (("plan", plan), ("roof", labels(draw.render(p, "roof")))):
        for i, a in enumerate(labs):
            for b in labs[i + 1:]:
                if overlap(a["box"], b["box"], 0.015):
                    out.append(("error", "label-label", f"{view}: '{a['text']}' on '{b['text']}'"))
    shapes = [(f["k"], furn_rect(f)) for f in p.furniture if furn_rect(f)]
    doors = [(o, swing(o)) for o in p.openings if o["t"] in ("hinged", "steel")]
    for lab in plan:
        box, txt = lab["box"], lab["text"]
        for k, r in shapes:
            if _crosses_rect(box, r):
                out.append(("warn", "label-furniture", f"'{txt}' crosses the {k} at {tuple(round(v, 2) for v in r)}"))
        for it in p.garden:
            if not it.get("near") or it["k"] not in GARDEN_SHAPES:
                continue
            r = it["r"]
            if it["k"] == "tree":
                hit = _crosses_circle(box, *r)
            elif it["k"] == "stair":
                hit = _crosses_poly(box, it["poly"])
            else:
                hit = _crosses_rect(box, r)
            if hit:
                out.append(("warn", "label-garden", f"'{txt}' crosses the {it['k']}"))
        for o, pts in doors:
            if any(inside(x, y, box, -0.02) for x, y in pts):
                out.append(("warn", "label-door", f"'{txt}' is in the swing of the door at "
                                                  f"{tuple(round(v, 2) for v in o['r'])}"))
        pts = grid((box[0] + 0.03, box[1] + 0.03, box[2] - 0.03, box[3] - 0.03), 0.04)
        if any(room_at(p, x, y) for x, y in pts) and any(in_wall(p, x, y) for x, y in pts):
            out.append(("warn", "label-wall", f"'{txt}' runs into a wall"))
    return out


# ---- doors -------------------------------------------------------------------------------------------------------

def door_findings(p):
    out = []
    obst = [(f["k"], furn_rect(f)) for f in p.furniture if furn_rect(f)]
    hinged = [o for o in p.openings if o["t"] in ("hinged", "steel")]
    sweeps = [swing(o) for o in hinged]
    for o, pts in zip(hinged, sweeps):
        where = tuple(round(v, 2) for v in o["r"])
        hits = sorted({k for x, y in pts for k, r in obst if inside(x, y, r, -0.01)})
        if hits:
            out.append(("error", "door-furniture", f"the door at {where} hits: {', '.join(hits)}"))
        if any(in_wall(p, x, y) for x, y in pts):
            out.append(("error", "door-wall", f"the door at {where} swings into a wall"))
    for i, a in enumerate(sweeps):
        for j in range(i + 1, len(sweeps)):
            b = set((round(x, 2), round(y, 2)) for x, y in sweeps[j])
            if any((round(x, 2), round(y, 2)) in b for x, y in a):
                out.append(("warn", "door-door", f"the doors at {tuple(round(v, 2) for v in hinged[i]['r'])} and "
                                                 f"{tuple(round(v, 2) for v in hinged[j]['r'])} swing into each other"))
    return out


# ---- rooms: the minimum sizes in the regulations (2.04), the mamad, the corridors -------------------------------

def _fixtures(p, r):
    ks = set()
    for f in p.furniture:
        fr = furn_rect(f)
        if fr and any(overlap(fr, q, 0.02) for q in r["rects"]):
            ks.add(f["k"])
    return ks


def room_findings(p):
    out = []
    for r in p.rooms:
        a = draw.Plan.room_area(r)
        big = max(r["rects"], key=draw.area)
        wmin = min(big[2] - big[0], big[3] - big[1])
        name = r["name"].replace("\n", " ") or r["id"]
        if is_bedroom(r):
            if a < 8.0 - EPS or wmin < 2.60 - EPS:
                out.append(("error", "reg-room", f"{name}: {a:.1f} m², {wmin:.2f} m wide (a bedroom: 8.0 and 2.60)"))
            if not any(o["t"] in ("window", "high", "glass") and any(overlap(o["r"], q, -0.06) for q in r["rects"])
                       for o in p.openings):
                out.append(("error", "rule12", f"{name}: no window"))
            if any(q[0] < 0.35 for q in r["rects"]):
                out.append(("error", "rule19", f"{name} is on the shared wall"))
        if r["kind"] == "wet":
            ks = _fixtures(p, r)
            need = (2.5, 1.45) if "bath" in ks else ((1.8, 0.90) if "shower" in ks else (1.1, 0.80))
            if a < need[0] - EPS or wmin < need[1] - EPS:
                out.append(("error", "reg-wet", f"{name}: {a:.1f} m², {wmin:.2f} m wide (needs {need[0]} and {need[1]})"))
        if r["kind"] == "mamad":
            if a < 9.0 - EPS or wmin < 1.60 - EPS:
                out.append(("error", "mamad-size", f"{name}: {a:.1f} m² net, {wmin:.2f} m wide (9.0 and 1.60)"))
            doors = [o for o in p.openings if o["t"] == "steel"
                     and any(overlap(o["r"], q, -0.06) for q in r["rects"])]
            if not doors:
                out.append(("error", "mamad-door", f"{name}: no steel door"))
            for o in doors:
                if any(room_at(p, x, y) is r for x, y in swing(o)):
                    out.append(("error", "mamad-door", f"{name}: the door opens inward"))
                x0, y0, x1, y1 = o["r"]          # a structural wall in front of the door: 1.10 m at least
                if (x1 - x0) >= (y1 - y0):
                    face = y1 if o["into"] > 0 else y0
                    zone = (x0, min(face, face + o["into"] * 1.1), x1, max(face, face + o["into"] * 1.1))
                else:
                    face = x1 if o["into"] > 0 else x0
                    zone = (min(face, face + o["into"] * 1.1), y0, max(face, face + o["into"] * 1.1), y1)
                if any(in_wall(p, x, y) for x, y in grid((zone[0] + 0.02, zone[1] + 0.02, zone[2] - 0.02,
                                                          zone[3] - 0.02))):
                    out.append(("error", "mamad-door", f"{name}: less than 1.10 m in front of the door"))
        if r["kind"] == "circ":                  # corridors: 0.90 at least (07, 4.6 and 5.1)
            for q in r["rects"]:
                w, h = q[2] - q[0], q[3] - q[1]
                if max(w, h) < 1.5 or min(w, h) >= 0.90 - EPS:
                    continue
                along_x = w > h
                wider = any(o is not q and (abs(o[1] - q[3]) < EPS or abs(o[3] - q[1]) < EPS if along_x else
                                            abs(o[0] - q[2]) < EPS or abs(o[2] - q[0]) < EPS)
                            and overlap((q[0] - 0.01, q[1] - 0.01, q[2] + 0.01, q[3] + 0.01), o) for o in r["rects"])
                if not wider:
                    out.append(("warn", "corridor", f"{name}: a corridor {min(w, h):.2f} m wide (common 0.90-1.00)"))
    return out


# ---- fixtures and beds: the room in front of them (07, 5.2 and 5.5, NKBA) ---------------------------------------

def _clear(p, zone, own):
    """The zone is inside rooms and free of furniture (other than its own piece)."""
    obst = [furn_rect(f) for f in p.furniture if f is not own and furn_rect(f) and f["k"] != "shower"]
    for x, y in grid(zone, 0.04):
        if room_at(p, x, y) is None or any(inside(x, y, r, -0.01) for r in obst):
            return False
    return True


def fixture_findings(p):
    out = []
    for f in p.furniture:
        if f["k"] == "wc":
            x0, y0, x1, y1 = furn_rect(f)
            face = f.get("face", "y1")
            d = {"y1": (0, 1), "y0": (0, -1), "x1": (1, 0), "x0": (-1, 0)}[face]
            cx, cy = f["r"][0], f["r"][1]
            for depth, lvl in ((0.53, "error"), (0.76, "warn")):
                tip = {"y1": y1, "y0": y0, "x1": x1, "x0": x0}[face]
                if d[1]:
                    zone = (cx - 0.22, min(tip, tip + d[1] * depth), cx + 0.22, max(tip, tip + d[1] * depth))
                else:
                    zone = (min(tip, tip + d[0] * depth), cy - 0.22, max(tip, tip + d[0] * depth), cy + 0.22)
                if not _clear(p, zone, f):
                    out.append((lvl, "wc-front", f"the WC at ({cx:.2f}, {cy:.2f}): less than {depth:.2f} m in front"))
                    break
            side = 0.38                           # the WC's center from a side wall (NKBA: 0.38 at least)
            zone = (cx - side, cy - 0.05, cx + side, cy + 0.05) if d[1] else (cx - 0.05, cy - side, cx + 0.05, cy + side)
            if any(room_at(p, x, y) is None for x, y in grid(zone, 0.02)):
                out.append(("warn", "wc-side", f"the WC at ({cx:.2f}, {cy:.2f}): less than 0.38 m from its center to a side wall"))
        if f["k"] == "basin":
            r = f["r"]
            room = room_at(p, (r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
            if not room:
                continue
            wide = (r[2] - r[0]) >= (r[3] - r[1])
            # the back of the basin is the long side against a wall; the front faces the room
            if wide:
                back_low = in_wall(p, (r[0] + r[2]) / 2, r[1] - 0.06) or room_at(p, (r[0] + r[2]) / 2, r[1] - 0.06) is not room
                zone = (r[0], r[3], r[2], r[3] + 0.53) if back_low else (r[0], r[1] - 0.53, r[2], r[1])
            else:
                back_low = in_wall(p, r[0] - 0.06, (r[1] + r[3]) / 2) or room_at(p, r[0] - 0.06, (r[1] + r[3]) / 2) is not room
                zone = (r[2], r[1], r[2] + 0.53, r[3]) if back_low else (r[0] - 0.53, r[1], r[0], r[3])
            if not _clear(p, zone, f):
                out.append(("warn", "basin-front", f"the basin at {tuple(round(v, 2) for v in r)}: less than 0.53 m in front"))
        if f["k"] == "bed":
            r, head = f["r"], f.get("head", "y0")
            along_y = head in ("y0", "y1")
            width = (r[2] - r[0]) if along_y else (r[3] - r[1])
            if width < 1.35:                      # single beds stand against a wall
                continue
            for depth, lvl in ((0.60, "error"), (0.76, "warn")):
                zones = []
                if along_y:
                    zones += [(r[0] - depth, r[1], r[0], r[3]), (r[2], r[1], r[2] + depth, r[3])]
                    zones.append((r[0], r[3], r[2], r[3] + depth) if head == "y0" else (r[0], r[1] - depth, r[2], r[1]))
                else:
                    zones += [(r[0], r[1] - depth, r[2], r[1]), (r[0], r[3], r[2], r[3] + depth)]
                    zones.append((r[2], r[1], r[2] + depth, r[3]) if head == "x0" else (r[0] - depth, r[1], r[0], r[3]))
                if not all(_clear(p, z, f) for z in zones):
                    out.append((lvl, "bed-sides", f"the double bed at {tuple(round(v, 2) for v in r)}: less than "
                                                  f"{depth:.2f} m on a side or at its foot"))
                    break
    return out


# ---- the stair to the roof: the regulations (07, 4.6) -------------------------------------------------------------

def stair_findings(p):
    out = []
    for it in p.garden:
        if it["k"] != "stair":
            continue
        s = it.get("spec")
        if not s:
            out.append(("warn", "stair-spec", "a stair drawn without its numbers: not checked"))
            continue
        rise, tread = s["height"] / s["risers"] * 100, s["tread"] * 100
        if not 10 <= rise <= 17.5 + EPS:
            out.append(("error", "stair-rise", f"risers of {rise:.1f} cm (10-17.5, 3.2.2.5)"))
        if tread < 26 - EPS:
            out.append(("error", "stair-tread", f"treads of {tread:.0f} cm (26 at least, 3.2.2.5)"))
        if not 61 - EPS <= 2 * rise + tread <= 63 + EPS:
            out.append(("warn", "stair-2r+t", f"2R+T = {2 * rise + tread:.1f} cm (61-63)"))
        if sum(s["flights"]) != s["risers"]:
            out.append(("error", "stair-spec", f"flights {s['flights']} do not add up to {s['risers']} risers"))
        for n in s["flights"]:
            if not 3 <= n <= 16:
                out.append(("error", "stair-flight", f"a flight of {n} risers (3-16, outdoor stairs)"))
        if s["width"] < 0.90 - EPS:
            out.append(("error", "stair-width", f"{s['width']:.2f} m wide (0.90)"))
        need = 1.20 if s.get("straight") else s["width"]
        if len(s["flights"]) > 1 and s["landing"] < need - EPS:
            out.append(("error", "stair-landing", f"a landing of {s['landing']:.2f} m ({need:.2f})"))
    return out


# ---- the hard rules of the checklist that can be measured (07, 7.1) ------------------------------------------------

def rule_findings(p):
    out = []
    for o in p.openings:
        if o["t"] not in ("hinged", "steel", "slide", "gap"):
            continue
        a, b = (room_at(p, x, y) for x, y in sides(o))
        if a and b and {is_bedroom(a), is_bedroom(b)} == {True, False} \
                and "public" in (a["kind"], b["kind"]):
            bed = a if is_bedroom(a) else b
            out.append(("error", "rule18", f"{bed['name'].replace(chr(10), ' ')} opens to the living space"))
    for rt in p.routes:
        n = draw.Plan.route_length(rt)
        if rt["kind"] == "alarm" and n > 12.5 + EPS:
            out.append(("error", "rule6", f"to the mamad, {rt['name']}: {n:.1f} m (up to 10-12)"))
        elif rt["kind"] == "alarm" and n > 10 + EPS:
            out.append(("warn", "rule6", f"to the mamad, {rt['name']}: {n:.1f} m (up to 10-12)"))
        if rt["kind"] == "groceries" and n > 12 + EPS:
            out.append(("error", "rule9", f"from the parking to the kitchen: {n:.1f} m (up to 12)"))
    tile, flat = p.roof_split()
    if tile + flat and tile / (tile + flat) < 0.30 - EPS:
        out.append(("error", "rule16", f"tiles on {tile / (tile + flat) * 100:.0f}% of the roof (30% at least)"))
    return out


def findings(p):
    out = [("error", "plan", e) for e in p.check()]
    for f in (room_findings, door_findings, fixture_findings, stair_findings, rule_findings, label_findings):
        out += f(p)
    waive = getattr(p, "waive", {})          # {code: reason} or {"code|text in the message": reason}

    def waived(code, msg):
        return code in waive or any(k.split("|", 1)[0] == code and k.split("|", 1)[1] in msg
                                    for k in waive if "|" in k)
    return [(("waived" if waived(code, msg) else lvl), code, msg) for lvl, code, msg in out]


def report(p):
    fs = findings(p)
    lines = [f"  {lvl:6} {code:16} {msg}" for lvl, code, msg in sorted(fs, key=lambda x: ("error", "warn", "waived").index(x[0]))]
    errors = sum(1 for f in fs if f[0] == "error")
    head = f"{p.cid}: {errors} errors, {sum(1 for f in fs if f[0] == 'warn')} warnings"
    return [head] + lines, errors


if __name__ == "__main__":
    # python checks.py [function ...]: your models (models.py), or a function of the example (example_models.py)
    import sys
    import example_models
    import models
    names = sys.argv[1:] or [f.__name__ for f in models.MODELS]
    for fn in names:
        mod = models if hasattr(models, fn) else example_models
        lines, _ = report(getattr(mod, fn)())
        print("\n".join(lines))
