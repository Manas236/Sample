"""
branding.py — the house identity, as configured at /settings
=============================================================
Single source of truth for everything company-specific: legal identity, contact
block, the document-number prefix, the print colour tokens and the logo. No
other module should hard-code a company name, a hex colour or an image — read
it from here instead.

╔══════════════════════════════════════════════════════════════════════════╗
║  NOTHING COMPANY-SPECIFIC IS WRITTEN IN THIS FILE                         ║
║  ------------------------------------------------------------------------║
║  Every identity value below ships BLANK. The company that runs this       ║
║  application types its own at /settings; `settings.py` stores them and    ║
║  calls apply_settings() / apply_logo() to push them onto this module.     ║
║  A blank statutory field renders as a visible amber "add …" chip in the   ║
║  app and on every printed document, so nothing goes out quietly wrong.    ║
║  A blank logo renders as the company name in text — never a broken image  ║
║  and never an empty box.                                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import html
import re
import urllib.parse

# =============================================================================
# 1. IDENTITY  (defaults — every one of them is a /settings field)
# =============================================================================
COMPANY_NAME      = ""    # trading name, as it heads the letterhead
COMPANY_LEGAL     = ""    # e.g. "M/s Example Projects Pvt Ltd"
COMPANY_TAGLINE   = ""    # one line under the name, e.g. "Civil & MEP Contractors"
COMPANY_ADDR      = ""
COMPANY_PHONE     = ""
COMPANY_EMAIL     = ""
COMPANY_WEB       = ""
COMPANY_GSTIN     = ""
COMPANY_PAN       = ""
COMPANY_BRANCHES  = ""
COMPANY_SIGNATORY = "Authorised Signatory"

# Short form used in reference numbers (e.g. "AB/TI/26-27/0001"). Blank is a
# valid configuration: the series then print without a prefix
# ("TI/26-27/0001"). It is a /settings field like the rest, but it is NOT a
# statutory detail, so a blank one never lights the nav's amber dot.
COMPANY_SHORT     = ""

# The name the browser tab and the nav show. DERIVED from COMPANY_NAME by
# apply_settings() — never set it directly. "QMS" until a name is entered.
APP_NAME_FALLBACK = "QMS"
APP_NAME          = APP_NAME_FALLBACK
APP_SUBTITLE      = "Quotation & Catalogue System"


# =============================================================================
# 1b. BANK DETAILS  (proforma invoice and RA tax invoice only)
# =============================================================================
# A proforma invoice is a request for money, so the remittance account has to
# print on it — a PI without these is not actionable by the customer's accounts
# department. Blank fields render as amber "add …" chips through field() exactly
# like the statutory block above, so an incomplete PI cannot go out looking
# finished. They are deliberately NOT used on the quotation: a quotation is an
# offer, not a demand for payment, and publishing the account number wider than
# necessary is a fraud surface.
BANK_NAME         = ""    # e.g. "Example Bank Ltd."
BANK_ACCOUNT_NAME = ""    # the name the account is held in (may differ from COMPANY_NAME)
BANK_ACCOUNT_NO   = ""
BANK_IFSC         = ""
BANK_BRANCH       = ""


# =============================================================================
# 1c. RUNTIME OVERRIDES  (the /settings page writes these)
# =============================================================================
# The values above are the *defaults*. `settings.py` stores the company's real
# details in STORE["settings"]["company"] and calls apply_settings() to push
# them onto this module, so the whole app re-brands without anyone editing
# Python.
#
# This only works because consumers read `B.COMPANY_ADDR` at render time, not
# `from branding import COMPANY_ADDR` at import time — a from-import binds a
# copy and would freeze at the default forever. Keep it that way: reach for
# these through the module (`B.X`), never by name.

# The fields a printed document needs. A blank one prints an amber chip, and
# the nav's amber dot stays lit until every one of them is filled in.
SETTINGS_KEYS = (
    "COMPANY_NAME",
    "COMPANY_LEGAL", "COMPANY_TAGLINE", "COMPANY_ADDR", "COMPANY_PHONE",
    "COMPANY_EMAIL", "COMPANY_WEB", "COMPANY_GSTIN", "COMPANY_PAN",
    "COMPANY_BRANCHES", "COMPANY_SIGNATORY",
    "BANK_NAME", "BANK_ACCOUNT_NAME", "BANK_ACCOUNT_NO", "BANK_IFSC",
    "BANK_BRANCH",
)

# Stored and applied exactly like the keys above, but NOT a statutory detail:
# blank is a valid configuration, so these never light the amber dot and never
# count toward the completeness meter.
OPTIONAL_KEYS = ("COMPANY_SHORT",)

# Snapshot of the import-time values, so a cleared field falls back to the
# module default rather than to an empty string. Taken once, at import, before
# anything can have overwritten it.
DEFAULTS = {k: globals()[k] for k in SETTINGS_KEYS + OPTIONAL_KEYS}


def app_name_of(company_name: str) -> str:
    """
    The tab/nav name for a trading name: an ALL-CAPS letterhead name reads as
    title case in a browser tab ("ACME BUILDERS" -> "Acme Builders"); a name
    typed in mixed case is kept exactly as typed. Blank -> APP_NAME_FALLBACK.
    """
    name = str(company_name or "").strip()
    if not name:
        return APP_NAME_FALLBACK
    return name.title() if name.isupper() else name


def apply_settings(saved: dict) -> None:
    """
    Push saved settings onto this module. Idempotent; safe to call repeatedly.

    A key that is missing or blank falls back to its DEFAULTS entry, which is
    what makes "clear the field and save" restore the default instead of
    leaving a permanent blank.
    """
    saved = saved or {}
    for key in SETTINGS_KEYS + OPTIONAL_KEYS:
        value = str(saved.get(key, "") or "").strip()
        globals()[key] = value or DEFAULTS[key]
    globals()["APP_NAME"] = app_name_of(COMPANY_NAME)
    _refresh_icon()


def current_settings() -> dict:
    """The live value of every statutory field — what the amber dot counts."""
    return {k: globals()[k] for k in SETTINGS_KEYS}


def current_optional() -> dict:
    """The live value of every optional field (the document-number prefix)."""
    return {k: globals()[k] for k in OPTIONAL_KEYS}


def _esc(v) -> str:
    """
    HTML-escape a value on its way onto a page.

    `pipeline.esc()` is the same call and is what the rest of the app uses, but
    this module imports nothing of ours on purpose — it sits at the bottom of
    the graph beside `pipeline.py` itself — so it reaches `html.escape`
    directly rather than growing an import.
    """
    return html.escape(str(v or ""), quote=True)


def field(value: str, hint: str) -> str:
    """
    Render an identity field, or a visible placeholder when it is still blank.

    Blank statutory details must never look like a deliberate omission on a
    document that goes to a customer, so they are flagged rather than hidden.

    ⚠ **The value is escaped here, and that is load-bearing.** Every field this
    renders comes from `/settings`, which means it is typed by a user — and an
    authenticated insider is part of the threat model. This is the single
    accessor for the statutory and bank blocks, so escaping here closes the
    letterhead on every document in the app at once. The chip is markup this
    function writes itself and is deliberately outside the escaper; `hint` is a
    literal at every call site.
    """
    value = _esc(value).strip()
    return value if value else f'<span class="todo-chip">add {hint}</span>'


def name_html(accent_class: str) -> str:
    """
    The company name with its last word in the accent colour — the two-tone
    letterhead wordmark. A one-word name prints in one colour; a blank name
    prints the amber "add company name" chip, never nothing.

    ⚠ **Escaped here.** The name is a /settings field — user text. `accent_class`
    is a literal at every call site.
    """
    name = str(COMPANY_NAME or "").strip()
    if not name:
        return field("", "company name")
    head, _, tail = name.rpartition(" ")
    if not head:
        return _esc(name)
    return f'{_esc(head)} <span class="{accent_class}">{_esc(tail)}</span>'


def name_text() -> str:
    """
    The company name as plain, ESCAPED text, for a footer or a heading — the
    app name ("QMS") until a company name has been entered, so a footer never
    opens on a bare separator. Escaped inside, like field(): do not escape the
    result again.
    """
    return _esc(str(COMPANY_NAME or "").strip() or APP_NAME)


def tagline_html(css_class: str = "lh-tag") -> str:
    """
    The tagline line under a letterhead name — `— tagline —` — or "" when no
    tagline is set, so a blank one never prints two dashes around nothing.
    """
    tag = str(COMPANY_TAGLINE or "").strip()
    if not tag:
        return ""
    return f'<div class="{css_class}">&#8212; {_esc(tag)} &#8212;</div>'


def foot_line() -> str:
    """
    The house line at the foot of a printed page — `legal name · tagline` —
    with a blank part left out rather than printed as a dangling separator.
    ESCAPED inside; `&middot;` is the house separator this writes itself.
    """
    parts = [str(COMPANY_LEGAL or COMPANY_NAME or "").strip(),
             str(COMPANY_TAGLINE or "").strip()]
    return " &middot; ".join(_esc(p) for p in parts if p) or _esc(APP_NAME)


def has(*values: str) -> bool:
    """True when every field passed has actually been filled in."""
    return all((v or "").strip() for v in values)


# =============================================================================
# 2. PRINT PALETTE  (the printed documents' colours — the SCREEN palette is
#    theme.py's; these are what the letterhead, the totals and the chips print)
# =============================================================================
RED        = "#D5121A"   # primary accent — the letterhead name, rules, totals
RED_DK     = "#A50D14"   # hover / pressed
RED_LT     = "#FDECEC"   # tinted surfaces, pills
NAVY       = "#2A086E"   # headings, document ink, the name's accent word
NAVY_DK    = "#1C0449"
NAVY_LT    = "#EDEAF9"
SAFFRON    = "#F2944A"   # a small accent only

# Dark-surface variants (the news module runs on a near-black canvas, where the
# print reds and navies go muddy).
RED_ON_DARK    = "#FF5A5F"
RED_ON_DARK_DK = "#E3392F"
RED_TINT_DARK  = "#3A1114"
INK        = "#1A1626"   # body text, warmed toward the navy
MUTED      = "#6B6478"
BORDER     = "#E4E0EC"
SURFACE    = "#FFFFFF"
CANVAS     = "#F6F4F9"

# CSS custom properties. Injected once at the top of the shared stylesheet so
# every existing var(--brand) reference re-themes without being touched.
CSS_TOKENS = f"""
  :root {{
    --bg:        {CANVAS};
    --surface:   {SURFACE};
    --brand:     {RED};
    --brand-dk:  {RED_DK};
    --brand-lt:  {RED_LT};
    --navy:      {NAVY};
    --navy-dk:   {NAVY_DK};
    --navy-lt:   {NAVY_LT};
    --saffron:   {SAFFRON};
    --text:      {INK};
    --muted:     {MUTED};
    --border:    {BORDER};
    --shadow-sm: 0 1px 3px rgba(26,22,38,.08), 0 1px 2px rgba(26,22,38,.06);
    --shadow-md: 0 6px 20px rgba(42,8,110,.14), 0 2px 6px rgba(26,22,38,.08);
    --radius:    14px;
    --font:      'DM Sans', 'Segoe UI', system-ui, sans-serif;
  }}

  /* Flags an identity field that still needs the company's real data. */
  .todo-chip {{
    display: inline-block;
    background: #FFF4D6;
    color: #8A5A00;
    border: 1px dashed #E0A93B;
    border-radius: 5px;
    padding: 0 .38em;
    font-size: .82em;
    font-weight: 600;
    font-style: normal;
    letter-spacing: 0;
    white-space: nowrap;
  }}
