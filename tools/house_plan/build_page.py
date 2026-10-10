# -*- coding: utf-8 -*-
"""Builds the page of the house models, with their images.

  python tools/house_plan/build_page.py            your models: models.py with texts.py -> deliverables/house/
  python tools/house_plan/build_page.py example    the example: the other house of the pair (example_models.py with
                                                   example_texts.py) -> deliverables/example/

Outputs:
  page.html                 the page: per model, the drawing (plan / walks / on the plot / roof / the two houses), the
                            3D model, zoom, the areas, the building rules and the automatic checks
  share/page.html           the same page as an Artifact fragment (<title> and <style> first, no document tags), to
                            publish as a private Artifact
  <id>-plan.png, -routes.png, -site.png, -roof.png, -pair.png   the images (ids in Latin letters)

The automatic checks (checks.py) run first; the build stops if a model listed in CURRENT has errors.
"""
import html
import importlib
import json
import math
import re
import sys
from pathlib import Path

import pymupdf

import checks
import draw
import house3d
import lot as S

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

LABEL = {"public": "מטבח, פינת אוכל, סלון ומבואה", "lobby2": "מבואת חדרים", "vest": "מבואת ההורים וארונות",
         "pass": "מעבר להורים"}
VIEWS = [("plan", "תוכנית"), ("routes", "מסלולים"), ("site", "על המגרש"), ("roof", "גג"), ("pair", "שני הבתים")]
ZOOM = {"plan": 1.6, "routes": 1.6, "site": 0.9, "roof": 0.8, "pair": 0.75}
LEGEND = [("alarm", "מהמיטה לממ\"ד"), ("groceries", "מהחניה למטבח"), ("guest", "מהדלת לשירותי האורחים"),
          ("laundry", "מחדר ההורים לכביסה ולחבלים")]
LEVELS = {"error": ("שגיאה", "fail"), "warn": ("לבדוק", "part"), "waived": ("התקבל בכוונה", "ok")}
LATIN = str.maketrans({"א": "a", "ב": "b", "ג": "c", "ד": "d", "ה": "e", "ו": "f", "ז": "g", "ח": "h", "ט": "i",
                       "י": "j", "כ": "k", "ל": "l", "מ": "m", "נ": "n", "ס": "s", "ע": "o", "פ": "p", "צ": "t",
                       "ק": "q", "ר": "r", "ש": "w", "ת": "x"})


def fid(p):
    """The id in file names, Latin letters only: model 3ב -> 3b."""
    return re.sub(r"[^A-Za-z0-9_-]", "", p.cid.translate(LATIN)) or "model"


def esc(s):
    return html.escape(s, quote=False)


def fill(text, values):
    """{name} in a text is a number computed from the drawing (facts below); a text never types a number by hand."""
    return re.sub(r"\{([^{}]+)\}", lambda m: values[m.group(1)], text)


def png(svg, path, zoom):
    tmp = path.with_suffix(".svg")
    tmp.write_text(svg, encoding="utf-8")
    try:
        pymupdf.open(tmp)[0].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(path)
    finally:
        tmp.unlink()


# ---- the numbers of a drawing ------------------------------------------------------------------------------------

def numbers(p):
    tile, flat = p.roof_split()
    pergola = sum(draw.area(g["r"]) for g in p.garden if g["k"] == "pergola")
    public = sum(p.room_area(r) for r in p.rooms if r["kind"] == "public")
    plot = S.W * S.D
    parking = draw.area(S.PARKING) + draw.area(S.PATH)
    return dict(gross=p.gross(), net=p.net(), walls=p.gross() - p.net(), tile=tile, flat=flat,
                tile_share=tile / (tile + flat) if tile + flat else 0.0, pergola=pergola, public=public,
                garden=plot - p.gross() - parking)


def rules(n):
    ok, bad = "✓", "✗"
    own = f"עד {S.MAX_BUILT:.0f} (התקרה שלכם), " if S.MAX_BUILT < S.KIBBUTZ_MAX else ""
    return [("שטח בנוי, כולל ממ\"ד וקירות", f"{n['gross']:.1f} מ\"ר", f"{own}עד {S.KIBBUTZ_MAX:.0f} (הקיבוץ)",
             ok if n["gross"] <= min(S.MAX_BUILT, S.KIBBUTZ_MAX) + 1e-6 else bad),
            ("גג רעפים", f"{n['tile_share'] * 100:.0f}%", "לפחות 30%", ok if n["tile_share"] >= S.MIN_TILE_SHARE else bad),
            ("קווי בניין", "3 מ' מהרחוב, מהגינה ומהצד הפנוי, 0 ומעלה בצד השותפים", "כמו בתוכנית", ok),
            ("פרגולה", f"{n['pergola']:.0f} מ\"ר", "עד 50 מ\"ר, גובה עד 3.5 מ'", ok if n["pergola"] <= S.MAX_PERGOLA else bad)]


