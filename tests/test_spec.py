"""
Phase 2 — the specification library, the variant model, and the demo data.

    ACCEPTANCE: seed an empty database (`tools/seed_demo.py`), open /boq/ — the
    complete "Office Fit-out, Tower B" BOQ is there, all three sections,
    subtotalling 1703625.00 / 490574.00.
    Pick a spec and a variant on a new line and the description, unit, HSN, SAC
    and both base rates populate; a rate already typed is not overwritten.
"""

import json

import pytest

import demo_seed as DS
import spec
from store import STORE
from conftest import seed_baseline


@pytest.fixture()
def seeded(client):
    """The fixture world: the demo seed's library and its BOQ, built through
    the routes (`tests/conftest.py`)."""
    client.get("/boq/")
    return client


# ── The library ────────────────────────────────────────────────────────────

def test_seeds_the_whole_library(seeded):
    assert len(STORE["specs"]) == len(DS.SPECS) == 15
    assert {s["code"] for s in STORE["specs"].values()} == {d["code"] for d in DS.SPECS}


def test_every_category_is_represented(seeded):
    seen = {s["category"] for s in STORE["specs"].values()}
    assert seen == set(spec.CATEGORIES)


def test_variants_is_always_a_list_and_never_empty(seeded):
    """
    Rule 1. An unsized item carries exactly one variant with an empty label,
    so every consumer has one code path instead of two.
    """
    for s in STORE["specs"].values():
        assert isinstance(s["variants"], list)
        assert len(s["variants"]) >= 1


def test_the_pipe_and_valve_families_carry_their_full_variant_sets(seeded):
    """The families are the whole point of the model."""
    sizes = {
        "CIV-BRK-MAS":    2,   # 115 / 230 mm
        "CIV-PLASTER":    2,   # 12 / 15 mm
        "FIN-GYP-PART":   2,   # 75 / 100 mm
        "FIN-VIT-TILE":   3,   # laying only, 600, 800 mm
        "ELE-CONDUIT":    4,   # 20, 25, 32, 40 mm — two-line labels
        "ELE-WIRE-FR":    3,   # 1.5, 2.5, 4 sq mm
        "PLB-CPVC":       8,   # 80 down to 15 mm
        "HVAC-SPLIT-AC":  2,   # 1.5 / 2 TR
        "MEC-EXH-FAN":    2,   # 300 / 450 mm
        "EQP-WATER-PUMP": 2,   # 1 / 2 HP
    }
    for code, n in sizes.items():
        s = spec.spec_by_code(code)
        assert s is not None, f"{code} missing from the library"
        assert len(s["variants"]) == n, code


def test_an_unsized_spec_has_one_blank_labelled_variant(seeded):
    s = spec.spec_by_code("PLB-EWC")
    assert len(s["variants"]) == 1
    assert s["variants"][0]["label"] == ""
    assert s["variants"][0]["dimension"] is None


def test_escalation_does_not_live_in_the_library(seeded):
    """
    An escalation belongs to a project, not to the material. Putting one here
    would make one job's negotiation look like a property of the clause.
    """
    for s in STORE["specs"].values():
        assert not any("escalation" in k for k in s)
        for v in s["variants"]:
            assert not any("escalation" in k for k in v)


def test_seeding_twice_does_not_duplicate(seeded, client):
    before = len(STORE["specs"])
    seed_baseline("specs")
    assert len(STORE["specs"]) == before


def test_seeded_specs_are_not_shared_with_the_module_constant(seeded):
    """
    Editing a seeded spec must not reach back into the seed's source in
    memory, or the next seed in the same process would carry the edit — the
    seed module's own data, and the fixture world built from it.
    """
    from conftest import restore_baseline

    s = spec.spec_by_code("ELE-WIRE-FR")
    s["variants"][0]["default_supply_base_rate"] = 99999.0
    src = [d for d in DS.SPECS if d["code"] == "ELE-WIRE-FR"][0]
    assert float(src["variants"][0][4]) == 18.5
    restore_baseline()
    again = spec.spec_by_code("ELE-WIRE-FR")
    assert again["variants"][0]["default_supply_base_rate"] == 18.5


# ── CRUD ───────────────────────────────────────────────────────────────────

FORM = {
    "code": "TEST-CLAUSE", "title": "A test clause", "category": "Plumbing",
    "spec_text": "Supply and installation of a test clause.",
    "supply_hsn": "73063090", "install_sac": "995462",
    "supply_gst_rate": "18", "install_gst_rate": "18",
    "var_label": ["100mm", "150mm"], "var_dimension": ["100", "150"],
    "var_dim_unit": ["mm", "mm"], "var_unit": ["Mtrs", "Mtrs"],
    "var_supply": ["1000", "1500"], "var_install": ["300", "400"],
}


