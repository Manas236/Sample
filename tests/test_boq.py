"""
Phase 1 acceptance — section A of a schedule, entered by hand.

The payload below is a fictional section A typed the way an office types a
customer's sheet: 20 priced lines, eight of them under one specification
header, two areas (Ground Floor / First Floor), supply and installation priced
separately, three lines whose agreed rate deliberately differs from base x
(1 + escalation), item 17 used twice, and one line whose base rates are "-"
because the rate was negotiated directly.

It is typed out rather than read from a workbook on purpose. This test has to
prove the form and the printed document stand up on their own, with nothing but
a browser and somebody keying in a schedule.

    ACCEPTANCE: the section subtotal reads 879141.00 supply / 299130 installation.
"""

import json

import pytest

from store import STORE

# The specification paragraph — over 1,000 characters, carrying a stray
# mis-encoded character around "Premium" on purpose, because the point of
# carrying it here is that real text of this size, as a customer's sheet hands
# it over, survives the round trip.
SPEC_4 = (
    'Supply and laying of vitrified tiles of approved make, �Premium� grade, in '
    'sizes as scheduled below, laid on a cement mortar bed of 1:4 not less than '
    '20 mm thick over the prepared base, including cutting, chamfering and '
    'grinding of edges where required, and filling the joints with matching '
    'epoxy grout.\n'
    'The work includes setting out the pattern as per the approved drawings, '
    'maintaining the levels and slopes shown, providing expansion joints at the '
    'intervals specified, and protecting the finished surface with a plastic '
    'sheet until handover.\n'
    'Tiles shall be from a single production batch per room, checked for shade '
    'variation before laying, and stacked on site on a level surface away from '
    'traffic. Broken, chipped or shaded tiles shall be rejected and replaced at '
    'no extra cost.\n'
    'The surface shall be cleaned of all mortar and grout residue, and the '
    'contractor shall hand over 2% spare tiles of each size, boxed and labelled.\n'
    'Measurement shall be for the finished area laid, deducting openings over '
    '0.5 sqm. Skirting and nosing are measured separately below.'
)


def line(item_no, desc, unit, gf, ff, s_base, s_pct, s_rate,
         i_base, i_pct, i_rate, parent="", remark=""):
    """One priced line. `gf`/`ff` are the two area quantities; None = blank."""
    area = {}
    if gf is not None:
        area["Ground Floor"] = gf
    if ff is not None:
        area["First Floor"] = ff
    return {
        "item_no": item_no, "parent_item_no": parent, "section": "A",
        "is_header": False, "description": desc, "remark": remark, "unit": unit,
        "area_qty": area, "total_qty": "",
        "supply_base_rate": s_base, "supply_escalation_pct": s_pct,
        "supply_rate": s_rate, "supply_hsn": "", "supply_gst_rate": "18",
        "install_base_rate": i_base, "install_escalation_pct": i_pct,
        "install_rate": i_rate, "install_sac": "", "install_gst_rate": "18",
    }


