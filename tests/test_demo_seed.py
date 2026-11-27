"""
`demo_seed.py` and `tools/seed_demo.py` — the fictional demo company.

Replaces `tests/test_seed_demo_scenario.py`, which tested
`tools/seed_demo_scenario.py` (a write/purge tool for one client's demo set);
both were removed with the client's seed (October 2026). The rules that file
pinned and that still have a subject are carried here:

1. ⚠ **NOTHING IN THE APPLICATION REACHES THE TOOL.** It is a command line an
   operator types, not a seeder. `boq.py` reads the seed MODULE for one thing —
   the sample schedule the create form's demo fill loads into the editor — and
   `test_import_directions.py` holds that.
2. ⚠ **A SECOND RUN ADDS NOTHING.** The old tool proved write-twice-creates-
   one-set; this one refuses any database that is not empty, so the proof is
   that a seeded store is never empty.
3. **No seeded employee joins the closed pre-day-rate set**, one employee is
   marked absent so the zero-cost path renders, and the markings share one
   site.

And the rules that are new with it:

4. **It is built through the routes.** Every record exists because a form was
   posted and accepted — the full build on an empty store is the proof, with
   every collection's count pinned.
5. **The interlock.** `QMS_DEMO_DATA` false, or an in-memory store, and the
   tool refuses before it writes anything.
6. **It is fictional.** Every GSTIN passes the check-character algorithm, every
   e-mail is on the reserved `.example` domain, and no user is created by the
   build (the tool mints the one admin, with a printed one-time password).
"""

import ast
import importlib.util
import pathlib

import pytest

import db
import demo_seed as DS
import gst_lookup
import settings as ST
from store import STORE

REPO = pathlib.Path(__file__).resolve().parent.parent


def _empty_store():
    """A brand-new database, as the boot leaves it: roles and the genuine
    default only. `users` keeps the harness's signed-in account."""
    for coll in db.COLLECTIONS:
        if coll not in ("users", "roles"):
            STORE[coll].clear()
    STORE["_settings_seeded"] = False
    ST.ensure_default_settings()


@pytest.fixture()
def built(client):
    _empty_store()
    users_before = dict(STORE["users"])
    ids = DS.build(client, STORE)
    return ids, users_before


