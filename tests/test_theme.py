"""
`theme.py` — the SCREEN palette (October 2026), and the line it may not cross.

1. **Contrast.** Every pairing that carries body text reads at 4.5 : 1 or
   better (WCAG 2.x AA), recomputed here from the hex values — the ratios in
   theme.py's docstring are pinned too, so a palette edit that drifts under
   the floor goes red naming the pair.
2. **The print palette does not move.** The screen tokens ride with the app
   shell (`_nav()`) and the two public pages, never with the stylesheet a
   printed sheet carries; and on a screen page the shell re-declares the
   print palette on the document's own container. `tests/test_print_golden.py`
   hashes every printed document; this file holds the mechanism.
3. **It is a leaf.** `theme.py` imports nothing at all.
"""

import re

import pytest

import branding as B
import chrome
import theme as T
from test_import_directions import imports_of
from test_print_golden import (  # noqa: F401  (fixtures)
    PRINT_ROUTES, pinned_identity, golden, golden_ra, golden_dc, golden_dpo,
    golden_merged, golden_ms)


# ── 1. Contrast ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,fg,bg", T.TEXT_PAIRS, ids=[p[0] for p in T.TEXT_PAIRS])
def test_every_text_pairing_reads_at_4_5_to_1(name, fg, bg):
    ratio = T.contrast(fg, bg)
    assert ratio >= 4.5, f"{name}: {fg} on {bg} is {ratio:.2f} : 1, under 4.5"


def test_the_ratios_quoted_in_the_docstring_are_the_measured_ones():
    quoted = {
        ("#1F2937", "#F6F7F9"): 13.69, ("#1F2937", "#FFFFFF"): 14.68,
        ("#6B7280", "#FFFFFF"): 4.83, ("#6B7280", "#F6F7F9"): 4.51,
        ("#0F1B2D", "#FFFFFF"): 17.28, ("#2563EB", "#FFFFFF"): 5.17,
        ("#2563EB", "#E8F0FE"): 4.51, ("#FFFFFF", "#1D4ED8"): 6.70,
        ("#0F766E", "#E6F4F1"): 4.84, ("#B45309", "#FEF3C7"): 4.51,
        ("#B91C1C", "#FEE2E2"): 5.30, ("#DC2626", "#FFFFFF"): 4.83,
        ("#15803D", "#DCFCE7"): 4.57, ("#CBD5E1", "#0F1B2D"): 11.64,
    }
    for (fg, bg), want in quoted.items():
        assert round(T.contrast(fg, bg), 2) == want, (fg, bg)


def test_the_two_shortfalls_in_the_brief_are_real_and_handled():
    """The brief's danger pair and two module accents are under 4.5 as text —
    measured, not assumed — and theme.py routes around each one."""
    assert T.contrast(T.DANGER, T.DANGER_BG) < 4.5
    assert T.contrast(T.DANGER_INK, T.DANGER_BG) >= 4.5
    assert "--st-crit: " + T.DANGER_INK in T.SCREEN_TOKENS
    for weak in ("#0284C7", "#D97706"):
        assert T.contrast(weak, T.SURFACE) < 4.5
        assert weak not in {ink for _a, ink, _t, _z in T.GROUP_COLOURS.values()}


def test_the_brief_palette_is_the_palette():
    assert (T.INK, T.PRIMARY, T.PRIMARY_HOVER, T.PRIMARY_SOFT) == (
        "#0F1B2D", "#2563EB", "#1D4ED8", "#E8F0FE")
    assert (T.ACCENT, T.ACCENT_SOFT) == ("#0F766E", "#E6F4F1")
    assert (T.AMBER, T.AMBER_BG) == ("#B45309", "#FEF3C7")
    assert (T.DANGER, T.DANGER_BG) == ("#DC2626", "#FEE2E2")
    assert (T.SUCCESS, T.SUCCESS_BG) == ("#15803D", "#DCFCE7")
    assert (T.BACKGROUND, T.SURFACE, T.BORDER, T.TEXT, T.MUTED) == (
        "#F6F7F9", "#FFFFFF", "#E2E6EC", "#1F2937", "#6B7280")
    assert T.MODULE_ACCENTS == ("#2563EB", "#0F766E", "#4F46E5", "#0284C7",
                                "#D97706", "#E11D48")
    assert T.RADIUS == "10px" and T.SHADOW_SM == "0 1px 2px rgba(15,27,45,.06)"
    assert "--radius:    10px" in T.SCREEN_TOKENS


# ── 2. Print does not move ──────────────────────────────────────────────────

def test_the_screen_tokens_are_not_in_the_stylesheet_a_printed_sheet_carries():
    import docsheet
    for sheet in (chrome.BASE_STYLES, docsheet.SHEET_STYLES):
        assert T.SCREEN_TOKENS not in sheet
        assert T.PRIMARY not in sheet, "a screen colour reached the print stylesheet"
    # ...and the print palette is still what the shared stylesheet declares.
    assert f"--brand:     {B.RED};" in B.CSS_TOKENS
    assert f"--navy:      {B.NAVY};" in B.CSS_TOKENS


def test_the_shell_carries_the_screen_tokens_and_restores_print_on_a_document(client):
    html = client.get("/").get_data(as_text=True)
    tokens, scope, styles = (html.index(T.SCREEN_TOKENS.strip()),
                             html.index(chrome.DOC_PALETTE_SCOPE.strip()),
                             html.index(chrome.CHROME_STYLES.strip()))
    assert tokens < scope < styles, "the order is what makes each one win"
    # The scope is the print palette, value for value — read off CSS_TOKENS.
    root = B.CSS_TOKENS.split(":root {", 1)[1].split("}", 1)[0]
    for decl in re.findall(r"--[a-z-]+:\s*[^;]+;", root):
        assert decl in chrome.DOC_PALETTE_SCOPE, decl
    assert ".doc-outer, .quotation-doc {" in chrome.DOC_PALETTE_SCOPE


@pytest.mark.parametrize("name,url", PRINT_ROUTES)
def test_no_print_route_receives_the_screen_tokens(
        name, url, client, golden, golden_ra, golden_dc, golden_dpo,
        golden_merged, golden_ms):
    """The nine print routes render no nav, so no screen token reaches paper.
    Built on the print goldens' own fixtures and route list."""
    html = client.get(url).get_data(as_text=True)
    assert "<html" in html, name
    assert "--primary:" not in html, f"{name}: the screen tokens reached a print route"
    assert T.PRIMARY not in html, f"{name}: a screen colour reached a print route"


def test_the_groups_read_their_colours_from_the_theme():
    for g in chrome.GROUPS:
        accent, _ink, tint, zone = T.GROUP_COLOURS[g.key]
        assert (g.accent, g.tint, g.zone) == (accent, tint, zone), g.key


def test_the_public_pages_wear_the_screen_palette():
    import auth
    import landing
    css = auth.AUTH_STANDALONE_STYLES
    for value in (T.BACKGROUND, T.TEXT, T.BORDER, T.PRIMARY, T.PRIMARY_HOVER,
                  T.DANGER_INK, T.DANGER_BG):
        assert value in css, value
    assert landing._PALETTE["accent"] == T.PRIMARY
    assert landing._PALETTE["text"] == T.TEXT


# ── 3. A leaf ───────────────────────────────────────────────────────────────

def test_theme_imports_nothing_at_all():
    assert imports_of("theme") == set()