"""

# =============================================================================
# 2b. CHART PALETTE  (dashboard only — imported by dashboard.py, not by BASE_STYLES)
# =============================================================================
# Charts do not get to pick colours by eye. Two roles, two rules:
#
#   ORDINAL  — the sales funnel. Stage order carries meaning (Budgetary → PO
#              Expected), so the colour has to carry that order too: ONE hue,
#              stepping light → dark as the deal nears close, with the lightest
#              step held at 2.09:1 on white so it never dissolves into the
#              surface.
#
#   STATUS   — won / open / lost. These mean good-neutral-bad, so they wear
#              reserved status colours, never a series palette, and they always
#              ship with a text label beside the swatch (never colour alone).
#
# Both sets were checked with the dataviz validator rather than judged by eye:
# the ramp passes monotone-lightness, adjacent-ΔL and light-end contrast; the
# status trio passes the lightness band, chroma floor, CVD separation (worst
# adjacent pair ΔE 20.3 protan) and 3:1 contrast on the light surface.
# Re-run the validator if you change a single hex here.
CHART_NAVY = [
    "#B0ABF9",   # step 0 — earliest stage, lightest
    "#928BDC",
    "#756CC0",
    "#594DA5",
    "#402E89",
    "#2A086E",   # step 5 — closest to close
]

CHART_WON     = "#0CA30C"   # status: good
CHART_LOST    = "#D03B3B"   # status: critical
CHART_SERIOUS = "#EC835A"   # status: serious  — chase this today
CHART_WARN    = "#FAB219"   # status: warning  — chase this week
CHART_OPEN    = CHART_NAVY[2]   # mid-ramp — "still in the funnel"

# Chart-only custom properties. Kept OUT of CSS_TOKENS so the quotation
# document and the other pages don't carry a palette they never draw with.
CHART_TOKENS = f"""
  :root {{
    --c-stage-0: {CHART_NAVY[0]};
    --c-stage-1: {CHART_NAVY[1]};
    --c-stage-2: {CHART_NAVY[2]};
    --c-stage-3: {CHART_NAVY[3]};
    --c-stage-4: {CHART_NAVY[4]};
    --c-stage-5: {CHART_NAVY[5]};
    --c-won:     {CHART_WON};
    --c-lost:    {CHART_LOST};
    --c-serious: {CHART_SERIOUS};
    --c-warn:    {CHART_WARN};
    --c-open:    {CHART_OPEN};
    --c-grid:    #ECE9F2;
    --c-track:   #F1EEF7;
  }}
