"""
po_parts.py — the seeded prefill list for extra purchase-order lines
====================================================================

⚠ **EVERY RATE IN THIS FILE IS AN ASSUMED PLACEHOLDER. NONE OF IT IS A QUOTED
OR VERIFIED MARKET PRICE. IT EXISTS SO A PURCHASE ORDER CAN BE RAISED BEFORE
THE VENDOR HAS PRICED THE LIST, AND EVERY FIGURE IS EXPECTED TO BE
OVERWRITTEN.**

That paragraph is the whole reason this file is allowed to exist, so it is the
first thing in it. A rate here has not been sourced, quoted, negotiated or
checked against a market. It is a number somebody put in so that the form has
something to put in the box, and the moment a vendor prices the line the figure
here is wrong. Nothing in this application may present one of these as a real
price — not in the UI, not in a report, not on a printed document.

────────────────────────────────────────────────────────────────────────────
WHAT THIS IS, AND THE FOUR THINGS IT IS NOT
────────────────────────────────────────────────────────────────────────────

A purchase order often carries parts that appear nowhere on the BOQ — site
consumables, fixings, safety gear. Those lines are **free text typed onto each
order**, and this list exists **only as a typeahead prefill** so an order can
be raised before anybody has priced it. The list below is a trade-neutral
starting set for a building contractor; a company replaces it with its own
purchasing list.

So this module is:

* **A flat module-level table.** Not a collection in `STORE`, not a document,
  not a record with an id, not persisted by `db.py`.
* **Not editable through the UI.** There is no parts-master page, no CRUD, no
  route. Changing a rate here is a code edit and a commit, which is the correct
  weight for changing a placeholder everybody is supposed to overwrite anyway.
* **Not a vocabulary.** Typing a description that matches nothing here is
  accepted exactly as typed, with a blank rate. The list narrows nothing.
* **Not a per-vendor rate table.** One assumed figure, not one per supplier.
  What a given vendor charges is what they quote, and that goes in the rate box.

`purchase.py` imports this module. This module imports **nothing** — not
`store`, not `pipeline`, not `branding` — which is what keeps that arrow
one-way and keeps this file at the bottom of the import graph. Keep it that
way.

════════════════════════════════════════════════════════════════════════════
THE ALIAS RULE — READ THIS BEFORE ADDING ONE
════════════════════════════════════════════════════════════════════════════

⚠ **AN ALIAS MAY EXIST ONLY IF THE PURCHASING LIST ITSELF CARRIES THAT EXACT
STRING. Everything else is deleted, and `tests/test_po_parts_aliases.py`
enforces it.**

`CLIENT_LINES` below is that list — the lines exactly as the purchasing team
wrote them, typos, duplicates and quantities included. ("Client" here means
the company running this application: it is the purchasing list of the client
of this software.)

The one permitted derivation is mechanical and is written down rather than
inferred: a line whose **trailing quantity** was dropped may also be reached by
the line without it. `CLIENT_LINE_QUANTITIES` names both such lines and spells
out the stripped form; nothing parses a quantity out of anything.

`MISSPELLINGS` is the second half of the record and does **not** generate
aliases. It explains why a canonical name departs from the list's own
spelling — `Soket` → `Socket` — so that the departure is auditable. The
list's spelling is then an alias because **it was written**, not because a map
says it is allowed.

**Why the rule exists, and it is a defect and not a tidy-up.** A prefill table
once shipped with 156 aliases nobody had written — plausible-looking
permutations generated to widen the prefill — and three classes of them were
actively wrong:

1. **A live wrong number.** Two spellings of one physical part reached two
   different placeholder rates, and **which figure landed on a purchase order
   depended on how somebody typed it.**
2. **An inch↔mm equivalence asserted as a spelling.** Whether `25mm` and `1"`
   are one part **is a pricing decision**, and dressing it as a spelling
   variant hides the decision inside a lookup table.
3. **A bare name silently choosing a size or a brand.** The operator gets a
   rate for a part they did not specify.

⚠ **NO CANONICAL PART IS MERGED OR SPLIT.** `25mm conduit bend` and
`1" conduit bend` are two entries with **no alias between them**, so typing one
can never fetch the other's rate. This module does **not** assert they are the
same part and does **not** assert they are different — see the open question
below.

**The consequence, and it is the correct one:** the prefill misses more often.
`grinding disc` does not fill a rate; the line is accepted exactly as typed,
with a blank rate and no assumed flag. **A match this list misses costs one
typed rate. A match it gets wrong puts a figure on a purchase order that nobody
chose**, which is `_norm()`'s doctrine applied one level up.

────────────────────────────────────────────────────────────────────────────
THE OPEN QUESTION THIS LIST LEAVES OPEN, ON PURPOSE
────────────────────────────────────────────────────────────────────────────

⚠ **Are `25mm conduit bend` and `1" conduit bend` the same part?** 25 mm is
about an inch, so they may be one item written two ways at two placeholder
rates — or two items bought separately. **This module does not answer it in
either direction.** Until the purchasing team does, they are two entries with
no path between them, which is the only arrangement that cannot put the wrong
figure on an order.

────────────────────────────────────────────────────────────────────────────
THE LIST HAS DUPLICATES, TYPOS AND QUANTITIES IN THE NAMES
────────────────────────────────────────────────────────────────────────────

Resolved into aliases rather than seeded twice, so that both spellings prefill
the same rate and the operator never has to know which one is the "real" one.
The substitutions applied, all of them from the list itself:

    Soket    -> Socket        Fastner  -> Fastener
    Angel    -> Angle         Lather   -> Leather
    Solvant  -> Solvent

and these were one item written several ways:

    "Cutting disc" / '4" Cutting disc' / "Cutting disc 4 inch"
    "8 mm Bullet Fastner" / "Bullet Fastner 8mm"
    "Thinner 5 ltr" / "Thinner 5ltr"

`Copper wire 1.5 sqmm coil` and `MCB 16a SP` each appear **twice** on the list
and are seeded once each.

⚠ **Two names carry a QUANTITY, and the quantity is dropped from the
canonical.** `Safety shoes 10no` is seeded as `Safety shoes` and
`Plywood 12MM - 05 sheets` as `Plywood 12 mm`. A quantity is something the
operator types into the qty box on the order; baking "10no" into a part name
would make every future order for eleven pairs read as a typo. Both lines are
in `CLIENT_LINES` verbatim, and `CLIENT_LINE_QUANTITIES` is what lets the
stripped form be an alias too.

⚠ **Grade variants are kept as separate parts, deliberately.**
`Emulsion paint 20 ltr` and `Emulsion paint premium 20 ltr` are two rows, and
so are `Wall putty 20 kg` and `Wall putty premium 20 kg`. They
are different goods at different rates, and folding them would lose the
distinction the list drew itself. **Neither bare name is an alias**: a bare
`emulsion paint` would choose a grade and a size for somebody who named
neither.
"""

