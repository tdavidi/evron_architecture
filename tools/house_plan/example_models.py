# -*- coding: utf-8 -*-
"""THE EXAMPLE: the models of the other house of the pair (the first family that planned with this method,
5.10.2026). Not a template for your house: your own models go in models.py, from your brief (docs/01-brief.md).
In the comments, "the user" means that family.

Five models, in the order they were made:
  1 · שתי חצרות, 2 · חצר כניסה, 3 · פטיו: three truly different forms on the same plot (stage 2 of the method);
  3ב: form 3 made smaller (about 129 m²); 3ג: 3ב with the work corner and the patio swapped (about 128 m²).
3ב and 3ג come from one function (_model_3b), so what they share changes in both.

The principles of the pair that these forms follow (docs/01-brief.md, "עקרונות הזוג"):
1. No bedroom against the shared wall: all the bedrooms (the mamad too) on the free side.
2. The house does not touch the other house along its whole length: open courts at the front and at the back, on the
   shared side, with windows into them. When both houses do the same, the courts face each other.
3. Attaching along part of the length is allowed, and on the shared side any distance is valid (the 3 m building line
   applies only to the other sides). No window in a wall that stands on the boundary itself. The courts are 3 m wide
   by choice: 6 m between the two houses if both do the same. The attached part carries only rooms that are not noise
   sensitive: kitchen cabinets, a pantry, wet rooms.

Coordinates in meters, in the plot frame of lot.py: x from the shared boundary (0) toward the free side, y from the
street (0) toward the garden. Exterior walls 25 cm, partitions 10 cm, mamad walls 25-30 cm.
"""
import math

from draw import Plan

TX = 3.0          # the courts: 3 m from the shared boundary


def entry_and_steps(p, door_x0, steps_x0=6.9):
    """A path from the side of the parking, steps up, and a covered landing at the front door."""
    if steps_x0 > 6.9:
        p.yard("paving", 6.85, 1.3, steps_x0, 2.4, near=True)
    p.yard("paving", steps_x0, 1.3, steps_x0 + 1.2, 2.4, near=True)
    p.yard("steps", steps_x0, 2.4, steps_x0 + 1.2, 3.6, along="y", n=4, near=True, up="+y")
    p.yard("paving", min(steps_x0, door_x0 - 0.3), 3.6, max(steps_x0 + 2.3, door_x0 + 1.4), 5.0, near=True)
    p.yard("canopy", door_x0 - 0.45, 3.4, door_x0 + 1.45, 5.0, near=True)
    p.yard("paving", 0.35, 0.0, 1.85, 5.0, near=True)
    p.entry = (steps_x0 + 0.6, 2.25, "+y")


def _labels(p, items):
    for x, y, text, size in items:
        p.mark(x, y, text, size=size, color="#1d1d1b", bold=True)


# ---- form 1: two courts ------------------------------------------------------------------------------------------

def form_courts():
    """1: two courts. One compact body, 3 m from the shared boundary; only the kitchen reaches the boundary, in the
    middle, between the front court and the back court. The night wing is round 5's, on the free side. The den moves
    to the front, by the entry and the front court; the dining and the living room take the whole garden side."""
    X1, Y0, YS = 15.25, 5.0, 15.25
    S0, S1 = 8.35, 11.85                       # the attached kitchen
    E, YI = X1 - 0.25, YS - 0.25
    p = Plan("1", "שתי חצרות", [(TX, Y0, X1, YS), (0.0, S0, TX, S1)])
    p.room_dims = True
    # night wing: round 5's wing, mirrored to the free side (the en-suite and the parents get windows to the east)
    p.room("mamad", "ממ\"ד\nחדר ילד 2", (12.15, 5.3, 14.95, 8.55), kind="mamad", at=(13.55, 6.45))
    p.room("kid", "חדר ילד 1", (8.9, 5.25, 11.9, 8.45), at=(10.4, 6.6))
    p.room("ensuite", "מקלחת\nהורים", (13.05, 8.8, E, 11.55), kind="wet", small=True, at=(13.75, 10.95))
    p.room("lobby2", "", (11.9, 8.8, 12.95, 11.55), (10.75, 8.55, 11.9, 11.55), (8.9, 8.55, 10.75, 9.65), kind="circ")
    p.room("bath", "מקלחת\nילדים", (8.9, 9.75, 10.65, 11.55), kind="wet", small=True, at=(9.6, 10.25))
    p.room("parents", "הורים", (11.7, 11.65, E, YI), at=(13.9, 12.1))
    p.room("laundry", "חדר\nכביסה", (9.85, 11.65, 11.6, YI), kind="service", small=True, at=(10.3, 14.35))
    p.door(12.2, 8.55, 12.9, 8.8, "x0", +1, kind="steel")       # mamad: opens out, into the lobby
    p.door(11.0, 8.45, 11.8, 8.55, "x1", +1)                     # child 1
    p.slide(8.8, 8.7, 8.9, 9.5)                                  # the night wing (pocket door)
    p.door(10.65, 9.85, 10.75, 10.55, "y0", +1)                  # children's bath
    p.door(12.0, 11.55, 12.8, 11.65, "x0", +1)                   # parents
    p.door(13.25, 11.55, 13.95, 11.65, "x0", -1)                 # en-suite, from the parents' room only
    p.door(10.8, 11.55, 11.5, 11.65, "x1", +1)                   # laundry, from the lobby
    p.door(10.0, YI, 10.8, YS, "x0", +1)                         # laundry: out to the drying yard
    p.window(13.05, Y0, 14.25, 5.3)                              # mamad
    p.window(9.65, Y0, 11.05, 5.25)                              # child 1
    p.window(E, 9.4, X1, 10.6, "high")                           # en-suite
    p.window(E, 12.3, X1, 14.1)                                  # parents, east
    p.window(12.65, YI, 14.25, YS)                               # parents, garden
    p.furn("bed", 14.05, 5.3, 14.95, 7.3, head="y0")
    p.furn("desk", 12.15, 5.45, 12.75, 6.85, chair=(13.1, 6.15), face="x0")
    p.furn("wardrobe", 13.15, 7.95, 14.95, 8.55)
    p.furn("bed", 8.9, 5.25, 9.9, 7.25, head="y0")
    p.furn("desk", 9.95, 5.25, 11.35, 5.85, chair=(10.65, 6.2), face="y0")
    p.furn("wardrobe", 11.3, 6.6, 11.9, 8.3)
    p.furn("shower", 13.8, 8.8, E, 9.8)
    p.furn("wc", 13.4, 8.92, face="y1")
    p.furn("basin", 14.45, 9.95, E, 11.35, n=2)
    p.furn("skylight", 11.35, 9.9, 12.65, 10.9)
    p.furn("shower", 8.9, 9.75, 9.8, 10.65)
    p.furn("wc", 9.45, 11.43, face="y0")
    p.furn("basin", 10.2, 10.7, 10.65, 11.5)
    p.furn("wardrobe", 11.7, 12.45, 12.3, YI)                    # closets toward the laundry room
    p.furn("bed", 13.0, 12.6, E, 14.2, head="x1")
    p.furn("crib", 13.8, 14.3, 14.9, YI - 0.05, head="x1")
    p.furn("tall", 10.95, 12.45, 11.6, 13.05, label="ארון")
    p.furn("washer", 10.95, 13.05, 11.6, 13.7)
    p.furn("washer", 10.95, 13.7, 11.6, 14.35)
    p.furn("tall", 10.95, 14.35, 11.6, YI, label="ארון")
    p.mark(10.78, 13.43, "×2", size=0.15, color="#55534d")
    p.furn("counter", 9.85, 11.75, 10.45, 12.45, front="x1", sink=(10.15, 12.1), sinkdir="y")
    p.furn("rug", 9.95, 12.75, 10.75, 14.1)                      # the drying rack
    # day zone: the den at the front, the kitchen in the attached part, the dining and the living along the garden
    p.room("den", "חדר עבודה\nואורחים", (3.25, 5.25, 6.25, 8.25), at=(4.75, 6.85))
    p.room("pantry", "מזווה", (3.25, 8.35, 6.25, 9.7), kind="service", small=True, at=(4.75, 9.15))
    p.room("wc", "שירותי\nאורחים", (6.35, 7.1, 7.45, 8.55), kind="wet", small=True, at=(6.85, 7.45))
    p.room("public", "", (6.35, 5.25, 8.8, 7.1), (7.45, 7.1, 8.8, 9.8), (6.35, 8.55, 7.45, 9.8),
           (0.25, 8.6, TX, 11.6), (TX, 8.6, 3.25, 11.65), (3.25, 9.8, 8.8, 11.65), (3.25, 11.65, 9.75, YI),
           kind="public")
    _labels(p, [(8.0, 6.6, "כניסה", 0.2), (1.55, 8.95, "מטבח", 0.24), (4.75, 14.75, "פינת אוכל", 0.22),
                (8.0, 14.75, "סלון", 0.24)])
    p.door(7.15, Y0, 8.15, 5.25, "x0", +1)                       # front door
    p.door(6.25, 6.3, 6.35, 7.0, "y1", -1)                      # den, from the entry
    p.slide(7.45, 7.3, 7.55, 8.1)                                # guest WC
    p.door(TX, 8.65, 3.25, 9.35, "y0", -1)                       # pantry, from the kitchen
    p.window(TX, 6.0, 3.25, 7.6)                                 # den: to the front court
    p.window(3.8, Y0, 5.8, 5.25, "high")                         # den: north light above the desk
    p.window(1.75, S0, 2.75, 8.6, "glass")                      # kitchen: a glass door to the front court
    p.window(0.95, S0, 1.6, 8.6)
    p.window(0.7, 11.6, 2.8, S1, "glass")                        # kitchen: to the back court
    p.window(TX, 12.2, 3.25, 14.6, "glass")                      # dining: to the back court
    p.window(3.9, YI, 8.9, YS, "glass")                          # dining and living: to the garden
    p.furn("desk", 3.25, 5.25, 4.65, 5.85, chair=(3.95, 6.2), face="y0")      # light from the side
    p.furn("desk", 4.85, 5.25, 6.25, 5.85, chair=(5.45, 6.2), face="y0")
    p.furn("sofa", 3.25, 7.35, 5.25, 8.25, back="y1", seats=2, open=(3.25, 6.65, 5.25, 8.25))
    p.furn("wardrobe", 8.2, 5.25, 8.8, 6.9)                      # coats and shoes, against child 1's wall
    p.furn("wc", 6.65, 8.37, face="y0")
    p.furn("basin", 6.4, 7.15, 6.85, 7.55)
    p.furn("shelf", 3.25, 8.35, 6.25, 8.7)                       # pantry: open shelves on both long walls
    p.furn("shelf", 3.6, 9.35, 6.25, 9.7)
    p.furn("fridge", 0.25, 8.6, 0.95, 9.35)                      # the kitchen wall on the shared boundary
    p.furn("counter", 0.25, 9.35, 0.85, 11.6, front="x1", sink=(0.55, 10.45), sinkdir="y")
    p.furn("island", 2.05, 9.65, 3.05, 11.45, hob=(2.55, 10.55), stools="x1", n=3)
    p.mark(2.55, 11.32, "תנור מתחת", size=0.13, color="#55534d")
    p.furn("table", 4.3, 12.05, 5.25, 14.05, seats=6, ends=True, extend=(4.3, 11.75, 5.25, 14.35))
    p.furn("sofa", 6.6, 11.95, 7.55, 14.15, back="x0", seats=3)
    p.furn("low", 7.95, 12.6, 8.5, 13.6)
    p.furn("tv", 9.35, 12.3, 9.75, 13.95)
    p.furn("armchair", 8.55, 14.15, 9.35, 14.95, back="y1")
    # outside
    entry_and_steps(p, door_x0=7.15)
    p.yard("lawn", 0.0, YS, 18.5, 22.0)
    p.yard("lawn", X1, Y0, 18.5, YS)
    p.yard("paving", 0.35, 4.0, 1.85, 5.0, near=True)            # the front court: steps up from the path,
    p.yard("steps", 0.35, 4.0, 1.85, 5.0, along="y", n=4, near=True, up="+y")
    p.yard("paving", 0.35, 5.0, 2.75, 8.35, near=True)           # a paved court with herbs and a tree
    p.yard("beds", 2.0, 5.35, 2.75, 7.4, near=True)
    p.yard("tree", 2.05, 6.35, 0.7, near=True)
    p.yard("deck", 0.25, S1, TX, YS, near=True)                  # the back court, part of the terrace
    p.yard("deck", TX, YS, 9.75, YS + 3.5, near=True)
    p.yard("pergola", 0.25, S1, TX, YS, near=True)
    p.yard("pergola", TX, YS, 9.75, YS + 3.5, near=True, label="מרפסת ופרגולה", at=(6.4, YS + 3.2))
    p.yard("outkitchen", 8.2, YS + 3.55, 9.75, YS + 4.3, near=True, label="טאבון", at=(9.0, YS + 4.75))
    p.yard("service", 9.85, YS, 11.85, 17.5, near=True, label="חצר תלייה", at=(10.85, 16.45))
    p.yard("hedge", 11.85, YS, 12.1, 17.75, near=True)
    p.yard("hedge", 9.75, 17.5, 12.1, 17.75, near=True)
    p.yard("hedge", -0.1, YS + 0.2, 0.15, 21.8)                  # on the boundary: a low hedge between the courts
    p.yard("hedge", -0.1, 5.2, 0.15, S0, near=True)
    p.yard("service", X1 + 0.2, 5.45, X1 + 1.1, 6.25, near=True, label="גז", at=(X1 + 0.65, 5.95))
    p.yard("hedge", X1, Y0, X1 + 1.5, Y0 + 0.25, near=True)
    p.yard("beds", 15.65, 9.2, 18.1, 14.7, label="ערוגות ירק")
    p.yard("tree", 16.6, 2.4, 1.2)
    p.yard("tree", 2.2, 19.8, 1.3)
    p.mark(15.3, 19.0, "דשא 6.4 × 6.75", size=0.24, color="#55704a")
    p.dim(TX, Y0, X1, Y0, off=-1.05, text=f"{X1 - TX:.2f}")
    p.dim(X1, Y0, X1, YS, off=0.75, text=f"{YS - Y0:.2f}")
    p.dim(0.0, S0, TX, S0, off=-0.45, text="3.00")
    # roof: flat over the den and the entry (a second floor can be built over them later, with the stair in the
    # den's place), over the night wing and the attached kitchen; tiles over the kitchen, the dining and the living
    p.roof_area("tile", TX, S0, 9.85, YS, slope="gable-x")
    p.roof_area("flat", TX, Y0, 8.85, S0)
    p.roof_area("flat", 8.85, Y0, X1, S0)
    p.roof_area("flat", 9.85, S0, X1, YS)
    p.roof_area("flat", 0.0, S0, TX, S1)
    # walks for the checklist
    p.route("alarm", (13.6, 12.55), (12.4, 12.2), (12.4, 11.1), (12.45, 9.3), (12.55, 8.3), name="הורים",
            at=(13.6, 13.0))
    p.route("alarm", (9.4, 7.6), (10.8, 8.0), (11.4, 9.1), (12.45, 9.3), (12.55, 8.3), name="ילד1", at=(9.6, 8.1))
    p.route("alarm", (4.3, 7.0), (5.9, 6.65), (6.8, 6.65), (7.9, 7.4), (8.3, 9.1), (9.5, 9.1), (12.45, 9.3),
            (12.55, 8.3), name="אורחים", at=(4.3, 7.45))
    p.route("groceries", (2.4, 0.6), (1.1, 1.5), (1.1, 5.4), (2.25, 7.6), (2.25, 8.9), (2.6, 9.0),
            name="קניות", at=(3.2, 0.35))
    p.route("guest", (7.65, 5.4), (7.9, 7.7), (7.6, 7.7), name="שירותים", at=(8.7, 4.75))
    p.route("laundry", (13.6, 12.55), (12.4, 12.2), (12.4, 11.1), (11.15, 11.0), (11.15, 12.3), (10.7, 13.4),
            name="כביסה", at=(13.6, 13.4))
    p.route("laundry", (10.4, 14.4), (10.4, 15.6), (10.85, 16.6), name="תלייה", at=(11.6, 16.9))
    return p


