"""
tests/test_demo_data_flag.py — demo data is OFF by default, 25 September 2026
=============================================================================

ABOUT.md §7 gap 35: *a brand new install filled itself with demo records — and
deleting them did not make them stay deleted.* This file is the OFF state, and
`tests/conftest.py` forces the flag ON for every other file in the suite,
exactly as `catalogue_unhidden` and `ladder_on` do for the other two switches.

⚠ **RE-DERIVED for the white-label product (October 2026).** Until then the
flag gated five LAZY seeders that page views and the boot ran. They are gone:
no page and no boot step seeds demo data whatever the flag says, and the
fictional company is written by `tools/seed_demo.py` — through the routes,
onto an EMPTY database, and only when `QMS_DEMO_DATA` is true. So the flag is
now the seed tool's interlock, and every claim below is the old claim made
against the new mechanism:

1. **Nothing demo is seeded** on a fresh install — flag off, and (new) flag on
   too, because no page seeds any more.
2. **Every GENUINE default is still there** — the charge heads, the
   measurement grid columns. ⚠ The spec library is NO LONGER one: the 56
   clauses it used to seed were one client's own trade library. A fresh
   install has an empty library, and both pickers render empty.
3. **A delete stays deleted** across a restart, with the flag on or off.
4. **The seed tool refuses** with the flag off (`tests/test_demo_seed.py`
   holds the rest of its interlock).

⚠ **The flag is set with `monkeypatch`, which undoes it per test.**
  `auth.demo_data_on()` re-reads `os.getenv` on every call and caches nothing,
  which is what makes that work — the same property `attachment.root()` and
  `auth.session_cookie_config()` are written for and for the same reason.
"""

import importlib.util
import inspect
import pathlib

import pytest

import auth
import branding as B
import db
import demo_seed as DS
import settings as ST
from store import STORE

REPO = pathlib.Path(__file__).resolve().parent.parent

# What a fresh-install test empties: every collection but the signed-in
# harness account and the builtin roles, which `auth.install()` mints.
_KEEP = ("users", "roles")

# Every page a first-time visitor is likely to open, and every page the old
# lazy seeders were wired to.
FIRST_VISIT = ("/", "/product/", "/address/", "/spec/", "/boq/", "/boq/create",
               "/quotation/create", "/projects/", "/settings/", "/charge/new",
               "/welcome/")


def _reset():
    """An empty store with the boot's flag down. A brand new install."""
    for coll in db.COLLECTIONS:
        if coll not in _KEEP:
            STORE[coll].clear()
    STORE["_settings_seeded"] = False


def _boot():
    """What `app._boot_persistence()` runs after loading, and what
    `auth.install()` runs — the only seeding left in the application."""
    ST.ensure_default_settings()
    B.apply_settings(ST.load_saved())
    auth.ensure_builtin_roles()


def _first_visit(client):
    for url in FIRST_VISIT:
        r = client.get(url)
        # The catalogue is hidden from everybody (auth.HIDDEN_BLUEPRINTS), so
        # its list answers 403 — still a visit the old seeder was wired to.
        ok = (200, 302, 403) if url == "/product/" else (200, 302)
        assert r.status_code in ok, (url, r.status_code)


def _demo_collections_are_empty():
    for coll in ("products", "addresses", "specs", "projects", "boqs"):
        assert STORE[coll] == {}, f"{coll} was seeded on a fresh install"
    assert set(STORE["settings"]) == {"charge_heads"}, sorted(STORE["settings"])


@pytest.fixture()
def demo_off(monkeypatch, client):
    monkeypatch.setenv("QMS_DEMO_DATA", "false")
    _reset()
    yield client
    _reset()


@pytest.fixture()
def demo_on(monkeypatch, client):
    monkeypatch.setenv("QMS_DEMO_DATA", "true")
    _reset()
    yield client
    _reset()


# ── 1. The default, which is the whole point ───────────────────────────────

def test_the_default_is_OFF_and_that_is_the_deliberate_asymmetry(monkeypatch):
    """
    ⚠ **The headline.** Every other flag in `auth.py` defaults to the local-dev
    value because a default that breaks `python app.py` gets deleted. This one
    is the other way round: the failure that matters is a client box nobody
    configured, and the safe side of that failure is the side that grows no
    data.
    """
    monkeypatch.delenv("QMS_DEMO_DATA", raising=False)
    assert auth.DEMO_DATA_DEFAULT is False
    assert auth.demo_data_on() is False