# ══════════════════════════════════════════════════════════════════════════
# THE PURCHASING LIST — the source of truth for the alias rule
# ══════════════════════════════════════════════════════════════════════════
#
# Grades are marked per line, so a later edit keeps the distinction:
#
#     (v)  verbatim — a spelling the list carries that differs from the canonical
#     (m)  a canonical name with a documented misspelling reversed
#     (—)  the canonical name, written exactly as the list has it
#
# **AN ALIAS MAY ONLY BE A STRING THAT APPEARS HERE** (or the stripped form of
# one named in CLIENT_LINE_QUANTITIES). To add an alias you must first add a
# list line, and adding a list line is a claim about what was written.
CLIENT_LINES = (
    "Cement OPC 53 grade 50 kg",                         # (—)
    "River sand",                                        # (—)
    "M-sand",                                            # (—)
    "TMT bar 8 mm",                                      # (—)
    "TMT bar 10 mm",                                     # (—)
    "Binding wire",                                      # (—)
    "Fly ash bricks",                                    # (—)
    "Plywood 12MM - 05 sheets",                          # (v) carries a qty
    "Wall putty 20 kg",                                  # (—)
    "Wall putty premium 20 kg",                          # (—)
    "Emulsion paint 20 ltr",                             # (—)
    "Emulsion paint premium 20 ltr",                     # (—)
    "Thinner 5 ltr",                                     # (v) one of two
    "Thinner 5ltr",                                      # (v) spellings
    "Tile adhesive 20 kg",                               # (—)
    "Tile grout 1 kg",                                   # (—)
    "Gypsum board 12.5 mm",                              # (—)
    "GI stud 75 mm",                                     # (—)
    "Ceiling suspension rod",                            # (—)
    "8 mm Bullet Fastner",                               # (v) one of two
    "Bullet Fastner 8mm",                                # (v) spellings
    "Anchor Fastner 10x75",                              # (m) Fastner
    "Self tapping screw 25 mm",                          # (—)
    "PVC conduit 20 mm",                                 # (—)
    "PVC conduit 25 mm",                                 # (—)
    "25mm conduit bend",                                 # (—) open question
    '1" conduit bend',                                   # (—) open question
    "Junction box 3-way",                                # (—)
    "Copper wire 1.5 sqmm coil",                         # (v) appeared TWICE
    "Copper wire 2.5 sq mm coil",                        # (—)
    "MCB 16a SP",                                        # (v) appeared TWICE
    "Modular switch 6A",                                 # (—)
    "Modular soket 16A",                                 # (m) Soket -> Socket
    "CPVC pipe 15 mm",                                   # (—)
    "CPVC elbow 15 mm",                                  # (—)
    "CPVC tee 15 mm",                                    # (—)
    "Solvant cement 100 ml",                             # (m) Solvant -> Solvent
    "Teflon tape",                                       # (—)
    "Ball valve 15 mm",                                  # (—)
    "Angel cock 15 mm",                                  # (m) Angel -> Angle
    "Cutting disc",                                      # (v) one of three
    '4" Cutting disc',                                   # (v) spellings
    "Cutting disc 4 inch",                               # (v)
    "Grinding disc 4 inch",                              # (—) NOT bare-named
    "Masonry drill bit 8 mm",                            # (—)
    "Safety helmet",                                     # (—)
    "Safety shoes 10no",                                 # (v) carries a qty
    "Lather hand gloves",                                # (m) Lather -> Leather
    "Reflective jacket",                                 # (—)
    "Measuring tape 5 m",                                # (—)
    "Masking tape 1 inch",                               # (—)
)