# ---- form 2: the entry court --------------------------------------------------------------------------------------

def _night_wing_forward(p, E, YI, parents_y1, strip_y1=9.6):
    """Forms 2 and 3: the night wing comes forward to the front building line (y=3) on the free side. The children at
    the front, the laundry on the east face with a door to the drying yard, then the parents' suite: a short closet
    hall that leads to the en-suite and to the bedroom, in the south-east corner."""
    p.room("kid", "חדר ילד 1", (9.0, 3.25, 11.95, 6.5), at=(10.45, 4.6))
    p.room("mamad", "ממ\"ד\nחדר ילד 2", (12.2, 3.3, 14.95, 6.6), kind="mamad", at=(13.55, 4.4))
    p.room("bath", "מקלחת\nילדים", (9.0, 6.6, 10.75, 8.4), kind="wet", small=True, at=(9.55, 7.0))
    p.room("lobby2", "", (10.85, 6.6, 12.0, 6.85), (10.85, 6.85, 13.1, 8.95), (9.0, 8.5, 10.85, strip_y1),
           (10.85, 8.95, 11.5, strip_y1), kind="circ")
    p.room("laundry", "חדר\nכביסה", (13.2, 6.85, E, 8.95), kind="service", small=True, at=(13.6, 7.25))
    p.room("vest", "ארונות", (11.6, 9.05, 13.1, 11.6), kind="circ", small=True, area_label=False, at=(12.75, 10.5))
    p.room("ensuite", "מקלחת\nהורים", (13.2, 9.05, E, 11.6), kind="wet", small=True, at=(14.15, 10.9))
    p.room("parents", "הורים", (11.6, 11.7, E, parents_y1), at=(13.95, 12.2))
    p.door(11.05, 6.5, 11.85, 6.6, "x0", +1)                     # child 1
    p.door(12.3, 6.6, 13.0, 6.85, "x1", +1, kind="steel")        # mamad: opens out, into the lobby
    p.door(10.75, 7.0, 10.85, 7.7, "y0", -1)                     # children's bath
    p.door(13.1, 7.3, 13.2, 8.0, "y0", +1)                       # laundry
    p.door(E, 7.6, E + 0.25, 8.4, "y1", +1)                      # laundry: out to the drying yard
    p.door(12.3, 8.95, 13.05, 9.05, "x1", +1)                    # the parents' suite
    p.door(13.1, 9.3, 13.2, 10.0, "y0", +1)                      # en-suite, from the parents' closets
    p.door(12.35, 11.6, 13.05, 11.7, "x1", +1)                   # parents' bedroom
    p.window(9.7, 3.0, 11.3, 3.25)                               # child 1
    p.window(13.0, 3.0, 14.2, 3.3)                               # mamad
    p.window(E, 9.7, E + 0.25, 10.9, "high")                     # en-suite
    p.window(E, 12.4, E + 0.25, 14.2)                            # parents, east
    p.window(12.4, parents_y1, 14.2, parents_y1 + 0.25)          # parents, garden
    p.furn("bed", 9.0, 3.25, 9.9, 5.25, head="y0")
    p.furn("desk", 10.55, 3.25, 11.95, 3.85, chair=(11.25, 4.2), face="y0")
    p.furn("wardrobe", 11.35, 4.6, 11.95, 6.3)
    p.furn("bed", 14.05, 3.3, 14.95, 5.3, head="y0")
    p.furn("desk", 12.2, 3.45, 12.8, 4.85, chair=(13.15, 4.15), face="x0")
    p.furn("wardrobe", 12.2, 6.0, 14.2, 6.6)
    p.furn("shower", 9.0, 6.6, 9.9, 7.5)
    p.furn("wc", 9.45, 8.28, face="y0")
    p.furn("basin", 10.3, 7.55, 10.75, 8.35)
    p.furn("counter", 14.4, 6.85, E, 7.45, front="x0", sink=(14.7, 7.15))
    p.furn("tall", 13.2, 8.35, 13.8, 8.95, label="ארון")
    p.furn("washer", 13.8, 8.35, 14.4, 8.95)
    p.furn("washer", 14.4, 8.35, E, 8.95)
    p.mark(14.1, 8.25, "×2", size=0.15, color="#55534d")
    p.furn("wardrobe", 11.6, 9.05, 12.2, 11.6)
    p.furn("shower", 13.85, 9.05, E, 10.25)
    p.furn("wc", 14.55, 11.45, face="y0")
    p.furn("basin", 13.2, 10.35, 13.7, 11.55, n=2)
    p.furn("wardrobe", 11.6, 12.4, 12.2, parents_y1)             # closets: the buffer toward the den
    p.furn("bed", 13.0, 12.65, E, 14.25, head="x1")
    p.furn("crib", 13.8, 14.4, 14.9, min(parents_y1, 15.05) - 0.05, head="x1")


