"""
pricesummary.py — the one-page PRICE SUMMARY cover and the terms library
========================================================================
Ported 27 November 2026 from the client line (Demo_Works `1e9bc9a` and
`71ea78a`, FEATURE_GAP.md rows 1a and 1b) as a reimplementation, not a copy:
the client line seeded its own customer's terms and a trade-specific title into
this module, and none of that is here. This product ships **no terms at all**.
The company builds its own library at `/settings/terms`.

What it does
------------
A printed BOQ can open with a one-page cover: the company's letterhead, who it
is for, one row per section with its supply, installation and total, the grand
total in words, a tax line, and a numbered **Terms & Conditions** list. The
detail schedule follows on the next page, unchanged.

What lives here, and what does not
----------------------------------
* **Layout only.** `summary_html()` lays out rows the CALLER has already priced
  and formatted. It computes no subtotal, no tax and no round-off: those stay
  in the chain (`boq.section_totals()`), the same rule `docsheet.py` follows
  for its totals rows. A cover that did its own sums could disagree with the
  detail pages; one that prints the chain's own figures cannot.
* **The library** — `STORE["settings"]["price_summary"]`:

      title      str   the cover's heading; blank prints DEFAULT_TITLE
      tax_line   str   the line under the total; blank prints DEFAULT_TAX_LINE
      library    list  [{id, text, category, on}]  — `on` = ticked by default
                       when a document's terms are first chosen

  It is read here and not in `settings.py` because `boq.py` may not import
  `settings.py` (`tests/test_import_directions.py`) — the reason `series.py`
  exists. `settings.py` owns the page that edits it.
* **Nothing is seeded.** CLAUDE.md: nothing seeds on a page view, and a fresh
  checkout is empty. An absent record reads as an empty library and the two
  defaults below.

The per-document fields (on a BOQ record), all optional
-------------------------------------------------------
    price_summary_on    bool  absent = OFF, so every BOQ raised before this
                              prints byte-for-byte as it did
    summary_terms       list  the document's OWN terms, as text
    print_orientation   str   "landscape" (absent = the BOQ's own landscape
                              page) or "portrait"

The snapshot rule
-----------------
A printed document prints ITS OWN `summary_terms`, never the live library. The
chosen terms are COPIED into the record when they are saved on the document,
and editing the library afterwards changes no document already raised — the
same rule as `/ra/print` reading the bill and never the live BOQ.

Imports
-------
`store` and `pipeline` only, so `boq.py` and `settings.py` can both reach it
and it can reach neither.
"""

import uuid

import pipeline as P
from store import STORE

RECORD = "price_summary"
DEFAULT_TITLE = "PRICE SUMMARY"
DEFAULT_TAX_LINE = "GST extra as applicable, at the rates in force on the date of invoice."

CATEGORIES = ("Scope", "Exclusions", "Site", "Payment", "Taxes", "Commercial",
              "Delivery", "Warranty", "Legal")
FALLBACK_CATEGORY = "Commercial"

FIELD_ON = "price_summary_on"
FIELD_TERMS = "summary_terms"
FIELD_ORIENT = "print_orientation"

PORTRAIT, LANDSCAPE = "portrait", "landscape"
ORIENTATIONS = (LANDSCAPE, PORTRAIT)

MAX_TERMS = 60
MAX_LIBRARY = 300
MAX_TERM_CHARS = 1000
MAX_TEXT_CHARS = 200


# =============================================================================
# CLEANING
# =============================================================================

def clean_text(raw, cap: int = MAX_TERM_CHARS) -> str:
    """One line of text: whitespace collapsed, capped. Never escaped here —
    escaping happens where it reaches HTML (CLAUDE.md, ABOUT.md §9)."""
    return " ".join(str(raw or "").split())[:cap]


def _norm(text: str) -> str:
    return clean_text(text).casefold()


def _entry(text: str, category: str = "", on: bool = False, eid: str = "") -> dict:
    return {"id": eid or uuid.uuid4().hex[:12],
            "text": clean_text(text),
            "category": category if category in CATEGORIES else FALLBACK_CATEGORY,
            "on": bool(on)}


