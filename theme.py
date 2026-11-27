"""
theme.py — the SCREEN palette.  A leaf: it imports nothing at all.

The printed documents keep their own palette (`branding.py` §2 — the
letterhead red, the document navy, the chips). This module is what every
SCREEN reads: the app shell, the dashboard, the registers and forms, the
sign-in pages and the public landing page.

How it reaches a page
---------------------
`SCREEN_TOKENS` is a `<style>` block that re-points the shared custom
properties (`--brand`, `--navy`, `--bg`, `--radius`, …) at this palette on
`:root`. It rides with the app shell (`chrome.CHROME_STYLES`, emitted by
`_nav()`) and with the two standalone public pages — and with NOTHING that a
print route renders. `docsheet.SHEET_STYLES` / `chrome.BASE_STYLES`, which the
printed sheets carry, still declare the print palette, so a printed document's
colours do not move (`tests/test_print_golden.py` hashes every one of them).

A document is also drawn INSIDE screen pages (`/quotation/view` and the other
document views). There the shell re-declares the print palette on the
document's own container, `.doc-outer` / `.quotation-doc`
(`chrome.DOC_PALETTE_SCOPE`), so a document looks the same on a screen page
as it does on paper.

Contrast — WCAG 2.x, measured with the relative-luminance formula
-----------------------------------------------------------------
Every pairing below that carries body text is at least 4.5 : 1.
`tests/test_theme.py` recomputes each one and fails under the floor.

    text   #1F2937 on background #F6F7F9   13.69
    text   #1F2937 on surface    #FFFFFF   14.68
    muted  #6B7280 on surface    #FFFFFF    4.83
    muted  #6B7280 on background #F6F7F9    4.51
    ink    #0F1B2D on surface    #FFFFFF   17.28   (and white on ink: rail)
    primary #2563EB on surface   #FFFFFF    5.17   (links; white on it 5.17)
    primary #2563EB on primary-soft #E8F0FE 4.51
    white  on primary-hover #1D4ED8          6.70
    accent #0F766E on accent-soft #E6F4F1   4.84
    amber  #B45309 on amber-bg   #FEF3C7    4.51
    danger-ink #B91C1C on danger-bg #FEE2E2 5.30   ← see DANGER_INK
    danger #DC2626 on surface    #FFFFFF    4.83
    success #15803D on success-bg #DCFCE7   4.57
    rail text #CBD5E1 on ink     #0F1B2D   11.64

⚠ **`#DC2626` on its own tint `#FEE2E2` is 3.95 : 1 — under the floor.** The
  brief's danger pair is kept as given for borders, icons and text on white;
  TEXT on the danger tint uses `DANGER_INK` (#B91C1C, the same hue, darker).
⚠ **Two module accents are not text colours.** `#0284C7` (4.10 on white) and
  `#D97706` (3.19) fail 4.5 as body text, so they are used only where WCAG asks
  3 : 1 — dots, rules, bars and icons. The buy-side group draws its dot and
  rule in `#D97706` and its TEXT in the amber `#B45309`.
"""

# ── The palette ───────────────────────────────────────────────────────────
INK            = "#0F1B2D"   # the shell's dark ground (rail), the darkest text
PRIMARY        = "#2563EB"
PRIMARY_HOVER  = "#1D4ED8"
PRIMARY_SOFT   = "#E8F0FE"
ACCENT         = "#0F766E"   # teal
ACCENT_SOFT    = "#E6F4F1"
AMBER          = "#B45309"   # text
AMBER_BG       = "#FEF3C7"
DANGER         = "#DC2626"
DANGER_BG      = "#FEE2E2"
DANGER_INK     = "#B91C1C"   # text ON the danger tint (see the docstring)
SUCCESS        = "#15803D"
SUCCESS_BG     = "#DCFCE7"
BACKGROUND     = "#F6F7F9"
SURFACE        = "#FFFFFF"
BORDER         = "#E2E6EC"
TEXT           = "#1F2937"
MUTED          = "#6B7280"
RAIL_TEXT      = "#CBD5E1"
RAIL_MUTED     = "#94A3B8"   # 6.74 on INK

# The six module accents, in the order the brief gives them.
MODULE_ACCENTS = ("#2563EB", "#0F766E", "#4F46E5", "#0284C7", "#D97706", "#E11D48")

