"""
boqexcess.py — BILLING ABOVE THE BOQ QUANTITY, allowed and never silent
=======================================================================
Ported 27 November 2026 from the client line (Demo_Works `ac887bc`,
FEATURE_GAP.md row 4c), reimplemented against this product's `ra.py`.

The rule
--------
Site measurement exceeding the schedule is normal for a contractor, so the
**BOQ-quantity ceiling is a warning, not a block**. When a line's CUMULATIVE
claim would pass its BOQ quantity, the RA form shows an amber per-line table
(BOQ qty, already claimed, this claim, excess) and asks for ONE reason for the
bill; a blank reason is refused. Saved, the bill carries:

    excess_lines   [{line_id, item_no, leg, boq_qty, previously, this,
                     cumulative_after, excess}]
    excess_reason  the text typed

**snapshotted at save and never recomputed.** A bill with no excess carries
NEITHER key, so every bill raised within its schedule — and every bill that
existed before this — is byte-identical, and so is its print.

⚠ **Only the BOQ-quantity ceiling softened** — `ra.overclaims()` reason
  `"overclaim"`. The installation MEASUREMENT cap (`"overmeasured"`), a line
  not in the schedule and the dispatched cap on a bill raised from challans
  (`ra.dc_overclaims()`) stay hard blocks, unchanged. `ra.overclaims()`
  itself is unchanged: it is the detector.
⚠ **The cumulative is DERIVED by summing** (`ra.overclaims()`), keyed on
  `line_id` and never on `item_no`; the item number is carried only as the
  label a person reads. The snapshot records what was true at save; nothing
  reads it back to decide anything.
⚠ **A leaf.** `store` and `pipeline` only. The band is SCREEN-ONLY
  (`no-print`) and renders "" when there is nothing to say.
"""

import pipeline as P

LINES_KEY = "excess_lines"
REASON_KEY = "excess_reason"
REASON_FIELD = "excess_reason"     # the posted box's name
REASON_MAX = 500

_AMBER = ("background:#fffbeb;border:1px solid #fcd34d;color:#78350f;"
          "border-radius:8px;padding:.7rem .9rem;margin:.6rem 0 1rem;"
          "font-size:.85rem;")


def _q(x) -> str:
    """A quantity as people write it: no trailing zeros."""
    v = round(float(x or 0.0), 3)
    return f"{v:,.3f}".rstrip("0").rstrip(".")


def snapshot(rows) -> list:
    """The stored shape, from `ra.overclaims()`'s rows (`approved`,
    `cumulative`, `over`) or from this module's own."""
    out = []
    for r in rows or []:
        out.append({
            "line_id": str(r.get("line_id") or ""),
            "item_no": str(r.get("item_no") or ""),
            "leg": str(r.get("leg") or ""),
            "boq_qty": round(float(r.get("boq_qty", r.get("approved")) or 0.0), 6),
            "previously": round(float(r.get("previously") or 0.0), 6),
            "this": round(float(r.get("this") or 0.0), 6),
            "cumulative_after": round(float(r.get("cumulative_after",
                                                  r.get("cumulative")) or 0.0), 6),
            "excess": round(float(r.get("excess", r.get("over")) or 0.0), 6),
        })
    return out


def read_reason(form) -> str:
    """The typed reason, whitespace collapsed and capped; "" when blank."""
    raw = (form.get(REASON_FIELD) if form is not None else "") or ""
    return " ".join(str(raw).split())[:REASON_MAX]


def refusal(rows) -> str:
    n = len(rows or [])
    return (f"{n} line{'' if n == 1 else 's'} would be billed above the BOQ "
            f"quantity. That is allowed: give the reason in the amber box "
            f"(“Reason for billing above BOQ”) and save again.")


def stamp(rec: dict, rows: list, reason: str) -> None:
    """Write the snapshot onto `rec`, or remove both keys when there is none."""
    if rows:
        rec[LINES_KEY] = snapshot(rows)
        rec[REASON_KEY] = str(reason or "")
    else:
        rec.pop(LINES_KEY, None)
        rec.pop(REASON_KEY, None)


def _table(rows) -> str:
    body = "".join(
        f'<tr><td>{P.esc(r["item_no"]) or "&mdash;"}</td>'
        f'<td>{P.esc(r["leg"])}</td>'
        f'<td style="text-align:right;">{_q(r["boq_qty"])}</td>'
        f'<td style="text-align:right;">{_q(r["previously"])}</td>'
        f'<td style="text-align:right;">{_q(r["this"])}</td>'
        f'<td style="text-align:right;"><b>{_q(r["excess"])}</b></td></tr>'
        for r in rows)
    return ('<table style="width:100%;margin:.5rem 0;border-collapse:collapse;'
            'font-size:.82rem;"><thead><tr>'
            '<th style="text-align:left;">Item</th><th style="text-align:left;">Leg</th>'
            '<th style="text-align:right;">BOQ qty</th>'
            '<th style="text-align:right;">Already claimed</th>'
            '<th style="text-align:right;">This claim</th>'
            '<th style="text-align:right;">Excess</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


def warning_html(rows, reason: str = "") -> str:
    """The amber per-line warning and the ONE reason box, for the entry form
    (it sits INSIDE the form). "" when no line is above its BOQ quantity."""
    rows = snapshot(rows)
    if not rows:
        return ""
    return (f'<div class="boq-excess-warn no-print" style="{_AMBER}">'
            f'<b>&#9888; Billed above BOQ quantity</b> &mdash; allowed, and recorded '
            f'on the bill with your reason.{_table(rows)}'
            f'<label for="{REASON_FIELD}"><b>Reason for billing above BOQ</b> '
            f'(required, one for the whole bill)</label>'
            f'<textarea id="{REASON_FIELD}" name="{REASON_FIELD}" rows="2" '
            f'maxlength="{REASON_MAX}" style="width:100%;margin-top:.3rem;">'
            f'{P.esc(reason)}</textarea></div>')


def band_html(rec: dict) -> str:
    """The screen-only band for a bill's VIEW page, from the STORED snapshot
    only. "" when the bill carries none."""
    rows = snapshot((rec or {}).get(LINES_KEY))
    if not rows:
        return ""
    return (f'<div class="boq-excess-band no-print" style="{_AMBER}">'
            f'<b>&#9888; Billed above BOQ</b> &mdash; reason: '
            f'{P.esc((rec or {}).get(REASON_KEY) or "")}{_table(rows)}</div>')
