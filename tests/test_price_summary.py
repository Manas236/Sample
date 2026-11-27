"""
The price-summary cover on the printed BOQ, and the terms library.

Ported 27 November 2026 (FEATURE_GAP.md rows 1a and 1b; `pricesummary.py`).
What these tests hold:

* **Off by default, byte for byte.** A BOQ that never ticked the cover prints
  exactly what it printed before the cover existed — no cover markup, no cover
  CSS, no portrait rule.
* **Nothing is seeded.** The library is empty until somebody fills it, and no
  page view writes it (CLAUDE.md: nothing seeds on a page view).
* **The cover prints the chain's own figures.** One row per section with
  `boq.section_totals()`, the grand total from `boq.boq_totals()`.
* **The snapshot rule.** A BOQ prints ITS OWN terms; editing the library later
  changes no BOQ already saved.
* **Escaped.** A term is user text and reaches the printed page escaped.
"""

import boq
import pricesummary as PS
from store import STORE
from conftest import demo_boq_id

BOQ_ID = demo_boq_id()


def _print(client):
    r = client.get(f"/boq/print/{BOQ_ID}")
    assert r.status_code == 200
    return r.get_data(as_text=True)


def _save_library(client, entries=(), new="", new_on=True, title="", tax=""):
    data = {"title": title, "tax_line": tax, "new_terms": new,
            "new_category": "Payment", "lib_id": [], "lib_text": [], "lib_cat": [],
            "lib_on": []}
    if new_on:
        data["new_on"] = "1"
    for e in entries:
        data["lib_id"].append(e["id"])
        data["lib_text"].append(e["text"])
        data["lib_cat"].append(e["category"])
        if e["on"]:
            data["lib_on"].append(e["id"])
    return client.post("/settings/terms", data=data)


# ── Off by default ──────────────────────────────────────────────────────────

def test_a_boq_without_the_cover_prints_no_cover(client):
    html = _print(client)
    assert "ps-cover" not in html
    assert "PRICE SUMMARY" not in html
    assert PS.PORTRAIT_CSS not in html
    assert PS.SUMMARY_CSS not in html


def test_the_library_is_empty_and_no_page_view_seeds_it(client):
    assert PS.library() == []
    assert client.get("/settings/terms").status_code == 200
    assert client.get(f"/boq/summary/{BOQ_ID}").status_code == 200
    assert PS.RECORD not in STORE["settings"]
    assert PS.default_terms() == []


# ── The library ─────────────────────────────────────────────────────────────

def test_the_library_saves_dedupes_and_deletes(client):
    r = _save_library(client, new="50% advance with order\n50% advance with order\n\nBalance against RA bills",
                      title="Commercial Offer", tax="GST @ 18% extra")
    assert r.status_code == 302
    lib = PS.library()
    assert [e["text"] for e in lib] == ["50% advance with order", "Balance against RA bills"]
    assert all(e["on"] and e["category"] == "Payment" for e in lib)
    assert PS.title() == "Commercial Offer" and PS.tax_line() == "GST @ 18% extra"

    # delete the first, untick the second
    data = {"title": "", "tax_line": "", "new_terms": "", "new_category": "Payment",
            "lib_id": [e["id"] for e in lib], "lib_text": [e["text"] for e in lib],
            "lib_cat": [e["category"] for e in lib], "lib_del": [lib[0]["id"]]}
    client.post("/settings/terms", data=data)
    lib2 = PS.library()
    assert [e["text"] for e in lib2] == ["Balance against RA bills"]
    assert lib2[0]["on"] is False
    assert PS.title() == PS.DEFAULT_TITLE


# ── The per-BOQ editor ──────────────────────────────────────────────────────

def test_the_editor_starts_from_the_library_defaults(client):
    _save_library(client, new="Validity 30 days")
    _save_library(client, entries=PS.library(), new="Warranty as per maker", new_on=False)
    html = client.get(f"/boq/summary/{BOQ_ID}").get_data(as_text=True)
    on_id = next(e["id"] for e in PS.library() if e["text"] == "Validity 30 days")
    off_id = next(e["id"] for e in PS.library() if e["text"] == "Warranty as per maker")
    assert f'value="{on_id}" checked' in html
    assert f'value="{off_id}" checked' not in html