def form_entry_court():
    """2: the entry court. The night wing comes forward to the street on the free side; the day zone sits back,
    behind an entry court on the partners' side. The dining stands in the attached part, between the entry court
    and the back court; the den stays by the living room, as decided in round 3."""
    XW, XN, X1 = TX, 8.75, 15.25
    YF, YD, YS = 3.0, 8.0, 15.5
    S0, S1 = YD, 12.25
    E, YI = X1 - 0.25, YS - 0.25
    p = Plan("2", "חצר כניסה", [(XN, YF, X1, YD), (XW, YD, X1, YS), (0.0, S0, XW, S1)])
    p.room_dims = True
    _night_wing_forward(p, E, YI, YI)
    p.slide(9.2, 9.6, 10.0, 9.7)                                 # the night wing (pocket door), from the passage
    # day zone
    p.room("pantry", "מזווה", (0.25, 8.25, XW, 9.65), kind="service", small=True, at=(1.65, 9.05))
    p.room("wc", "שירותי\nאורחים", (5.55, 8.25, 6.65, 9.7), kind="wet", small=True, at=(6.1, 8.6))
    p.room("den", "חדר עבודה\nואורחים", (8.5, 11.95, 11.5, YI), at=(10.0, 13.75))
    p.room("public", "", (0.25, 9.75, XW, 12.0), (XW, 9.75, 3.25, 12.0), (3.25, 8.25, 5.45, 11.7),
           (5.45, 9.8, 8.8, 11.7), (6.75, 8.25, 8.8, 9.8), (3.25, 11.7, 8.4, YI), (8.8, 9.7, 11.5, 11.85),
           kind="public")
    _labels(p, [(7.8, 9.35, "כניסה", 0.2), (4.35, 9.6, "מטבח", 0.24), (1.6, 11.85, "פינת אוכל", 0.22),
                (6.0, 14.95, "סלון", 0.24)])
    p.door(6.75, YD, 7.75, 8.25, "x1", +1)                       # front door, from the entry court
    p.slide(6.65, 8.75, 6.75, 9.55)                              # guest WC
    p.door(2.2, 9.65, 2.9, 9.75, "x1", -1)                       # pantry, from the dining corner (opens in)
    p.door(9.75, 11.85, 10.45, 11.95, "x1", +1)                  # den, from the passage
    p.slide(8.4, 12.2, 8.5, 14.9)                                # den: a sliding wall to the living room
    p.window(3.4, YD, 4.65, 8.25)                                # kitchen: over the sink, to the entry court
    p.window(5.85, YD, 6.45, 8.25, "high")                       # guest WC
    p.window(0.8, S0, 2.4, 8.25, "high")                         # pantry
    p.window(0.5, 12.0, 2.75, S1, "glass")                       # dining: to the back court
    p.window(XW, 12.55, 3.25, 13.05)                             # living: a narrow window to the back court
    p.window(3.9, YI, 7.9, YS, "glass")                          # living: to the garden
    p.window(9.2, YI, 10.8, YS)                                  # den
    p.furn("wardrobe", 8.2, 8.25, 8.8, 9.6)                      # coats and shoes, against the night wing
    p.furn("wc", 5.85, 9.52, face="y0")
    p.furn("basin", 6.2, 8.28, 6.62, 8.7)
    p.furn("shelf", 0.25, 8.25, XW, 8.6)                         # pantry: open shelves on both long walls
    p.furn("shelf", 0.25, 9.3, 2.1, 9.65)
    p.furn("counter", 3.25, 8.25, 4.75, 8.85, front="y1", sink=(4.0, 8.55))
    p.furn("fridge", 4.75, 8.25, 5.45, 9.0)
    p.furn("island", 3.45, 9.95, 5.45, 10.9, hob=(4.45, 10.42), stools="y1", n=3)
    p.mark(4.45, 10.82, "תנור מתחת", size=0.13, color="#55534d")
    p.furn("table", 0.6, 10.45, 2.6, 11.35, seats=6, ends=True, extend=(0.45, 10.45, 3.75, 11.35))
    p.furn("tv", 3.25, 13.3, 3.65, 14.9)
    p.furn("low", 4.5, 13.6, 5.05, 14.6)
    p.furn("sofa", 5.45, 13.0, 6.4, 15.2, back="x1", seats=3)
    p.furn("armchair", 4.3, 12.15, 5.1, 12.95, back="y0")
    p.furn("desk", 8.5, 11.95, 9.7, 12.55, chair=(9.1, 12.9), face="y0")
    p.furn("desk", 10.9, 12.25, 11.5, 13.65, chair=(10.55, 12.95), face="x1")
    p.furn("sofa", 9.0, 14.35, 11.0, YI, back="y1", seats=2, open=(9.0, 13.65, 11.0, YI))
    p.furn("tall", 10.95, 9.7, 11.5, 11.0, label="ארון")       # a utility closet in the passage
    # outside: the entry court, the back court, the terrace and the garden
    p.yard("paving", 6.9, 1.3, 8.1, 2.4, near=True)
    p.yard("steps", 6.9, 2.4, 8.1, 3.6, along="y", n=4, near=True, up="+y")
    p.yard("paving", 0.35, 0.0, 1.85, 4.0, near=True)
    p.yard("steps", 0.35, 4.0, 1.85, 5.0, along="y", n=4, near=True, up="+y")
    p.yard("paving", 0.35, 5.0, XN, YD, near=True)
    p.yard("paving", 6.85, 3.6, XN, 5.0, near=True)
    p.yard("canopy", 6.3, 6.9, 8.2, YD, near=True)
    p.yard("beds", 3.3, 5.2, 6.4, 5.9, near=True)
    p.yard("tree", 2.0, 6.6, 0.9, near=True)
    p.entry = (7.5, 2.25, "+y")
    p.yard("lawn", 0.0, YS, 18.5, 22.0)
    p.yard("lawn", X1, YF, 18.5, YS)
    p.yard("deck", 0.25, S1, XW, YS, near=True)
    p.yard("deck", XW, YS, 8.4, YS + 3.5, near=True)
    p.yard("pergola", 0.25, S1, XW, YS, near=True)
    p.yard("pergola", XW, YS, 8.4, YS + 3.5, near=True, label="מרפסת ופרגולה", at=(5.7, YS + 3.2))
    p.yard("outkitchen", 7.3, YS + 3.55, 8.4, YS + 4.3, near=True, label="טאבון", at=(7.85, YS + 4.75))
    p.yard("service", X1, 6.4, 17.6, 9.6, near=True, label="חצר תלייה", at=(16.4, 8.1))
    p.yard("hedge", X1, 6.15, 17.85, 6.4, near=True)
    p.yard("hedge", 17.6, 6.4, 17.85, 9.85, near=True)
    p.yard("hedge", X1, 9.6, 17.85, 9.85, near=True)
    p.yard("hedge", -0.1, YS + 0.2, 0.15, 21.8)
    p.yard("hedge", -0.1, 5.2, 0.15, S0, near=True)
    p.yard("service", 16.55, 8.55, 17.45, 9.35, near=True, label="גז", at=(17.0, 9.05))
    p.yard("beds", 15.65, 10.6, 18.1, 15.0, label="ערוגות ירק")
    p.yard("tree", 2.2, 19.8, 1.3)
    p.mark(14.0, 19.2, "דשא 9 × 6.5", size=0.24, color="#55704a")
    p.dim(XN, YF, X1, YF, off=-0.9, text=f"{X1 - XN:.2f}")
    p.dim(X1, YF, X1, YS, off=0.75, text=f"{YS - YF:.2f}")
    p.dim(XW, YS, X1, YS, off=0.9, text=f"{X1 - XW:.2f}")
    p.dim(0.0, S0, XW, S0, off=-0.45, text="3.00")
    # roof: tiles over the day zone; flat over the night wing and the attached part
    p.roof_area("tile", XW, YD, XN, YS, slope="gable-x")
    p.roof_area("flat", XN, YF, X1, YS)
    p.roof_area("flat", 0.0, S0, XW, S1)
    # walks
    p.route("alarm", (13.6, 12.9), (12.75, 12.2), (12.7, 11.4), (12.6, 9.6), (12.65, 8.3), (12.65, 7.0),
            name="הורים", at=(13.6, 13.35))
    p.route("alarm", (9.6, 4.6), (11.45, 6.2), (11.6, 7.4), (12.65, 7.6), (12.65, 7.0), name="ילד1",
            at=(9.6, 5.05))
    p.route("alarm", (9.3, 13.4), (10.1, 12.4), (10.1, 11.4), (9.6, 10.2), (9.6, 9.2), (11.5, 8.0),
            (12.65, 7.6), (12.65, 7.0), name="אורחים", at=(9.3, 13.85))
    p.route("groceries", (5.6, 0.6), (7.3, 1.85), (7.3, 3.6), (7.25, 8.4), (6.9, 9.8), (5.4, 9.6), (5.1, 9.2),
            name="קניות", at=(5.6, 0.35))
    p.route("guest", (7.25, 8.4), (7.0, 9.25), name="שירותים", at=(8.9, 7.6))
    p.route("laundry", (13.6, 12.9), (12.75, 12.2), (12.7, 11.4), (12.6, 9.6), (12.9, 8.1), (13.5, 7.65),
            name="כביסה", at=(13.6, 13.8))
    p.route("laundry", (14.0, 7.7), (15.4, 8.0), (16.4, 7.9), name="תלייה", at=(16.4, 6.95))
    return p