SECTION_A = {
    "sections": [{
        "code": "A",
        "title": "FLOORING & FINISHES, As per Technical Specifications Part-A",
        "areas": ["Ground Floor", "First Floor"],
    }],
    "lines": [
        # The specification header — paragraph only, no quantity, no rate.
        {"item_no": "4", "parent_item_no": "", "section": "A", "is_header": True,
         "description": SPEC_4, "remark": "", "unit": "", "area_qty": {},
         "total_qty": "", "supply_base_rate": "", "supply_escalation_pct": "",
         "supply_rate": "", "supply_hsn": "", "supply_gst_rate": "",
         "install_base_rate": "", "install_escalation_pct": "",
         "install_rate": "", "install_sac": "", "install_gst_rate": ""},

        # 4.1 - 4.8, the sizes under it.
        line("4.1", "800 x 800 mm",            "Sqm", None,   4, "1500", "15", "1725",   "900", "0", "900", parent="4"),
        line("4.2", "600 x 1200 mm",           "Sqm", None,  12, "1300", "15", "1495",   "800", "0", "800", parent="4"),
        line("4.3", "600 x 600 mm",            "Sqm", None,  62, "1100", "15", "1265",   "700", "0", "700", parent="4"),
        line("4.4", "400 x 400 mm",            "Sqm", None,  90,  "900", "15", "1035",   "600", "0", "600", parent="4"),
        line("4.5", "300 x 600 mm, wall",      "Sqm", None,  60,  "800", "15", "920",    "500", "0", "500", parent="4"),
        line("4.6", "300 x 300 mm, anti-skid", "Sqm",   12,  28,  "700", "15", "805",    "400", "0", "400", parent="4"),
        line("4.7", "Skirting 100 mm high",    "Rmt",   10,  28,  "300", "15", "345",    "150", "0", "150", parent="4"),
        line("4.8", "Step nosing",             "Rmt",   18,  80,  "250", "15", "287.5",  "120", "0", "120", parent="4"),

        # Rate deliberately above base x (1 + escalation) — the edge polish is
        # priced into the line and the sheet says so in the remark column. The
        # form must keep the rate as entered.
        line("5", "Granite counter top 20 mm thick with full-bullnose edge polish "
                  "on two sides, fixed on brackets.", "Sqm", 20, 135, "2200", "", "2850",
             "400", "0", "400", remark="edge polish priced into the line"),
        line("6", "Granite threshold 150 mm wide, edge polished.", "Rmt", None, 1,
             "600", "", "780", "150", "0", "150", remark="edge polish priced into the line"),
        line("9", "Marble window sill 100 mm wide with nosing.", "Rmt", None, 1,
             "500", "", "640", "120", "0", "120", remark="nosing priced into the line"),

        # Base rate "-" — negotiated directly, not escalated. Not zero.
        line("17", "Supply, Installation, fixing & polishing of 12 mm toughened "
                   "glass partition with patch fittings.", "Sqm", None, 1,
             "-", "", "4800", "-", "", "900"),

        line("17", "Supply and fixing of aluminium sliding window with mesh "
                   "shutter, powder coated.", "Sqm", None, 1,
             "11000", "7", "13770", "1500", "0", "1500",
             remark="2000/nos extra for the mesh shutter"),
        line("19", "Supply and fixing of ACP wall cladding 4 mm on aluminium "
                   "framework.", "Sqm", 1, 1, "6000", "7", "6420", "2500", "0", "2500"),
        line("20", "Supply and fixing of mortise lock with handle set and "
                   "master-key cylinder.", "Nos", None, 1, "5500", "7", "7885",
             "600", "0", "600", remark="2000/nos extra for the master-key set"),
        line("21", "Supply and fixing of hydraulic door closer with floor "
                   "spring.", "Nos", 4, 3, "2450", "7", "4621.5",
             "600", "0", "600", remark="2000/nos extra for the floor spring"),
        line("22", "Supply and fixing of tower bolt and door stopper set.", "Nos",
             None, 1, "5000", "7", "5350", "4800", "0", "4800"),
        line("23", "Supply and fixing of door viewer.", "Nos", None, 1,
             "900", "7", "963", "450", "0", "450"),
        line("24", "Supply and fixing of engraved signage plate.", "Nos", None, 1,
             "1400", "15", "1610", "350", "0", "350"),
        line("25", "Providing, fabricating and painting MS brackets for the false "
                   "ceiling support framework.", "Kgs.", 450, None, "65", "7", "69.55",
             "100", "0", "100"),
    ],
}

FORM = {
    "date": "2026-07-31",
    "rev_no": "0",
    "project_name": "Lakeside Business Park",
    "site_location": "Sector 19, Navi Mumbai",
    "rate_basis_label": "Site A Rates",
    "account_name": "Example Developers Pvt Ltd",
    "bill_city": "Navi Mumbai",
    "bill_state": "Maharashtra",
    "payment_terms": "50% Advance, Balance Before Dispatch",
    "delivery_terms": "FOR Site",
    "boq_json": json.dumps(SECTION_A),
}


