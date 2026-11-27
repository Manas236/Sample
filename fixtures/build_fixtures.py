"""
fixtures/build_fixtures.py — the synthetic workbooks, rebuilt from code.

    python fixtures/build_fixtures.py

Writes three files, every figure in them fictional:

    fixtures/demo_boq.xlsx          the seeded BOQ ("Office Fit-out, Tower B")
                                    as a contractor's workbook would carry it —
                                    the importer tests prove an import of it
                                    reproduces the seeded schedule line for line
    fixtures/demo_annexure.xlsx     the same schedule extended with nine RA
                                    claim columns, out of order, and two
                                    #VALUE! cells an import report must name
    demo_files/sample_boq.xlsx      ~15 lines on two tabs, for demonstrating
                                    Import BOQ from Excel live: a cover sheet,
                                    a schedule with sections, a parent line with
                                    sub-items, blank cells and a discount column

They are committed, so a fresh clone has them; this script is what makes them
reproducible. It reads `demo_seed.py` for the schedule and nothing else of the
application. Needs openpyxl (a runtime pin in requirements.txt).
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

FIXTURES = REPO / "fixtures"
DEMO_FILES = REPO / "demo_files"

DEMO_BOQ = FIXTURES / "demo_boq.xlsx"
DEMO_ANNEXURE = FIXTURES / "demo_annexure.xlsx"
SAMPLE_BOQ = DEMO_FILES / "sample_boq.xlsx"

# The demo workbook's columns — what `tests/test_boq_import.py` maps, by index:
#   0 item  1 description  2 Ground Floor  3 First Floor  4 total qty  5 unit
#   6 supply base  7 supply esc %  8 supply rate  9 supply amount
#   10 install base  11 install esc %  12 install rate  13 install amount
DEMO_HEAD = ["Item", "Description", "Ground Floor", "First Floor", "Total Qty", "Unit",
             "Supply Base Rate", "Supply Esc %", "Supply Rate", "Supply Amount",
             "Installation Base Rate", "Installation Esc %", "Installation Rate",
             "Installation Amount"]

# The nine RA claim columns on the annexure, in the order the sheet carries
# them — deliberately NOT numeric order, which is the point of the fixture.
ANNEXURE_RA = ["RA1", "RA2", "RA3", "RA5", "RA7", "RA9", "RA4", "RA6", "RA8"]
ANNEXURE_RA_COLS = ["N", "Q", "T", "W", "Z", "AC", "AG", "AJ", "AM"]
ANNEXURE_ERRORS = ["AF28", "AP28"]


def _rate(base, pct, rate):
    """The unit rate exactly as `boq._clean_lines()` derives it."""
    if rate is not None:
        return float(rate)
    if base is None:
        return 0.0
    return float(base) * (1.0 + float(pct or 0.0) / 100.0)


def _demo_rows():
    """The seeded schedule as worksheet rows: sections, headers, lines, totals."""
    import demo_seed as DS

    rows = [["Bill of Quantities — " + DS.BOQ_META["project_name"]] + [None] * 13,
            list(DEMO_HEAD)]
    grand_s = grand_i = 0.0
    for sec in DS.BOQ_SECTIONS:
        rows.append([sec["code"], sec["title"]] + [None] * 12)
        sub_s = sub_i = 0.0
        for li in DS.BOQ_LINES:
            if li["section"] != sec["code"]:
                continue
            if li.get("is_header"):
                rows.append([li["item_no"], li["description"]] + [None] * 12)
                continue
            areas = li.get("area_qty") or {}
            qty = (sum(areas.values()) if areas else li.get("total_qty")) or 0
            s_rate = _rate(li.get("supply_base_rate"), li.get("supply_escalation_pct"),
                           li.get("supply_rate"))
            i_rate = _rate(li.get("install_base_rate"), li.get("install_escalation_pct"),
                           li.get("install_rate"))
            s_amt, i_amt = s_rate * qty, i_rate * qty
            sub_s += s_amt
            sub_i += i_amt
            # A line priced on NEITHER track is a nil-priced line, and a sheet
            # says so with an explicit 0 in both amounts — which is what tells
            # the importer it is deliberate rather than a missing rate.
            nil = not s_rate and not i_rate
            rows.append([li["item_no"], li["description"],
                         areas.get("Ground Floor"), areas.get("First Floor"),
                         float(qty), li["unit"],
                         li.get("supply_base_rate"), li.get("supply_escalation_pct"),
                         s_rate if s_rate else None, 0.0 if nil else (s_amt or None),
                         li.get("install_base_rate"), li.get("install_escalation_pct"),
                         i_rate if i_rate else None, 0.0 if nil else (i_amt or None)])
        rows.append([None, f"SUB TOTAL ({sec['code']})"] + [None] * 7
                    + [round(sub_s, 2), None, None, None, round(sub_i, 2)])
        grand_s += sub_s
        grand_i += sub_i
    rows.append([None, "GRAND TOTAL (A+B+C)"] + [None] * 7
                + [round(grand_s, 2), None, None, None, round(grand_i, 2)])
    return rows


def build_demo_boq(path=DEMO_BOQ):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Quotation"
    for row in _demo_rows():
        ws.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def build_demo_annexure(path=DEMO_ANNEXURE):
    """The schedule on 'Sheet2', with nine RA claim columns (label in row 3)
    and two Excel error cells in row 28."""
    import openpyxl
    from openpyxl.utils import column_index_from_string

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws["A1"] = "Abstract"
    ws2 = wb.create_sheet("Sheet2")
    ws2["A1"] = "Annexure — running account claims"
    for r, row in enumerate(_demo_rows()[1:], start=3):
        for c, v in enumerate(row, start=1):
            if v is not None:
                ws2.cell(row=r, column=c, value=v)
    for label, col in zip(ANNEXURE_RA, ANNEXURE_RA_COLS):
        c = column_index_from_string(col)
        ws2.cell(row=3, column=c, value=label)
        ws2.cell(row=3, column=c + 1, value="Amount")
    for ref in ANNEXURE_ERRORS:
        ws2[ref] = "#VALUE!"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


# ── the live-demo workbook ──────────────────────────────────────────────────
#
# ~15 lines across two sections. The DISCOUNT column is the sheet's own: the
# list (base) rate, the discount, and the net rate the amount is worked from.
# The importer maps Supply Base Rate and Supply Rate by their headings and
# leaves Discount % unmapped ("— ignore —"): the discount is already in the
# net rate, so the amounts check clean and nothing needs a human.
SAMPLE_HEAD = ["Sl. No.", "Description of Item", "Unit", "Qty", "Supply Base Rate",
               "Discount %", "Supply Rate", "Supply Amount", "Installation Rate",
               "Installation Amount"]
# (item, description, unit, qty, base, discount %, installation rate) — a None
# rate is a blank cell; a header row carries a description only.
SAMPLE_SECTIONS = [
    ("A", "INTERIOR WORKS", [
        ("1", "Gypsum board partition on GI frame, both faces finished.", None, None, None, None, None),
        ("1.1", "75 mm partition", "Sqm", 140, 1450, 10, 380),
        ("1.2", "100 mm partition", "Sqm", 60, 1680, 10, 420),
        ("2", "Mineral fibre ceiling tiles 600 x 600 mm on grid", "Sqm", 320, 980, None, 160),
        ("3", "Vitrified tile flooring 600 x 600 mm", "Sqm", 280, 1150, None, 210),
        ("4", "Skirting 100 mm high, matching tile", "Rmt", 190, 220, None, 60),
        ("5", "Acrylic emulsion paint, two coats on putty", "Sqm", 900, 85, 5, None),
        ("6", "Solid core flush door 35 mm with frame", "Nos", 12, 14500, None, 1800),
    ]),
    ("B", "ELECTRICAL WORKS", [
        ("1", "FRLS copper wire, multi-strand, 1100 V grade.", None, None, None, None, None),
        ("1.1", "1.5 sq mm", "Rmt", 1500, 18.5, None, 6),
        ("1.2", "2.5 sq mm", "Rmt", 900, 29, None, 7),
        ("2", "PVC conduit 20 mm, concealed", "Rmt", 450, 48, None, 22),
        ("3", "Modular switch board, 6 module, complete", "Nos", 36, 950, None, 150),
        ("4", "LED panel light 2 x 2 ft, 36 W", "Nos", 48, 2350, 8, 250),
        ("5", "Distribution board 8-way TPN with MCBs", "Nos", 2, 14500, None, None),
    ]),
]


def _sample_rows():
    rows = [["Demo Projects Pvt Ltd — Sample BOQ for import"] + [None] * 9,
            ["Project: Retail Store Fit-out (sample)"] + [None] * 9,
            [None] * 10,
            list(SAMPLE_HEAD)]
    totals = []
    for code, title, lines in SAMPLE_SECTIONS:
        rows.append([code, title] + [None] * 8)
        sub_s = sub_i = 0.0
        for item, desc, unit, qty, base, disc, i_rate in lines:
            if qty is None:
                rows.append([item, desc] + [None] * 8)
                continue
            rate = round(base * (1 - (disc or 0) / 100.0), 2)
            s_amt = round(rate * qty, 2)
            i_amt = round(i_rate * qty, 2) if i_rate is not None else None
            sub_s += s_amt
            sub_i += i_amt or 0.0
            rows.append([item, desc, unit, qty, base, disc, rate, s_amt, i_rate, i_amt])
        rows.append([None, f"SUB TOTAL ({code})", None, None, None, None, None,
                     round(sub_s, 2), None, round(sub_i, 2)])
        totals.append((code, title, sub_s, sub_i))
    rows.append([None, "GRAND TOTAL (A+B)", None, None, None, None, None,
                 round(sum(t[2] for t in totals), 2), None,
                 round(sum(t[3] for t in totals), 2)])
    return rows, totals


def build_sample_boq(path=SAMPLE_BOQ):
    import openpyxl
    from openpyxl.styles import Font

    rows, totals = _sample_rows()
    wb = openpyxl.Workbook()
    cover = wb.active
    cover.title = "Summary"
    cover.append(["Demo Projects Pvt Ltd"])
    cover.append(["Retail Store Fit-out (sample) — summary of the BOQ"])
    cover.append([])
    cover.append(["Section", "Description", "Supply", "Installation"])
    for code, title, s, i in totals:
        cover.append([code, title, round(s, 2), round(i, 2)])
    cover.append([None, "Total", round(sum(t[2] for t in totals), 2),
                  round(sum(t[3] for t in totals), 2)])
    cover.append([])
    cover.append(["All names and figures in this workbook are fictional."])
    cover["A1"].font = Font(bold=True, size=13)

    ws = wb.create_sheet("BOQ")
    for row in rows:
        ws.append(row)
    ws["A1"].font = Font(bold=True, size=12)
    for c in ws[4]:
        c.font = Font(bold=True)
    for col, width in zip("ABCDEFGHIJ", (8, 54, 7, 8, 14, 11, 12, 14, 15, 17)):
        ws.column_dimensions[col].width = width
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def main() -> int:
    for build in (build_demo_boq, build_demo_annexure, build_sample_boq):
        p = build()
        print(f"wrote {p.relative_to(REPO)} ({p.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
