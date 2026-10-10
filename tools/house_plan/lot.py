# -*- coding: utf-8 -*-
"""The representative plot of the pair, measured from the vector plans of the neighborhood. (Not named site.py: that
is a stdlib module.) Both houses of the pair stand on plots like this one, as mirror images of each other.

Coordinates in meters, aligned with the plot (not with north):
  x runs along the street, from the shared wall with the other house of the pair (x=0) to the free side (x=18.5);
  y runs from the street (y=0) to the back boundary with the green strip (y=22).
In the drawings the street is at the top and the garden at the bottom. Facing directions (azimuth):
street side 17° (NNE), garden side 197° (SSW), free side 107° (ESE), shared wall 287° (WNW).
North is 17° to the left of "up" (plans are north-up and the streets are rotated ~17°).
The other house of the pair is the mirror image: its shared wall is on its east side. The page can draw any model
as the mirror image (the "תמונת מראה" box), so one set of coordinates serves both houses.

What was measured (the layout and systems sheets of the neighborhood; details in docs/02-site.md):
- the representative plot: 18.5 x 22.0 m (~407 sqm); most plots in the neighborhood are 18.1-18.2 x 22.0 m.
- parking: two stalls 2.5 x 5.0 m at x 1.85-6.85, with a 1.5 m paved strip at x 0.35-1.85 (entrance path). The other
  house of the pair has the mirror image on its side, so the two paths meet at the shared boundary.
- building lines: 3 m from the street, the garden and the free side. On the shared side any distance is valid, from 0
  up, and a house need not touch the other one along its whole length; no window in a wall standing on the boundary.
- one floor level (±0.00) for both houses of the pair. The street in front is ~0.9-1.2 m lower; the parking is at the
  street side with no wall, and a retaining wall runs along the rest of the front boundary. At the back: a retaining
  wall, then a green strip ~12 m wide (trees, a path, benches), then houses about 1 m higher than this pair.
- utilities: an electricity pillar at the front corner on the shared boundary, a sewer connection at the front under the
  parking (~3 m from the shared boundary), the water main along the street.
"""

W, D = 18.5, 22.0          # plot frontage (x) and depth (y)
FRONT, SIDE, BACK, SHARED = 3.0, 3.0, 3.0, 0.0
ENVELOPE = (SHARED, FRONT, W - SIDE, D - BACK)      # buildable area: 15.5 x 16
PARKING = (1.85, 0.0, 6.85, 5.0)                    # two 2.5 x 5.0 stalls
STALLS = [(1.85, 0.0, 4.35, 5.0), (4.35, 0.0, 6.85, 5.0)]
PATH = (0.35, 0.0, 1.85, 5.0)                       # paved strip from the street
AZ_UP = 17                 # azimuth of "up" in the drawings (toward the street)
STRIP = 12.2               # width of the green strip behind the plot

# limits that every model is checked against
KIBBUTZ_MAX = 160.0        # the kibbutz ceiling: gross, the mamad and the walls included
MAX_BUILT = 160.0          # the family's own ceiling (gross): set it from docs/01-brief.md
MIN_TILE_SHARE = 0.30
MAX_PERGOLA = 50.0