def test_add_spec(seeded, client):
    r = client.post("/spec/add", data=FORM)
    assert r.status_code == 302
    s = spec.spec_by_code("TEST-CLAUSE")
    assert s and len(s["variants"]) == 2
    assert s["variants"][1]["default_supply_base_rate"] == 1500.0


def test_edit_exists_from_day_one(seeded, client):
    """
    ABOUT.md §7.2 calls product.py's missing edit route the highest-value gap
    in the repo. A library of 56 clauses cannot be maintained by re-adding.
    """
    s = spec.spec_by_code("PLB-EWC")
    r = client.post(f"/spec/edit/{s['id']}", data=dict(
        FORM, code="PLB-EWC", title="European water closet, revised"))
    assert r.status_code == 302
    assert spec.spec_by_code("PLB-EWC")["title"] == "European water closet, revised"


def test_edit_and_add_share_validation(seeded, client):
    """Both must reject the same thing — a fork is how one stops validating."""
    s = spec.spec_by_code("PLB-EWC")
    for url in ("/spec/add", f"/spec/edit/{s['id']}"):
        r = client.post(url, data=dict(FORM, code="X", supply_hsn="8413-A"))
        assert r.status_code == 200
        assert "4, 6 or 8 digits" in r.get_data(as_text=True)


def test_rejected_form_keeps_the_users_clause(seeded, client):
    """
    address._validate()'s contract: always return data. Throwing away 1500
    characters because a code was mistyped is not acceptable.
    """
    long_text = "Supply and installation of " + ("x" * 1400)
    r = client.post("/spec/add", data=dict(FORM, code="", spec_text=long_text))
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "needs a code" in body
    assert long_text in body
    assert spec.spec_by_code("") is None


def test_duplicate_code_is_rejected(seeded, client):
    r = client.post("/spec/add", data=dict(FORM, code="PLB-EWC"))
    assert r.status_code == 200
    assert "already used" in r.get_data(as_text=True)


def test_editing_a_spec_may_keep_its_own_code(seeded, client):
    """The uniqueness check must not trip over the record being edited."""
    s = spec.spec_by_code("PLB-EWC")
    r = client.post(f"/spec/edit/{s['id']}",
                    data=dict(FORM, code="PLB-EWC"))
    assert r.status_code == 302


def test_blank_variant_rows_become_one_unsized_variant(seeded, client):
    r = client.post("/spec/add", data=dict(
        FORM, code="UNSIZED-1",
        var_label=["", "", ""], var_dimension=["", "", ""],
        var_dim_unit=["", "", ""], var_unit=["", "", ""],
        var_supply=["", "", ""], var_install=["", "", ""]))
    assert r.status_code == 302
    s = spec.spec_by_code("UNSIZED-1")
    assert len(s["variants"]) == 1
    assert s["variants"][0]["label"] == ""
    assert s["variants"][0]["dimension"] is None


def test_multiple_variants_all_need_labels(seeded, client):
    r = client.post("/spec/add", data=dict(
        FORM, code="NOLABEL", var_label=["", "150mm"]))
    assert r.status_code == 200
    assert "every variant needs a label" in r.get_data(as_text=True)


def test_delete_has_no_dependency_guard(seeded, client):
    """
    A BOQ line carries no spec_id — spec_text is copied onto it and edited
    there — so a spec has no dependents by construction and deleting one
    cannot reach a BOQ. The absence of a guard is the design.
    """
    s = spec.spec_by_code("ELE-WIRE-FR")
    sid = s["id"]
    boq = next(iter(STORE["boqs"].values()))
    before = [dict(li) for li in boq["line_items"]]

    # POST, because deleting is a POST now — the GET is a confirmation page.
    # What this test is about is the absence of a DEPENDENCY guard, not the
    # method; see tests/test_delete_methods.py for the method itself.
    assert client.get(f"/spec/delete/{sid}").status_code == 200
    assert sid in STORE["specs"], "the confirmation page must not destroy"

    r = client.post(f"/spec/delete/{sid}")
    assert r.status_code == 302
    assert sid not in STORE["specs"]
    assert boq["line_items"] == before

    import boq as boq_mod
    sup, ins, _t = boq_mod.boq_totals(boq)
    assert round(sup, 2) == 1703625.00 and round(ins, 2) == 490574.00


def test_user_text_is_escaped(seeded, client):
    r = client.post("/spec/add", data=dict(
        FORM, code="XSS-1", title='<script>alert(1)</script>',
        spec_text='clause & <b>bold</b>'))
    assert r.status_code == 302
    s = spec.spec_by_code("XSS-1")
    html = client.get(f"/spec/view/{s['id']}").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "clause &amp; &lt;b&gt;bold&lt;/b&gt;" in html