"""

# =============================================================================
# 3. ARTWORK — the logo is a /settings upload, never a file in this repository
# =============================================================================
# Logos are inlined as data URIs rather than served from /static: every page in
# this app is a self-contained string, and a printed or emailed document must
# still show the logo with no server to fetch it from.
#
# `logo.py` re-encodes an upload into three PNGs (256 px for the letterhead,
# 64 px for the nav, 32 px for the tab) and `settings.py` stores them in
# STORE["settings"]["logo"]; apply_logo() puts them here. With no logo the
# three are "", logo_img() returns "", and every page prints the company name
# in text instead — there is no artwork to fall back to, by design.
LOGO_URI     = ""        # nav bar / small chrome (64 px)
LOGO_DOC_URI = ""        # letterhead, print quality (256 px)
FAVICON_URI  = ""        # browser tab (32 px) — or the monogram below
HEAD_ICON    = ""        # the <link rel="icon"> every page drops into <head>

# The only shape a stored logo may have. Anything else in the record — a value
# edited straight into MySQL, say — is ignored rather than put into an <img src>.
_LOGO_RE = re.compile(r"^data:image/png;base64,[A-Za-z0-9+/]+={0,2}$")
_LOGO_MAX = 400 * 1024

# The monogram's colours. A literal on purpose: this module imports nothing,
# and the tab icon must not move when a screen colour does.
_MONO_BG = "#0F1B2D"
_MONO_FG = "#FFFFFF"


def _logo_value(rec: dict, key: str) -> str:
    val = (rec or {}).get(key) or ""
    if isinstance(val, str) and len(val) <= _LOGO_MAX and _LOGO_RE.match(val):
        return val
    return ""


def has_logo() -> bool:
    """True when a logo has been uploaded at /settings."""
    return bool(LOGO_DOC_URI or LOGO_URI)


def initials() -> str:
    """Up to two letters for the monogram — the first letters of the first two
    words of the trading name, or the first letter of the app name."""
    words = [w for w in re.split(r"[^0-9A-Za-z]+", str(COMPANY_NAME or "")) if w]
    if not words:
        return APP_NAME_FALLBACK[:1].upper()
    return "".join(w[0] for w in words[:2]).upper()


def monogram_uri() -> str:
    """A 32 px SVG square carrying initials(): the tab icon when no logo is set."""
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
           f"<rect width='32' height='32' rx='7' fill='{_MONO_BG}'/>"
           f"<text x='16' y='21' text-anchor='middle' font-family='Arial,sans-serif' "
           f"font-size='{13 if len(initials()) > 1 else 16}' font-weight='700' "
           f"fill='{_MONO_FG}'>{_esc(initials())}</text></svg>")
    return "data:image/svg+xml," + urllib.parse.quote(svg, safe="")


def _refresh_icon() -> None:
    """Re-derive the tab icon after the name or the logo changed."""
    fav = FAVICON_URI if (FAVICON_URI and has_logo()) else monogram_uri()
    globals()["HEAD_ICON"] = f'<link rel="icon" href="{fav}"/>'


def apply_logo(rec: dict) -> None:
    """
    Push the stored logo record onto this module. Idempotent. A missing or
    malformed record clears all three, which is the no-logo configuration.
    """
    globals()["LOGO_DOC_URI"] = _logo_value(rec, "doc")
    globals()["LOGO_URI"] = _logo_value(rec, "nav") or LOGO_DOC_URI
    globals()["FAVICON_URI"] = _logo_value(rec, "favicon")
    _refresh_icon()


_refresh_icon()


def page_title(page: str) -> str:
    """
    Consistent browser-tab titles: 'Quotations · <company>'.

    ⚠ **`page` is escaped here.** A `<title>` element is RCDATA, so a `<script>`
    inside it does not run — but the seven characters `</title>` end it, and
    everything after them is parsed as ordinary HTML. Nine routes reached this
    with a record's `ref` straight off the store, so a document reference
    reading `</title><script>…` executed on every page that named it. The app
    name is derived from the /settings company name, so it is escaped too.
    `&middot;` is the house separator this function writes itself and stays
    outside the escaper.

    Callers pass plain text — escaping twice prints `&amp;` for a `&` in a
    reference, the class of bug `tests/test_entity_fallbacks.py` catches.
    """
    return f"{_esc(page)} &middot; {_esc(APP_NAME)}"


def logo_img(px: int = 30, doc: bool = False, alt: str = "") -> str:
    """<img> for the uploaded logo, or "" when none is set. `doc=True` uses the
    higher-resolution copy."""
    uri = LOGO_DOC_URI if doc else LOGO_URI
    if not uri:
        return ""
    # `uri` is a validated base64 PNG data URI (see _LOGO_RE), generated by
    # logo.py rather than typed, and is deliberately left raw.
    alt = _esc(alt or f"{COMPANY_NAME or APP_NAME} logo")
    return (f'<img src="{uri}" alt="{alt}" width="{px}" height="{px}" '
            f'style="width:{px}px;height:{px}px;object-fit:contain;display:block;"/>')


def logo_mark(px: int = 56, css_class: str = "lh-mark") -> str:
    """The letterhead's logo slot — `<div class="lh-mark"><img…></div>` — or ""
    with no logo, so a document never prints an empty box beside the name."""
    img = logo_img(px, doc=True)
    return f'<div class="{css_class}">{img}</div>' if img else ""


def monogram_html(px: int = 28) -> str:
    """
    The logo when one is set, otherwise a square carrying the initials — for
    the few chrome spots that are ONLY a mark (the collapsed rail), where
    leaving out the image would leave an empty link.
    """
    img = logo_img(px)
    if img:
        return img
    size = max(12, int(px * .42))
    return (f'<span class="brand-mono" aria-hidden="true" style="display:inline-flex;'
            f'align-items:center;justify-content:center;width:{px}px;height:{px}px;'
            f'border-radius:7px;background:{_MONO_BG};color:{_MONO_FG};'
            f'font-weight:700;font-size:{size}px;letter-spacing:.02em;'
            f'line-height:1;">{_esc(initials())}</span>')