# =============================================================================
# THE LIBRARY — STORE["settings"]["price_summary"]
# =============================================================================

def _rec() -> dict:
    rec = STORE.get("settings", {}).get(RECORD)
    return rec if isinstance(rec, dict) else {}


def title() -> str:
    return clean_text(_rec().get("title"), MAX_TEXT_CHARS) or DEFAULT_TITLE


def tax_line() -> str:
    return clean_text(_rec().get("tax_line"), MAX_TEXT_CHARS) or DEFAULT_TAX_LINE


def library() -> list:
    """The library as stored, cleaned on the way out. Never written here."""
    out = []
    for e in _rec().get("library") or []:
        if isinstance(e, dict) and clean_text(e.get("text")):
            out.append(_entry(e.get("text"), e.get("category", ""),
                              e.get("on", False), str(e.get("id") or "")))
    return out


def default_terms() -> list:
    """The texts a document starts with: the library entries ticked ON."""
    return [e["text"] for e in library() if e["on"]]


def save_library(title_text: str, tax_text: str, entries: list) -> None:
    """Replace the record. `entries` is a list of {id?, text, category, on};
    blank texts and duplicates (case-insensitive) are dropped, order kept."""
    seen, clean = set(), []
    for e in entries:
        ent = _entry(e.get("text"), e.get("category", ""), e.get("on", False),
                     str(e.get("id") or ""))
        key = _norm(ent["text"])
        if not key or key in seen:
            continue
        seen.add(key)
        clean.append(ent)
    STORE["settings"][RECORD] = {
        "title": clean_text(title_text, MAX_TEXT_CHARS),
        "tax_line": clean_text(tax_text, MAX_TEXT_CHARS),
        "library": clean[:MAX_LIBRARY],
    }


def add_to_library(texts: list, category: str = FALLBACK_CATEGORY) -> int:
    """Append texts the library does not already hold (OFF by default).
    Returns how many were added."""
    rec = _rec()
    lib = library()
    have = {_norm(e["text"]) for e in lib}
    added = 0
    for t in texts:
        if _norm(t) and _norm(t) not in have and len(lib) < MAX_LIBRARY:
            lib.append(_entry(t, category, False))
            have.add(_norm(t))
            added += 1
    if added:
        save_library(rec.get("title", ""), rec.get("tax_line", ""), lib)
    return added


# =============================================================================
# THE PER-DOCUMENT FIELDS
# =============================================================================

def is_on(doc: dict) -> bool:
    return bool((doc or {}).get(FIELD_ON))


def terms_of(doc: dict) -> list:
    return [clean_text(t) for t in ((doc or {}).get(FIELD_TERMS) or [])
            if clean_text(t)][:MAX_TERMS]


def orientation_of(doc: dict) -> str:
    o = (doc or {}).get(FIELD_ORIENT)
    return o if o in ORIENTATIONS else LANDSCAPE


def carry_fields(src: dict) -> dict:
    """The fields a revision inherits from the document it revises."""
    out = {}
    for k in (FIELD_ON, FIELD_TERMS, FIELD_ORIENT):
        if k in (src or {}):
            out[k] = src[k]
    return out


def fields_from_form(form) -> tuple:
    """
    Read the per-document editor. Returns (fields, own_terms, error).

    The terms list is: every library entry whose id was ticked (`lib_pick`),
    in LIBRARY order, then each non-blank line of `own_terms`, in the order
    typed. `own_terms` comes back separately so the caller can offer
    "also save to the library".
    """
    picked = set(form.getlist("lib_pick"))
    terms = [e["text"] for e in library() if e["id"] in picked]
    own = [clean_text(x) for x in (form.get("own_terms") or "").splitlines()]
    own = [x for x in own if x]
    seen, merged = set(), []
    for t in terms + own:
        if _norm(t) not in seen:
            seen.add(_norm(t))
            merged.append(t)
    if len(merged) > MAX_TERMS:
        return {}, own, f"At most {MAX_TERMS} terms on one document."
    orient = form.get(FIELD_ORIENT) or LANDSCAPE
    if orient not in ORIENTATIONS:
        return {}, own, "Pick Portrait or Landscape."
    return ({FIELD_ON: bool(form.get(FIELD_ON)), FIELD_TERMS: merged,
             FIELD_ORIENT: orient}, own, "")