def test_reference_note_is_on_the_library_pages(seeded, client):
    """
    The seeded rates are a starting point, not a price list. A library that
    does not say so invites somebody to quote them at a different customer.
    """
    s = spec.spec_by_code("PLB-EWC")
    for url in ("/spec/", f"/spec/view/{s['id']}", "/spec/add"):
        assert "reference defaults" in client.get(url).get_data(as_text=True)


# ── The demo BOQ ───────────────────────────────────────────────────────────

def test_demo_boq_is_complete_and_correct(seeded):
    boqs = STORE["boqs"]
    assert len(boqs) == 1
    b = next(iter(boqs.values()))
    assert [s["code"] for s in b["sections"]] == ["A", "B", "C"]
    assert len(b["line_items"]) == 24

    import boq as boq_mod
    sup, ins, tot = boq_mod.boq_totals(b)
    assert round(sup, 2) == 1703625.00
    assert round(ins, 2) == 490574.00
    assert round(tot, 2) == 2194199.00


def test_demo_boq_section_subtotals(seeded):
    import boq as boq_mod

    b = next(iter(STORE["boqs"].values()))
    expected = {"A": (1006370.00, 335055.00),
                "B": (416140.00, 82984.00),
                "C": (281115.00, 72535.00)}
    for code, (want_s, want_i) in expected.items():
        got_s, got_i = boq_mod.section_totals(b, code)
        assert round(got_s, 2) == want_s, code
        assert round(got_i, 2) == want_i, code


def test_areas_are_per_section_in_the_demo_boq(seeded):
    b = next(iter(STORE["boqs"].values()))
    areas = {s["code"]: s["areas"] for s in b["sections"]}
    assert areas == {"A": ["Ground Floor", "First Floor"], "B": ["Ground Floor"], "C": []}


def test_demo_boq_item_numbers_are_strings_without_float_dust(seeded):
    b = next(iter(STORE["boqs"].values()))
    nos = [li["item_no"] for li in b["line_items"]]
    assert all(isinstance(n, str) for n in nos)
    assert "1.1" in nos and "1.2" in nos and "2.1" in nos and "2.3" in nos
    assert not any("999999" in n or "000000" in n for n in nos)


def test_demo_boq_keeps_the_rates_that_contradict_their_escalation(seeded):
    """
    A line whose agreed rate differs from base x (1 + escalation) for a
    documented reason keeps the rate as entered. Re-deriving it from the base
    would erase a real commercial decision and the subtotals would stop
    matching the schedule.
    """
    b = next(iter(STORE["boqs"].values()))
    off = [li for li in b["line_items"]
           if not li["is_header"] and li["supply_base_rate"]
           and abs(li["supply_base_rate"] * (1 + li["supply_escalation_pct"] / 100.0)
                   - li["supply_rate"]) > 0.005]
    assert len(off) == 1
    # B item 3: base 12500 + 0% = 12500, agreed 14500 — 2,000/nos for the MCCB.
    three = [li for li in off if li["item_no"] == "3" and li["section"] == "B"][0]
    assert three["supply_rate"] == 14500.0
    assert "2,000/nos extra" in three["remark"]


def test_demo_boq_carries_the_dash_base_rates(seeded):
    """A "-" in the sheet is None here — negotiated directly, not free."""
    b = next(iter(STORE["boqs"].values()))
    none_base = [li for li in b["line_items"]
                 if not li["is_header"] and li["supply_base_rate"] is None
                 and li["supply_rate"] > 0]
    assert none_base, "expected lines whose rate was entered directly"


def test_demo_boq_nil_priced_lines_survive(seeded):
    """Section C item 5 — a quantity, no rate. Valid, per rule 7."""
    b = next(iter(STORE["boqs"].values()))
    nil = [li for li in b["line_items"]
           if not li["is_header"] and li["total_qty"] > 0
           and li["supply_amount"] == 0 and li["install_amount"] == 0]
    assert [(li["section"], li["item_no"]) for li in nil] == [("C", "5")]


def test_demo_boq_specification_hierarchy(seeded):
    b = next(iter(STORE["boqs"].values()))
    headers = [li for li in b["line_items"] if li["is_header"]]
    assert len(headers) == 4
    for h in headers:
        assert h["total_qty"] == 0.0
        assert h["supply_amount"] == 0.0 and h["install_amount"] == 0.0
        kids = [li for li in b["line_items"]
                if li["parent_item_no"] == h["item_no"] and li["section"] == h["section"]]
        assert kids, f"header {h['item_no']} has no children"
    kids_b2 = [li["item_no"] for li in b["line_items"]
               if li["parent_item_no"] == "2" and li["section"] == "B"]
    assert kids_b2 == ["2.1", "2.2", "2.3"]