# ---- form 3: the patio, chosen by the user ------------------------------------------------------------------------

def _patio_stair(p, x0, y0, x1, y1, w=0.9):
    """The stair to the roof terrace, in the patio (the user, round 4; the place is my recommendation): three winders
    in the north-west corner, a flight along the wall of the bedroom lobby, three winders in the north-east corner,
    and a flight along the blank wall of the parents' closets that arrives on the roof over the den. 19 risers of
    about 17.5 cm for about 3.3 m, 0.9 m wide. The den's window stays clear: the stair passes above it."""
    xa, xb, yb = x0 + w, x1 - w, y0 + w
    n_n, n_e = 4, 8                                  # treads in the two flights; with the six winders, 18 treads
    gn, ge = (xb - xa) / n_n, (y1 - yb) / n_e
    t = w * math.tan(math.radians(30))               # the winders turn 30 degrees each
    lines = [(xa, yb, x0, yb - t), (xa, yb, xa - t, y0)]
    lines += [(xa + i * gn, y0, xa + i * gn, yb) for i in range(n_n + 1)]
    lines += [(xb, yb, xb + t, y0), (xb, yb, x1, yb - t)]
    lines += [(xb, yb + i * ge, x1, yb + i * ge) for i in range(n_e)]
    r = w / 2                                        # the walking line, along the middle of the stair
    turn = [math.radians(a) for a in range(0, 91, 15)]
    walk = [(xa - r * math.cos(a), yb - r * math.sin(a)) for a in turn]
    walk += [(xb + r * math.sin(a), yb - r * math.cos(a)) for a in turn] + [(xb + r, y1 - 0.12)]
    p.yard("stair", x0, y0, x1, y1, near=True, roof=True, lines=lines, walk=walk,
           poly=[(x0, y0), (x1, y0), (x1, y1), (xb, y1), (xb, yb), (x0, yb)],
           rail=[(xa, yb - 0.05), (xb + 0.05, yb - 0.05), (xb + 0.05, y1)],
           label="עולה לגג", at=(xa, yb + 0.27), size=0.13)
    p.gaps.append((xb, y1 - 0.1, x1, y1 + 0.3))      # the railing on the roof opens where the stair arrives


ROOF_H = 3.3   # from the floor to the roof terrace: a 2.75 m ceiling, the slab and the roof build-up (round 4)


def _patio_stair_l(p, x1, y0, y1, w=0.9, n1=5, n2=14, t=0.27):
    """Model 3ב (the user, 5.10.2026): the climb starts facing east, as the user suggested. Five risers east along the
    patio's south wall, below the sill of the work corner's window; a landing in the south-east corner; fourteen
    risers north along the blank east wall, onto the roof over the bedroom hall. 19 risers of about 17.4 cm for about
    3.3 m, treads of 27 cm (2R+T about 62), 0.9 m wide: the regulations allow risers up to 17.5 cm and need a landing
    (docs/07-design-research.md, 4.6). All of it inside the patio."""
    xa, yl = x1 - w, y1 - w                          # the landing: xa..x1, yl..y1
    xf, ytop = xa - (n1 - 1) * t, yl - (n2 - 1) * t  # the first riser (west) and the last one (north)
    lines = [(xf + i * t, yl, xf + i * t, y1) for i in range(n1)]
    lines += [(xa, yl - j * t, x1, yl - j * t) for j in range(n2)]
    xm, ym = xa + w / 2, yl + w / 2
    rise = ROOF_H / (n1 + n2)                        # for the 3D view: the treads (x0, y0, x1, y1, top) and the rails
    steps3d = [(xf + i * t, yl, xf + (i + 1) * t, y1, (i + 1) * rise) for i in range(n1 - 1)]
    steps3d.append((xa, yl, x1, y1, n1 * rise))
    steps3d += [(xa, yl - (j + 1) * t, x1, yl - j * t, (n1 + 1 + j) * rise) for j in range(n2 - 1)]
    rails3d = [[(xf + 0.25, yl - 0.05, rise + 0.9), (xa - 0.05, yl - 0.05, n1 * rise + 0.9),
                (xa - 0.05, ytop + 0.1, (n1 + n2 - 1) * rise + 0.9)]]
    p.yard("stair", xf, ytop, x1, y1, near=True, roof=True, lines=lines, steps3d=steps3d, rails3d=rails3d,
           walk=[(xf + 0.13, ym), (xm - 0.2, ym), (xm, ym - 0.2), (xm, ytop + 0.1)],
           poly=[(xf, yl), (xa, yl), (xa, ytop), (x1, ytop), (x1, y1), (xf, y1)],
           rail=[(xf + 0.25, yl - 0.05), (xa - 0.05, yl - 0.05), (xa - 0.05, ytop + 0.1)],
           label="עולה לגג", at=(xf - 0.42, yl + 0.35), size=0.13,
           spec=dict(height=ROOF_H, risers=n1 + n2, tread=t, flights=[n1, n2], width=w, landing=w))
    p.gaps.append((xa, ytop - 0.45, x1, ytop + 0.1))  # the railing on the roof opens where the stair arrives