# The two list lines whose trailing QUANTITY was dropped from the canonical
# name, with the stripped form written out. Nothing parses a quantity out of
# anything — this is the whole of the permitted derivation, and it is a table
# of two rows precisely so that it cannot quietly grow into a rule.
CLIENT_LINE_QUANTITIES = {
    "Safety shoes 10no":         "Safety shoes",
    "Plywood 12MM - 05 sheets":  "Plywood 12MM",
}

# The list's own misspellings, and the corrections applied when the canonical
# name was written.
#
# ⚠ **This map does NOT license an alias.** It records why a canonical departs
# from the list's spelling, so the departure is auditable. The list's spelling
# is an alias because it is in `CLIENT_LINES` — because it was written — and for
# no other reason. Reading this map as "any string containing `soket` may be an
# alias" is how 156 invented aliases happened once.
MISSPELLINGS = {
    "soket":   "socket",
    "fastner": "fastener",
    "angel":   "angle",
    "lather":  "leather",
    "solvant": "solvent",
}


# Every entry: canonical display name -> {unit, assumed_rate, aliases}.
#
# `unit` and `assumed_rate` are both a PREFILL. The form leaves each editable
# and the operator overwrites either without ceremony; nothing downstream reads
# this file, so a change here affects the next line typed and no order already
# raised.
#
# ⚠ `aliases` are the list's OWN spellings and nothing else — see the alias
# rule in the docstring. A row with no alias is the ordinary case: it means the
# canonical name is what the list says. **Do not add a "plausible variant".**
PARTS = {
    "Cement OPC 53 grade 50 kg":   {"unit": "Bag",   "assumed_rate": 390.0,
                                    "aliases": []},
    "River sand":                  {"unit": "Brass", "assumed_rate": 6500.0,
                                    "aliases": []},
    "M-sand":                      {"unit": "Brass", "assumed_rate": 5200.0,
                                    "aliases": []},
    "TMT bar 8 mm":                {"unit": "Kg",    "assumed_rate": 62.0,
                                    "aliases": []},
    "TMT bar 10 mm":               {"unit": "Kg",    "assumed_rate": 61.0,
                                    "aliases": []},
    "Binding wire":                {"unit": "Kg",    "assumed_rate": 85.0,
                                    "aliases": []},
    "Fly ash bricks":              {"unit": "Nos",   "assumed_rate": 7.0,
                                    "aliases": []},
    # The list says "Plywood 12MM - 05 sheets". The "- 05 sheets" is a
    # QUANTITY, not part of the name: dropped from the canonical, it belongs in
    # the qty box on the order. Both the line and its stripped form are aliases
    # — CLIENT_LINE_QUANTITIES is the permission.
    "Plywood 12 mm":               {"unit": "Sheet", "assumed_rate": 1350.0,
                                    "aliases": ["Plywood 12MM - 05 sheets",
                                                "Plywood 12MM"]},
    # ⚠ Two grades, two rows — and neither bare name is an alias.
    "Wall putty 20 kg":            {"unit": "Bag",   "assumed_rate": 780.0,
                                    "aliases": []},
    "Wall putty premium 20 kg":    {"unit": "Bag",   "assumed_rate": 980.0,
                                    "aliases": []},
    # ⚠ Two grades, two rows, and NEITHER bare name is an alias.
    "Emulsion paint 20 ltr":       {"unit": "Can",   "assumed_rate": 4200.0,
                                    "aliases": []},
    "Emulsion paint premium 20 ltr":
                                   {"unit": "Can",   "assumed_rate": 5600.0,
                                    "aliases": []},
    # "Thinner 5 ltr" and "Thinner 5ltr" — one item, two spellings.
    "Thinner 5 ltr":               {"unit": "Can",   "assumed_rate": 650.0,
                                    "aliases": ["Thinner 5ltr"]},
    "Tile adhesive 20 kg":         {"unit": "Bag",   "assumed_rate": 520.0,
                                    "aliases": []},
    "Tile grout 1 kg":             {"unit": "Kg",    "assumed_rate": 110.0,
                                    "aliases": []},
    "Gypsum board 12.5 mm":        {"unit": "Nos",   "assumed_rate": 420.0,
                                    "aliases": []},
    "GI stud 75 mm":               {"unit": "Mtr",   "assumed_rate": 175.0,
                                    "aliases": []},
    "Ceiling suspension rod":      {"unit": "Nos",   "assumed_rate": 18.0,
                                    "aliases": []},
    # The list carried this twice — "8 mm Bullet Fastner" and "Bullet Fastner
    # 8mm". One part, both spellings, `Fastner` -> `Fastener`.
    "Bullet fastener 8mm":         {"unit": "Nos",   "assumed_rate": 12.0,
                                    "aliases": ["8 mm Bullet Fastner",
                                                "Bullet Fastner 8mm"]},
    "Anchor fastener 10x75":       {"unit": "Nos",   "assumed_rate": 28.0,
                                    "aliases": ["Anchor Fastner 10x75"]},
    "Self tapping screw 25 mm":    {"unit": "Nos",   "assumed_rate": 1.5,
                                    "aliases": []},
    "PVC conduit 20 mm":           {"unit": "Nos",   "assumed_rate": 75.0,
                                    "aliases": []},
    "PVC conduit 25 mm":           {"unit": "Nos",   "assumed_rate": 95.0,
                                    "aliases": []},
    # ⚠ Two separate entries with no alias between them — the open question.
    "25mm conduit bend":           {"unit": "Nos",   "assumed_rate": 18.0,
                                    "aliases": []},
    '1" conduit bend':             {"unit": "Nos",   "assumed_rate": 20.0,
                                    "aliases": []},
    "Junction box 3-way":          {"unit": "Nos",   "assumed_rate": 22.0,
                                    "aliases": []},
    # "Copper wire 1.5 sqmm coil" appeared twice on the list. Seeded once, and
    # the list's own spelling is the alias.
    "Copper wire 1.5 sq mm coil":  {"unit": "Coil",  "assumed_rate": 1650.0,
                                    "aliases": ["Copper wire 1.5 sqmm coil"]},
    "Copper wire 2.5 sq mm coil":  {"unit": "Coil",  "assumed_rate": 2650.0,
                                    "aliases": []},
    # "MCB 16a SP" appeared twice on the list. Seeded once.
    "MCB 16A SP":                  {"unit": "Nos",   "assumed_rate": 180.0,
                                    "aliases": ["MCB 16a SP"]},
    "Modular switch 6A":           {"unit": "Nos",   "assumed_rate": 45.0,
                                    "aliases": []},
    "Modular socket 16A":          {"unit": "Nos",   "assumed_rate": 85.0,
                                    "aliases": ["Modular soket 16A"]},
    "CPVC pipe 15 mm":             {"unit": "Nos",   "assumed_rate": 260.0,
                                    "aliases": []},
    "CPVC elbow 15 mm":            {"unit": "Nos",   "assumed_rate": 12.0,
                                    "aliases": []},
    "CPVC tee 15 mm":              {"unit": "Nos",   "assumed_rate": 15.0,
                                    "aliases": []},
    "Solvent cement 100 ml":       {"unit": "Nos",   "assumed_rate": 95.0,
                                    "aliases": ["Solvant cement 100 ml"]},
    "Teflon tape":                 {"unit": "Nos",   "assumed_rate": 15.0,
                                    "aliases": []},
    "Ball valve 15 mm":            {"unit": "Nos",   "assumed_rate": 240.0,
                                    "aliases": []},
    "Angle cock 15 mm":            {"unit": "Nos",   "assumed_rate": 210.0,
                                    "aliases": ["Angel cock 15 mm"]},
    # "Cutting disc", '4" Cutting disc' and "Cutting disc 4 inch" — one item.
    # The bare `cutting disc` IS one of the list's three spellings, which is
    # why it survives where `grinding disc` does not.
    "Cutting disc 4 inch":         {"unit": "Nos",   "assumed_rate": 45.0,
                                    "aliases": ["Cutting disc",
                                                '4" Cutting disc']},
    # ⚠ `grinding disc` is NOT an alias. The list wrote the size; a bare name
    #   here would hand out the 4-inch rate to somebody who named no size.
    "Grinding disc 4 inch":        {"unit": "Nos",   "assumed_rate": 60.0,
                                    "aliases": []},
    "Masonry drill bit 8 mm":      {"unit": "Nos",   "assumed_rate": 120.0,
                                    "aliases": []},
    "Safety helmet":               {"unit": "Nos",   "assumed_rate": 180.0,
                                    "aliases": []},
    # The list wrote "Safety shoes 10no". The "10no" is a QUANTITY and is
    # dropped from the canonical — it belongs in the qty box, not in the part
    # name — but the line is still the list's line, so it is an alias.
    "Safety shoes":                {"unit": "Pair",  "assumed_rate": 1150.0,
                                    "aliases": ["Safety shoes 10no"]},
    # `Lather` -> `Leather`.
    "Leather hand gloves":         {"unit": "Pair",  "assumed_rate": 95.0,
                                    "aliases": ["Lather hand gloves"]},
    "Reflective jacket":           {"unit": "Nos",   "assumed_rate": 650.0,
                                    "aliases": []},
    "Measuring tape 5 m":          {"unit": "Nos",   "assumed_rate": 130.0,
                                    "aliases": []},
    "Masking tape 1 inch":         {"unit": "Nos",   "assumed_rate": 90.0,
                                    "aliases": []},
}


