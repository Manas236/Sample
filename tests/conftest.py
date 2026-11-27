"""
Shared test fixtures.

`DB_ENABLED=false` is set **before** `app` is imported, because `db.py` reads
its config into `_CFG` at import time and `load_dotenv()` does not override a
variable that is already in the environment. Without this the suite would try
to reach the developer's real MySQL and write test records into it.

⚠ **THE SUITE DOES NOT READ THE CHECKOUT'S `.env` AT ALL** — 25 September 2026,
  CLIENT_CHANGES.md §0, the thirty-first block. See `_never_read_dotenv()`
  below for what that means and why it had to be total rather than a list of
  names.
"""

import os
import pathlib
import sys


# ── The checkout's `.env` must not reach the suite ─────────────────────────
#
# ⚠ **MEASURED, not anticipated.** With a production-shaped `.env` in the
#   checkout — `SESSION_COOKIE_SECURE=true`, `DB_STRICT=true`, a real password
#   — the suite went **2 failed, 2845 passed** on 25 September 2026. That
#   matters because running the tests is the one check an operator performs
#   after a deploy, and it was useless on the only box where it is most wanted.
#
# **Why this, and not "set the handful of names conftest cares about".**
# `db.py` calls `load_dotenv(override=False)` at import, so **every** variable
# in `.env` that the suite has not already set reaches the application. A list
# of names here would be a list somebody has to remember to extend, and the
# variable nobody remembered is the one that breaks the deploy check. Replacing
# the loader is total: no value in `.env` can reach the suite, whatever it is
# called and whenever it is added.
#
# ⚠ **It has to run BEFORE `db` is imported.** `db.py` does
#   `from dotenv import load_dotenv`, which binds the function object at ITS
#   import — patching the attribute afterwards would rebind nothing.
#
# ⚠ **This changes nothing about the running application.** `.env` still
#   reaches `python app.py` and `gunicorn` exactly as it always has; this is
#   the test process and only the test process. `tests/test_env_isolation.py`
#   asserts that `db.py` still calls the loader unconditionally.
def _never_read_dotenv() -> None:
    import dotenv

    def _refuse(*_a, **_kw):
        """Stand in for `dotenv.load_dotenv`, and load nothing."""
        return False

    dotenv.load_dotenv = _refuse
    dotenv.main.load_dotenv = _refuse


_never_read_dotenv()

os.environ["DB_ENABLED"] = "false"
os.environ.setdefault("SECRET_KEY", "test-secret")

# ⚠ **THE DEMO INTERLOCK IS FORCED ON FOR THE SUITE, and it is `=` rather
#   than `setdefault` on purpose** (ABOUT.md §7 gap 35).
#
# `QMS_DEMO_DATA` defaults to **off**, because the failure that matters is a
# production box nobody configured. The suite builds its fixture world FROM
# the demo seed (see `_build_baseline()` below), and a developer or a
# production box with `QMS_DEMO_DATA=false` in the environment must not turn
# the whole suite red for a reason that has nothing to do with the code.
# `tests/test_demo_data_flag.py` covers the OFF state, setting the variable per
# test with `monkeypatch`.
os.environ["QMS_DEMO_DATA"] = "true"

# The local-dev session-cookie values, set explicitly rather than left to the
# defaults. `.env` can no longer reach the suite, but a developer or a CI job
# with these exported in the REAL environment still can — and
# `SESSION_COOKIE_SECURE=true` there would turn `tests/test_deployment_config.py`
# red for a reason that has nothing to do with the code under test.
os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["SESSION_COOKIE_HTTPONLY"] = "true"
os.environ["SESSION_COOKIE_SAMESITE"] = "Lax"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from store import STORE  # noqa: E402