def walks(p):
    return {r["name"]: f"{draw.Plan.route_length(r):.1f}" for r in p.routes}


def perimeter(p):
    return sum(math.dist((a, b), (c, d)) for a, b, c, d in draw._outline(p.blocks))


def room_rows(p):
    return [(LABEL.get(r["id"]) or r["name"].replace("\n", " "), p.room_area(r)) for r in p.rooms]


def open_areas(p):
    """What the built area leaves out: an open patio and a roof terrace, in m²."""
    patio = sum(draw.area(g["r"]) for g in p.garden if g["k"] == "paving" and g.get("roof"))
    terrace = sum(draw.area(x["r"]) for x in p.roof if x["k"] == "terrace")
    return patio, terrace


def _clip_area(poly, r):
    """The area of a polygon inside a rectangle (Sutherland-Hodgman, then the shoelace formula)."""
    pts = list(poly)
    for axis, v, side in ((0, r[0], 1), (0, r[2], -1), (1, r[1], 1), (1, r[3], -1)):
        keep = lambda q: (q[axis] - v) * side >= 0
        out = []
        for i, b in enumerate(pts):
            a = pts[i - 1]
            if keep(a) != keep(b):
                t = (v - a[axis]) / (b[axis] - a[axis])
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            if keep(b):
                out.append(b)
        pts = out
        if not pts:
            return 0.0
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def facts(p):
    """Numbers computed from the drawing, for the texts: {שטח בנוי}, {קירות חוץ}, {פטיו פנוי}, {רום} and so on."""
    n = numbers(p)
    patio, terrace = open_areas(p)
    out = {"שטח בנוי": f"{n['gross']:.1f}", "שטח בנוי0": f"{n['gross']:.0f}", "נטו": f"{n['net']:.1f}",
           "קירות חוץ": f"{perimeter(p):.1f}", "רעפים": f"{n['tile_share'] * 100:.0f}", "מרפסת גג": f"{terrace:.0f}"}
    r = next((g["r"] for g in p.garden if g["k"] == "paving" and g.get("roof")), None)
    if r:
        free = draw.area(r) - sum(_clip_area(g["poly"], r) for g in p.garden if g["k"] == "stair" and g.get("poly"))
        out.update({"פטיו": f"{patio:.1f}", "פטיו מידות": f"{r[2] - r[0]:.2f} × {r[3] - r[1]:.2f}",
                    "פטיו פנוי": f"{free:.1f}"})
    for g in p.garden:
        if g["k"] == "stair" and g.get("spec"):
            sp = g["spec"]
            out.update({"מדרגות": str(sp["risers"]), "רום": f"{sp['height'] / sp['risers'] * 100:.1f}",
                        "שלח": f"{sp['tread'] * 100:.0f}"})
    return out


def model_values(p):
    return {**walks(p), **facts(p)}


# ---- the two houses of the pair ----------------------------------------------------------------------------------

def _shift(q, dx):
    """Move a whole plan along x (for the mirror image, on the other plot of the pair)."""
    def r4(r):
        return (r[0] + dx, r[1], r[2] + dx, r[3]) if len(r) == 4 else (r[0] + dx,) + tuple(r[1:])
    q.blocks = [r4(b) for b in q.blocks]
    for r in q.rooms:
        r["rects"] = [r4(x) for x in r["rects"]]
        if r["at"]:
            r["at"] = (r["at"][0] + dx, r["at"][1])
    for o in q.openings:
        o["r"] = r4(o["r"])
    for f in q.furniture:
        f["r"] = r4(f["r"])
        for k in ("sink", "hob", "chair"):
            if f.get(k):
                f[k] = (f[k][0] + dx, f[k][1])
        for k in ("extend", "open"):
            if f.get(k):
                f[k] = r4(f[k])
    for g in q.garden:
        g["r"] = r4(g["r"])
        if g.get("at"):
            g["at"] = (g["at"][0] + dx, g["at"][1])
        for k in ("poly", "walk", "rail"):
            if g.get(k):
                g[k] = [(x + dx, y) for x, y in g[k]]
        if g.get("rails"):
            g["rails"] = [[(x + dx, y) for x, y in rl] for rl in g["rails"]]
        if g.get("lines"):
            g["lines"] = [(xa + dx, ya, xb + dx, yb) for xa, ya, xb, yb in g["lines"]]
    for m in q.marks:
        m["x"] += dx
    q.zones = [r4(z) for z in q.zones]
    q.routes, q.dims = [], []
    return q