def test_demo_boq_lines_carry_hsn_and_sac_from_the_library(seeded):
    b = next(iter(STORE["boqs"].values()))
    priced = [li for li in b["line_items"] if not li["is_header"]]
    assert all(li["install_sac"] for li in priced)
    # 20 priced lines; the two with no goods on them (testing and the nil
    # line) carry no HSN.
    assert sum(1 for li in priced if li["supply_hsn"]) == 18


def test_demo_boq_prints(seeded, client):
    b = next(iter(STORE["boqs"].values()))
    html = client.get(f"/boq/view/{b['id']}").get_data(as_text=True)
    for figure in ("10,06,370.00", "4,16,140.00", "2,81,115.00",
                   "17,03,625.00", "4,90,574.00"):
        assert figure in html, figure
    assert "BASIC VALUE SUBTOTAL (A)" in html
    assert "BASIC VALUE SUBTOTAL (B)" in html
    assert "BASIC VALUE SUBTOTAL (C)" in html
    assert "size:A4 landscape" in html


def test_editing_a_spec_does_not_reach_the_seeded_boq(seeded, client):
    """
    `spec_text` is COPIED onto a BOQ line, never referenced — the same freeze
    every issued document in this app relies on.
    """
    s = spec.spec_by_code("ELE-WIRE-FR")
    b = next(iter(STORE["boqs"].values()))
    header = [li for li in b["line_items"]
              if li["is_header"] and li["item_no"] == "2" and li["section"] == "B"][0]
    original = header["description"]

    client.post(f"/spec/edit/{s['id']}", data=dict(
        FORM, code="ELE-WIRE-FR", spec_text="REWRITTEN"))
    assert spec.spec_by_code("ELE-WIRE-FR")["spec_text"] == "REWRITTEN"
    assert header["description"] == original
    # The clause text the schedule was written from, verbatim.
    assert original == next(li["description"] for li in DS.BOQ_LINES
                            if li["section"] == "B" and li["item_no"] == "2")


# ── The picker ─────────────────────────────────────────────────────────────

def _picker_payload(client):
    import boq as boq_mod
    return json.loads(boq_mod._spec_catalog_json())


def test_picker_payload_carries_what_the_form_fills(seeded, client):
    payload = _picker_payload(client)
    assert len(payload) == 15
    one = [v for v in payload.values() if v["code"] == "ELE-WIRE-FR"][0]
    assert one["spec_text"] and one["supply_hsn"] and one["install_sac"]
    assert one["supply_gst_rate"] == 18.0 and one["install_gst_rate"] == 18.0
    assert len(one["variants"]) == 3
    v = one["variants"][0]
    assert set(v) == {"label", "unit", "s_base", "i_base"}
    assert v["unit"] == "Rmt"


def test_picker_payload_carries_no_writeback_handle(seeded, client):
    """
    The browser copies values onto a line; it must not be handed anything that
    would let it write back, and the line stores no spec id.
    """
    payload = _picker_payload(client)
    for v in payload.values():
        assert "id" not in v


def test_unsized_spec_exposes_its_single_variant(seeded, client):
    payload = _picker_payload(client)
    ewc = [v for v in payload.values() if v["code"] == "PLB-EWC"][0]
    assert len(ewc["variants"]) == 1
    assert ewc["variants"][0]["label"] == ""


def test_create_page_ships_the_library_and_the_bulk_insert(seeded, client):
    """
    Structure only — that the page carries the library and the controls.

    What the picker *does* with a value is tested by running the real
    JavaScript in tests/test_picker_js.py. This used to assert on source
    strings like `if (!L.supply_base_rate`, which is how a test keeps passing
    while the feature is broken: the string was still there, and the rule it
    encoded was the wrong rule.
    """
    html = client.get("/boq/create").get_data(as_text=True)
    assert "var SPECS = " in html
    assert "insertFamily()" in html
    assert 'id="bulk-spec"' in html and 'id="bulk-section"' in html
    assert "function fillFromSpec" in html
    assert "function fillFromVariant" in html


def test_create_page_no_longer_offers_the_sales_catalogue(seeded, client):
    """
    product.py serves the quotation chain and its base_price is not a BOQ
    supply rate. The BOQ picker must not point at it.
    """
    html = client.get("/boq/create").get_data(as_text=True)
    assert "fill from spec library" in html
    assert "fill from catalogue" not in html
