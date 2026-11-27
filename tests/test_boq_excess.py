"""
Billing above the BOQ quantity — allowed with ONE reason, never silent.

Ported 27 November 2026 (FEATURE_GAP.md row 4c; `boqexcess.py`). What these
tests hold:

* Above the BOQ quantity with NO reason is refused — the old block, with a
  message that says a reason will let it through.
* With a reason it saves, and the bill carries `excess_lines` +
  `excess_reason`, snapshotted; the RA view shows the band; the print does
  not change.
* A bill within its schedule carries NEITHER key.
* The cumulative is summed across bills (keyed on line_id), so a second bill
  that only passes the BOQ quantity together with the first is caught.
* The measurement cap stays hard (covered by the measurement suites, which
  this change did not touch); here, a line outside the schedule stays hard.
"""

import json

import boqexcess as BX
from store import STORE
from test_ra_routes import seeded, priced, payload, make_bill, claim_for  # noqa: F401


def _post(client, boq_id, rows, reason=None):
    data = {"date": "2026-08-06", "ra_json": payload(rows)}
    if reason is not None:
        data[BX.REASON_FIELD] = reason
    return client.post(f"/ra/create?boq={boq_id}&leg=supply", data=data)


def test_above_boq_without_a_reason_is_refused_and_asks_for_one(client, seeded):
    li = priced(seeded, 1)[0]
    r = _post(client, seeded, [(li["line_id"], li["total_qty"] + 3, li["supply_rate"])])
    html = r.get_data(as_text=True)
    assert STORE["ra_bills"] == {}
    assert "would be billed above the BOQ quantity" in html
    assert f'name="{BX.REASON_FIELD}"' in html          # the amber box is on the form
    assert "boq-excess-warn" in html


def test_above_boq_with_a_reason_saves_and_snapshots(client, seeded):
    li = priced(seeded, 1)[0]
    qty = li["total_qty"] + 3
    r = _post(client, seeded, [(li["line_id"], qty, li["supply_rate"])],
              reason="Site measurement exceeded the schedule  — agreed with PMC")
    assert r.status_code == 302
    (bill,) = STORE["ra_bills"].values()
    assert bill[BX.REASON_KEY] == "Site measurement exceeded the schedule — agreed with PMC"
    (row,) = bill[BX.LINES_KEY]
    assert row["line_id"] == li["line_id"]
    assert row["boq_qty"] == round(li["total_qty"], 6)
    assert row["excess"] == 3.0
    assert row["this"] == qty and row["previously"] == 0.0


def test_a_bill_within_its_schedule_carries_neither_key(client, seeded):
    li = priced(seeded, 1)[0]
    r = _post(client, seeded, [(li["line_id"], li["total_qty"], li["supply_rate"])])
    assert r.status_code == 302
    (bill,) = STORE["ra_bills"].values()
    assert BX.LINES_KEY not in bill and BX.REASON_KEY not in bill


def test_the_excess_is_cumulative_across_bills(client, seeded):
    li = next(x for x in priced(seeded) if x["total_qty"] >= 10)
    half = li["total_qty"] / 2
    make_bill(seeded, 1, claims=[claim_for(li, half)])
    r = _post(client, seeded, [(li["line_id"], half + 1, li["supply_rate"])])
    assert "would be billed above the BOQ quantity" in r.get_data(as_text=True)
    r = _post(client, seeded, [(li["line_id"], half + 1, li["supply_rate"])], reason="Extra run")
    assert r.status_code == 302
    new = [b for b in STORE["ra_bills"].values() if b.get(BX.LINES_KEY)]
    (row,) = new[0][BX.LINES_KEY]
    assert row["previously"] == round(half, 6) and row["excess"] == 1.0


def test_the_view_shows_the_band_and_the_print_does_not(client, seeded):
    li = priced(seeded, 1)[0]
    _post(client, seeded, [(li["line_id"], li["total_qty"] + 1, li["supply_rate"])],
          reason="Measured at site")
    (rid,) = STORE["ra_bills"].keys()
    view = client.get(f"/ra/view/{rid}").get_data(as_text=True)
    assert "boq-excess-band" in view and "Measured at site" in view
    printed = client.get(f"/ra/print/{rid}").get_data(as_text=True)
    assert "boq-excess" not in printed


def test_a_line_outside_the_schedule_is_still_a_hard_block(client, seeded):
    li = priced(seeded, 1)[0]
    bogus = "f" * 12
    rows = [(li["line_id"], 1, li["supply_rate"]), (bogus, 1, 100)]
    r = _post(client, seeded, rows, reason="any")
    assert STORE["ra_bills"] == {}
    assert r.status_code == 200


def test_the_reason_is_escaped_on_the_view(client, seeded):
    li = priced(seeded, 1)[0]
    _post(client, seeded, [(li["line_id"], li["total_qty"] + 1, li["supply_rate"])],
          reason="<b>x</b>")
    (rid,) = STORE["ra_bills"].keys()
    view = client.get(f"/ra/view/{rid}").get_data(as_text=True)
    assert "&lt;b&gt;x&lt;/b&gt;" in view and "<b>x</b>" not in view


def test_snapshot_and_stamp_are_pure():
    rec = {}
    BX.stamp(rec, [], "r")
    assert rec == {}
    BX.stamp(rec, [{"line_id": "a", "item_no": "1", "leg": "supply", "approved": 2,
                    "previously": 1, "this": 3, "cumulative": 4, "over": 2}], "why")
    assert rec[BX.LINES_KEY][0]["excess"] == 2.0 and rec[BX.REASON_KEY] == "why"
    BX.stamp(rec, [], "")
    assert rec == {}
    assert json.dumps(BX.snapshot(None)) == "[]"