@pytest.fixture(autouse=True)
def _empty_register(request):
    """
    Every test here types a schedule into a register that holds no other —
    the module's premise since it was written. The fixture world carries the
    seeded demo BOQ, so it is set aside AFTER the client fixture restores the
    world, and the numbering and counts below are this file's BOQs alone.
    """
    for name in ("client", "anon_client"):
        if name in request.fixturenames:
            request.getfixturevalue(name)
    STORE["boqs"].clear()
    yield


@pytest.fixture()
def created(client):
    r = client.post("/boq/create", data=FORM)
    assert r.status_code == 302, r.data[:2000]
    assert len(STORE["boqs"]) == 1
    bid = next(iter(STORE["boqs"]))
    return bid, STORE["boqs"][bid]


# ── The acceptance ─────────────────────────────────────────────────────────

def test_section_a_subtotals(created):
    import boq

    _bid, b = created
    supply, install = boq.section_totals(b, "A")
    assert round(supply, 2) == 879141.00
    assert round(install, 2) == 299130.00


def test_subtotals_print_on_the_document(client, created):
    bid, _b = created
    html = client.get(f"/boq/view/{bid}").get_data(as_text=True)
    assert "BASIC VALUE SUBTOTAL (A)" in html
    # Indian digit grouping, no currency symbol — quotation._inr().
    assert "8,79,141.00" in html
    assert "2,99,130.00" in html


def test_record_level_subtotals_match_the_lines(created):
    import boq

    _bid, b = created
    supply, install, total = boq.boq_totals(b)
    assert round(b["supply_subtotal"], 2) == round(supply, 2) == 879141.00
    assert round(b["install_subtotal"], 2) == round(install, 2) == 299130.00
    assert round(b["subtotal"], 2) == round(total, 2) == 1178271.00


# ── The shape (§4.2 / §4.3) ────────────────────────────────────────────────

def test_item_no_is_a_string_never_a_float(created):
    _bid, b = created
    for li in b["line_items"]:
        assert isinstance(li["item_no"], str)
        assert isinstance(li["parent_item_no"], str)
    nos = [li["item_no"] for li in b["line_items"]]
    assert "4.1" in nos and "4.4" in nos
    assert not any("0000000" in n for n in nos)


def test_item_no_normaliser_kills_float_dust():
    """Values a source workbook really holds for 4.1, 4.4 and 4.6."""
    from boq import _item_no

    assert _item_no(4.0999999999999996) == "4.1"
    assert _item_no(4.4000000000000004) == "4.4"
    assert _item_no(4.5999999999999996) == "4.6"
    assert _item_no("24.b") == "24.b"
    assert _item_no(24) == "24"


def test_dash_base_rate_is_none_not_zero(created):
    """
    "-" means the rate was agreed directly. It is not zero and not missing.
    """
    _bid, b = created
    drop = [li for li in b["line_items"]
            if li["description"].startswith("Supply, Installation, fixing & polishing of 12 mm")][0]
    assert drop["supply_base_rate"] is None
    assert drop["install_base_rate"] is None
    assert drop["supply_rate"] == 4800.0
    assert drop["install_rate"] == 900.0


def test_rate_is_kept_as_entered_when_it_contradicts_the_escalation(created):
    """
    Item 20 is 5500 + 7%, which is 5885 — but the agreed rate is 7885 because a
    master-key set is priced into the line. Recomputing it from the escalation
    would rewrite an agreed price.
    """
    _bid, b = created
    li = [x for x in b["line_items"] if x["item_no"] == "20"][0]
    assert li["supply_base_rate"] == 5500.0
    assert li["supply_escalation_pct"] == 7.0
    assert li["supply_rate"] == 7885.0
    assert li["supply_amount"] == 7885.0