# =============================================================================
# PRINT
# =============================================================================

# Plain string, interpolated as a value — nothing in it needs doubling.
SUMMARY_CSS = """
<style>
  .ps-cover { break-after:page; page-break-after:always; }
  .ps-title { text-align:center; font-weight:700; letter-spacing:.06em;
              font-size:13pt; margin:2mm 0 3mm; }
  .ps-table { width:100%; border-collapse:collapse; margin-top:3mm; }
  .ps-table th, .ps-table td { border:var(--rule); padding:5px 6px; }
  .ps-table th { text-align:left; font-weight:700; }
  .ps-table .ps-n  { width:12mm; text-align:center; }
  .ps-table .ps-amt { width:32mm; text-align:right; white-space:nowrap; }
  .ps-table tr.ps-total td { font-weight:700; }
  .ps-words { margin-top:2mm; font-style:italic; }
  .ps-tax   { margin-top:1mm; font-weight:700; }
  .ps-terms { margin-top:5mm; }
  .ps-terms-title { font-weight:700; margin-bottom:1.5mm; }
  .ps-terms ol { margin:0; padding-left:6mm; }
  .ps-terms li { margin:0 0 1mm; }
</style>
"""

# A portrait page for a sheet whose own stylesheet asks for landscape: a later
# @page rule of equal specificity wins (docsheet.LANDSCAPE_CSS's mechanism, the
# other way round), and the portrait column widths the BOQ already carries
# (`boq.BOQ_DOC_STYLES`, `orientation:portrait`) then apply on their own.
PORTRAIT_CSS = """
<style>
  @media print { @page { size:A4 portrait; margin:9mm 8mm 8mm; } }
  .boq-outer { max-width:210mm; }
</style>
"""


def orientation_css(doc: dict) -> str:
    return PORTRAIT_CSS if orientation_of(doc) == PORTRAIT else ""


def summary_html(*, meta_html: str, heads: tuple, rows: list, total_cells: list,
                 words: str, terms: list) -> str:
    """
    The cover's body. Every argument is the caller's, already formatted:

        meta_html     the header block, built and escaped by the caller
        heads         column heads for the amount columns, e.g. ("Supply", …)
        rows          [(sr, description, [amount strings])] — sr and
                      description are escaped HERE; amounts are not (money is
                      never escaped, ABOUT.md §9)
        total_cells   [amount strings] for the TOTAL row
        words         the amount in words, as the chain renders it
        terms         the document's own terms (`terms_of(doc)`), escaped HERE
    """
    head_cells = "".join(f'<th class="ps-amt">{P.esc(h)}</th>' for h in heads)
    body = "".join(
        f'<tr><td class="ps-n">{P.esc(sr)}</td><td>{P.esc(desc)}</td>'
        + "".join(f'<td class="ps-amt">{a}</td>' for a in amts) + "</tr>"
        for sr, desc, amts in rows)
    total = ("".join(f'<td class="ps-amt">{a}</td>' for a in total_cells))
    terms_html = ""
    if terms:
        items = "".join(f"<li>{P.esc(t)}</li>" for t in terms)
        terms_html = (f'<div class="ps-terms"><div class="ps-terms-title">'
                      f'Terms &amp; Conditions</div><ol>{items}</ol></div>')
    return f"""
      <div class="ps-title">{P.esc(title())}</div>
      {meta_html}
      <table class="ps-table">
        <thead><tr><th class="ps-n">Sr.</th><th>Description</th>{head_cells}</tr></thead>
        <tbody>{body}
          <tr class="ps-total"><td></td><td>TOTAL</td>{total}</tr>
        </tbody>
      </table>
      <div class="ps-words">{words}</div>
      <div class="ps-tax">{P.esc(tax_line())}</div>
      {terms_html}"""