def form_patio():
    """3: the patio, chosen by the user (5.10.2026). Form 2, with a patio at the hinge between the entry, the living
    room, the den and the night wing; the house is 0.75 m deeper, so the built area stays about the same.

    Round 1 of comments (the user, 5.10.2026): "the kitchen is small".
    - The guest WC moves to the other side of the front door, where the coat cabinet was. So that the door to the
      night wing stays, it reaches 1.15 m into the entry court. A short wall by the ovens and a 0.9 m opening from the
      entry keep its door out of sight of the island, the table and the sofa.
    - In its place the kitchen grows: a longer counter by the sink, then the fridge, then a tall cabinet with the
      oven, and above it a compact oven with a microwave, at heights you do not bend for.
    - The pantry keeps one row of shelves. In place of the other, a shallow cabinet wall faces the dining corner,
      and the pantry door looks like one of its doors.
    - An entry cabinet outside, under the canopy: the electrical cabinet, a fire extinguisher and shoes.
    - The island: drawers on the cook's side, knee space on the seating side, and a fourth stool at its end.

    Rounds 2-3: an L kitchen, one straight cabinet wall, the entry cabinet turned to flank the porch, and the wall
    toward the patio cut back. Over the porch a pergola of concrete columns and beams, with no ceiling; the
    covering comes later.

    Round 4: a stair from the patio to a roof terrace (the user): the flat roof over the bedroom side, with a railing
    all around; the tiles stay over the day zone. The stair's place is my recommendation (_patio_stair).
    """
    XW, XN, X1 = TX, 8.75, 15.25
    YF, YD, YS = 3.0, 8.0, 16.25
    S0, S1 = YD, 12.25
    PX0, PX1, PY0, PY1 = 8.5, 11.35, 9.7, 12.7          # the patio, open to the sky
    E, YI = X1 - 0.25, YS - 0.25
    p = Plan("3", "פטיו", [(XN, YF, X1, YD), (7.65, 6.85, XN, YD), (XW, YD, X1, PY0), (XW, PY0, PX0, PY1),
                           (PX1, PY0, X1, PY1), (XW, PY1, X1, YS), (0.0, S0, XW, S1)])
    p.room_dims = True
    _night_wing_forward(p, E, YI, YI, strip_y1=9.45)
    p.slide(XN, 8.7, 9.0, 9.4)                                   # the night wing (pocket door), from the entry
    # the patio: the stair to the roof takes the place of the two beds along the north and east walls (round 4)
    p.yard("paving", PX0, PY0, PX1, PY1, near=True, roof=True)
    p.yard("tree", PX0 + 1.0, PY1 - 1.0, 0.75, near=True, roof=True)
    _patio_stair(p, PX0, PY0, PX1, PY1)
    _labels(p, [(PX0 + 0.95, PY1 - 0.95, "פטיו", 0.24)])
    # the entry: the front door, the guest WC on its other side, and a wide opening into the day zone. The wall toward
    # the patio is cut back to the patio's corner (round 3), so the entry sees the patio; the WC door is a hidden door
    p.room("wc", "שירותי\nאורחים", (7.9, 7.1, XN, 8.5), kind="wet", small=True, at=(8.32, 7.95))
    p.room("lobby", "מבואה", (6.65, 8.25, 7.8, 8.6), (6.65, 8.6, XN, 9.45), (6.65, 9.45, PX0 - 0.25, 9.8),
           kind="circ", small=True, at=(7.75, 9.2))
    p.door(6.65, YD, 7.55, 8.25, "x1", +1)                       # front door: when open, it hides the WC door
    p.slide(7.95, 8.5, 8.65, 8.6)                                # guest WC: a hidden door, in the colour of the wall
    p.mark(8.3, 8.78, "דלת נסתרת", size=0.12, color="#55534d")
    p.gap(6.65, 9.75, PX0 - 0.25, 9.85)                          # from the entry into the day zone
    p.window(8.1, 6.85, 8.55, 7.1, "high")                       # guest WC
    p.furn("wc", 8.47, 7.19, face="y1")
    p.furn("basin", 7.9, 7.12, 8.2, 7.45)
    # the pantry: one row of shelves; toward the dining corner one straight run of shallow cabinets, and the pantry
    # door is the last door of the run, flush with the others: from outside it is one long cabinet
    p.room("pantry", "מזווה", (0.25, 8.25, XW, 9.25), kind="service", small=True, at=(1.6, 8.8))
    p.door(2.3, 9.25, XW, 9.7, "x1", +1)                         # pantry: its door is a cabinet door
    p.furn("shelf", 0.25, 8.25, XW, 8.6)
    p.furn("tall", 0.25, 9.35, 2.3, 9.7, label="ארונות")
    p.mark(2.65, 9.95, "דלת נסתרת", size=0.13, color="#55534d")
    # the kitchen, an L (the user): the counter by the sink and the fridge along the north wall; on the short leg,
    # along the entry wall, a tall corner cabinet with the microwave (a diagonal door) and the oven tower
    p.furn("counter", 3.25, 8.25, 5.2, 8.85, front="y1", sink=(4.2, 8.55))
    p.furn("fridge", 5.2, 8.25, 5.95, 9.0)
    p.furn("tall", 5.95, 8.25, 6.55, 8.85, label="מיקרוגל")
    p.furn("tall", 5.95, 8.85, 6.55, 9.45, label="תנורים")
    p.furn("island", 3.45, 10.2, 5.65, 11.2, hob=(4.55, 10.52), stools="y1", n=3, overhang=0.4)
    p.furn("stool", 5.92, 10.7)
    # the rest of the day zone (as before)
    p.room("den", "חדר עבודה\nואורחים", (8.5, 12.95, 11.5, YI), at=(10.0, 14.6))
    p.room("public", "", (0.25, 9.7, XW, 12.0), (0.25, 9.35, 2.3, 9.7), (XW, 9.7, 3.25, 12.0),
           (3.25, 8.25, 6.55, 9.8), (3.25, 9.8, 8.25, 11.7), (3.25, 11.7, 8.25, YI), (8.25, 12.95, 8.4, YI),
           kind="public")
    _labels(p, [(4.3, 9.65, "מטבח", 0.24), (1.1, 10.08, "פינת אוכל", 0.2), (5.4, 15.7, "סלון", 0.24)])
    p.slide(8.4, 13.15, 8.5, 15.75)                              # den: a sliding wall to the living room
    # glass to the patio
    p.window(8.25, 10.0, PX0, 12.45, "glass")                    # living room: a sliding glass door
    p.window(9.2, 9.45, 10.85, PY0)                              # bedroom lobby
    p.window(8.9, PY1, 11.1, 12.95)                              # den
    # other windows
    p.window(3.55, YD, 4.85, 8.25)                               # kitchen: over the sink, to the entry court
    p.window(0.8, S0, 2.4, 8.25, "high")                         # pantry
    p.window(0.5, 12.0, 2.75, S1, "glass")                       # dining: to the back court
    p.window(XW, 12.55, 3.25, 13.05)                             # living: to the back court
    p.window(3.9, YI, 7.9, YS, "glass")                          # living: to the garden
    p.window(9.2, YI, 10.8, YS)                                  # den
    p.furn("table", 0.6, 10.65, 2.6, 11.55, seats=6, ends=True, extend=(0.45, 10.65, 3.2, 11.55))
    p.furn("tv", 3.25, 13.8, 3.65, 15.4)
    p.furn("low", 4.5, 14.1, 5.05, 15.1)
    p.furn("sofa", 5.45, 13.5, 6.4, 15.7, back="x1", seats=3)
    p.furn("armchair", 4.3, 12.4, 5.1, 13.2, back="y0")
    p.furn("desk", 10.9, 13.2, 11.5, 14.6, chair=(10.55, 13.9), face="x1")
    p.furn("desk", 8.6, 14.95, 10.0, YI, chair=(9.3, 14.6), face="y1")
    p.furn("sofa", 8.6, 12.95, 10.6, 13.85, back="y0", seats=2, open=(8.6, 12.95, 10.6, 14.55))
    # outside: the entry court with the entry cabinet, the back court, the terrace and the garden
    p.yard("paving", 6.9, 1.3, 8.1, 2.4, near=True)
    p.yard("steps", 6.9, 2.4, 8.1, 3.6, along="y", n=4, near=True, up="+y")
    p.yard("paving", 0.35, 0.0, 1.85, 4.0, near=True)
    p.yard("steps", 0.35, 4.0, 1.85, 5.0, along="y", n=4, near=True, up="+y")
    p.yard("paving", 0.35, 5.0, XN, YD, near=True)
    p.yard("paving", 6.85, 3.6, XN, 5.0, near=True)
    p.yard("outkitchen", 6.0, 6.85, 6.55, YD, near=True)          # the entry cabinet, along the porch, doors to it
    # over the porch a pergola (the user, round 3): concrete columns and beams only, no concrete ceiling. A beam
    # between the two columns, and from each column a beam to the house wall: over the entry cabinet, and along the
    # WC. The covering (wood, polycarbonate or other) is laid on the beams later.
    p.yard("beam", 6.0, 5.9, 7.65, 6.15, near=True)
    p.yard("beam", 6.0, 6.15, 6.25, YD, near=True)
    p.yard("beam", 7.4, 6.15, 7.65, YD, near=True)
    p.yard("column", 6.0, 5.9, 6.25, 6.15, near=True)
    p.yard("column", 7.4, 5.9, 7.65, 6.15, near=True)
    p.mark(7.15, 5.6, "עמודים וקורות בטון", size=0.14, color="#55534d")
    p.mark(6.83, 6.55, "קירוי בהמשך", size=0.12, color="#55534d")
    p.mark(5.3, 7.35, "ארון כניסה", size=0.15, color="#1d1d1b")
    p.mark(5.3, 7.6, "חשמל · מטף · נעליים", size=0.13, color="#55534d")
    p.yard("beds", 3.3, 5.2, 6.4, 5.9, near=True)
    p.yard("tree", 2.0, 6.6, 0.9, near=True)
    p.entry = (7.5, 2.25, "+y")
    p.yard("lawn", 0.0, YS, 18.5, 22.0)
    p.yard("lawn", X1, YF, 18.5, YS)
    p.yard("deck", 0.25, S1, XW, YS, near=True)
    p.yard("deck", XW, YS, 8.4, YS + 3.25, near=True)
    p.yard("pergola", 0.25, S1, XW, YS, near=True)
    p.yard("pergola", XW, YS, 8.4, YS + 3.25, near=True, label="מרפסת ופרגולה", at=(5.7, YS + 2.95))
    p.yard("outkitchen", 7.3, YS + 3.3, 8.4, YS + 4.05, near=True, label="טאבון", at=(7.85, YS + 4.5))
    p.yard("service", X1, 6.4, 17.6, 9.6, near=True, label="חצר תלייה", at=(16.4, 8.1))
    p.yard("hedge", X1, 6.15, 17.85, 6.4, near=True)
    p.yard("hedge", 17.6, 6.4, 17.85, 9.85, near=True)
    p.yard("hedge", X1, 9.6, 17.85, 9.85, near=True)
    p.yard("hedge", -0.1, YS + 0.2, 0.15, 21.8)
    p.yard("hedge", -0.1, 5.2, 0.15, S0, near=True)
    p.yard("service", 16.55, 8.55, 17.45, 9.35, near=True, label="גז", at=(17.0, 9.05))
    p.yard("beds", 15.65, 10.6, 18.1, 15.0, label="ערוגות ירק")
    p.yard("tree", 2.2, 19.8, 1.3)
    p.mark(14.0, 19.6, "דשא 9 × 5.75", size=0.24, color="#55704a")
    p.dim(XN, YF, X1, YF, off=-0.9, text=f"{X1 - XN:.2f}")
    p.dim(X1, YF, X1, YS, off=0.75, text=f"{YS - YF:.2f}")
    p.dim(XW, YS, X1, YS, off=0.9, text=f"{X1 - XW:.2f}")
    p.dim(0.0, S0, XW, S0, off=-0.45, text="3.00")
    # the roof (the user, round 4): tiles over the day zone; over the bedroom side a terrace with a railing all
    # around, the patio's edges too; the low roof over the attached part stays a plain flat roof
    p.roof_area("tile", XW, YD, PX0, YS, slope="gable-x")
    terrace = [(XN, YF, X1, YD), (7.65, 6.85, XN, YD), (PX0, YD, X1, PY0), (PX1, PY0, X1, YS), (PX0, PY1, PX1, YS)]
    for r in terrace:
        p.roof_area("terrace", *r)
    p.roof_area("flat", 0.0, S0, XW, S1)
    p.mark(12.1, 5.25, "מרפסת גג", size=0.36, color="#1d1d1b", bold=True, roof=True)
    p.mark(12.1, 5.7, f"{sum((r[2] - r[0]) * (r[3] - r[1]) for r in terrace):.0f} מ\"ר, מעקה מסביב",
           size=0.22, color="#55534d", roof=True)
    p.mark(PX1 - 0.45, PY1 + 0.55, "מגיעים מהפטיו", size=0.2, color="#55534d", roof=True)
    p.route("alarm", (13.6, 12.9), (12.75, 12.2), (12.7, 11.4), (12.6, 9.6), (12.65, 8.3), (12.65, 7.0),
            name="הורים", at=(13.6, 13.35))
    p.route("alarm", (9.6, 4.6), (11.45, 6.2), (11.6, 7.4), (12.65, 7.6), (12.65, 7.0), name="ילד1",
            at=(9.6, 5.05))
    p.route("alarm", (9.3, 14.2), (8.0, 13.6), (7.2, 11.0), (7.1, 9.6), (8.3, 9.05), (9.4, 9.05), (11.5, 8.0),
            (12.65, 7.6), (12.65, 7.0), name="אורחים", at=(9.3, 14.65))
    p.route("groceries", (5.6, 0.6), (7.3, 1.85), (7.3, 3.6), (7.1, 8.4), (7.1, 9.95), (6.2, 9.9), (5.6, 9.35),
            name="קניות", at=(5.6, 0.35))
    p.route("guest", (7.1, 8.4), (7.75, 8.75), (8.3, 8.7), name="שירותים", at=(6.2, 7.6))
    p.route("laundry", (13.6, 12.9), (12.75, 12.2), (12.7, 11.4), (12.6, 9.6), (12.9, 8.1), (13.5, 7.65),
            name="כביסה", at=(13.6, 13.8))
    p.route("laundry", (14.0, 7.7), (15.4, 8.0), (16.4, 7.9), name="תלייה", at=(16.4, 6.95))
    return p