def render_pair(p, bidi=False):
    """This house on its plot, and the other house of the pair as its mirror image (an assumption, to coordinate with
    the other family): the courts on the shared side face each other."""
    W, D = S.W, S.D
    ours = draw.mirrored(draw.mirrored(p))           # a copy
    ours.routes, ours.dims = [], []
    theirs = _shift(draw.mirrored(p), -W)
    g = draw.Svg(bidi)
    vb = (-W - 0.6, -3.2, 2 * W + 1.2, D + 6.6)
    g.add(f'<rect x="{draw.c(vb[0])}" y="{draw.c(vb[1])}" width="{draw.c(vb[2])}" height="{draw.c(vb[3])}" '
          f'fill="{draw.PAPER}"/>')
    g.rect((vb[0], -3.2, vb[0] + vb[2], -1.2), fill="#e2e0da")
    g.rect((vb[0], -1.2, vb[0] + vb[2], 0.0), fill="#f1f0ec")
    g.text(0, -1.9, "הרחוב", size=0.42, color="#6d6a62")
    g.rect((vb[0], D, vb[0] + vb[2], vb[1] + vb[3]), fill="#eaf2e3")
    g.text(0, D + 1.6, "הרצועה הירוקה", size=0.42, color="#55704a")
    g.rect((-W, 0, W, D), fill="#fcfcfa")
    for q, sign in ((theirs, -1), (ours, 1)):
        for it in q.garden:
            if it["k"] == "lawn":
                draw._garden(g, it)
        for st in S.STALLS:
            r = st if sign > 0 else (-st[2], st[1], -st[0], st[3])
            g.rect(r, fill="#f2f1ee", stroke="#77746b", sw=1.3)
        for it in q.garden:
            if it["k"] != "lawn":
                draw._garden(g, it)
        draw._house(g, q)
    g.line(0, -1.2, 0, D + 0.4, stroke="#2f5d9b", sw=6)
    for x in (-W, W):
        g.line(x, 0, x, D, stroke="#2f5d9b", sw=2.4, extra='stroke-dasharray="30 8"')
    g.line(-W, 0, W, 0, stroke="#2f5d9b", sw=2.4, extra='stroke-dasharray="30 8"')
    g.line(-W, D, W, D, stroke="#2f5d9b", sw=2.4, extra='stroke-dasharray="30 8"')
    g.text(W / 2, D + 2.75, "הבית הזה", size=0.5, bold=True)
    g.text(-W / 2, D + 2.75, "הבית השני בזוג: תמונת מראה (הנחה, לתיאום)", size=0.5, color="#6d6a62", bold=True)
    g.text(0.2, D + 0.95, "הגבול המשותף", size=0.3, color="#2f5d9b", anchor="start")
    vbs = " ".join(str(draw.c(v)) for v in vb)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vbs}" width="{draw.c(vb[2]) * 0.4:.0f}" '
            f'height="{draw.c(vb[3]) * 0.4:.0f}">' + "".join(g.parts) + "</svg>")


def render(p, view, mirror=False, bidi=False):
    if view == "pair":
        return render_pair(p, bidi)
    return draw.render(p, view, mirror=mirror, bidi=bidi)


# ---- the 3D model and the zoom -----------------------------------------------------------------------------------

BASE3D = [("top", "מבט על"), ("plan", "מלמעלה"), ("garden", "מהגינה"), ("street", "מהרחוב")]
ZOOM_BUTTONS = ('<div class="zoom"><button type="button" data-z="in" aria-label="הגדלה">+</button>'
                '<button type="button" data-z="out" aria-label="הקטנה">−</button>'
                '<button type="button" data-z="reset" aria-label="כל השרטוט">⤢</button></div>')


def views3d(T, p):
    """The places to stand in a model, from the texts: {view: dict(pos=[x, height, y], dir=[...], label=...)}."""
    return T.VIEWS3D.get(p.cid, {}) if hasattr(T, "VIEWS3D") else {}