def test_a_blank_value_means_unset_rather_than_false(monkeypatch):
    """`QMS_DEMO_DATA=` is an operator who left the line in, not one who
    set it to false — and both answer the same way here, which is why this is
    asserted rather than assumed."""
    monkeypatch.setenv("QMS_DEMO_DATA", "   ")
    on, problems = auth.demo_data_config()
    assert on is False
    assert problems == []


@pytest.mark.parametrize("raw,expected", [
    ("true", True), ("True", True), ("1", True), ("yes", True), ("on", True),
    ("false", False), ("FALSE", False), ("0", False), ("no", False), ("off", False),
])
def test_the_usual_spellings_of_a_boolean_are_read(monkeypatch, raw, expected):
    monkeypatch.setenv("QMS_DEMO_DATA", raw)
    assert auth.demo_data_on() is expected


def test_an_unparseable_value_is_REPORTED_and_never_silently_true(monkeypatch):
    """
    ⚠ **The one misconfiguration with no symptom at all.**
    `QMS_DEMO_DATA=ture` resolved by truthiness would let the seed tool write a
    fictional company onto a client's server and say nothing. It falls back to
    the default — which is OFF — and names the value.
    """
    monkeypatch.setenv("QMS_DEMO_DATA", "ture")
    on, problems = auth.demo_data_config()
    assert on is False, "an unparseable value must never resolve to True"
    assert len(problems) == 1
    assert "QMS_DEMO_DATA" in problems[0] and "ture" in problems[0]


def test_the_config_form_has_no_side_effect_so_it_can_be_read_twice(monkeypatch):
    """`demo_data_config()` is the form the tests read, precisely because
    `demo_data_on()` prints a warning once per process and a once-only side
    effect cannot be asserted twice."""
    monkeypatch.setenv("QMS_DEMO_DATA", "nonsense")
    assert auth.demo_data_config() == auth.demo_data_config()


# ── 2. Nothing demo is seeded — flag off, and flag on ──────────────────────

def test_nothing_demo_is_seeded_with_the_flag_off(demo_off):
    _boot()
    _first_visit(demo_off)
    _demo_collections_are_empty()


def test_nothing_demo_is_seeded_with_the_flag_ON_either(demo_on):
    """
    New with the white-label product, and the reason the flag could become an
    interlock: the flag no longer reaches a page at all. Turning it on for a
    demo box does not make the application seed — only the tool does.
    """
    _boot()
    _first_visit(demo_on)
    _demo_collections_are_empty()


def test_the_specimen_company_identity_is_not_seeded(demo_off):
    """
    ⚠ A specimen GSTIN, bank and account number print on a customer's tax
    invoice. The application carries none: the identity is blank until
    somebody types it on /settings (or the demo seed posts it there).
    """
    _boot()
    assert ST.RECORD_ID not in STORE["settings"]
    assert ST.load_saved() == {}
    assert B.COMPANY_GSTIN == "" and B.BANK_NAME == "" and B.BANK_ACCOUNT_NO == ""


def test_the_seed_fills_what_these_tests_find_empty_so_they_are_not_vacuous(demo_on):
    """
    ⚠ **The non-vacuity guard for every test above it.** Those assert that
    collections are EMPTY; that only means something while the demo seed would
    fill the same collections. Built through the routes, with the flag on.
    """
    _boot()
    DS.build(demo_on, STORE, stages=DS.TEST_BASELINE)
    assert len(STORE["addresses"]) == 6
    assert len(STORE["specs"]) == 15
    assert len(STORE["projects"]) == 1
    assert len(STORE["boqs"]) == 1
    assert STORE["settings"][ST.RECORD_ID]["COMPANY_GSTIN"] == DS.COMPANY["COMPANY_GSTIN"]
    # The catalogue is hidden in this product, so the demo writes no products;
    # the OFF test's `products == {}` is proved by the page visits alone.
    assert STORE["products"] == {}


# ── 3. Genuine defaults are still there; the library is no longer one ──────