# ---- model 3ב: form 3 made smaller for the budget, and model 3ג: its work corner and patio swapped -----------------

def _patio_stair_straight(p, x1, ytop, w=0.9, n1=10, n2=9, t=0.27, landing=1.2, open_from=None):
    """Model 3ג (5.10.2026): the patio opens to the garden, so the stair climbs from the garden, straight, along the
    parents' blank wall, onto the roof over the work corner. 19 risers of about 17.4 cm and treads of 27 cm, in two
    flights (n1 below, n2 above) with a 1.2 m landing, as the regulations want between flights in the same direction
    (docs/07-design-research.md, 4.6). It starts about a meter out in the garden. open_from: below this y the east
    side has no wall, so a rail."""
    xa = x1 - w
    yl1 = ytop + (n2 - 1) * t                        # the landing: yl1..yl2
    yl2 = yl1 + landing
    yb = yl2 + (n1 - 1) * t                          # the first riser, in the garden
    lines = [(xa, yb - i * t, x1, yb - i * t) for i in range(n1)]
    lines += [(xa, yl1 - j * t, x1, yl1 - j * t) for j in range(n2)]
    xm = xa + w / 2
    rails = [[(xa + 0.05, yb - 0.1), (xa + 0.05, ytop + 0.1)]]
    rise = ROOF_H / (n1 + n2)                        # for the 3D view: the treads (x0, y0, x1, y1, top) and the rails
    steps3d = [(xa, yb - (i + 1) * t, x1, yb - i * t, (i + 1) * rise) for i in range(n1 - 1)]
    steps3d.append((xa, yl1, x1, yl2, n1 * rise))
    steps3d += [(xa, yl1 - (j + 1) * t, x1, yl1 - j * t, (n1 + 1 + j) * rise) for j in range(n2 - 1)]
    up = [(yb - 0.1, rise + 0.9), (yl2, n1 * rise + 0.9), (yl1, n1 * rise + 0.9), (ytop + 0.1, (n1 + n2 - 1) * rise + 0.9)]
    rails3d = [[(xa + 0.05, y, z) for y, z in up]]
    if open_from is not None:                        # it ends on the landing, where the parents' wall begins
        rails.append([(x1 - 0.05, yb - 0.1), (x1 - 0.05, open_from)])
        rails3d.append([(x1 - 0.05, y, z) for y, z in up[:2]] + [(x1 - 0.05, open_from, n1 * rise + 0.9)])
    p.yard("stair", xa, ytop, x1, yb, near=True, roof=True, lines=lines, steps3d=steps3d, rails3d=rails3d,
           walk=[(xm, yb - 0.13), (xm, ytop + 0.1)],
           poly=[(xa, ytop), (x1, ytop), (x1, yb), (xa, yb)], rails=rails,
           label="עולה לגג", at=(xa - 0.45, yb - 0.15), size=0.13,
           spec=dict(height=ROOF_H, risers=n1 + n2, tread=t, flights=[n1, n2], width=w, landing=landing,
                     straight=True))
    p.gaps.append((xa, ytop - 0.45, x1, ytop + 0.1))  # the railing on the roof opens where the stair arrives


