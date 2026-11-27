"""
DEMO BRANCH: the solar EPC seed (`solar_seed.py`) and its tool.

Built in memory through the routes, exactly as `tools/seed_demo.py` builds it
into MySQL. These tests hold the story the demo script walks through, the
tool's refusals (the demo-database name guard above all, because `--reset`
drops a database), and that nobody's real data is in it.
"""

import importlib.util
import pathlib

import pytest

import auth
import db
import pricesummary as PS
import solar_seed as SS
from store import STORE

REPO = pathlib.Path(__file__).resolve().parent.parent


def _empty_store():
    for c in db.COLLECTIONS:
        if c not in ("users", "roles"):
            STORE[c].clear()


@pytest.fixture()
def built(client):
    _empty_store()
    return SS.build(client, STORE)


def _tool():
    spec = importlib.util.spec_from_file_location("seed_demo_tool", REPO / "tools" / "seed_demo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_seed_builds_every_collection_through_the_routes(built):
    counts = {c: len(STORE[c]) for c in db.COLLECTIONS
              if STORE[c] and c not in ("users", "roles")}
    assert counts == {
        "quotations": 2, "purchases": 5, "purchase_orders": 2, "specs": 16, "boqs": 3,
        "ra_bills": 4, "receipts": 2, "delivery_challans": 4, "measurements": 1,
        "projects": 2, "charges": 5, "employees": 6, "attendance": 270, "attachments": 5,
        "addresses": 11, "settings": 8,
    }
    assert SS.is_seeded(STORE)


def test_project_1_revision_carries_the_cover_and_supersedes_rev_0(built):
    r0, r1 = STORE["boqs"][built["boq1_r0"]], STORE["boqs"][built["boq1"]]
    assert r1["supersedes"] == built["boq1_r0"] and r1["rev_no"] == 1
    assert PS.is_on(r0) and PS.is_on(r1)
    assert PS.terms_of(r1) == PS.terms_of(r0) and len(PS.terms_of(r1)) == 10
    ids0 = {li["line_id"] for li in r0["line_items"]}
    assert ids0 == {li["line_id"] for li in r1["line_items"]}, "a revision keeps its line_ids"


def test_ra2_bills_one_line_above_the_boq_with_its_reason(built):
    ra2 = STORE["ra_bills"][built["ra2"]]
    (row,) = ra2["excess_lines"]
    assert row["boq_qty"] == 4200 and row["cumulative_after"] == 4450 and row["excess"] == 250
    assert "4,450 m" in ra2["excess_reason"]


def test_the_balances_carry_forward(built):
    ra1, ra2, ra3 = (STORE["ra_bills"][built[k]] for k in ("ra1", "ra2", "ra3"))
    tds = round(ra1["claim_subtotal"] * 0.02, 0)
    assert ra2["prev_balance"] == pytest.approx(tds)            # RA1's TDS still owed
    assert ra3["prev_balance"] > ra2["grand_total"] * 0.10      # RA2 short-paid
    assert all(b["status"] == "issued" for b in (ra1, ra2, ra3))
    assert "TDS u/s 194C" in STORE["receipts"][built["receipt1"]]["notes"]


def test_the_purchase_side_is_priced_at_cost_and_the_margin_is_positive(built):
    b = STORE["boqs"][built["boq1"]]
    billed = sum(STORE["ra_bills"][built[k]]["claim_subtotal"] for k in ("ra1", "ra2", "ra3"))
    bought = sum(float(p.get("subtotal") or 0) for p in STORE["purchases"].values()
                 if p.get("project_id") == built["project1"])
    charges = sum(float(c["taxable_amount"]) for c in STORE["charges"].values())
    assert bought + charges < billed, "Project 1 shows a positive margin"
    draft = STORE["purchase_orders"][built["inquiries"][0]]
    po = STORE["purchases"][built["po_modules"]]
    assert po.get("draft_id") == draft["id"], "the winning inquiry was converted"
    assert b["supersedes"]


def test_every_print_route_for_every_seeded_document_renders(built, client):
    urls = ([f"/boq/print/{i}" for i in STORE["boqs"]]
            + [f"/ra/print/{i}" for i in STORE["ra_bills"]]
            + [f"/dc/print/{i}" for i in STORE["delivery_challans"]]
            + [f"/po/print/{i}" for i in STORE["purchase_orders"]]
            + [f"/measurement/print/{i}" for i in STORE["measurements"]]
            + [f"/quotation/view/{i}" for i in STORE["quotations"]]
            + [f"/purchase/view/{i}" for i in STORE["purchases"]])
    bad = [(u, client.get(u).status_code) for u in urls]
    bad = [x for x in bad if x[1] != 200]
    assert not bad, bad
    assert len(urls) == 3 + 4 + 4 + 2 + 1 + 2 + 5


def test_one_login_per_role():
    for username, display, role, password in SS.USERS:
        assert role in {f"role-{k}" for k in auth.BUILTIN_ROLES}
    assert len({u[2] for u in SS.USERS}) == len(auth.BUILTIN_ROLES)


def test_the_tool_refuses_a_database_that_is_not_the_demo_one(monkeypatch, capsys):
    monkeypatch.setenv("QMS_DEMO_DATA", "true")
    monkeypatch.setitem(db.CONFIG, "name", "qms")
    called = []
    tool = _tool()
    monkeypatch.setattr(tool, "_reset", lambda *_a: called.append(1) or 0)
    assert tool.main(["--reset"]) == 2
    assert "only works on the demo database 'qms_demo'" in capsys.readouterr().out
    assert called == [], "nothing may be dropped when the name is wrong"


def test_the_reset_refuses_with_demo_data_off(monkeypatch, capsys):
    monkeypatch.setenv("QMS_DEMO_DATA", "false")
    monkeypatch.setitem(db.CONFIG, "name", SS.DEMO_DB_NAME)
    tool = _tool()
    monkeypatch.setattr(tool, "_reset", lambda *_a: pytest.fail("reset ran"))
    assert tool.main(["--reset"]) == 2
    assert "QMS_DEMO_DATA is not true" in capsys.readouterr().out


def test_the_fictional_identity_lives_only_in_the_solar_seed():
    strings = (SS.COMPANY["COMPANY_GSTIN"], SS.COMPANY["COMPANY_EMAIL"],
               SS.COMPANY["COMPANY_LEGAL"], SS.COMPANY["BANK_IFSC"])
    for path in REPO.glob("*.py"):
        if path.stem == "solar_seed":
            continue
        src = path.read_text(encoding="utf8")
        for s in strings:
            assert s not in src, f"{path.name} carries the solar demo identity {s!r}"