def data3d(T, p):
    inner = {k: {kk: vv for kk, vv in v.items() if kk != "label"} for k, v in views3d(T, p).items()}
    extras = dict(views=inner, rugs=getattr(T, "RUGS", {}).get(p.cid, []), plants=[],
                  nlabels=["השותפים\nהנחה: שתי קומות", "השכנים\nהנחה: שתי קומות"])
    return house3d.data(p, label_at={}, extras=extras, sides_out=True)


def buttons3d(T, p):
    return BASE3D + [(k, v.get("label", k)) for k, v in views3d(T, p).items()]


def view3d_html(T, p):
    views = "".join(f'<button data-view="{v}"{" aria-pressed=true" if v == "top" else ""}>{t}</button>'
                    for v, t in buttons3d(T, p))
    data = json.dumps(data3d(T, p), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<div class="view h3d" data-view="3d" data-mirror="0" hidden>
    <div class="bar">
      <div class="grp" role="group" aria-label="מבט"><span>מבט:</span>{views}</div>
      <div class="grp" role="group" aria-label="הגג"><span>הגג:</span>
        <button data-roof="off" aria-pressed="true">בלי</button><button data-roof="on">עם</button>
        <button data-roof="shade">בלי, עם הצל שלו</button></div>
      <div class="grp"><label><input type="checkbox" class="labels" checked> שמות החדרים</label>
        <label><input type="checkbox" class="neighbors" checked> השכנים</label></div>
      <div class="grp" role="group" aria-label="שמש"><span>שמש:</span>
        <button data-season="winter" aria-pressed="true">חורף</button><button data-season="summer">קיץ</button>
        <input type="range" class="hour" min="7" max="17" step="0.25" value="12" aria-label="שעה">
        <output class="sunread"></output></div>
    </div>
    <div class="stage"><canvas></canvas><div class="msg">טוען את ההדמיה...</div>
      <div class="zoom"><button type="button" data-zoom="in" aria-label="הגדלה">+</button>
        <button type="button" data-zoom="out" aria-label="הקטנה">−</button></div></div>
    <p class="hint small">גוררים כדי לסובב, ולחיצה ימנית או שתי אצבעות כדי להזיז. זום: הכפתורים בפינה, Ctrl וגלגלת,
      או צביטה. הריהוט, הצבעים והחומרים לדוגמה בלבד. תקרה 2.75 מ'.</p>
    <script type="application/json" class="h3d-data">{data}</script>
  </div>"""


def viewer_js():
    return (HERE / "house3d.js").read_text(encoding="utf-8").replace("</", "<\\/")


# ---- the page ----------------------------------------------------------------------------------------------------

def area_html(p, n):
    """The built area of the house: the one the arnona is paid on. An open patio, pergolas and a roof terrace are not
    in it."""
    patio, terrace = open_areas(p)
    out = [f"הפטיו הפתוח ({patio:.1f} מ\"ר)"] if patio else []
    out += ["הפרגולות", "מרפסת הכניסה"]
    out += [f"מרפסת הגג ({terrace:.0f} מ\"ר, לבדוק במועצה)"] if terrace else []
    return (f'<div class="area"><b>סה"כ שטח בנוי: {n["gross"]:.1f} מ"ר</b> <span class="small">· הבית עצמו, '
            f'כולל הקירות והממ"ד. לא כולל: {esc(", ".join(out[:-1]))} ו{esc(out[-1])}.</span></div>')


def checks_html(p):
    fs = sorted(checks.findings(p), key=lambda x: ("error", "warn", "waived").index(x[0]))
    if not fs:
        return '<p class="small">הבדיקות האוטומטיות עברו בלי הערות.</p>'
    rows = "".join(f"<tr><td><span class='st {LEVELS[lvl][1]}'>{LEVELS[lvl][0]}</span></td><td>{esc(msg)}</td></tr>"
                   for lvl, _, msg in fs)
    return f'<table class="t"><tbody>{rows}</tbody></table>'


def round_html(r, w, latest):
    """One round of comments on a model: the latest in full, the earlier ones folded."""
    changes = "".join(f"<li><b>{esc(a)}.</b> {esc(fill(b, w))}</li>" for a, b in r["changes"])
    follows = "".join(f"<li>{esc(fill(t, w))}</li>" for t in r.get("follows", []))
    same = f'<p class="small"><b>מה לא השתנה:</b> {esc(r["unchanged"])}</p>' if r.get("unchanged") else ""
    inner = f'<ul>{changes}</ul>' + (f'<p class="small"><b>מה נובע מזה:</b></p><ul class="small">{follows}</ul>'
                                     if follows else "") + same
    if latest:
        return f'<h3>{esc(r["title"])}</h3>{inner}'
    return f'<details class="more"><summary>{esc(r["title"])}</summary>{inner}</details>'


def model_html(T, p, first):
    ab, n, w = T.ABOUT[p.cid], numbers(p), model_values(p)
    views = []
    for view, _ in VIEWS:
        for mirror in ((False,) if view == "pair" else (False, True)):
            hidden = "" if (view, mirror) == ("plan", False) else " hidden"
            views.append(f'<div class="view" data-view="{view}" data-mirror="{int(mirror)}"{hidden}>'
                         f'{render(p, view, mirror=mirror)}</div>')
    views.append(view3d_html(T, p))
    seg = "".join(f'<button data-set="{v}"{" class=on" if v == "plan" else ""}>{t}</button>' for v, t in VIEWS)
    seg += '<button data-set="3d">תלת-ממד</button>'
    legend = "".join(f'<span class="lg"><i style="background:{draw.ROUTE_COLORS[k]}"></i>{t}</span>' for k, t in LEGEND)
    lst = lambda xs: "".join(f"<li>{esc(fill(x, w))}</li>" for x in xs)
    rows = "".join(f"<tr><td>{esc(a)}</td><td class='num'>{b:.1f}</td></tr>" for a, b in room_rows(p))
    rule_rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td class='num'>{d}</td></tr>" for a, b, c, d in rules(n))
    life = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(fill(b, w))}</td></tr>" for a, b in ab.get("life", []))
    life_card = (f'<div class="card" style="margin-top:12px"><h3>הבית לאורך השנים</h3>'
                 f'<table class="t"><tbody>{life}</tbody></table></div>') if life else ""
    rounds = getattr(T, "ROUNDS", {}).get(p.cid, [])
    rounds_card = ('<div class="card chg" style="margin-top:12px">'
                   + "".join(round_html(r, w, i == 0) for i, r in enumerate(rounds)) + "</div>") if rounds else ""
    pros_cons = (f'<div class="grid2"><div class="card"><h3>בעד</h3><ul>{lst(ab.get("pros", []))}</ul></div>'
                 f'<div class="card"><h3>נגד</h3><ul>{lst(ab.get("cons", []))}</ul></div></div>'
                 if ab.get("pros") or ab.get("cons") else "")
    return f"""
<section class="concept" id="m-{fid(p)}" data-cid="{p.cid}"{'' if first else ' hidden'}>
  {area_html(p, n)}
  <p class="idea"><b>{esc(fill(ab.get('size', ''), w))}</b> {esc(fill(ab.get('idea', ''), w))}</p>
  <div class="viewbar">
    <div class="seg" role="group" aria-label="תצוגה">{seg}</div>
    <label class="small mirrorbox"><input type="checkbox" class="mirror"> תמונת מראה (הבית השני בזוג)</label>
  </div>
  <div class="legend small">{legend}<span>המספר: מטרים, לפי השרטוט</span></div>
  <p class="small pairnote" hidden>הבית השני בזוג מצויר כתמונת מראה של הבית הזה. זו הנחה: כך החצרות בצד המשותף נמצאות
    זו מול זו.</p>
  <div class="paper">{ZOOM_BUTTONS}{''.join(views)}</div>
  <p class="small zoomhint">זום בשרטוט: הכפתורים בפינה, Ctrl וגלגלת, צביטה, או לחיצה כפולה. כשמוגדל, גוררים כדי להזיז.</p>
  {rounds_card}
  {pros_cons}
  {life_card}
  <details class="more"><summary>פרטים נוספים: הבדיקות האוטומטיות, שטחים וכללי הבנייה</summary>
  <div class="card" style="margin-top:12px"><h3>הבדיקות האוטומטיות</h3>{checks_html(p)}</div>
  <div class="grid2">
    <div class="card"><h3>שטחים (נטו, מ"ר)</h3>
      <table class="t"><tbody>{rows}</tbody>
      <tfoot><tr><td>סה"כ נטו</td><td class="num">{n['net']:.1f}</td></tr>
      <tr><td>קירות (כולל קירות הממ"ד)</td><td class="num">{n['walls']:.1f}</td></tr>
      <tr><td><b>שטח בנוי (ברוטו)</b></td><td class="num"><b>{n['gross']:.1f}</b></td></tr></tfoot></table></div>
    <div class="card"><h3>כללי הבנייה</h3>
      <table class="t"><thead><tr><th>נושא</th><th>בדגם</th><th>הכלל</th><th></th></tr></thead><tbody>{rule_rows}</tbody></table>
      <p class="small">קירות חוץ: {perimeter(p):.1f} מ'.</p></div>
  </div>
  </details>
</section>"""


EXTRA_CSS = """
.st{display:inline-block;font-size:12px;font-weight:600;padding:0 8px;border-radius:999px;white-space:nowrap}
.st.ok{background:var(--accent-bg);color:var(--accent)} .st.part{background:var(--warn-bg);color:var(--warn)}
.st.fail{background:#fbe3e3;color:#a32d2d}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;margin:2px 0 8px}
.lg i{display:inline-block;width:18px;height:4px;border-radius:2px;margin-inline-end:6px;vertical-align:middle}
details.more{margin-top:12px}
details.more>summary{cursor:pointer;color:var(--accent);font-weight:600;padding:4px 0}
.seg{flex-wrap:wrap}
.tabs button.on,.seg button.on{color:var(--card)}
.chg li{margin:6px 0}
.area{margin:4px 0 10px;padding:8px 12px;border-radius:10px;background:var(--accent-bg)}
.paper{position:relative}
.zoom{position:absolute;top:8px;left:8px;display:flex;flex-direction:column;gap:4px;z-index:3}
.zoom button{width:34px;height:34px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);
  font-size:19px;line-height:1;cursor:pointer;padding:0;opacity:.92}
.h3d .zoom{top:10px;left:10px}
.h3d .bar{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;margin:0 0 10px}
.h3d .grp{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.h3d .grp>span{font-size:13px;color:var(--muted)}
.h3d .bar button{font:inherit;font-size:14px;padding:4px 12px;border-radius:999px;border:1px solid var(--line);
  background:var(--card);color:var(--text);cursor:pointer}
.h3d .bar button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.h3d .bar label{font-size:14px;display:flex;gap:4px;align-items:center;cursor:pointer}
.h3d .bar input[type=range]{width:160px;accent-color:var(--accent)}
.h3d .sunread{font-size:13px;color:var(--muted);min-width:16em}
.h3d .stage{position:relative;height:min(72vh,780px);min-height:360px;border-radius:10px;overflow:hidden;
  background:#dfe9f2;touch-action:none}
.h3d .stage canvas{display:block;width:100%;height:100%}
.h3d .msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#3a3833;
  pointer-events:none;text-align:center;padding:16px}
.h3d .hint{margin:6px 2px 0}
@media (max-width:600px){.h3d .stage{height:58vh}.h3d .bar input[type=range]{width:120px}}
"""

SCRIPT = r"""
const show = (sec) => {
  const view = sec.querySelector('.seg button.on').dataset.set;
  const pair = view === 'pair' || view === '3d';
  const mir = !pair && sec.querySelector('.mirror').checked ? '1' : '0';
  sec.querySelectorAll('.view').forEach(v => v.hidden = !(v.dataset.view === view && v.dataset.mirror === mir));
  sec.querySelector('.legend').style.display = view === 'routes' ? '' : 'none';
  sec.querySelector('.mirrorbox').style.visibility = pair ? 'hidden' : '';
  sec.querySelector('.pairnote').hidden = view !== 'pair';
  sec.querySelector('.paper > .zoom').style.display = view === '3d' ? 'none' : '';
  sec.querySelector('.zoomhint').hidden = view === '3d';
  const h3 = sec.querySelector('.h3d');
  if (view === '3d' && h3 && !h3.dataset.on) {   // the 3D model loads the first time its tab opens
    h3.dataset.on = '1';
    window.House3D.mount(h3, JSON.parse(h3.querySelector('.h3d-data').textContent), {ctrlWheel: true});
  }
};
// zoom in the drawings: the buttons, Ctrl and the wheel (or a pinch), two fingers, or a double click.
const zoomers = new WeakMap();
function zoomer(svg) {
  if (zoomers.has(svg)) return zoomers.get(svg);
  const b = svg.viewBox.baseVal, base = [b.x, b.y, b.width, b.height];
  let vb = base.slice();
  const zoomed = () => vb[2] < base[2] - 0.5;
  const apply = () => {
    svg.setAttribute('viewBox', vb.map(v => v.toFixed(1)).join(' '));
    svg.style.touchAction = zoomed() ? 'none' : 'pan-x pan-y';
    svg.style.cursor = zoomed() ? 'grab' : '';
  };
  const clamp = () => {
    vb[0] = Math.min(Math.max(vb[0], base[0]), base[0] + base[2] - vb[2]);
    vb[1] = Math.min(Math.max(vb[1], base[1]), base[1] + base[3] - vb[3]);
  };
  const at = (k, cx, cy) => {
    const w = Math.min(base[2], Math.max(base[2] / 10, vb[2] / k)), h = w * base[3] / base[2];
    vb = [cx - (cx - vb[0]) * w / vb[2], cy - (cy - vb[1]) * h / vb[3], w, h];
    clamp(); apply();
  };
  const pt = (x, y) => {
    const r = svg.getBoundingClientRect();
    return [vb[0] + (x - r.left) / r.width * vb[2], vb[1] + (y - r.top) / r.height * vb[3]];
  };
  const reset = () => { vb = base.slice(); apply(); };
  svg.addEventListener('wheel', e => {
    if (!e.ctrlKey) return;
    e.preventDefault(); at(Math.exp(-e.deltaY * 0.004), ...pt(e.clientX, e.clientY));
  }, {passive: false});
  svg.addEventListener('dblclick', e => { e.preventDefault(); zoomed() ? reset() : at(2.5, ...pt(e.clientX, e.clientY)); });
  const ptrs = new Map();
  let pinch = null;
  svg.addEventListener('pointerdown', e => {
    ptrs.set(e.pointerId, [e.clientX, e.clientY]);
    if (ptrs.size === 2) { const [a, c] = [...ptrs.values()]; pinch = {d: Math.hypot(a[0] - c[0], a[1] - c[1]), w: vb[2]}; }
    if (zoomed() || ptrs.size === 2) svg.setPointerCapture(e.pointerId);
  });
  svg.addEventListener('pointermove', e => {
    if (!ptrs.has(e.pointerId)) return;
    const prev = ptrs.get(e.pointerId);
    ptrs.set(e.pointerId, [e.clientX, e.clientY]);
    if (ptrs.size === 2 && pinch) {
      const [a, c] = [...ptrs.values()], d = Math.hypot(a[0] - c[0], a[1] - c[1]) || 1;
      at(vb[2] / (pinch.w * pinch.d / d), ...pt((a[0] + c[0]) / 2, (a[1] + c[1]) / 2));
    } else if (ptrs.size === 1 && zoomed()) {
      const r = svg.getBoundingClientRect();
      vb[0] -= (e.clientX - prev[0]) / r.width * vb[2]; vb[1] -= (e.clientY - prev[1]) / r.height * vb[3];
      clamp(); apply();
    }
  });
  const up = e => { ptrs.delete(e.pointerId); if (ptrs.size < 2) pinch = null; };
  svg.addEventListener('pointerup', up);
  svg.addEventListener('pointercancel', up);
  const z = {in: () => at(1.5, vb[0] + vb[2] / 2, vb[1] + vb[3] / 2), out: () => at(1 / 1.5, vb[0] + vb[2] / 2, vb[1] + vb[3] / 2), reset};
  apply();
  zoomers.set(svg, z);
  return z;
}
document.querySelectorAll('.paper').forEach(paper => {
  paper.querySelectorAll(':scope > svg, :scope > .view:not(.h3d) > svg').forEach(zoomer);
  paper.querySelectorAll(':scope > .zoom button').forEach(b => b.addEventListener('click', () => {
    const v = [...paper.querySelectorAll(':scope > .view')].find(x => !x.hidden);
    const svg = (v || paper).querySelector('svg');
    if (svg) zoomer(svg)[b.dataset.z]();
  }));
});
document.querySelectorAll('.concept').forEach(sec => {
  sec.querySelectorAll('.seg button').forEach(b => b.addEventListener('click', () => {
    sec.querySelectorAll('.seg button').forEach(x => x.classList.toggle('on', x === b)); show(sec);
  }));
  sec.querySelector('.mirror').addEventListener('change', () => show(sec));
  show(sec);
});
document.querySelectorAll('#tabs button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('#tabs button').forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('.concept').forEach(s => s.hidden = s.dataset.cid !== b.dataset.tab);
}));
"""


def page(T, plans):
    css = (HERE / "page.css").read_text(encoding="utf-8") + EXTRA_CSS
    first = getattr(T, "FIRST", None) or plans[-1].cid
    marks = getattr(T, "MARK", {})
    tabs = "".join(f'<button data-tab="{p.cid}" class="{"on" if p.cid == first else ""}">{esc(T.ABOUT[p.cid]["title"])}'
                   f' · {numbers(p)["gross"]:.0f} מ"ר{esc(marks.get(p.cid, ""))}</button>' for p in plans)
    body = "".join(model_html(T, p, p.cid == first) for p in plans)
    P = T.PAGE
    cards = "".join(f'<div class="card"><div class="small">{esc(a)}</div><div class="kpi">{esc(b)}</div>'
                    f'<div class="small">{esc(c)}</div></div>' for a, b, c in P.get("cards", []))
    sections = ""
    for title, items in P.get("sections", []):
        sections += f'<h2>{esc(title)}</h2><div class="card"><ul>' + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul></div>"
    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(P['title'])}</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>{esc(P['title'])}</h1>
<p class="sub">{esc(P.get('sub', ''))}</p>
<div class="grid">{cards}</div>
<h2>{esc(P.get('models_title', 'הדגמים'))}</h2>
<div class="tabs" id="tabs">{tabs}</div>
{body}
{sections}
</main>
<script>{viewer_js()}</script>
<script>{SCRIPT}</script>
</body>
</html>
"""


def share_page(page_html, leaks=None):
    """The Artifact fragment: <title> and <style> first, then the content (the viewer adds the document skeleton).
    leaks: a regex of what must not appear in the shared page (names, plot numbers); the build stops if it does."""
    s = page_html
    if leaks:
        found = sorted({m.group(0) for t in re.findall(r">([^<]+)<", s) for m in re.finditer(leaks, t)})
        if found:
            raise SystemExit(f"share: left in the page: {found}")
    title = re.search(r"<title>.*?</title>", s, re.S).group(0)
    css = re.search(r"<style>(.*?)</style>", s, re.S).group(1)
    dark = re.search(r'@media \(prefers-color-scheme: dark\)\{:root:not\(\[data-theme="light"\]\)\{(.*?)\}\}', css)
    if dark:
        d = dark.group(1)
        css = css.replace(d + "}}", d + ";color-scheme:dark}}", 1) + ':root[data-theme="dark"]{' + d + ";color-scheme:dark}\n"
    body = re.search(r"<body>(.*)</body>", s, re.S).group(1).strip()
    return f"{title}\n<style>{css}</style>\n{body}\n"


def main():
    example = len(sys.argv) > 1 and sys.argv[1] == "example"
    M = importlib.import_module("example_models" if example else "models")
    T = importlib.import_module("example_texts" if example else "texts")
    out = ROOT / "deliverables" / ("example" if example else "house")
    out.mkdir(parents=True, exist_ok=True)
    fns = M.FORMS if example else M.MODELS
    if not fns:
        raise SystemExit("models.py has no models yet (MODELS is empty). The example: build_page.py example")
    plans = [f() for f in fns]
    current = set(getattr(T, "CURRENT", [p.cid for p in plans]))
    failed = []
    for p in plans:
        lines, errors = checks.report(p)
        print("\n".join(lines if p.cid in current else lines[:1]))
        if errors and p.cid in current:
            failed.append(p.cid)
    if failed:
        raise SystemExit(f"the automatic checks failed: {', '.join(failed)}")
    for p in plans:
        for view, _ in VIEWS:
            png(render(p, view, bidi=True), out / f"{fid(p)}-{view}.png", ZOOM[view])
    html_page = page(T, plans)
    (out / "page.html").write_text(html_page, encoding="utf-8")
    (out / "share").mkdir(exist_ok=True)
    (out / "share" / "page.html").write_text(share_page(html_page, getattr(T, "LEAKS", None)), encoding="utf-8")
    for p in plans:
        n = numbers(p)
        print(f"{p.cid}: gross {n['gross']:.1f}, net {n['net']:.1f}, tile {n['tile_share'] * 100:.0f}%, "
              f"exterior walls {perimeter(p):.1f}")
    print("wrote", out / "page.html")


if __name__ == "__main__":
    main()