def test_header_row_carries_the_spec_and_no_numbers(created):
    _bid, b = created
    hdr = [li for li in b["line_items"] if li["is_header"]][0]
    assert hdr["item_no"] == "4"
    assert len(hdr["description"]) > 1000
    assert hdr["total_qty"] == 0.0
    assert hdr["supply_amount"] == 0.0
    assert hdr["install_amount"] == 0.0
    assert hdr["area_qty"] == {}


def test_header_row_is_excluded_from_the_subtotal(created):
    """A header has no amount, so it cannot move a subtotal even if one crept in."""
    import boq

    _bid, b = created
    b["line_items"][0]["supply_amount"] = 999999.0   # a header, per the test above
    supply, _install = boq.section_totals(b, "A")
    assert round(supply, 2) == 879141.00


def test_total_qty_is_the_sum_of_its_areas(created):
    _bid, b = created
    for li in b["line_items"]:
        if li["is_header"] or not li["area_qty"]:
            continue
        assert round(sum(li["area_qty"].values()), 6) == round(li["total_qty"], 6)
    # 4.6: 12 Ground Floor + 28 First Floor = 40
    li46 = [x for x in b["line_items"] if x["item_no"] == "4.6"][0]
    assert li46["total_qty"] == 40.0
    assert li46["area_qty"] == {"Ground Floor": 12.0, "First Floor": 28.0}


def test_blank_area_is_absent_not_zero(created):
    """
    An item that is not on a floor has no entry for it. Storing 0.0 would put
    every item on every floor with a quantity of none, which is a different
    claim and prints a different sheet.
    """
    _bid, b = created
    li41 = [x for x in b["line_items"] if x["item_no"] == "4.1"][0]
    assert li41["area_qty"] == {"First Floor": 4.0}
    assert "Ground Floor" not in li41["area_qty"]


def test_areas_live_on_the_section(created):
    _bid, b = created
    assert b["sections"] == [{
        "code": "A",
        "title": "FLOORING & FINISHES, As per Technical Specifications Part-A",
        "areas": ["Ground Floor", "First Floor"],
    }]


def test_ref_is_fy_scoped_and_max_plus_one(client, created):
    _bid, b = created
    assert b["ref"] == "DP/BOQ/26-27/0001"
    assert b["fy"] == "26-27"
    client.post("/boq/create", data=FORM)
    refs = sorted(x["ref"] for x in STORE["boqs"].values())
    assert refs == ["DP/BOQ/26-27/0001", "DP/BOQ/26-27/0002"]


# ── The document ───────────────────────────────────────────────────────────

def test_document_prints_landscape(client, created):
    bid, _b = created
    html = client.get(f"/boq/view/{bid}").get_data(as_text=True)
    assert "size:A4 landscape" in html


def test_responsive_breakpoint_is_scoped_to_screen(client, created):
    """An unscoped max-width breakpoint fires on paper — ABOUT.md §5."""
    bid, _b = created
    html = client.get(f"/boq/view/{bid}").get_data(as_text=True)
    assert "@media screen and (max-width:760px)" in html
    assert "@media (max-width:760px)" not in html


# ── The sheet on a portrait page — a phone's print service picks the paper ──
#
# 20 September 2026. The owner printed the BOQ from a phone: Chrome for Android
# laid the sheet out at the CSS `A4 landscape` page box and scaled the whole
# box onto the portrait paper the print service chose — every page 55% full,
# everything at 73%. `boq.BOQ_DOC_STYLES` carries a column set that fits a
# portrait page and `boq.BOQ_DOC_SCRIPT` withdraws the size request on a touch
# device. ABOUT.md §5 `/boq`, "The document".

def _col_widths_mm(css_block: str) -> dict:
    """`{cw-sno: 12.0, …}` parsed out of one block of `.boq-table col.cw-*` rules."""
    import re
    return {m.group(1): float(m.group(2))
            for m in re.finditer(r"col\.(cw-[a-z]+)\s*\{\s*width:([\d.]+)mm", css_block)}


