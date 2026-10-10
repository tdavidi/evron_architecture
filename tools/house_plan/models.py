# -*- coding: utf-8 -*-
"""YOUR models: the drawings of your house, one function per model. build_page.py builds the page from MODELS, with
the texts of texts.py.

Start from your brief (docs/01-brief.md) and the method (docs/00-method.md): first the outdoor rooms and the
relations, then 3-4 truly different forms, and only then the details. The example (example_models.py) shows how a
model is written; it is the other family's house, not a template for yours.

The API, in short (draw.py has the full one):
  p = Plan(cid, name, blocks)       blocks: the built rectangles (x0, y0, x1, y1), gross. A patio is a place with no block.
  p.room(id, name, rect, ..., kind="room"|"wet"|"circ"|"service"|"public"|"mamad", at=(x, y))   net rectangles
      bedroom ids: "parents", "mamad", and ids that start with "kid" (kid, kid2...): the checks know them as bedrooms
  p.door(x0, y0, x1, y1, hinge, into, kind="hinged"|"steel")   p.slide(...)   p.gap(...)
  p.window(x0, y0, x1, y1, kind="window"|"high"|"glass")
  p.furn(kind, x0, y0, x1, y1, ...)  bed, sofa, table, island, counter, tall, fridge, wardrobe, wc, basin, shower...
  p.yard(kind, x0, y0, x1, y1, ...)  lawn, paving, pergola, tree, beds, steps, stair...
  p.roof_area(kind, x0, y0, x1, y1, slope=...)   tile, flat, terrace (see the example)
  p.mark(x, y, text, ...)  p.dim(x0, y0, x1, y1, ...)  p.zone(...)   labels, dimension lines, zones
  p.route(kind, *points, name=...)   the walks: alarm, groceries, guest, laundry
  p.waive = {code: reason}           a finding of the checks accepted on purpose, with the reason
Coordinates in meters, in the plot frame of lot.py: x from the shared boundary (0) to the free side (18.5), y from the
street (0) to the garden (22). Exterior walls 25 cm, partitions 10 cm, mamad walls 25-30 cm. Every coordinate a
multiple of 5 cm (the 3D model rasterizes the plan on a 5 cm grid).
"""
from draw import Plan  # noqa: F401

MODELS = []       # e.g. [model_1, model_2, model_3]: the order of the tabs on the page