def test_the_spec_library_is_EMPTY_on_a_fresh_install_and_both_pickers_render(demo_off):
    """
    ⚠ **REVERSED (October 2026).** This was
    `test_the_spec_library_is_a_genuine_default_and_is_still_seeded` — 56
    clauses seeded on every install, because an empty library is an empty
    picker. Those clauses were one client's own trade library. The product
    ships none, so an empty picker is now the first-run state, and the property
    that matters is that every page holding a picker still renders.
    """
    _boot()
    _first_visit(demo_off)
    assert STORE["specs"] == {}
    for url in ("/boq/create", "/quotation/create", "/spec/", "/spec/add"):
        assert demo_off.get(url).status_code == 200, url


def test_the_demo_fill_needs_no_library_and_writes_nothing(demo_off):
    """
    Replaces `test_the_boq_seeder_still_seeds_the_library_even_though_it_seeds_
    no_boq`, whose ordering bug cannot exist once there is no BOQ seeder. What
    is left of it: `/boq/create?demo=1` loads the sample schedule into the
    EDITOR from `demo_seed`'s data, not from the library, and writes nothing.
    """
    _boot()
    html = demo_off.get("/boq/create?demo=1").get_data(as_text=True)
    assert "demo-banner" in html
    assert DS.BOQ_META["project_name"] in html
    _demo_collections_are_empty()


def test_the_charge_heads_are_a_genuine_default_and_are_still_seeded(demo_off):
    """`/charge/new` renders a dropdown from these. An empty list is an
    unusable page, and there is nothing of anybody else's in a list of expense
    categories."""
    ST.ensure_default_settings()
    assert ST.CHARGE_HEADS_RECORD in STORE["settings"]
    assert ST.charge_heads() == list(ST.DEFAULT_CHARGE_HEADS)
    assert ST.charge_heads(), "the charge heads must not be empty"


def test_the_measurement_grid_columns_are_a_genuine_default(demo_off):
    """They are a module constant with a settings override, not a seeded row,
    so the flag cannot reach them — asserted rather than assumed, because the
    joint measurement sheet is unrenderable without them."""
    assert len(ST.measurement_columns()) == len(ST.DEFAULT_MEASUREMENT_COLUMNS)
    assert ST.measurement_columns(), "the grid columns must not be empty"


# ── 4. A delete stays deleted across a restart ─────────────────────────────

def test_a_deleted_record_stays_deleted_across_a_restart(demo_on):
    """
    ⚠ **The half of gap 35 that made deleting pointless.** The boot's flag is
    deliberately not persisted (`db.py`), so it goes with the process. A
    restart is simulated the way one actually behaves — the collections survive
    (they came out of MySQL), the flag does not — and with demo data ON, the
    case the old seeders got wrong.
    """
    _boot()
    DS.build(demo_on, STORE, stages=DS.TEST_BASELINE)
    assert len(STORE["addresses"]) == 6

    # The operator deletes the demo addresses at go-live.
    STORE["addresses"].clear()

    # RESTART.
    STORE["_settings_seeded"] = False
    _boot()
    _first_visit(demo_on)

    assert STORE["addresses"] == {}, (
        "the demo addresses came back after a restart — this is exactly the "
        "behaviour gap 35 reports")
    # ...and the seed tool will not put them back either: the database is not
    # empty, so it refuses the whole run.
    assert DS.emptiness_problems(STORE)


def test_a_deleted_GENUINE_default_does_come_back_so_the_restart_is_real(demo_on):
    """
    ⚠ **The mutation proof for the test above, kept as a test.** The restart
    simulation must reach the seeding the boot really does — otherwise "nothing
    came back" proves nothing. The charge heads are the one record a restart
    restores, and they come back.
    """
    _boot()
    STORE["settings"].pop(ST.CHARGE_HEADS_RECORD)
    STORE["_settings_seeded"] = False
    _boot()
    assert ST.CHARGE_HEADS_RECORD in STORE["settings"], (
        "the restart simulation did not reach ensure_default_settings() — the "
        "test above it proves nothing")


# ── 5. No lazy seeder is left, and the boot seeds only the defaults ────────