def _model_3b(swap=False):
    """The day zone, the night wing and the parents are the same in 3ב and 3ג; swap=True gives 3ג."""
    XW, XN, X1 = TX, 8.75, 15.25
    YF, YD, YS = 3.0, 8.0, 16.25
    S0, S1 = YD, 12.25
    PX0, PX1, PY0, PY1 = 8.5, 11.35, 9.7, 14.15          # 3ב: the patio, open to the sky: 2.85 × 4.45 m
    E, YI = X1 - 0.25, YS - 0.25
    YP = 14.6                                            # the parents' south wall, outside: the corner steps back
    WY = 11.55                                           # 3ג: the work corner's south wall, outside
    if not swap:
        p = Plan("3ב", "פטיו, מוקטן", [(XN, YF, X1, YD), (7.65, 6.85, XN, YD), (XW, YD, X1, PY0),
                                       (XW, PY0, PX0, PY1), (PX1, PY0, X1, YP), (XW, PY1, PX1, YS), (PX1, YP, 11.6, YS),
                                       (0.0, S0, XW, S1)])
    else:
        p = Plan("3ג", "פטיו לגינה", [(XN, YF, X1, YD), (7.65, 6.85, XN, YD), (XW, YD, X1, PY0),
                                      (XW, PY0, PX1, WY), (XW, WY, PX0, YS), (PX1, PY0, X1, YP), (0.0, S0, XW, S1)])
    p.room_dims = True
    # the night wing, at the front as in form 3: the children, the mamad and the children's bath
    p.room("kid", "חדר ילד 1", (9.0, 3.25, 11.95, 6.5), at=(10.45, 4.6))
    p.room("mamad", "ממ\"ד\nחדר ילד 2", (12.2, 3.3, 14.95, 6.6), kind="mamad", at=(13.45, 4.75))
    p.room("bath", "מקלחת\nילדים", (9.0, 6.6, 10.75, 8.4), kind="wet", small=True, at=(9.55, 7.0))
    p.room("lobby2", "", (10.85, 6.6, 12.0, 6.85), (10.85, 6.85, 13.1, 8.45), (9.0, 8.5, 10.85, 9.45),
           (10.85, 8.45, 11.5, 9.45), kind="circ")
    p.door(11.05, 6.5, 11.85, 6.6, "x0", +1)                     # child 1
    p.door(12.3, 6.6, 13.0, 6.85, "x1", +1, kind="steel")        # mamad: opens out, into the hall
    p.door(10.75, 6.7, 10.85, 7.4, "y0", -1)                     # children's bath: clear of the basin (the checks)
    p.window(9.7, 3.0, 11.3, 3.25)                               # child 1
    p.window(13.0, 3.0, 14.2, 3.3)                               # mamad
    p.furn("bed", 9.0, 3.25, 9.9, 5.25, head="y0")
    p.furn("desk", 10.55, 3.25, 11.95, 3.85, chair=(11.25, 4.2), face="y0")
    p.furn("wardrobe", 11.35, 4.6, 11.95, 6.3)
    p.furn("bed", 14.05, 3.3, 14.95, 5.3, head="y0")
    p.furn("desk", 12.2, 3.45, 12.8, 4.85, chair=(13.15, 4.15), face="x0")
    p.furn("wardrobe", 12.2, 6.0, 14.2, 6.6)
    p.furn("shower", 9.0, 6.6, 9.9, 7.5)
    p.furn("wc", 9.45, 8.28, face="y0")
    p.furn("basin", 10.3, 7.55, 10.75, 8.35)
    p.slide(XN, 8.7, 9.0, 9.4)                                   # the night wing (pocket door), from the entry
    # the laundry (3): two machines, one above the other, the sink and a storage column, in one row along the south
    # wall; the doors to the hall and to the drying yard face each other along the north wall
    p.room("laundry", "חדר\nכביסה", (13.2, 6.85, E, 8.45), kind="service", small=True, at=(14.6, 7.02))
    p.door(13.1, 6.95, 13.2, 7.7, "y0", +1)                      # laundry, from the hall
    p.door(E, 6.95, E + 0.25, 7.75, "y0", +1)                    # laundry: out to the drying yard
    p.furn("tall", 13.2, 7.85, 13.8, 8.45, label="ארון")
    p.furn("washer", 13.8, 7.85, 14.4, 8.45)
    p.mark(14.08, 7.8, "×2", size=0.15, color="#55534d")
    p.furn("counter", 14.4, 7.85, E, 8.45, front="y0", sink=(14.7, 8.15))
    # the parents (1, 2): the door from the hall into a passage along the patio wall, where the closets of the
    # vestibule were; the en-suite across the suite, its door in the passage; the passage opens into the bedroom
    p.room("pass", "", (11.6, 8.55, 12.6, 10.55), kind="circ", area_label=False)
    p.room("ensuite", "מקלחת הורים", (12.7, 8.55, E, 10.55), kind="wet", small=True, at=(13.4, 9.52))
    p.room("parents", "הורים", (11.6, 10.65, E, 14.35), at=(13.95, 13.75))
    p.door(11.75, 8.45, 12.55, 8.55, "x0", +1)                   # the parents' door, from the hall
    p.door(12.6, 8.75, 12.7, 9.45, "y0", +1)                     # en-suite, from the passage: not seen from the bed
    p.gap(11.6, 10.55, 12.6, 10.65)                              # the passage opens into the bedroom, no door
    p.window(E, 9.0, E + 0.25, 10.2, "high")                     # en-suite, over the shower
    p.window(E, 13.45, E + 0.25, 14.25)                          # parents, east: beside the bed, not behind its head
    p.window(12.4, 14.35, 14.2, YP)                              # parents, garden
    p.furn("shower", 14.1, 8.55, E, 10.55)
    p.furn("wc", 13.85, 8.64, face="y1")
    p.furn("basin", 12.8, 10.05, 14.0, 10.55, n=2)
    p.furn("wardrobe", 11.6, 11.55, 12.2, 14.35)                 # one closet wall, 2.8 m
    p.furn("bed", 13.0, 11.7, E, 13.3, head="x1")
    if not swap:
        # the patio (4, 5): longer, over half of the den; the stair in an L along its south wall and blank east wall
        p.yard("paving", PX0, PY0, PX1, PY1, near=True, roof=True)
        p.yard("tree", 9.45, 11.3, 0.75, near=True, roof=True)
        _patio_stair_l(p, PX1, PY0, PY1)
        _labels(p, [(9.45, 11.35, "פטיו", 0.24)])
    else:
        # the patio (3ג): from the work corner to the garden, open on its south side. The stair from the garden
        p.yard("paving", PX0, WY, PX1, YS, near=True, roof=True)
        p.yard("tree", 9.45, 13.35, 0.75, near=True, roof=True)
        _patio_stair_straight(p, PX1, WY, open_from=YP)
        _labels(p, [(9.45, 13.4, "פטיו", 0.24)])
    # the entry and the pantry: as in form 3. The guest WC (the checks): the WC was 0.28 m from the side wall, with
    # the basin beside it in a 0.85 m room. Now the WC is in the middle of the back wall, and a hand basin on the side
    p.room("wc", "שירותי\nאורחים", (7.9, 7.1, XN, 8.5), kind="wet", small=True, at=(8.2, 8.02), dims=False)
    p.room("lobby", "מבואה", (6.65, 8.25, 7.8, 8.6), (6.65, 8.6, XN, 9.45), (6.65, 9.45, PX0 - 0.25, 9.8),
           kind="circ", small=True, at=(7.75, 9.2))
    p.door(6.65, YD, 7.55, 8.25, "x1", +1)                       # front door: when open, it hides the WC door
    p.slide(7.95, 8.5, 8.65, 8.6)                                # guest WC: a hidden door, in the colour of the wall
    p.mark(8.3, 8.78, "דלת נסתרת", size=0.12, color="#55534d")
    p.gap(6.65, 9.75, PX0 - 0.25, 9.85)                          # from the entry into the day zone
    p.window(8.1, 6.85, 8.55, 7.1, "high")                       # guest WC
    p.furn("wc", 8.325, 7.19, face="y1")                        # 0.42 m from each side wall
    p.furn("basin", 8.53, 8.05, 8.75, 8.45)                      # a hand basin on the side wall, by the door
    p.room("pantry", "מזווה", (0.25, 8.25, XW, 9.25), kind="service", small=True, at=(1.6, 8.8))
    p.door(2.3, 9.25, XW, 9.7, "x1", +1)                         # pantry: its door is a cabinet door
    p.furn("shelf", 0.25, 8.25, XW, 8.6)
    p.furn("tall", 0.25, 9.35, 2.3, 9.7, label="ארונות")
    p.mark(2.65, 9.95, "דלת נסתרת", size=0.13, color="#55534d")
    p.waive = {"label-door|דלת נסתרת": "the label names the door it stands by",
               "wc-front|0.76 m": "the guest WC is 1.40 m long: 0.70 m in front of the WC, 0.76 is common (07, 2.4)"}
    # the kitchen: as in form 3
    p.furn("counter", 3.25, 8.25, 5.2, 8.85, front="y1", sink=(4.2, 8.55))
    p.furn("fridge", 5.2, 8.25, 5.95, 9.0)
    p.furn("tall", 5.95, 8.25, 6.55, 8.85, label="מיקרוגל")
    p.furn("tall", 5.95, 8.85, 6.55, 9.45, label="תנורים")
    p.furn("island", 3.45, 10.2, 5.65, 11.2, hob=(4.55, 10.52), stools="y1", n=3, overhang=0.4)
    p.furn("stool", 5.92, 10.7)
    public = [(0.25, 9.7, XW, 12.0), (0.25, 9.35, 2.3, 9.7), (XW, 9.7, 3.25, 12.0), (3.25, 8.25, 6.55, 9.8),
              (3.25, 9.8, 8.25, 11.7), (3.25, 11.7, 8.25, YI)]
    if not swap:
        # the work corner (4): half of the den, a long desk for two facing the garden; glass to the patio, and toward
        # the living room a glass partition with a door-wide opening and no door (the user). No sofa bed.
        p.room("den", "פינת עבודה", (PX0, 14.4, PX1, YI), at=(9.95, 14.66))
        p.room("public", "", *public, (8.25, 14.4, 8.4, YI), kind="public")
    else:
        # the work corner (3ג, the user): by the corridor to the bedrooms, behind the night wing's door; glass along
        # the corridor with a door-wide opening and no door, so the patio's light reaches the corridor through it.
        # A long desk for two, facing the patio
        p.room("den", "פינת עבודה", (PX0, PY0, PX1, 11.3), at=(9.95, 9.98))
        p.room("public", "", *public, kind="public")
    _labels(p, [(4.3, 9.65, "מטבח", 0.24), (1.1, 10.08, "פינת אוכל", 0.2), (4.75, 15.75, "סלון", 0.24)])
    if not swap:
        p.gap(8.4, 14.45, 8.5, 15.3)                             # the work corner: a door-wide opening, no door
        p.window(8.4, 15.3, 8.5, YI)                             # and a glass partition
        p.window(8.7, PY1, 11.15, 14.4)                          # work corner: glass to the patio
        p.window(9.2, YI, 10.8, YS)                              # work corner: to the garden
        p.furn("desk", 8.55, 15.3, 9.95, YI, chair=(9.25, 14.97), face="y1")
        p.furn("desk", 9.95, 15.3, 11.3, YI, chair=(10.62, 14.97), face="y1")
        # glass to the patio, longer now
        p.window(8.25, 10.0, PX0, 13.9, "glass")                 # living room: sliding glass, about 3.9 m
        p.window(9.2, 9.45, 10.85, PY0)                          # bedroom hall
    else:
        p.gap(9.55, 9.45, 10.35, PY0)                            # from the corridor: a door-wide opening, no door
        p.window(9.05, 9.45, 9.5, PY0)                           # and glass along the corridor, on both sides of it
        p.window(10.4, 9.45, 11.3, PY0)
        p.window(8.7, 11.3, 11.15, WY)                           # work corner: glass to the patio
        p.furn("desk", 8.55, 10.6, 11.3, 11.3)
        p.furn("chair", 9.25, 10.27, face="y1")
        p.furn("chair", 10.62, 10.27, face="y1")
        p.window(8.25, 11.8, PX0, 15.75, "glass")                # living room: sliding glass to the patio, about 4 m
    # other windows of the day zone: as in form 3
    p.window(3.55, YD, 4.85, 8.25)                               # kitchen: over the sink, to the entry court
    p.window(0.8, S0, 2.4, 8.25, "high")                         # pantry
    p.window(0.5, 12.0, 2.75, S1, "glass")                       # dining: to the back court
    p.window(XW, 12.55, 3.25, 13.05)                             # living: to the back court
    p.window(3.9, YI, 7.9, YS, "glass")                          # living: to the garden
    p.furn("table", 0.6, 10.65, 2.6, 11.55, seats=6, ends=True, extend=(0.45, 10.65, 3.2, 11.55))
    p.furn("tv", 3.25, 13.8, 3.65, 15.4)
    if not swap:
        p.furn("low", 4.5, 14.1, 5.05, 15.1)
        p.furn("sofa", 5.45, 13.5, 6.4, 15.7, back="x1", seats=3)
        p.furn("armchair", 4.3, 12.4, 5.1, 13.2, back="y0")
    else:   # the work corner is no longer entered from here, so the sofa moves 0.4 m from the TV (the user's remark)
        p.furn("low", 4.85, 14.1, 5.4, 15.1)
        p.furn("sofa", 5.85, 13.5, 6.8, 15.7, back="x1", seats=3)
        p.furn("armchair", 4.6, 12.4, 5.4, 13.2, back="y0")
    # outside: as in form 3, and the garden comes in where the corner stepped back
    p.yard("paving", 6.9, 1.3, 8.1, 2.4, near=True)
    p.yard("steps", 6.9, 2.4, 8.1, 3.6, along="y", n=4, near=True, up="+y")
    p.yard("paving", 0.35, 0.0, 1.85, 4.0, near=True)
    p.yard("steps", 0.35, 4.0, 1.85, 5.0, along="y", n=4, near=True, up="+y")
    p.yard("paving", 0.35, 5.0, XN, YD, near=True)
    p.yard("paving", 6.85, 3.6, XN, 5.0, near=True)
    p.yard("outkitchen", 6.0, 6.85, 6.55, YD, near=True)
    p.yard("beam", 6.0, 5.9, 7.65, 6.15, near=True)
    p.yard("beam", 6.0, 6.15, 6.25, YD, near=True)
    p.yard("beam", 7.4, 6.15, 7.65, YD, near=True)
    p.yard("column", 6.0, 5.9, 6.25, 6.15, near=True)
    p.yard("column", 7.4, 5.9, 7.65, 6.15, near=True)
    p.mark(7.15, 5.6, "עמודים וקורות בטון", size=0.14, color="#55534d")
    p.mark(6.83, 6.55, "קירוי בהמשך", size=0.12, color="#55534d")
    p.mark(5.3, 7.35, "ארון כניסה", size=0.15, color="#1d1d1b")
    p.mark(5.3, 7.6, "חשמל · מטף · נעליים", size=0.13, color="#55534d")
    p.yard("beds", 3.3, 5.2, 6.4, 5.9, near=True)
    p.yard("tree", 2.0, 6.6, 0.9, near=True)
    p.entry = (7.5, 2.25, "+y")
    p.yard("lawn", 0.0, YS, 18.5, 22.0)
    p.yard("lawn", X1, YF, 18.5, YS)
    p.yard("lawn", PX1 if swap else 11.6, YP, X1, YS)
    p.yard("deck", 0.25, S1, XW, YS, near=True)
    p.yard("deck", XW, YS, 8.4, YS + 3.25, near=True)
    p.yard("pergola", 0.25, S1, XW, YS, near=True)
    p.yard("pergola", XW, YS, 8.4, YS + 3.25, near=True, label="מרפסת ופרגולה", at=(5.7, YS + 2.95))
    p.yard("outkitchen", 7.3, YS + 3.3, 8.4, YS + 4.05, near=True, label="טאבון", at=(7.85, YS + 4.5))
    p.yard("service", X1, 6.4, 17.6, 9.6, near=True, label="חצר תלייה", at=(16.4, 8.1))
    p.yard("hedge", X1, 6.15, 17.85, 6.4, near=True)
    p.yard("hedge", 17.6, 6.4, 17.85, 9.85, near=True)
    p.yard("hedge", X1, 9.6, 17.85, 9.85, near=True)
    p.yard("hedge", -0.1, YS + 0.2, 0.15, 21.8)
    p.yard("hedge", -0.1, 5.2, 0.15, S0, near=True)
    p.yard("service", 16.55, 8.55, 17.45, 9.35, near=True, label="גז", at=(17.0, 9.05))
    p.yard("beds", 15.65, 10.6, 18.1, 15.0, label="ערוגות ירק")
    p.yard("tree", 2.2, 19.8, 1.3)
    p.mark(14.0, 19.6, "דשא 9 × 5.75" if not swap else "דשא 7.15 × 5.75", size=0.24, color="#55704a")
    p.dim(XN, YF, X1, YF, off=-0.9, text=f"{X1 - XN:.2f}")
    p.dim(X1, YF, X1, YP, off=0.75, text=f"{YP - YF:.2f}")
    if not swap:
        p.dim(XW, YS, 11.6, YS, off=0.9, text=f"{11.6 - XW:.2f}")
    else:
        p.dim(XW, YS, PX0, YS, off=0.9, text=f"{PX0 - XW:.2f}")
    p.dim(0.0, S0, XW, S0, off=-0.25, text="3.00")
    # the roof: tiles over the day zone as before; the terrace all around the patio and over the night wing
    p.roof_area("tile", XW, YD, PX0, YS, slope="gable-x")
    if not swap:
        terrace = [(XN, YF, X1, YD), (7.65, 6.85, XN, YD), (PX0, YD, X1, PY0), (PX1, PY0, X1, PY1),
                   (PX0, PY1, 11.6, YS), (11.6, PY1, X1, YP)]
    else:
        terrace = [(XN, YF, X1, YD), (7.65, 6.85, XN, YD), (PX0, YD, X1, PY0), (PX0, PY0, PX1, WY), (PX1, PY0, X1, YP)]
    for r in terrace:
        p.roof_area("terrace", *r)
    p.roof_area("flat", 0.0, S0, XW, S1)
    p.mark(12.1, 5.25, "מרפסת גג", size=0.36, color="#1d1d1b", bold=True, roof=True)
    p.mark(12.1, 5.7, f"{sum((r[2] - r[0]) * (r[3] - r[1]) for r in terrace):.0f} מ\"ר, מעקה מסביב",
           size=0.22, color="#55534d", roof=True)
    if not swap:
        p.mark(PX1 - 0.45, PY0 - 0.6, "מגיעים מהפטיו", size=0.2, color="#55534d", roof=True)
    else:
        p.mark(PX1 - 0.45, WY - 0.6, "מגיעים מהגינה", size=0.2, color="#55534d", roof=True)
    # walks for the checklist: guests sleep in the mamad while it is free, later on a sofa bed in the living room
    p.route("alarm", (13.9, 12.5), (13.3, 11.3), (12.4, 11.05), (12.05, 10.5), (12.05, 8.5), (12.45, 7.6),
            (12.65, 7.0), name="הורים", at=(13.9, 12.95))
    p.route("alarm", (9.6, 4.6), (11.45, 6.2), (11.6, 7.4), (12.65, 7.6), (12.65, 7.0), name="ילד1",
            at=(9.6, 5.05))
    p.route("alarm", (6.3 if swap else 5.9, 14.6), (7.0, 13.9), (7.2, 11.0), (7.1, 9.6), (8.3, 9.05), (9.4, 9.05), (11.0, 8.95),
            (12.1, 7.7), (12.65, 7.0), name="אורחים", at=(6.3 if swap else 5.9, 15.05))
    p.route("groceries", (5.6, 0.6), (7.3, 1.85), (7.3, 3.6), (7.1, 8.4), (7.1, 9.95), (6.2, 9.9), (5.6, 9.35),
            name="קניות", at=(5.6, 0.35))
    p.route("guest", (7.1, 8.4), (7.75, 8.75), (8.3, 8.7), name="שירותים", at=(6.2, 7.6))
    p.route("laundry", (13.9, 12.5), (13.3, 11.3), (12.4, 11.05), (12.05, 10.5), (12.05, 8.5), (12.7, 7.4),
            (13.5, 7.3), name="כביסה", at=(13.9, 13.4))
    p.route("laundry", (14.0, 7.3), (15.4, 7.35), (16.4, 7.9), name="תלייה", at=(16.4, 6.95))
    return p