def test_both_document_routes_carry_the_portrait_sheet_and_the_script(client, created):
    """
    The two routes render one `_document_html()`; both must load the sheet
    that fits a portrait page and the script that lets a phone print on one.
    The register and the editor draw no section table and must NOT load
    either — `BOQ_STYLES` is golden-pinned through four register pages and
    the sheet-only rules are kept out of it for that reason.
    """
    import boq

    bid, _b = created
    for url in (f"/boq/view/{bid}", f"/boq/print/{bid}"):
        html = client.get(url).get_data(as_text=True)
        assert boq.BOQ_DOC_STYLES in html, f"{url} does not load BOQ_DOC_STYLES"
        assert boq.BOQ_DOC_SCRIPT in html, f"{url} does not load BOQ_DOC_SCRIPT"
        # The landscape request is still made — a desktop browser honours it.
        assert "size:A4 landscape" in html
        # …and withdrawn only where the print service picks the paper itself.
        assert "(pointer: coarse)" in html
        assert "@page { size:auto; }" in html

    for url in ("/boq/", "/boq/create", "/ra/", "/receipt/", "/merged/"):
        html = client.get(url).get_data(as_text=True)
        assert "cw-sno" not in html, f"{url} loads the sheet-only stylesheet"
        assert "(pointer: coarse)" not in html, f"{url} loads BOQ_DOC_SCRIPT"


def test_the_portrait_column_set_is_scoped_to_a_portrait_page_or_a_phone_screen():
    """
    The narrower widths may fire on a portrait PAGE or on a phone SCREEN and
    nowhere else. `screen and (max-width:760px)` is the app's own breakpoint
    (`test_responsive_breakpoint_is_scoped_to_screen`); an unscoped max-width
    half would narrow the landscape sheet on paper, which is the fault that
    test exists to stop.
    """
    import boq

    css = boq.BOQ_DOC_STYLES
    assert "@media print and (orientation:portrait), screen and (max-width:760px)" in css
    assert "@media (max-width:760px)" not in css
    assert "@media (orientation:portrait)" not in css
    # The phone-screen block is scoped to `screen` outright.
    assert "@media screen and (max-width:760px)" in css


def test_the_portrait_column_set_leaves_room_for_the_description():
    """
    A4 portrait gives 194mm inside the sheet's 8mm side margins. The client's
    real sections declare up to two areas, and a 1,500-character clause needs
    about 60mm of description to fit on one page at 6.5pt. The widths are
    parsed out of the stylesheet rather than copied here, so widening one
    past the page fails by name.
    """
    import boq

    css = boq.BOQ_DOC_STYLES
    landscape_block, portrait_block = css.split("@media print and (orientation:portrait)")
    wide, narrow = _col_widths_mm(landscape_block), _col_widths_mm(portrait_block)

    expected = {"cw-sno", "cw-area", "cw-qty", "cw-unit",
                "cw-base", "cw-esc", "cw-rate", "cw-amt"}
    assert set(wide) == expected and set(narrow) == expected

    # The landscape figures are the ones the sheet has always printed at.
    assert wide == {"cw-sno": 12, "cw-area": 14, "cw-qty": 15, "cw-unit": 13,
                    "cw-base": 16, "cw-esc": 11, "cw-rate": 18, "cw-amt": 24}
    # Every portrait width is narrower, and none is too narrow for its widest
    # value: a bold eight-figure subtotal in `cw-amt`, "Installation" in
    # `cw-rate` (13.2mm of bold Arial at 6.5pt, plus padding).
    for k in expected:
        assert narrow[k] < wide[k], f"{k} is not narrower on a portrait page"
    assert narrow["cw-amt"] >= 19 and narrow["cw-rate"] >= 15

    # The issued print on a two-area section: Sr, 2 areas, qty, unit, then
    # rate + amount per track. 194mm less that must leave ≥ 60mm.
    fixed = (narrow["cw-sno"] + 2 * narrow["cw-area"] + narrow["cw-qty"]
             + narrow["cw-unit"] + 2 * (narrow["cw-rate"] + narrow["cw-amt"]))
    assert 194 - fixed >= 60, f"only {194 - fixed}mm left for the description"