def _norm(text) -> str:
    """
    The matching key: lowercased, with every run of whitespace collapsed to one.

    Deliberately shallow. It folds the differences that are certainly noise — a
    stray double space, a capital letter — and folds nothing else. It does NOT
    strip punctuation, because `1.5 sq mm` and `15 sq mm` differ by a full stop
    and collapsing them would prefill the wrong rate on a wire size. A match
    this list misses costs one typed rate; a match it gets wrong puts a figure
    on a purchase order that nobody chose.
    """
    return " ".join(str(text or "").lower().split())


def permitted_alias_keys() -> set:
    """
    Every normalised string an alias is allowed to be.

    The client's own lines, plus the stripped form of the two that carried a
    trailing quantity. **Nothing else, ever** — this function is the alias rule
    expressed as code, and `tests/test_po_parts_aliases.py` is what enforces it
    against `PARTS`.

    It is exported rather than reimplemented in the test on purpose: a test
    carrying its own copy of the rule is a second definition that can drift,
    which is the same defect the `xlNorm()` removal closed one file along.
    """
    keys = {_norm(line) for line in CLIENT_LINES}
    keys |= {_norm(stripped) for stripped in CLIENT_LINE_QUANTITIES.values()}
    return keys


def _build_index() -> dict:
    """
    `{normalised name or alias: canonical name}`, built once at import.

    Both directions are indexed — the canonical name and every alias — so that
    `Socket 15mm` and `Soket 15mm` land on the same row. A duplicate key is a
    seeding mistake rather than a runtime condition, and
    `tests/test_po_extra_lines.py` asserts there are none; here the first
    definition simply wins, because a table that silently lost a part would be
    worse than one that ignored a redundant alias.
    """
    index = {}
    for canonical, row in PARTS.items():
        index.setdefault(_norm(canonical), canonical)
        for alias in row.get("aliases") or ():
            index.setdefault(_norm(alias), canonical)
    return index


