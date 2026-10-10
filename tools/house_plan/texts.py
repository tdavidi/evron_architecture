# -*- coding: utf-8 -*-
"""The texts of YOUR page (build_page.py): one entry per model in models.py, by the model's id (Plan(cid, ...)).

Writing rules (CLAUDE.md, "ניסוחים בדפים"): every text understandable to anyone, not only to builders: first a short
explanation in everyday words, the numbers and the technical details after it. A number in a text is never typed by
hand: {name} is computed from the drawing (build_page.facts): {שטח בנוי}, {נטו}, {קירות חוץ}, {רעפים}, {מרפסת גג},
{פטיו}, {פטיו מידות}, {פטיו פנוי}, {מדרגות}, {רום}, {שלח}, and the walks of the model by their names.
"""

PAGE = dict(
    title="הבית שלנו: הדגמים",
    sub="",                       # e.g. "שלב 2 מתוך 4 · שלוש צורות על המגרש המייצג · <date>"
    cards=[],                     # [(label, big text, small text)]: where we are, what is needed from you, what is next
    models_title="הדגמים",
    sections=[],                  # [(title, [items])]: after the models, e.g. the open questions of this round
)

ABOUT = {
    # "1": dict(title="1 · <name>", size="{שטח בנוי} מ\"ר.", idea="<the idea, in one or two sentences>",
    #           pros=["..."], cons=["..."], life=[("היום", "..."), ("בעוד 7 שנים", "..."), ("בעוד 15 שנים", "...")]),
}

ROUNDS = {
    # "1": [dict(title="סבב 2: <what was asked> (<date>)", changes=[("<what>", "<how>")], follows=["<what follows>"],
    #            unchanged="<what stayed>")],      # the latest round first
}

CURRENT = []          # the models being worked on: the build stops if their automatic checks have errors
FIRST = None          # the model whose tab opens first (None: the last one)
MARK = {}             # e.g. {"2": " (נבחר)"}
VIEWS3D = {}          # where to stand inside the 3D model, per model: see example_texts.py
RUGS = {}
LEAKS = None          # a regex of what must not appear in share/page.html, e.g. the family's names