# ── Authentication ─────────────────────────────────────────────────────────
#
# Phase 3B closed this application: `auth._gate()` refuses every endpoint that
# is not PUBLIC, so without a session the ~920 tests written before it would
# all redirect to /login and assert against the redirect page.
#
# `client` therefore arrives signed in. That is blunt on purpose and it hides
# gating bugs by construction — a test using this fixture can never tell you
# whether a route was reachable without a session. `tests/test_access_control.py`
# is what covers that, using `anon_client` below, and it is the reason this
# fixture is allowed to be as blunt as it is. **Do not add access-control
# assertions to tests that use `client`; they would pass for the wrong reason.**
#
# The seeded account holds the **Owner** role, not Director. CLIENT_CHANGES-2.md
# B3 splits the two — a Director administers users but "cannot alter role
# definitions" — so a Director session would 403 on `/roles/*` and the page
# sweeps in `test_page_chrome.py` and `test_entity_fallbacks.py` would fail on a
# rule working exactly as specified.
TEST_USER = "test-owner"
TEST_PASSWORD = "test-owner-password"


def ensure_test_user():
    """The seeded Owner the suite signs in as. Idempotent."""
    import auth

    auth.ensure_builtin_roles()
    user = auth.find_user(TEST_USER)
    if user is None:
        user = auth.create_user(TEST_USER, "Test Owner", TEST_PASSWORD,
                                ["role-owner"], created_by="conftest")
    user["active"] = True
    return user


def printable(record):
    """
    Mark one approvable record APPROVED, so B7's print gate lets it through.

    CC-2 **B7** (29 August 2026): *"an unapproved document may be viewed, but
    not printed or downloaded."* `/ra/print/<id>` refuses an unapproved bill,
    which is correct and is asserted directly in `tests/test_approval_b7.py`.

    Every test that existed before B7 builds its bill as a fixture and then
    prints it to check the **document**, not the ladder — so those fixtures now
    have to describe a document that can actually be printed. This is what says
    so, in one place, rather than an `approval_status` key scattered through
    eight files with no explanation attached to any of it.

    ⚠ **It writes the status directly and does not climb the ladder**, because
    the suite signs in as the Owner and the Owner cannot approve a record the
    Owner raised — B6's creator guard, working exactly as specified. Climbing it
    properly would mean inventing two more users in every one of those files to
    test something they are not about. `tests/test_approval.py` is where the
    ladder is climbed for real.
    """
    record["approval_status"] = "approved"
    return record