def _tool():
    spec = importlib.util.spec_from_file_location(
        "seed_demo_tool", REPO / "tools" / "seed_demo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── 1. Nothing in the application reaches the tool ──────────────────────────

def test_nothing_in_the_application_reaches_the_tool():
    for path in REPO.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not any(n.split(".")[-1] == "seed_demo" for n in names), path.name


# ── 4. Built through the routes ─────────────────────────────────────────────

def test_the_full_seed_builds_every_document_through_the_routes(built):
    ids, _ = built
    counts = {c: len(STORE[c]) for c in db.COLLECTIONS
              if STORE[c] and c not in ("users", "roles")}
    assert counts == {
        "settings": 6, "specs": 15, "addresses": 6, "projects": 1, "boqs": 1,
        "measurements": 1, "delivery_challans": 2, "ra_bills": 2, "receipts": 1,
        "purchase_orders": 1, "purchases": 2, "charges": 5, "attachments": 5,
        "quotations": 1, "proformas": 1, "invoices": 1,
        "employees": 3, "attendance": 9,
    }
    assert sorted(STORE["settings"]) == [
        "charge_heads", "company", "delivery_challan_series", "landing",
        "measurement_columns", "po_draft_series"]
    assert len(STORE["boqs"][ids["boq"]]["line_items"]) == len(DS.BOQ_LINES) == 24


def test_the_chain_is_in_the_states_the_demo_describes(built):
    import dcbill

    ids, _ = built
    supply, install = STORE["ra_bills"][ids["ra_supply"]], STORE["ra_bills"][ids["ra_install"]]
    assert supply["status"] == "issued"
    assert install["status"] == "draft"
    # Challan 1 is billed — by the issued supply RA raised from it; challan 2 is not.
    dc1, dc2 = ids["dc"]
    assert dcbill.billed_by(dc1) and dcbill.billed_by(dc1)[0] == ids["ra_supply"]
    assert dcbill.billed_by(dc2) is None
    # The receipt is against the issued bill.
    assert STORE["receipts"][ids["receipt"]].get("ra_id") == ids["ra_supply"]


def test_the_discount_is_a_negative_escalation_on_one_line(built):
    ids, _ = built
    lines = STORE["boqs"][ids["boq"]]["line_items"]
    discounted = [li for li in lines if (li.get("supply_escalation_pct") or 0) < 0]
    assert len(discounted) == 1
    li = discounted[0]
    assert (li["section"], li["item_no"]) == ("A", "4")
    assert li["supply_rate"] == round(li["supply_base_rate"] * 0.9, 2)


# ── 2. A second run adds nothing ───────────────────────────────────────────

def test_an_empty_store_may_be_seeded(client):
    _empty_store()
    STORE["users"].clear()
    assert DS.emptiness_problems(STORE) == []


def test_a_seeded_store_is_never_empty_so_a_second_run_adds_nothing(built):
    problems = DS.emptiness_problems(STORE)
    assert problems, "a seeded database read as empty — a second run would double it"
    assert any(p.startswith("boqs holds 1") for p in problems)
    assert any("company" in p for p in problems if p.startswith("settings"))


def test_the_genuine_defaults_do_not_make_a_store_look_seeded(client):
    _empty_store()
    STORE["users"].clear()
    assert set(STORE["settings"]) == {"charge_heads"}
    assert STORE["roles"], "the builtin roles exist"
    assert DS.emptiness_problems(STORE) == []


# ── 6. Fictional, and it creates no login ───────────────────────────────────

def test_the_build_creates_no_user(built):
    _, users_before = built
    assert STORE["users"] == users_before, (
        "demo_seed.build() created a user. The one admin is minted by "
        "tools/seed_demo.py, with a password it prints once.")


def test_every_seeded_gstin_passes_the_check_character():
    gstins = [DS.COMPANY["COMPANY_GSTIN"]] + [a["gstin"] for a in DS.ADDRESSES if a["gstin"]]
    assert len(gstins) == 6
    for g in gstins:
        assert gst_lookup.check_digit_ok(g), g
    assert gst_lookup.pan_of(DS.COMPANY["COMPANY_GSTIN"]) == DS.COMPANY["COMPANY_PAN"]


def test_every_seeded_contact_is_on_the_reserved_example_domain():
    emails = [DS.COMPANY["COMPANY_EMAIL"]] + [a.get("email") or "" for a in DS.ADDRESSES]
    emails = [e for e in emails if e]
    assert emails
    for e in emails:
        assert e.endswith(".example"), e
    assert DS.COMPANY["COMPANY_WEB"].endswith(".example")


# ── 3. People ───────────────────────────────────────────────────────────────

def test_no_seeded_employee_joins_the_closed_pre_day_rate_set(built):
    for e in STORE["employees"].values():
        assert "monthly_salary" not in e
        assert e.get("rate_model") != "pre_day_rate"
        assert e.get("day_rate") and e["day_rate"] < 5000, "a DAY rate, not a salary"


def test_one_marking_is_absent_and_every_marking_shares_one_site(built):
    ids, _ = built
    marks = list(STORE["attendance"].values())
    assert sorted(m["status"] for m in marks).count("absent") == 1
    assert {m.get("site_address_id") for m in marks} == {ids["addresses"]["site"]}
    assert {m.get("project_id") for m in marks} == {ids["project"]}


# ── 5. The interlock ────────────────────────────────────────────────────────

def test_the_tool_refuses_with_demo_data_off(monkeypatch, capsys):
    monkeypatch.setenv("QMS_DEMO_DATA", "false")
    before = {c: len(STORE[c]) for c in db.COLLECTIONS}
    assert _tool().main([]) == 2
    assert "REFUSED: QMS_DEMO_DATA is not true" in capsys.readouterr().out
    assert {c: len(STORE[c]) for c in db.COLLECTIONS} == before


def test_the_tool_refuses_an_in_memory_store(monkeypatch, capsys):
    """The suite runs with persistence off, which is exactly the case: a seed
    into a store that is not written anywhere would vanish at exit."""
    monkeypatch.setenv("QMS_DEMO_DATA", "true")
    assert not db.is_live()
    before = {c: len(STORE[c]) for c in db.COLLECTIONS}
    assert _tool().main([]) == 2
    assert "persistence is not live" in capsys.readouterr().out
    assert {c: len(STORE[c]) for c in db.COLLECTIONS} == before