def test_saving_the_cover_and_printing_it(client):
    _save_library(client, new="Validity 30 days")
    pick = PS.library()[0]["id"]
    r = client.post(f"/boq/summary/{BOQ_ID}", data={
        PS.FIELD_ON: "1", PS.FIELD_ORIENT: PS.LANDSCAPE, "lib_pick": [pick],
        "own_terms": "Site water and power by client\n"})
    assert r.status_code == 302
    b = STORE["boqs"][BOQ_ID]
    assert b[PS.FIELD_ON] is True
    assert b[PS.FIELD_TERMS] == ["Validity 30 days", "Site water and power by client"]

    html = _print(client)
    cover = html.split('class="doc-outer boq-outer ps-cover"')[1].split('class="doc-outer boq-outer"')[0]
    assert PS.DEFAULT_TITLE in cover
    for s in boq._sections_of(b):
        sup, ins = boq.section_totals(b, s["code"])
        assert boq._inr(sup + ins) in cover
    sup, ins, total = boq.boq_totals(b)
    assert boq._inr(total) in cover
    assert cover.index("Validity 30 days") < cover.index("Site water and power by client")
    # the schedule still follows, whole
    assert "BILL OF QUANTITIES" in html.split("ps-cover")[-1]


def test_own_terms_can_be_saved_to_the_library(client):
    client.post(f"/boq/summary/{BOQ_ID}", data={
        PS.FIELD_ON: "1", PS.FIELD_ORIENT: PS.LANDSCAPE,
        "own_terms": "Net metering liaison in our scope", "save_own": "1",
        "own_category": "Scope"})
    lib = PS.library()
    assert [(e["text"], e["category"], e["on"]) for e in lib] == [
        ("Net metering liaison in our scope", "Scope", False)]


def test_portrait_asks_for_a_portrait_page_and_landscape_does_not(client):
    client.post(f"/boq/summary/{BOQ_ID}", data={PS.FIELD_ORIENT: PS.PORTRAIT})
    assert PS.PORTRAIT_CSS in _print(client)
    client.post(f"/boq/summary/{BOQ_ID}", data={PS.FIELD_ORIENT: PS.LANDSCAPE})
    assert PS.PORTRAIT_CSS not in _print(client)


def test_an_unknown_orientation_is_refused(client):
    r = client.post(f"/boq/summary/{BOQ_ID}", data={PS.FIELD_ORIENT: "sideways"})
    assert r.status_code == 200
    assert "Portrait or Landscape" in r.get_data(as_text=True)
    assert PS.FIELD_ORIENT not in STORE["boqs"][BOQ_ID]


def test_the_snapshot_rule(client):
    _save_library(client, new="Payment within 15 days")
    pick = PS.library()[0]["id"]
    client.post(f"/boq/summary/{BOQ_ID}", data={PS.FIELD_ON: "1", PS.FIELD_ORIENT: PS.LANDSCAPE,
                                                "lib_pick": [pick]})
    e = PS.library()[0]
    client.post("/settings/terms", data={"title": "", "tax_line": "", "new_terms": "",
                                         "new_category": "Payment", "lib_id": [e["id"]],
                                         "lib_text": ["Payment within 60 days"],
                                         "lib_cat": [e["category"]]})
    html = _print(client)
    assert "Payment within 15 days" in html
    assert "Payment within 60 days" not in html


def test_a_term_is_escaped_on_the_print(client):
    client.post(f"/boq/summary/{BOQ_ID}", data={
        PS.FIELD_ON: "1", PS.FIELD_ORIENT: PS.LANDSCAPE,
        "own_terms": '<script>alert(1)</script> & "quotes"'})
    html = _print(client)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; &quot;quotes&quot;" in html


def test_a_revision_carries_the_cover_fields():
    src = {PS.FIELD_ON: True, PS.FIELD_TERMS: ["a"], PS.FIELD_ORIENT: PS.PORTRAIT, "ref": "x"}
    assert PS.carry_fields(src) == {PS.FIELD_ON: True, PS.FIELD_TERMS: ["a"],
                                    PS.FIELD_ORIENT: PS.PORTRAIT}
    assert PS.carry_fields({"ref": "x"}) == {}


def test_the_boq_view_links_the_editor(client):
    html = client.get(f"/boq/view/{BOQ_ID}").get_data(as_text=True)
    assert f"/boq/summary/{BOQ_ID}" in html