def chain_ready(boq_id, legs=("supply", "installation")):
    """
    Satisfy CC-2 **C1**'s order of working for one BOQ, so `/ra/create` opens.

    C1 (29 August 2026, fifth override block) states the chain and `ra.py`
    enforces it **by URL**:

        BoQ -> Delivery Challan -> RA-Supply
        BoQ -> Measurement      -> RA-Installation

    Every test written before C1 raises its bill straight off a seeded schedule
    with neither step behind it, and every one of them is about the **bill** —
    the over-claim arithmetic, the tax slabs, the carried balance, the printed
    sheet — rather than about the chain. So their fixtures now have to describe
    a project a claim can actually be raised on. This is what says so, in one
    place, rather than a challan and a measurement pasted into eleven files with
    no explanation attached to any of them. It is `printable()` above, one item
    along, and it exists for the same reason.

    ⚠ **It writes the records directly and does not go through the forms**, for
    `printable()`'s reason: the suite signs in as the Owner, and an Owner cannot
    approve a measurement the Owner raised (B6's creator guard, working exactly
    as specified). Climbing the ladder properly would mean inventing two more
    users in every one of those files to test something they are not about.
    `tests/test_c1_order_of_working.py` is where the chain is exercised for
    real, through the routes, and it deliberately does **not** call this.

    The measurement carries **every line of the schedule at its full BOQ
    quantity**, so it moves no ceiling that was not already there: before C1 the
    installation ceiling was the BOQ quantity, and after this helper it is the
    BOQ quantity again. A test that was measuring the over-claim guard is still
    measuring the same numbers.

    `boq_id` defaults to the seeded schedule (`demo_boq_id()`).
    """
    import approval
    import boq as BQ
    import measurement as MS
    import settings as ST
    from store import STORE

    boq_id = boq_id or demo_boq_id()
    boq = (STORE.get("boqs") or {}).get(boq_id) or {}

    if "supply" in legs:
        STORE.setdefault("delivery_challans", {})[f"c1-dc-{boq_id}"] = {
            "id": f"c1-dc-{boq_id}", "ref": "C1/DC/0001",
            "date": "2026-08-01", "boq_id": boq_id,
            "boq_ref": boq.get("ref", ""), "items": [],
        }

    if "installation" in legs:
        items = [{"line_id": li.get("line_id"),
                  "item_no": li.get("item_no"),
                  "description": li.get("description", ""),
                  "unit": li.get("unit", ""),
                  "is_header": False,
                  "qty": float(li.get("total_qty") or 0.0),
                  "boq_qty": float(li.get("total_qty") or 0.0)}
                 for li in boq.get("line_items") or []
                 if not li.get("is_header") and BQ._line_id(li.get("line_id"))]
        # ⚠ **THE JOINT MODEL, and the fixture carries BOTH halves on purpose**
        #   (6 September 2026). `items` is what feeds `approved_qty_by_line()`
        #   and therefore the installation ceiling; `grid_*` is what prints.
        #   A fixture carrying only `items` would leave every new output sink on
        #   the joint sheet — the four header fields, the row labels and the
        #   remarks — unpoisoned by `tests/test_escaping.py`, which is exactly
        #   the failure that file exists to remember: `measurements` sat in
        #   `POISONED_COLLECTIONS` while its fields were all `""`, so the sweep
        #   walked every route and tested nothing.
        STORE.setdefault("measurements", {})[f"c1-ms-{boq_id}"] = {
            "id": f"c1-ms-{boq_id}", "ref": "C1/MS/0001",
            "fy": "26-27", "date": "2026-08-01", "boq_id": boq_id,
            "boq_ref": boq.get("ref", ""), "items": items,
            "created_by": "conftest",
            "approval_status": approval.APPROVED,
            "grid_model": MS.GRID_MODEL_JOINT,
            "grid_columns": [dict(c) for c in ST.DEFAULT_MEASUREMENT_COLUMNS],
            "grid_rows": [
                {"label": "Ground Floor", "values": {"len": 12.5, "wt": 4.0},
                 "remarks": "wall at the lift lobby"},
                {"label": "Basement", "values": {"area": 30.0, "fixed": 6.0},
                 "remarks": "basement store"},
            ],
            "system": "Civil and electrical works",
            "material": "As per BOQ",
            "dia_meter": "20 mm to 100 mm",
            "area": "All Area",
            "site_label": "Tower B, Navi Mumbai",
            "site_source": "project",
        }


# ── The fixture world: the demo seed's first stages ─────────────────────────
#
# Every test starts from the FICTIONAL company `demo_seed.py` builds — its
# identity, its spec library, its address book, its project and its BOQ — plus
# the twelve catalogue products below. It is built ONCE per session, through
# the application's own routes exactly as `tools/seed_demo.py` builds it, and
# restored per test from a deep copy.
#
# ⚠ **It is DETERMINISTIC on purpose.** The print and page goldens hash whole
#   responses, and a schedule whose ids changed every session would move them
#   every run. So while it builds, `uuid.uuid4` draws from a seeded generator
#   and every `*_at` timestamp is then pinned. The real seed is untouched by
#   this: it is the test's own fixture discipline, nothing more.
BASELINE_COLLECTIONS = ("settings", "specs", "addresses", "projects", "boqs", "products")
_BASELINE = {}