# The four shell groups: (accent for dots / rules / icons, text colour, tint,
# zone). The text colour is the accent itself wherever that reads at 4.5 : 1.
GROUP_COLOURS = {
    "sell": ("#2563EB", "#2563EB", "#E8F0FE", "#F8FAFF"),
    "proj": ("#0F766E", "#0F766E", "#E6F4F1", "#F7FCFB"),
    "buy":  ("#D97706", "#B45309", "#FEF3C7", "#FFFDF7"),
    "lib":  ("#4F46E5", "#4F46E5", "#EEF2FF", "#FAFAFF"),
}

# Cards: one radius and one quiet shadow.
RADIUS     = "10px"
SHADOW_SM  = "0 1px 2px rgba(15,27,45,.06)"
SHADOW_MD  = "0 8px 24px rgba(15,27,45,.10), 0 1px 2px rgba(15,27,45,.06)"

# Every pairing the contrast test holds to 4.5 : 1 — (name, foreground, background).
TEXT_PAIRS = (
    ("text on background",        TEXT, BACKGROUND),
    ("text on surface",           TEXT, SURFACE),
    ("muted on surface",          MUTED, SURFACE),
    ("muted on background",       MUTED, BACKGROUND),
    ("ink on surface",            INK, SURFACE),
    ("white on ink",              SURFACE, INK),
    ("primary on surface",        PRIMARY, SURFACE),
    ("primary on background",     PRIMARY, BACKGROUND),
    ("white on primary",          SURFACE, PRIMARY),
    ("white on primary hover",    SURFACE, PRIMARY_HOVER),
    ("primary on primary soft",   PRIMARY, PRIMARY_SOFT),
    ("accent on accent soft",     ACCENT, ACCENT_SOFT),
    ("accent on surface",         ACCENT, SURFACE),
    ("amber on amber bg",         AMBER, AMBER_BG),
    ("danger ink on danger bg",   DANGER_INK, DANGER_BG),
    ("danger on surface",         DANGER, SURFACE),
    ("success on success bg",     SUCCESS, SUCCESS_BG),
    ("success on surface",        SUCCESS, SURFACE),
    ("rail text on ink",          RAIL_TEXT, INK),
    ("rail muted on ink",         RAIL_MUTED, INK),
) + tuple((f"{k} group text on its tint", v[1], v[2]) for k, v in GROUP_COLOURS.items()) \
  + tuple((f"{k} group text on surface", v[1], SURFACE) for k, v in GROUP_COLOURS.items())


def contrast(fg: str, bg: str) -> float:
    """The WCAG 2.x contrast ratio of two `#RRGGBB` colours."""
    def lum(h):
        h = h.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
    hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _group_rules() -> str:
    lines = []
    for key, (accent, ink, tint, zone) in GROUP_COLOURS.items():
        lines.append(f"    --g-{key}: {accent}; --g-{key}-i: {ink}; "
                     f"--g-{key}-t: {tint}; --g-{key}-z: {zone};")
    return "\n".join(lines)


# The shared custom properties, re-pointed for the screen. The OLD names stay
# (every module's stylesheet reads var(--brand), var(--navy), …), so the whole
# app re-themes without a stylesheet being touched; the NEW names are what new
# screen CSS should read.
SCREEN_TOKENS = f"""
<style>
  :root {{
    --primary: {PRIMARY}; --primary-hover: {PRIMARY_HOVER}; --primary-soft: {PRIMARY_SOFT};
    --accent: {ACCENT}; --accent-soft: {ACCENT_SOFT};
    --amber: {AMBER}; --amber-bg: {AMBER_BG};
    --danger: {DANGER}; --danger-bg: {DANGER_BG}; --danger-ink: {DANGER_INK};
    --success: {SUCCESS}; --success-bg: {SUCCESS_BG};
    --ink: {INK};

    --bg:        {BACKGROUND};
    --surface:   {SURFACE};
    --brand:     {PRIMARY};
    --brand-dk:  {PRIMARY_HOVER};
    --brand-lt:  {PRIMARY_SOFT};
    --navy:      {INK};
    --navy-dk:   {INK};
    --navy-lt:   {PRIMARY_SOFT};
    --saffron:   {ACCENT};
    --text:      {TEXT};
    --muted:     {MUTED};
    --border:    {BORDER};
    --shadow-sm: {SHADOW_SM};
    --shadow-md: {SHADOW_MD};
    --radius:    {RADIUS};

    --ground: {BACKGROUND}; --ink-muted: {MUTED}; --hair: {BORDER};
{_group_rules()}
    --st-good: {SUCCESS}; --st-good-bg: {SUCCESS_BG};
    --st-warn: {AMBER};   --st-warn-bg: {AMBER_BG};
    --st-crit: {DANGER_INK}; --st-crit-bg: {DANGER_BG};
  }}
  body {{ background: var(--bg); color: var(--text); }}
</style>
"""
