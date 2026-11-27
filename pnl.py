"""
pnl.py — a project's profit & loss: planned vs actual, and money still owed
==========================================================================
27 November 2026, FEATURE_GAP.md row 7 — a lean REIMPLEMENTATION of the idea
in the client line's `pnl.py` (Demo_Works `2df435e`, `456c980`, `9edba90`),
by the product owner's decision. It reverses this product's C6 block
(PROGRESS.md C6, ABOUT.md §2o): the project page now shows a margin.

The labour question C6 was blocked on, and how this answers it
--------------------------------------------------------------
C6 waited on ONE question: which labour cost is authoritative, the BOQ's
installation base rate or the attendance wages — subtracting both counts
labour twice. Here they are never in the same figure:

* **PLANNED** uses the BOQ ONLY: contract value (the selling rates) against
  the planned cost (qty × each track's BASE rate — supply AND installation,
  so planned labour is the installation base rate). Nothing actual enters it.
* **ACTUAL** uses actual costs ONLY: purchase orders and work orders
  (taxable value), expenses & charges (taxable amount) and site labour
  (attendance wages through `attendance.cost_of`, passed IN by the caller).
  No BOQ base rate enters it.

So labour is counted once in each, and the two are compared, never summed.

Definitions (all EXCLUDING GST, which is a pass-through)
--------------------------------------------------------
    contract        the CURRENT revision of each BOQ chain on the project
                    (a superseded revision is never counted — no stacking)
    planned_cost    Σ qty × base rate on those revisions; a track with no base
                    rate counts its selling rate (zero planned margin on it)
    billed          Σ `claim_subtotal` of ISSUED RA bills on any revision of
                    those chains; drafts are counted separately, cancelled
                    bills never
    billed_gross    the same bills' `grand_total` (with GST) — what is owed
    received        Σ receipts (amount + write-off) against those bills
    outstanding     billed_gross − received
    committed       Σ `taxable_value` of the project's purchase orders that
                    are not Cancelled (issued work is a commitment whether or
                    not it has been delivered)
    charges         Σ `taxable_amount` of the project's expenses
    labour          the caller's figure, or None when the viewer may not see
                    wages (B4: HR information is withheld from Sales,
                    Purchase and Accounts); the actual figures then EXCLUDE
                    labour and say so
    actual_margin   billed − (committed + charges + labour)

⚠ **A leaf.** `store` and `pipeline` only; it reads collections raw, the way
  `series.py` does, because `boq.py`, `ra.py` and `purchase.py` may not all be
  imported from one place. It renders no page; `projectview.py` draws it.
⚠ **Derived, nothing stored.** Every figure is recomputed on each view from
  the documents' own stored totals; nothing here writes STORE.
"""

import math

import pipeline as P
from store import STORE


def _f(v) -> float:
    try:
        return float(v or 0.0)
    except (TypeError, ValueError):
        return 0.0


# =============================================================================
# THE BOQ CHAINS ON A PROJECT
# =============================================================================

def project_boqs(project_id: str) -> list:
    return [b for b in (STORE.get("boqs") or {}).values()
            if b.get("project_id") == project_id]


def current_revisions(project_id: str) -> list:
    """Each chain's tip: a BOQ on the project that no other BOQ supersedes."""
    boqs = project_boqs(project_id)
    superseded = {str(b.get("supersedes") or "") for b in (STORE.get("boqs") or {}).values()}
    return [b for b in boqs if b.get("id") not in superseded]


def _qty(li: dict) -> float:
    if li.get("total_qty") not in (None, ""):
        return _f(li.get("total_qty"))
    return sum(_f(v) for v in (li.get("area_qty") or {}).values())


def plan_of(boq: dict) -> tuple:
    """(contract, planned_cost) for one BOQ, from its own lines."""
    contract = cost = 0.0
    for li in boq.get("line_items") or []:
        if li.get("is_header"):
            continue
        q = _qty(li)
        for track in ("supply", "install"):
            amount = _f(li.get(f"{track}_amount"))
            contract += amount
            base = li.get(f"{track}_base_rate")
            cost += q * _f(base) if base not in (None, "") else amount
    return round(contract, 2), round(cost, 2)


# =============================================================================
# THE FIGURES
# =============================================================================

