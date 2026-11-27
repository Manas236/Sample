"""
The synthetic workbooks — and proof that the app never needs them.

`fixtures/demo_boq.xlsx` and `fixtures/demo_annexure.xlsx` are SYNTHETIC: built
by `fixtures/build_fixtures.py` from `demo_seed.py`, every figure fictional,
committed so a fresh clone has them. They do real work here: they check that
the seed module and the workbook built from it still agree, which is the
regression the importer's own reproduction test is measured against.
"""

import pytest

import demo_seed as DS

openpyxl = pytest.importorskip("openpyxl", reason="openpyxl not installed")


def test_the_suite_runs_without_the_workbooks():
    """
    The contract: the app never reads THESE workbooks at runtime, so a checkout
    without them is fully functional and fully tested apart from these.

    `/boq/import` reads the OPERATOR'S uploaded workbook through
    `sheetimport.py`. What stays true is what this test asserts — neither
    `boq.py` nor `spec.py` reads one, and the seeded schedule is
    `demo_seed.py`, never a file. `tests/test_import_directions.py::
    test_only_sheetimport_reads_a_workbook` holds the whole-app rule.
    """
    # demo_seed is committed and self-contained — this holds either way.
    assert len(DS.SPECS) == 15
    assert len(DS.BOQ_LINES) == 24
    # And neither schedule module imports openpyxl.
    import boq
    import spec
    for mod in (boq, spec):
        src = open(mod.__file__, encoding="utf8").read()
        assert "openpyxl" not in src, f"{mod.__name__} reads a workbook at runtime"


def _item_rows(ws):
    """(section, item_no) for every row carrying an item number, in sheet order.
    A section row is a single letter with a title and no figures."""
    rows, section = [], ""
    for r in ws.iter_rows(min_row=3, values_only=True):
        item, desc = r[0], r[1]
        if item is None:
            continue
        item = str(item).strip()
        if len(item) == 1 and item.isalpha() and all(v is None for v in r[2:]):
            section = item
            continue
        rows.append((section, item))
    return rows


def test_the_seed_still_matches_the_demo_workbook(demo_boq_xlsx):
    """
    `fixtures/demo_boq.xlsx` is built from `demo_seed.py`. If the seed changes
    and the workbook is not rebuilt, the two drift apart silently — and the
    importer's reproduction test stops measuring anything.
    """
    ws = openpyxl.load_workbook(demo_boq_xlsx, data_only=True)["Quotation"]
    rows = _item_rows(ws)
    assert len(rows) == len(DS.BOQ_LINES)
    for (sec, item), line in zip(rows, DS.BOQ_LINES):
        assert line["item_no"] == item, f"{sec} {item}"
        assert line["section"] == sec, f"{sec} {item}"


def test_the_workbook_still_totals_what_the_seed_says(demo_boq_xlsx):
    ws = openpyxl.load_workbook(demo_boq_xlsx, data_only=True)["Quotation"]
    grand = [r for r in ws.iter_rows(values_only=True)
             if r[1] and str(r[1]).startswith("GRAND TOTAL")]
    assert len(grand) == 1
    supply, install = grand[0][9], grand[0][13]

    def rate(li, track):
        if li.get(f"{track}_rate") is not None:
            return float(li[f"{track}_rate"])
        base = li.get(f"{track}_base_rate")
        if base is None:
            return 0.0
        return float(base) * (1.0 + float(li.get(f"{track}_escalation_pct") or 0) / 100.0)

    def qty(li):
        a = li.get("area_qty") or {}
        return float(sum(a.values()) if a else li.get("total_qty") or 0)

    lines = [li for li in DS.BOQ_LINES if not li.get("is_header")]
    seeded_s = sum(rate(li, "supply") * qty(li) for li in lines)
    seeded_i = sum(rate(li, "install") * qty(li) for li in lines)
    # The seeded schedule's own totals, pinned — the same figures
    # `/boq/view` shows for DP/BOQ/26-27/0001.
    assert round(seeded_s, 2) == 1703625.00
    assert round(seeded_i, 2) == 490574.00
    assert round(supply, 2) == round(seeded_s, 2)
    assert round(install, 2) == round(seeded_i, 2)


def test_annexure_carries_the_nine_ra_claims(demo_annexure_xlsx):
    """The RA replay fixture: nine claim columns, deliberately out of numeric
    order, and the two #VALUE! cells an import report has to name."""
    ws = openpyxl.load_workbook(demo_annexure_xlsx, data_only=True)["Sheet2"]
    labels = [ws[f"{c}3"].value for c in ("N", "Q", "T", "W", "Z", "AC", "AG", "AJ", "AM")]
    assert labels == ["RA1", "RA2", "RA3", "RA5", "RA7", "RA9", "RA4", "RA6", "RA8"]
    assert ws["AF28"].value == "#VALUE!"
    assert ws["AP28"].value == "#VALUE!"