def test_no_lazy_seeder_is_left_anywhere_in_the_application():
    """
    Replaces the three `product.py` disarm tests. The disarm existed because
    `product.py` was frozen and its demo seeder could not be edited; the seeder
    held one client's catalogue, so it was removed with the rest (October 2026)
    and the disarm with it. What has to stay true is that none comes back.
    """
    dead_docs = {"integration", "product_view_additions"}   # ABOUT.md §8
    for path in REPO.glob("*.py"):
        if path.stem in dead_docs:
            continue
        src = path.read_text(encoding="utf8")
        assert "ensure_demo_" not in src, f"{path.name} carries a lazy demo seeder"
        if path.stem not in ("settings", "store", "db"):
            assert '"_settings_seeded"' not in src, path.name
    import app as app_module
    assert not hasattr(app_module, "disarm_frozen_demo_seeder")


def test_the_boot_sequence_seeds_only_the_genuine_defaults():
    """
    Read from `inspect.getsource` of the function rather than by searching the
    whole file, because the names appear in comments too — which is precisely
    how a file-wide check once passed against a mutation.
    """
    import app as app_module

    calls = [ln.strip() for ln in
             inspect.getsource(app_module._boot_persistence).splitlines()
             if ln.strip() and not ln.strip().startswith("#")]
    assert "ensure_default_settings()" in calls
    assert not any("ensure_demo" in c or "demo_seed" in c for c in calls), calls


def test_the_seed_tool_refuses_with_the_flag_off(monkeypatch, capsys, client):
    monkeypatch.setenv("QMS_DEMO_DATA", "false")
    spec = importlib.util.spec_from_file_location(
        "seed_demo_tool", REPO / "tools" / "seed_demo.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    before = {c: len(STORE[c]) for c in db.COLLECTIONS}
    assert tool.main([]) == 2
    assert "QMS_DEMO_DATA is not true" in capsys.readouterr().out
    assert {c: len(STORE[c]) for c in db.COLLECTIONS} == before


# ── 6. Blank identity renders — no crash, no leftover specimen string ──────

def test_branding_defaults_are_blank_so_a_cleared_field_does_not_fall_back():
    """
    ⚠ **DEPLOY.md §6.3 once asserted the opposite and was wrong.** It said a
    blank field fell back to the DEFAULTS snapshot, "which is the specimen
    value, not nothing". `branding.DEFAULTS` is snapshotted from the module's
    own import-time values, and those are `""` for every identity field.
    """
    for key in ("COMPANY_NAME", "COMPANY_LEGAL", "COMPANY_ADDR", "COMPANY_WEB",
                "COMPANY_GSTIN", "COMPANY_PAN", "COMPANY_BRANCHES", "BANK_NAME",
                "BANK_ACCOUNT_NAME", "BANK_ACCOUNT_NO", "BANK_IFSC",
                "BANK_BRANCH"):
        assert B.DEFAULTS[key] == "", (
            f"branding.DEFAULTS[{key!r}] is {B.DEFAULTS[key]!r} — a cleared "
            f"field would fall back to it and print on a customer's invoice")


def test_the_fictional_identity_lives_only_in_the_seed():
    """
    White-label (October 2026): the demo company's identifying strings are in
    `demo_seed.py` and nowhere else in the application, so a client box that
    never ran the seed cannot print one.
    """
    # The account number is all zeros, which any module may contain; the
    # strings below are the ones only this company has.
    strings = (DS.COMPANY["COMPANY_GSTIN"], DS.COMPANY["COMPANY_PAN"],
               DS.COMPANY["COMPANY_EMAIL"], DS.COMPANY["BANK_IFSC"],
               DS.COMPANY["COMPANY_LEGAL"])
    for path in REPO.glob("*.py"):
        if path.stem == "demo_seed":
            continue
        src = path.read_text(encoding="utf8")
        for s in strings:
            assert s not in src, f"{path.name} carries the demo identity {s!r}"


def test_a_blank_identity_renders_the_amber_todo_chip_and_not_an_empty_string():
    """Blank means the existing amber marker — the thing that stops a document
    going out silently empty — rather than nothing at all."""
    assert "todo-chip" in B.field("", "GSTIN")
    assert "todo-chip" not in B.field(DS.COMPANY["COMPANY_GSTIN"], "GSTIN")