def figures(project_id: str, labour=None) -> dict:
    boq_ids = {b.get("id") for b in project_boqs(project_id)}
    tips = current_revisions(project_id)
    contract = planned_cost = 0.0
    for b in tips:
        c, k = plan_of(b)
        contract += c
        planned_cost += k

    bills = [r for r in (STORE.get("ra_bills") or {}).values()
             if r.get("boq_id") in boq_ids and r.get("status") != "cancelled"]
    issued = [r for r in bills if r.get("status") == "issued"]
    drafts = [r for r in bills if r.get("status") != "issued"]
    issued_ids = {r.get("id") for r in issued}
    billed = sum(_f(r.get("claim_subtotal")) for r in issued)
    billed_gross = sum(_f(r.get("grand_total")) for r in issued)
    received = sum(_f(x.get("amount")) + _f(x.get("write_off"))
                   for x in (STORE.get("receipts") or {}).values()
                   if x.get("ra_id") in issued_ids)

    pos = [p for p in (STORE.get("purchases") or {}).values()
           if p.get("project_id") == project_id and p.get("status") != "Cancelled"]
    committed = sum(_f(p.get("taxable_value") if p.get("taxable_value") is not None
                       else p.get("subtotal")) for p in pos)
    charges = sum(_f(c.get("taxable_amount")) for c in (STORE.get("charges") or {}).values()
                  if c.get("project_id") == project_id)
    actual_cost = committed + charges + (labour or 0.0)

    def pct(part, whole):
        return round(100.0 * part / whole, 1) if whole else None

    return {
        "revisions": tips, "contract": round(contract, 2),
        "planned_cost": round(planned_cost, 2),
        "planned_margin": round(contract - planned_cost, 2),
        "planned_margin_pct": pct(contract - planned_cost, contract),
        "bills_issued": len(issued), "bills_draft": len(drafts),
        "draft_value": round(sum(_f(r.get("claim_subtotal")) for r in drafts), 2),
        "billed": round(billed, 2), "billed_gross": round(billed_gross, 2),
        "received": round(received, 2), "outstanding": round(billed_gross - received, 2),
        "committed": round(committed, 2), "charges": round(charges, 2),
        "labour": None if labour is None else round(labour, 2),
        "actual_cost": round(actual_cost, 2),
        "actual_margin": round(billed - actual_cost, 2),
        "actual_margin_pct": pct(billed - actual_cost, billed),
        "billed_pct": pct(billed, contract), "received_pct": pct(received, billed_gross),
        "cost_pct": pct(actual_cost, planned_cost),
    }


# =============================================================================
# DRAWING — inline SVG and CSS bars, no script, nothing external
# =============================================================================

# Plain string, interpolated as a value — nothing in it needs doubling.
PNL_CSS = """
<style>
  .pnl-tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
               gap:.7rem; margin:.4rem 0 1rem; }
  .pnl-tile { border:1px solid var(--border); border-radius:10px; padding:.7rem .85rem;
              background:var(--surface); }
  .pnl-tile .k { font-size:.75rem; color:var(--muted); text-transform:uppercase;
                 letter-spacing:.04em; }
  .pnl-tile .v { font-size:1.25rem; font-weight:700; margin-top:.15rem; }
  .pnl-tile .s { font-size:.78rem; color:var(--muted); margin-top:.1rem; }
  .pnl-pos { color:#15803d; } .pnl-neg { color:#b91c1c; }
  .pnl-grid { display:grid; grid-template-columns:minmax(220px,300px) 1fr; gap:1.2rem;
              align-items:center; }
  @media (max-width:760px) { .pnl-grid { grid-template-columns:1fr; } }
  .pnl-legend { list-style:none; padding:0; margin:.5rem 0 0; font-size:.82rem; }
  .pnl-legend li { margin:.2rem 0; }
  .pnl-sw { display:inline-block; width:.8rem; height:.8rem; border-radius:3px;
            margin-right:.4rem; vertical-align:-1px; }
  .pnl-bar { margin:.55rem 0; font-size:.84rem; }
  .pnl-bar .t { display:flex; justify-content:space-between; gap:1rem; }
  .pnl-track { height:.6rem; border-radius:99px; background:var(--border); overflow:hidden;
               margin-top:.25rem; }
  .pnl-fill { height:100%; border-radius:99px; background:var(--brand); }
  .pnl-note { font-size:.78rem; color:var(--muted); margin-top:.7rem; }
</style>
"""

SLICE_COLOURS = ("#2563eb", "#f59e0b", "#10b981", "#8b5cf6")


def money(v) -> str:
    """On-screen money, the app's convention (ABOUT.md §9). Not escaped."""
    return f"&#8377;&nbsp;{_f(v):,.0f}"