INDEX = _build_index()


def lookup(description):
    """
    `(canonical_name, unit, assumed_rate)` for a typed description, or `None`.

    `None` is the ordinary answer, not a failure: an extra line is free text
    and most of what gets typed will not be on this list. The caller keeps what
    was typed and leaves the rate blank.

    ⚠ **It misses more than it used to, and that is the fix rather than a
    regression.** 156 invented aliases were deleted on 29 August 2026 — see the
    alias rule in the docstring. A miss costs one typed rate; the alternative
    was a table that answered confidently for strings nobody had written.

    ⚠ **A hit returns an ASSUMED rate.** The caller must mark the line so the
    figure is never mistaken for one a vendor gave us — `purchase.py` sets
    `rate_is_assumed` when, and only when, it fills a BLANK rate box from this
    table. A figure that was in the box on submit is the operator's price,
    this table's own figure included (the owner's ruling, 14 September 2026:
    *"if I have entered price it is not a placeholder"*). So the form offers
    the rate as ghost text and never writes it into the box.
    """
    canonical = INDEX.get(_norm(description))
    if not canonical:
        return None
    row = PARTS[canonical]
    return canonical, row["unit"], float(row["assumed_rate"])


def prefill_map() -> dict:
    """
    `{normalised name or alias: {"u": unit, "r": assumed_rate}}` — the whole
    seeded table, flattened for a **dictionary lookup and nothing more**.

    Built from `INDEX`, deliberately, rather than from `PARTS`. `INDEX` is the
    exact key set `lookup()` matches on, so this map and the server agree on
    what "matches" **by construction** — the same keys, the same aliases
    already resolved, the same normalisation applied once, here, in Python.

    ⚠ **This exists so that the browser never has to know any of that.** The
    page renders this map and does one lookup on it. It holds no alias table,
    no canonical names and no rule about what counts as a match, so there is no
    second implementation to drift from this one. Until 29 August 2026 the page
    carried its own `xlNorm()` reimplementing `_norm()` in JavaScript, with
    nothing checking that the two agreed; the map it fed also carried **only
    canonical names**, so not one of the client's own spellings ever prefilled.

    ⚠ **It is a convenience, not the mechanism.** `purchase._parse_extra_lines()`
    fills a blank rate from this same table on POST, so the feature works with
    JavaScript disabled, broken, or never executed. A miss here costs a live
    preview and nothing else.

    ⚠ Every `r` is an ASSUMED PLACEHOLDER — see the top of this file.
    """
    return {key: {"u": PARTS[canonical]["unit"],
                  "r": float(PARTS[canonical]["assumed_rate"])}
            for key, canonical in INDEX.items()}


def suggestions() -> list:
    """
    Canonical names, sorted, for the form's `<datalist>`.

    Canonical names only. The aliases are for *matching* what somebody typed,
    not for offering the client's own typos back to him as suggestions.
    """
    return sorted(PARTS)