def test_every_col_is_widthed_by_class_not_inline(client, created):
    """
    An inline `style="width:…"` on a `<col>` cannot be overridden by a media
    query, so the portrait set could never reach it. Every column carries its
    class and no inline style, and the classes follow the header's order.
    """
    import re

    bid, _b = created
    for url, expect in ((f"/boq/print/{bid}", ["cw-sno", "cw-desc", "cw-area", "cw-area",
                                                "cw-qty", "cw-unit", "cw-rate", "cw-amt",
                                                "cw-rate", "cw-amt"]),
                        (f"/boq/view/{bid}", ["cw-sno", "cw-desc", "cw-area", "cw-area",
                                               "cw-qty", "cw-unit", "cw-base", "cw-esc",
                                               "cw-rate", "cw-amt", "cw-base", "cw-rate",
                                               "cw-amt"])):
        html = client.get(url).get_data(as_text=True)
        cg = re.search(r"<colgroup>(.*?)</colgroup>", html, re.S).group(1)
        assert 'style="' not in cg, f"{url}: a <col> still carries an inline width"
        assert re.findall(r'<col class="(cw-[a-z]+)"/>', cg) == expect


def test_area_columns_are_the_sections_own(client, created):
    bid, _b = created
    html = client.get(f"/boq/view/{bid}").get_data(as_text=True)
    assert '<th class="b-area">Ground Floor</th>' in html
    assert '<th class="b-area">First Floor</th>' in html


def test_dash_prints_as_a_dash_not_a_zero(client, created):
    bid, _b = created
    html = client.get(f"/boq/view/{bid}").get_data(as_text=True)
    assert '<td class="b-base">-</td>' in html


def test_remarks_do_not_print(client, created):
    """
    Internal pricing notes stay off the customer's copy — the same call the
    quotation makes about deal-desk fields. `boq.PRINT_REMARKS` flips it.
    """
    import boq

    assert boq.PRINT_REMARKS is False
    bid, _b = created
    html = client.get(f"/boq/view/{bid}").get_data(as_text=True)
    assert "2000/nos extra for the master-key set" not in html
    # …but the value is still on the record.
    li = [x for x in STORE["boqs"][bid]["line_items"] if x["item_no"] == "20"][0]
    assert li["remark"] == "2000/nos extra for the master-key set"


def test_user_text_is_escaped(client):
    """
    ~1500 characters of client text go onto a printed document. proforma.py's
    discipline, not quotation.py's.
    """
    payload = json.loads(FORM["boq_json"])
    payload["lines"][1]["description"] = '<script>alert("x")</script> & 100mm'
    form = dict(FORM, boq_json=json.dumps(payload),
                account_name='Acme <b>Ltd</b> & Co')
    r = client.post("/boq/create", data=form)
    bid = next(iter(STORE["boqs"]))
    html = client.get(f"/boq/view/{bid}").get_data(as_text=True)
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert "Acme &lt;b&gt;Ltd&lt;/b&gt; &amp; Co" in html


# ── Validation ─────────────────────────────────────────────────────────────

def test_rejected_post_writes_nothing(client):
    r = client.post("/boq/create", data=dict(FORM, account_name=""))
    assert r.status_code == 200
    assert STORE["boqs"] == {}
    assert "customer account name" in r.get_data(as_text=True)


def test_line_in_an_undeclared_section_is_rejected(client):
    payload = json.loads(FORM["boq_json"])
    payload["lines"][1]["section"] = "Z"
    r = client.post("/boq/create", data=dict(FORM, boq_json=json.dumps(payload)))
    assert r.status_code == 200
    assert STORE["boqs"] == {}
    assert "not defined above" in r.get_data(as_text=True)


def test_duplicate_section_code_is_rejected(client):
    payload = json.loads(FORM["boq_json"])
    payload["sections"].append({"code": "A", "title": "again", "areas": []})
    r = client.post("/boq/create", data=dict(FORM, boq_json=json.dumps(payload)))
    assert r.status_code == 200
    assert STORE["boqs"] == {}
    assert "used twice" in r.get_data(as_text=True)