def form_patio_small():
    """3ב: form 3 made smaller for the budget (the user, 5.10.2026). Form 3 stays as it is, as a model of its own
    (and in the git tag house-form3-round4), so this is a copy of form_patio with the changes, not a change to it.

    The user's directions, with my recommendations, all accepted:
    1. The parents' room without the strip by the bed where the crib stood: 3.40 × 3.70 instead of 3.40 × 4.30. Along
       the bed (the closets, the walk at its foot and the bed) nothing changes. The bed's head is on a solid wall.
    2. The en-suite turned 90 degrees, across the suite, and no closet vestibule: from the hall a 0.9 m passage along
       the patio wall leads into the bedroom with no door, and the en-suite door is in the passage, out of sight of
       the bed. One closet wall in the bedroom.
    3. The laundry 1.60 m deep instead of 2.10: two machines (the user's correction), the sink and a storage column
       in one row. The suite moves north with it, and the hall in front of the mamad is 1.60 m deep.
    Together the suite is 1.65 m shorter, taken from the garden side: the south-east corner of the house steps back.
    4-5. The patio grows south to 4.45 m, over half of the den, and the den becomes a work corner for two facing the
       garden, with glass to the patio, and toward the living room a glass partition with a door-wide opening and
       no door (the user). No sofa bed. The stair to the roof (after a check of the regulations, the user's
       variant): it starts facing east along the south wall, turns at a landing and climbs north along the
       patio's blank east wall. The passage to the parents is 1.0 m wide.
    6. The living strip from the entry to the garden: checked against what is common, it stays (5.10.2026).
    The automatic checks (5.10.2026) moved the children's bath door off the basin, the guest WC to the middle of
    its back wall with a hand basin on the side, and three labels.
    """
    return _model_3b(swap=False)


def form_patio_swap():
    """3ג: model 3ב with the work corner and the patio swapped (the user's idea, 5.10.2026): "עמדת העבודה תעבור
    למסדרון המעבר לחדרי השינה, מופרדת בזכוכית לאורכה אך עם פתח ברוחב של דלת בלי דלת ... ואז פאה אחת של הפטיו
    יוצאת מהבית לחלוטין וזה נותן פתרון טוב יותר לניקוז המים".
    - The work corner, 2.85 × 1.60, is by the corridor to the bedrooms, behind the night wing's door. Glass along the
      corridor, with a door-wide opening and no door. A long desk for two, facing the patio.
    - The patio, 2.85 × 4.70, runs from the work corner to the garden and is open on its south side: the water runs
      out to the garden, and the winter sun comes in.
    - The stair to the roof: straight, with a landing, along the parents' blank wall, from the garden to the roof
      over the work corner.
    Everything else as in 3ב.
    """
    return _model_3b(swap=True)


FORMS = [form_courts, form_entry_court, form_patio, form_patio_small, form_patio_swap]


def all_forms():
    return [f() for f in FORMS]
