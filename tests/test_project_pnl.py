"""
The project Profit & Loss (`pnl.py`, 27 November 2026, FEATURE_GAP.md row 7).

What these tests hold, on a small synthetic project written straight into the
store (the shape every other project-page test uses):

* PLANNED is the current revision's contract against its base-rate cost; a
  superseded revision is never counted (no stacking).
* ACTUAL is billed (issued RA bills only) against purchase orders (not
  cancelled), expenses and site labour; drafts are counted separately and a
  cancelled bill never.
* Labour is passed in, or None for a role that may not see wages — and the
  page then says the actual figures exclude it.
* Still owed = issued bills incl. GST − receipts (amount + write-off).
* The project page renders the panel, an RA-bills table, and the BOQ panel
  lists the latest revision only.
"""

import pytest

import auth
import pnl as PNL
from store import STORE


def _line(lid, qty, s_rate, s_base, i_rate=0.0, i_base=None):
    return {"line_id": lid, "section": "A", "item_no": lid, "total_qty": qty,
            "supply_rate": s_rate, "supply_base_rate": s_base,
            "supply_amount": qty * s_rate, "install_rate": i_rate,
            "install_base_rate": i_base, "install_amount": qty * i_rate}


@pytest.fixture()
def project():
    saved = {c: dict(STORE[c]) for c in ("projects", "boqs", "ra_bills", "receipts",
                                         "purchases", "charges")}
    for c in saved:
        STORE[c].clear()
    STORE["projects"]["px"] = {"id": "px", "name": "PnL test"}
    # rev 0 (superseded) and rev 1 (current) — only rev 1 counts.
    STORE["boqs"]["r0"] = {"id": "r0", "ref": "B/0001", "rev_no": 0, "supersedes": "",
                           "project_id": "px",
                           "line_items": [_line("aaaaaaaaaaaa", 10, 120, 100)]}
    STORE["boqs"]["r1"] = {"id": "r1", "ref": "B/0002", "rev_no": 1, "supersedes": "r0",
                           "project_id": "px",
                           "line_items": [_line("aaaaaaaaaaaa", 10, 110, 100, 20, 15),
                                          {"is_header": True, "line_id": "bbbbbbbbbbbb"}]}
    STORE["ra_bills"].update({
        "b1": {"id": "b1", "boq_id": "r1", "status": "issued", "claim_subtotal": 1000.0,
               "grand_total": 1180.0},
        "b2": {"id": "b2", "boq_id": "r0", "status": "issued", "claim_subtotal": 200.0,
               "grand_total": 236.0},
        "b3": {"id": "b3", "boq_id": "r1", "status": "draft", "claim_subtotal": 300.0,
               "grand_total": 354.0},
        "b4": {"id": "b4", "boq_id": "r1", "status": "cancelled", "claim_subtotal": 999.0,
               "grand_total": 999.0},
    })
    STORE["receipts"]["rc"] = {"id": "rc", "ra_id": "b1", "amount": 900.0, "write_off": 50.0}
    STORE["purchases"].update({
        "p1": {"id": "p1", "project_id": "px", "status": "Issued", "taxable_value": 700.0},
        "p2": {"id": "p2", "project_id": "px", "status": "Cancelled", "taxable_value": 5000.0},
        "p3": {"id": "p3", "project_id": "other", "status": "Issued", "taxable_value": 5000.0},
    })
    STORE["charges"]["c1"] = {"id": "c1", "project_id": "px", "taxable_amount": 80.0}
    yield "px"
    for c, v in saved.items():
        STORE[c].clear()
        STORE[c].update(v)


def test_planned_uses_the_current_revision_only(project):
    f = PNL.figures(project)
    assert [b["id"] for b in f["revisions"]] == ["r1"]
    assert f["contract"] == 10 * 110 + 10 * 20               # 1,300
    assert f["planned_cost"] == 10 * 100 + 10 * 15           # 1,150
    assert f["planned_margin"] == 150 and f["planned_margin_pct"] == pytest.approx(11.5)


def test_a_track_without_a_base_rate_counts_at_its_selling_rate():
    contract, cost = PNL.plan_of({"line_items": [_line("cccccccccccc", 2, 50, None, 10, None)]})
    assert contract == cost == 120


def test_actual_counts_issued_bills_and_live_orders(project):
    f = PNL.figures(project, labour=120.0)
    assert f["billed"] == 1200.0                             # b1 + b2 (any revision); not b3, b4
    assert f["bills_issued"] == 2 and f["bills_draft"] == 1 and f["draft_value"] == 300.0
    assert f["committed"] == 700.0                           # not the cancelled, not another project's
    assert f["charges"] == 80.0 and f["labour"] == 120.0
    assert f["actual_cost"] == 900.0 and f["actual_margin"] == 300.0
    assert f["actual_margin_pct"] == 25.0


def test_still_owed_is_issued_gross_less_receipts(project):
    f = PNL.figures(project)
    assert f["billed_gross"] == 1180.0 + 236.0
    assert f["received"] == 950.0 and f["outstanding"] == 1416.0 - 950.0


def test_withheld_labour_is_none_and_the_panel_says_so(project):
    f = PNL.figures(project, labour=None)
    assert f["labour"] is None and f["actual_cost"] == 780.0
    html = PNL.panel_html(f)
    assert "excl. labour" in html and "withheld for your role" in html
    assert "Site labour &mdash;" not in html          # no labour slice in the legend


def test_the_pie_leaves_out_empty_slices_and_escapes_labels():
    svg = PNL.pie_svg([("A <b>", 10), ("Zero", 0)])
    assert "A &lt;b&gt;" in svg and "Zero" not in svg
    assert PNL.pie_svg([("x", 0)]) == ""


def test_the_project_page_renders_the_panel_and_the_ra_bills(client, project):
    html = client.get(f"/projects/view/{project}").get_data(as_text=True)
    assert "Profit &amp; Loss" in html and "Running Account Bills" in html
    f = PNL.figures(project, labour=0.0)
    assert PNL.money(f["contract"]) in html and PNL.money(f["outstanding"]) in html
    # latest revision only in the BOQ panel; the superseded one is a note
    assert "Superseded, not counted" in html and "B/0001" in html


def test_a_role_without_attendance_sees_the_labour_withheld(client, project):
    import app  # noqa: F401
    u = auth.create_user("pnl_accounts", "Acc", "x-Acc-1", ["role-accountant"],
                         created_by="test")
    try:
        with client.session_transaction() as s:
            s[auth.SESSION_KEY] = u["id"]
        html = client.get(f"/projects/view/{project}").get_data(as_text=True)
        assert "withheld for your role" in html
    finally:
        STORE["users"].pop(u["id"], None)