# The hidden catalogue's fixture rows. `product.py` seeds nothing; the
# catalogue tests (run under `catalogue_unhidden`) and the purchase form's item
# rows read these. Twelve trade-neutral items with FIXED ids, three of them
# assemblies, so the BOM, the picker and the purchase arithmetic have something
# real to walk.
_P = {
    "main_pump":  "a1000001-beef-4000-8000-000000000001",
    "pump_bare":  "a1000002-beef-4000-8000-000000000002",
    "motor75":    "a1000003-beef-4000-8000-000000000003",
    "base_frame": "a1000004-beef-4000-8000-000000000004",
    "engine":     "a1000005-beef-4000-8000-000000000005",
    "radiator":   "a1000006-beef-4000-8000-000000000006",
    "lub_oil":    "a1000007-beef-4000-8000-000000000007",
    "battery":    "a1000008-beef-4000-8000-000000000008",
    "fuel_tank":  "a1000009-beef-4000-8000-000000000009",
    "booster":    "a100000a-beef-4000-8000-00000000000a",
    "cabinet":    "a100000b-beef-4000-8000-00000000000b",
    "hose_reel":  "a100000c-beef-4000-8000-00000000000c",
}


def _product(key, name, part_no, unit, price, desc, ptype, children=(), hsn=""):
    return {"id": _P[key], "name": name, "part_no": part_no, "hsn": hsn, "unit": unit,
            "base_price": float(price), "description": desc, "type": ptype,
            "children": [{"product_id": _P[k], "qty": q} for k, q in children]}


TEST_PRODUCTS = [
    _product("radiator", "RADIATOR COOLANT", "RAD-001", "L", 8_500,
             "Standard coolant for diesel engines. 10L fill capacity.", "standalone", hsn="38200000"),
    _product("lub_oil", "LUB OIL", "OIL-002", "L", 3_200,
             "15W-40 mineral lubricant. Recommended change: 250 hrs.", "standalone", hsn="27101980"),
    _product("battery", "BATTERY 180 AMP", "BAT-003", "pcs", 12_500,
             "12V / 180 Ah sealed lead-acid. Maintenance-free.", "standalone", hsn="85071000"),
    _product("fuel_tank", "FUEL TANK 200 LTR", "FT-004", "pcs", 18_000,
             "Mild steel fuel tank, 200L capacity, coated interior.", "standalone", hsn="73090090"),
    _product("cabinet", "WALL-MOUNTED SAFETY CABINET", "SAF-005", "pcs", 2_450,
             "Powder-coated steel cabinet with lock and wall bracket.", "standalone", hsn="94032090"),
    _product("hose_reel", "WATER HOSE REEL 30 M", "HR-006", "pcs", 9_800,
             "Swinging hose reel drum, 20 mm bore rubber hose with shut-off nozzle.",
             "standalone", hsn="84249000"),
    _product("pump_bare", "END SUCTION PUMP 80/26", "PMP-010", "set", 125_000,
             "Horizontal end-suction pump. Flow: 80 m3/hr, Head: 26m.", "support", hsn="84137010"),
    _product("motor75", "75KW/100HP MOTOR", "MOT-011", "pcs", 210_000,
             "TEFC squirrel cage induction motor. 75kW, 4-pole, 415V/50Hz.", "support", hsn="85015290"),
    _product("base_frame", "PUMP BASE FRAME 80/26", "FRM-012", "pcs", 45_000,
             "Fabricated MS base frame for the 80/26 pump + motor set.", "support", hsn="73089090"),
    _product("main_pump", "MAIN PUMP SET - ELECTRIC", "MPS-100", "set", 850_000,
             "Complete electric-driven main pump set: pump, motor and base frame, "
             "coupled and factory tested.", "assembly",
             (("pump_bare", 1), ("motor75", 1), ("base_frame", 1)), hsn="84137010"),
    _product("engine", "DIESEL ENGINE DRIVE PACKAGE", "DEP-200", "set", 380_000,
             "Diesel engine drive package. Radiator-cooled, electric start, "
             "with fuel tank and first fill.", "assembly",
             (("radiator", 1), ("lub_oil", 5), ("fuel_tank", 1)), hsn="84089090"),
    _product("booster", "PRESSURE BOOSTER PUMP SET", "PBP-300", "set", 95_000,
             "Pressure-maintenance booster pump. Auto start/stop on pressure drop.",
             "assembly", (("battery", 1),), hsn="84137010"),
]