def pie_svg(parts: list, size: int = 180) -> str:
    """A donut from [(label, value)]; zero and negative values are left out."""
    parts = [(l, v) for l, v in parts if _f(v) > 0]
    total = sum(v for _l, v in parts)
    if not total:
        return ""
    r, c, w = size * 0.38, size / 2, size * 0.17
    circ = 2 * math.pi * r
    arcs, offset = [], 0.0
    for i, (label, v) in enumerate(parts):
        frac = v / total
        arcs.append(
            f'<circle cx="{c}" cy="{c}" r="{r:.2f}" fill="none" '
            f'stroke="{SLICE_COLOURS[i % len(SLICE_COLOURS)]}" stroke-width="{w:.2f}" '
            f'stroke-dasharray="{frac * circ:.2f} {circ:.2f}" '
            f'stroke-dashoffset="{-offset * circ:.2f}" '
            f'transform="rotate(-90 {c} {c})"><title>{P.esc(label)}: '
            f'{round(100 * frac)}%</title></circle>')
        offset += frac
    legend = "".join(
        f'<li><span class="pnl-sw" style="background:{SLICE_COLOURS[i % len(SLICE_COLOURS)]};">'
        f'</span>{P.esc(label)} &mdash; {money(v)} ({round(100 * v / total)}%)</li>'
        for i, (label, v) in enumerate(parts))
    return (f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" '
            f'aria-label="Cost split">{"".join(arcs)}</svg>'
            f'<ul class="pnl-legend">{legend}</ul>')


def bar_html(label: str, part, whole, pct) -> str:
    width = max(0.0, min(100.0, pct or 0.0))
    shown = "&mdash;" if pct is None else f"{pct:g}%"
    return (f'<div class="pnl-bar"><div class="t"><span>{P.esc(label)}</span>'
            f'<span>{money(part)} of {money(whole)} &middot; <b>{shown}</b></span></div>'
            f'<div class="pnl-track"><div class="pnl-fill" style="width:{width:.1f}%;"></div>'
            f'</div></div>')


def _signed(v) -> str:
    cls = "pnl-pos" if _f(v) >= 0 else "pnl-neg"
    return f'<span class="{cls}">{money(v)}</span>'


def panel_html(fig: dict) -> str:
    """The Profit & Loss panel body. Every figure is `figures()`'s."""
    labour_seen = fig["labour"] is not None
    draft_note = f", {fig['bills_draft']} draft" if fig["bills_draft"] else ""
    pm = fig["planned_margin_pct"]
    am = fig["actual_margin_pct"]
    tiles = (
        f'<div class="pnl-tile"><div class="k">Contract value</div>'
        f'<div class="v">{money(fig["contract"])}</div>'
        f'<div class="s">current revision{"s" if len(fig["revisions"]) != 1 else ""}, excl. GST</div></div>'
        f'<div class="pnl-tile"><div class="k">Billed to date</div>'
        f'<div class="v">{money(fig["billed"])}</div>'
        f'<div class="s">{fig["bills_issued"]} issued RA bill{"s" if fig["bills_issued"] != 1 else ""}'
        f'{draft_note}</div></div>'
        f'<div class="pnl-tile"><div class="k">Still owed</div>'
        f'<div class="v">{money(fig["outstanding"])}</div>'
        f'<div class="s">of {money(fig["billed_gross"])} billed incl. GST</div></div>'
        f'<div class="pnl-tile"><div class="k">Planned margin</div>'
        f'<div class="v">{_signed(fig["planned_margin"])}</div>'
        f'<div class="s">{"" if pm is None else f"{pm:g}% of contract"}</div></div>'
        f'<div class="pnl-tile"><div class="k">Actual margin to date</div>'
        f'<div class="v">{_signed(fig["actual_margin"])}</div>'
        f'<div class="s">{"" if am is None else f"{am:g}% of billed"}'
        f'{"" if labour_seen else " &middot; excl. labour"}</div></div>')
    parts = [("Purchase & work orders", fig["committed"]), ("Expenses & charges", fig["charges"])]
    if labour_seen:
        parts.append(("Site labour", fig["labour"]))
    pie = pie_svg(parts) or '<p class="pnl-note">No costs booked to this project yet.</p>'
    bars = (bar_html("Billed against contract", fig["billed"], fig["contract"], fig["billed_pct"])
            + bar_html("Received against billed", fig["received"], fig["billed_gross"],
                       fig["received_pct"])
            + bar_html("Cost to date against planned cost", fig["actual_cost"],
                       fig["planned_cost"], fig["cost_pct"]))
    note = ("All figures exclude GST except <i>Still owed</i> and <i>Received</i>. "
            "Planned uses the BOQ's base rates (our cost) on the current revision; actual "
            "uses purchase and work orders (taxable value, issued or not yet delivered), "
            "expenses and site labour wages. The two are compared, never added, so labour "
            "is counted once in each.")
    if not labour_seen:
        note += " Site labour is withheld for your role, so the actual figures exclude it."
    return (f'<div class="pnl-tiles">{tiles}</div>'
            f'<div class="pnl-grid"><div>{pie}</div><div>{bars}</div></div>'
            f'<p class="pnl-note">{note}</p>')