def test_bad_hsn_is_rejected(client):
    payload = json.loads(FORM["boq_json"])
    payload["lines"][1]["supply_hsn"] = "8413-A"
    r = client.post("/boq/create", data=dict(FORM, boq_json=json.dumps(payload)))
    assert r.status_code == 200
    assert STORE["boqs"] == {}
    assert "4, 6 or 8 digits" in r.get_data(as_text=True)


def test_a_nil_priced_line_is_valid(client):
    """
    A line can carry a quantity and no rate at all (priced inside another
    item). It is a real line and must not be rejected — handover §4.2 rule 7.
    """
    payload = json.loads(FORM["boq_json"])
    payload["lines"].append(line(
        "37", "Exacavation of trenches up to 1.5 mts. in depth.", "Mtrs",
        140, None, "", "", "", "", "", ""))
    r = client.post("/boq/create", data=dict(FORM, boq_json=json.dumps(payload)))
    assert r.status_code == 302
    b = next(iter(STORE["boqs"].values()))
    nil = [x for x in b["line_items"] if x["item_no"] == "37"][0]
    assert nil["total_qty"] == 140.0
    assert nil["supply_rate"] == 0.0
    assert nil["supply_amount"] == 0.0


def test_section_with_no_areas_takes_a_typed_total(client):
    """
    Section C declares no areas at all: the total quantity stands alone and
    there is nothing to reconcile it against.
    """
    payload = {
        "sections": [{"code": "C", "title": "PLUMBING PUMPS", "areas": []}],
        "lines": [dict(line("1a", "Main water supply pump", "Nos.", None, None,
                            "", "", "", "60000", "0", "60000"),
                       section="C", total_qty="1")],
    }
    r = client.post("/boq/create", data=dict(FORM, boq_json=json.dumps(payload)))
    assert r.status_code == 302
    b = next(iter(STORE["boqs"].values()))
    li = b["line_items"][0]
    assert li["area_qty"] == {}
    assert li["total_qty"] == 1.0
    assert li["install_amount"] == 60000.0
    assert li["supply_amount"] == 0.0


# ── The register ───────────────────────────────────────────────────────────

def test_register_lists_the_boq(client, created):
    html = client.get("/boq/").get_data(as_text=True)
    assert "DP/BOQ/26-27/0001" in html
    assert "Lakeside Business Park" in html


def test_view_of_a_missing_boq_redirects(client):
    r = client.get("/boq/view/nope")
    assert r.status_code == 302
    assert "/boq/" in r.headers["Location"]


def test_every_row_has_the_same_column_count(client, created):
    """
    Every table row must span exactly as many columns as the head declares.

    A colspan that is one out does not raise — the browser silently reflows the
    table and the money columns stop lining up under their headings, which is
    the kind of defect that only shows up on paper after it has been sent.
    """
    from html.parser import HTMLParser

    bid, _b = created
    html = client.get(f"/boq/view/{bid}").get_data(as_text=True)
    body = html.split('<table class="boq-table">')[1].split("</table>")[0]

    class Rows(HTMLParser):
        def __init__(self):
            super().__init__()
            self.rows, self.cur, self.pending = [], None, {}
            self.row_i = 0

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag == "tr":
                self.cur = self.pending.pop(self.row_i, 0)
            elif tag in ("td", "th") and self.cur is not None:
                self.cur += int(a.get("colspan", 1))
                for r in range(1, int(a.get("rowspan", 1))):
                    self.pending[self.row_i + r] = self.pending.get(self.row_i + r, 0) + int(a.get("colspan", 1))

        def handle_endtag(self, tag):
            if tag == "tr" and self.cur is not None:
                self.rows.append(self.cur)
                self.cur = None
                self.row_i += 1

    p = Rows()
    p.feed(body)
    assert p.rows, "no rows parsed"
    assert len(set(p.rows)) == 1, f"ragged table: column counts {sorted(set(p.rows))}"