def _build_baseline():
    """Build the fixture world once — through the routes, deterministically."""
    import copy
    import random
    import re
    import uuid

    import app as app_module
    import auth
    import branding as B
    import demo_seed as DS
    import settings as ST

    app_module.app.config["TESTING"] = True
    for key in BASELINE_COLLECTIONS:
        STORE[key].clear()
    rng = random.Random(20261015)
    real_uuid4 = uuid.uuid4
    uuid.uuid4 = lambda: uuid.UUID(int=rng.getrandbits(128), version=4)
    try:
        STORE["_settings_seeded"] = False
        ST.ensure_default_settings()
        user = ensure_test_user()
        with app_module.app.test_client() as c:
            with c.session_transaction() as sess:
                sess[auth.SESSION_KEY] = user["id"]
            DS.build(c, STORE, stages=DS.TEST_BASELINE)
    finally:
        uuid.uuid4 = real_uuid4
    for p in TEST_PRODUCTS:
        STORE["products"][p["id"]] = copy.deepcopy(p)

    stamp = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}")

    def _pin(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.endswith("_at") and isinstance(v, str) and stamp.match(v):
                    obj[k] = "2026-08-01 10:00" + (":00" if v.count(":") == 2 else "")
                else:
                    _pin(v)
        elif isinstance(obj, list):
            for v in obj:
                _pin(v)

    for key in BASELINE_COLLECTIONS:
        _pin(STORE[key])
        _BASELINE[key] = copy.deepcopy(STORE[key])
    B.apply_settings(ST.load_saved())
    B.apply_logo(ST.load_logo())


def restore_baseline():
    """Put the fixture world back — the six baseline collections and the
    branding module's live identity — exactly as `_build_baseline()` left it."""
    import copy

    import branding as B
    import settings as ST

    if not _BASELINE:
        _build_baseline()
    for key in BASELINE_COLLECTIONS:
        STORE[key].clear()
        STORE[key].update(copy.deepcopy(_BASELINE[key]))
    B.apply_settings(ST.load_saved())
    B.apply_logo(ST.load_logo())


def seed_baseline(*collections) -> None:
    """
    Put back any baseline record MISSING from `collections`, leaving every
    other record — a test's own — where it is. The old `ensure_demo_*()`
    seeders' exact contract (fill a gap, never overwrite), now that no module
    seeds anything: a test that cleared the address book and wants the demo
    book back calls `seed_baseline("addresses")`.
    """
    import copy

    if not _BASELINE:
        _build_baseline()
    for key in collections or BASELINE_COLLECTIONS:
        for rid, rec in _BASELINE[key].items():
            if rid not in STORE[key]:
                STORE[key][rid] = copy.deepcopy(rec)


def demo_boq_id() -> str:
    """
    The seeded schedule's id — "Office Fit-out, Tower B", revision 0.

    Found by its FIXED baseline id, never by its name: a test may rewrite the
    name (`test_escaping.py` appends a payload to every string), and a lookup
    by name would then miss it and "repair" a store the test had built on
    purpose. If a test removed it, it is put back the old `ensure_demo_boq()`
    way — the gaps filled, nothing that is there overwritten.
    """
    if not _BASELINE:
        _build_baseline()
    (bid,) = _BASELINE["boqs"]
    if bid not in STORE["boqs"]:
        seed_baseline("specs", "addresses", "projects", "boqs")
    return bid


def demo_line(section: str, item_no: str) -> dict:
    """One line of the seeded schedule, named the way a person names it."""
    for li in STORE["boqs"][demo_boq_id()]["line_items"]:
        if li["section"] == section and li["item_no"] == item_no:
            return li
    raise KeyError((section, item_no))


def demo_address_id(key: str) -> str:
    """The id of one seeded address, by its `demo_seed.ADDRESSES` key."""
    import demo_seed as DS

    # Read from the BUILT baseline, not the live store: several test modules
    # use an address id at import time (a module constant, a default
    # argument), before any fixture has run. Ids are deterministic, so the
    # baseline's id is the live one.
    if not _BASELINE:
        _build_baseline()
    label = next(a["label"] for a in DS.ADDRESSES if a["key"] == key)
    return next(aid for aid, a in _BASELINE["addresses"].items()
                if a.get("label") == label)


def _fresh_store():
    """The per-test reset the `client` fixture has always done."""
    restore_baseline()
    for key in ("quotations", "proformas", "invoices", "purchases",
                # C1/C2 (29 August 2026). `chain_ready()` plants a challan and
                # an approved measurement keyed on the BOQ id, and the demo BOQ
                # has ONE fixed id — so without clearing these two a sheet
                # planted by one test would satisfy C1 for the next one and the
                # chain guard would be untestable.
                "measurements", "delivery_challans",
                # C3 (2 Sep 2026), and for a sharper version of the same
                # reason. A merged document is keyed on two RA bill ids, and
                # the fixtures use FIXED ids (`r1-supply`, `r3-install`) — so a
                # merged document planted by one test goes on holding the next
                # test's bills, and `merged_ra.create()` correctly refuses to
                # merge them again. The guard is right; the leak was the store.
                "merged_ras"):
        STORE[key].clear()
    # B8 (2 Sep 2026). Metadata rows are per-test for the same reason every
    # other collection is: a charge id planted by one test must not arrive
    # carrying the previous test's supplier bill. The FILES are isolated
    # separately and more strongly — see `_attachment_store` below.
    STORE.setdefault("attachments", {}).clear()
    # Import BOQ from Excel (29 Sep 2026). A staged upload and a remembered
    # layout are per-test for the reason above: a layout confirmed by one test
    # would send the next test's upload straight past the preview, and a staged
    # row left behind reads to `test_hardening.py` exactly like a seeder.
    STORE.setdefault("boq_imports", {}).clear()
    STORE.setdefault("import_layouts", {}).clear()
    # GSTIN auto-fill (29 Sep 2026). A cached lookup planted by one test would
    # fill the next test's form with no CAPTCHA and gate its save on a status
    # it never asked about. The RAM-only portal sessions and the per-user rate
    # buckets are reset too — the whole suite signs in as ONE Owner, so ten
    # lookups anywhere would rate-limit every later test.
    STORE.setdefault("gst_cache", {}).clear()
    import gst_lookup
    gst_lookup._SESSIONS.clear()
    gst_lookup._CALLS.clear()


# ── B8: attachments never touch the developer's real store ─────────────────
#
# ⚠ **AUTOUSE, and it has to be.** `attachment.root()` defaults to
# `<repo>/attachments/`, which is where the running application keeps real
# scanned supplier bills. A test that posts a charge writes a file, and without
# this fixture it would write it **there** — and `test_attachments.py`'s cascade
# tests would then delete files out of that same directory. Opting in per test
# would mean the one test that forgot was the one that did the damage.
#
# `attachment.root()` re-reads the environment on every call rather than caching
# it in a module constant, precisely so this fixture works.
@pytest.fixture(autouse=True)
def _attachment_store(tmp_path, monkeypatch):
    """Point the attachment store at a per-test temporary directory."""
    d = tmp_path / "attachments"
    d.mkdir()
    monkeypatch.setenv("ATTACHMENT_DIR", str(d))
    yield d


# ── GSTIN auto-fill: NO test may reach the real GST portal ─────────────────
#
# ⚠ **AUTOUSE, for the reason `_attachment_store` is.** Several sweeps GET
# every route in the application — reachability, escaping, chrome — and
# `/address/gst/captcha` is a route whose whole job is an outbound call to
# services.gst.gov.in. Opting in per test would mean the one sweep that forgot
# was the one that phoned a government portal from CI.
#
# `gst_lookup._open()` is the single function in that module that touches the
# network (an AST test in `tests/test_gst_lookup.py` holds that), so replacing
# it is total. Here it RAISES — exactly what a dropped connection does — so a
# sweep sees the ordinary "Auto-fill unavailable" answer. The GST tests
# replace it again with recorded answers, inside this fixture's patch.
@pytest.fixture(autouse=True)
def _no_gst_network(monkeypatch):
    import gst_lookup

    def _refuse(*_a, **_kw):
        raise OSError("tests/conftest.py: the GST portal is not reachable from the suite")

    monkeypatch.setattr(gst_lookup, "_open", _refuse)
    monkeypatch.delenv("GST_API_KEY", raising=False)
    yield


# ── The smallest real files of each type B8 accepts ────────────────────────
#
# ⚠ **Real headers, not `b"fake png"`.** `attachment.sniff()` reads the leading
# bytes, so a fixture that is not really a PNG would be rejected — and a test
# that passed against a fake would be asserting nothing about the guard it is
# there to exercise. Each of these begins with the exact signature
# `attachment.SIGNATURES` looks for.
# No escape sequences here on purpose: `bytes.fromhex()` states each signature
# as the hex a file viewer shows, and `bytes(n)` is n zero bytes. A literal
# backslash escape in a fixture is one transcription error away from being a
# file that is not the type it claims, which is the one thing these must not be.
PNG_BYTES = bytes.fromhex("89504e470d0a1a0a") + bytes(64)
JPEG_BYTES = bytes.fromhex("ffd8ffe0") + bytes(64)
PDF_BYTES = b"%PDF-1.4" + bytes.fromhex("0a25c7ec8fa20a") + bytes(32)

# ⚠ **A real Windows executable header, labelled as an image.** This is the
# file CC-2's type gate exists for and the one the mutation proof uses: the
# name says .png, the browser says image/png, and only the bytes disagree.
EXE_BYTES = bytes.fromhex("4d5a9000") + bytes(64)


def upload(data: bytes, filename: str = "bill.png", content_type: str = "image/png"):
    """
    One multipart file part, as Werkzeug's test client wants it.

    ⚠ **`filename` and `content_type` are the CALLER's to lie with**, and
    several tests do exactly that. They are what a browser sends and what an
    attacker controls; `attachment.sniff()` reads neither.
    """
    import io

    return (io.BytesIO(data), filename, content_type)


def charge_form(**over):
    """
    A complete, valid `/charge/new` post — attachment included.

    B8 makes the attachment **compulsory on a charge**, so every test that
    creates one through the form has to send a file. This is that form in one
    place rather than in each of them.
    """
    form = {
        "date": "2026-08-29", "person": "R. Surveyor", "head": "Travel",
        "description": "Site visit", "taxable_amount": "1200", "gst_rate": "0",
        "attachment": upload(PNG_BYTES),
    }
    form.update(over)
    return form


@pytest.fixture()
def client():
    """A Flask test client, signed in as the seeded Owner, over a fresh STORE."""
    import app as app_module
    import auth

    app_module.app.config["TESTING"] = True
    _fresh_store()
    user = ensure_test_user()
    with app_module.app.test_client() as c:
        with c.session_transaction() as sess:
            sess[auth.SESSION_KEY] = user["id"]
        yield c


@pytest.fixture()
def anon_client():
    """
    A test client with **no session at all** — the anonymous caller.

    A separate client rather than a logged-out `client`, because
    `session.clear()` on a client that has already been signed in still leaves a
    cookie jar, and "refused because the cookie was cleared" is a weaker
    statement than "refused having never had one".
    """
    import app as app_module

    app_module.app.config["TESTING"] = True
    _fresh_store()
    ensure_test_user()
    with app_module.app.test_client() as c:
        yield c


REPO = pathlib.Path(__file__).resolve().parent.parent

# The synthetic workbooks (fixtures/README.md) — committed, and rebuilt by
# `fixtures/build_fixtures.py`. Looked for in fixtures/ and demo_files/.
_FIXTURE_DIRS = (REPO / "fixtures", REPO / "demo_files")


def find_fixture(name: str):
    """The path to a synthetic workbook, or None when it is not there."""
    for d in _FIXTURE_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def require_fixture(name: str):
    """
    The path to a synthetic workbook, or an explicit skip.

    Skip, never fail: a checkout that deleted them can rebuild them with
    `python fixtures/build_fixtures.py`, and the message says so rather than
    saying "skipped" and leaving the reader to work out why.
    """
    p = find_fixture(name)
    if p is None:
        pytest.skip(f"fixture workbook {name!r} not found in fixtures/ or "
                    f"demo_files/ - rebuild it with "
                    f"`python fixtures/build_fixtures.py`")
    return p


@pytest.fixture()
def demo_boq_xlsx():
    return require_fixture("demo_boq.xlsx")


@pytest.fixture()
def demo_annexure_xlsx():
    return require_fixture("demo_annexure.xlsx")


@pytest.fixture()
def fixtures_dir():
    return REPO


@pytest.fixture()
def catalogue_unhidden():
    """
    Empty `auth.HIDDEN_BLUEPRINTS` for one test, and put it back afterwards.

    The product catalogue is hidden from everybody on the shipped
    configuration (11 September 2026, CLIENT_CHANGES.md §0 twenty-seventh
    block) — `product.py` itself is untouched and fully frozen. The tests that
    exercise its pages run under this fixture so they keep proving the module
    works for the day it is un-hidden, rather than being rewritten into 403
    checks that prove nothing about it. `tests/test_product_hidden.py` covers
    the hidden state on its own.

    The set is mutated in place, never rebound, so every reader that goes
    through `auth.blueprint_hidden()` sees the change — and the teardown
    restores the exact contents rather than assuming what they were.
    """
    import auth

    saved = set(auth.HIDDEN_BLUEPRINTS)
    auth.HIDDEN_BLUEPRINTS.clear()
    try:
        yield
    finally:
        auth.HIDDEN_BLUEPRINTS.clear()
        auth.HIDDEN_BLUEPRINTS.update(saved)


@pytest.fixture()
def ladder_on():
    """
    Switch the approval ladder ON for one test, and put it back afterwards.

    The ladder is switched OFF on the shipped configuration (12 September
    2026, CLIENT_CHANGES.md §0 twenty-eighth block — `approval.LADDER_ON`).
    The tests that prove the ladder — `tests/test_approval.py`, the B7 print
    gate, the B8 download gate, the measurement cap and pin, the dashboard's
    pending tile — run under this fixture so they keep proving it for the day
    it returns, rather than being rewritten into OFF checks that prove nothing
    about it. `tests/test_approvals_off.py` covers the OFF state on its own.

    Applied module-wide with `pytestmark = pytest.mark.usefixtures("ladder_on")`
    so it is in force BEFORE a test's own fixtures create records: a record
    created while the ladder is off is stamped `raised_while_approvals_off`
    at create and is never gated afterwards, which is exactly the thing an
    ON-state test must not be handed by accident.

    The module attribute is rebound rather than mutated because it is a bool;
    every reader goes through `approval.ladder_on()`, which reads it fresh.
    """
    import approval

    saved = approval.LADDER_ON
    approval.LADDER_ON = True
    try:
        yield
    finally:
        approval.LADDER_ON = saved
