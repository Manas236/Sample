"""
The SCREEN pages, pinned byte-for-byte — committed BEFORE the chrome moves.

`tests/test_print_golden.py` pins the printed documents and one form. Nothing
pinned the ordinary screen pages — the registers, the settings form, the user
list, the dashboard itself — so a change to the shared chrome those pages all
render (`dashboard.BASE_STYLES`, `dashboard._nav()`) was measurable on the one
form the print file happens to hash and on nothing else.

Two changes to that chrome follow this file, and this file is what makes each
of them a measurement rather than a hope:

1. **The extraction** — `BASE_STYLES`, `_nav()` and everything nav-only move
   out of `dashboard.py` into a leaf, `chrome.py`, and every module that
   reached into `dashboard.py` for them imports the leaf instead. That is a
   refactor, and a refactor that moves a single rendered byte is not one:
   **every digest below must be byte-identical across it.** The order is the
   one that made the `docsheet.py` and `boqpick.py` extractions safe — the
   baseline is committed first, against the code as it stands, so a digest
   taken here is an observation and not a description of the result.

2. **The sidebar** — the chrome is redrawn. Every page here is expected to
   move, and the per-block digests are what say *where*: `head` and `main`
   must hold still on every page but the dashboard while `chrome` moves,
   because a redesign of the navigation has no business touching a register's
   table. That re-baseline happens in that commit and only there.

   ✅ **Both measured, 14 September 2026.** Across the extraction all 22 pages
   were byte-identical (commit `efa3467`). Across the sidebar, **`main` is
   byte-identical on all 21 register pages** and moved on the dashboard only,
   where the module zones and the status chips ARE the content. The shell —
   the stylesheet and script `_nav()` now emits first, then the rail and the
   top bar — is what moved everywhere else. The pre-redesign three-block
   digests are in commit `52ad1f8` rather than repeated here; every `main`
   digest below is that commit's, unchanged, except the dashboard's.

### The shape

Each page is rendered from a **fixed** store — fixed ids, fixed dates, fixed
figures, a fixed signed-in user, today's date pinned — and hashed whole
(sha256) and in four blocks split on the markers every screen page carries:

    head    <head>  …  up to the shell      the page's <head> and <body> opening
    shell   the shell's <style> … up to <nav   chrome.CHROME_STYLES + CHROME_SCRIPT
    chrome  <nav    …  up to <main          the rail and the top stack
    main    <main   …  end of the page       the page's own body

`_blocks()` and `_sha()` are the print file's own, imported rather than
copied, so the two files cannot disagree about what a block digest is.

### Re-deriving these numbers

Literals, not computed — regenerating them from the code under test would
make the file assert that the code equals itself. When a change is intended,
run the suite, read the digest out of the failure, paste it in **in the same
commit as the change**, and say in the commit body which block moved and why.
"""

from datetime import date as _real_date

import pytest

import auth
import branding as B
import settings as settings_mod
from store import STORE
from test_print_golden import (  # noqa: F401  (fixtures are used by pytest)
    _blocks, _sha,
    pinned_identity, golden, golden_ra, golden_dc, golden_dpo, golden_merged,
    golden_ms, golden_picker, pinned_counts,
    GOLD_TI, GOLD_PI, GOLD_PO, GOLD_DC, GOLD_DPO, GOLD_MERGED, GOLD_MS,
    GOLD_PICK_BOQ,
)
from conftest import seed_baseline
import demo_seed as DS


# ── The markers every screen page carries ──────────────────────────────────
#
# `<nav` and `<main` without their closing bracket, so the same marker finds
# `<nav>` today and a `<nav class="…">` tomorrow: the point of the split is to
# survive the redesign and report which side of it a change landed on.
PAGE_BLOCKS = [
    ("head",   "<head>"),
    # ⚠ **A fourth block from the sidebar commit (14 September 2026).**
    #   `_nav()` now emits the shell's own stylesheet and script FIRST, in the
    #   body, before the rail — so a split at `<nav` alone put ~25 KB of chrome
    #   in the `head` block and reported every page's head as moved when no
    #   page's `<head>` element had changed. The shell is its own block now,
    #   from the first byte of `chrome.CHROME_STYLES` to the rail; `head` is
    #   the page's `<head>` element and its `<body>` opening, which is what it
    #   was always meant to hold.
    #   ⚠ October 2026: the shell now OPENS with `theme.SCREEN_TOKENS` (the
    #   screen palette), emitted by `_nav()` ahead of `CHROME_STYLES`, so the
    #   marker is that block's first bytes. Same boundary, same meaning.
    ("shell",  "<style>\n  :root {\n    --primary:"),
    ("chrome", "<nav"),
    ("main",   "<main"),
]

GOLD_USER = "gold-owner"
GOLD_PROJECT = "gold-project"
GOLD_PROJECT_2 = "gold-project-2"
GOLD_SITE = "gold-site-addr"
GOLD_EMP = "gold-emp-1"
GOLD_EMP_2 = "gold-emp-2"
GOLD_RCPT = "gold-receipt"
GOLD_CHARGE = "gold-charge"
GOLD_DATE = "2026-08-16"


class _FixedToday(_real_date):
    """
    `datetime.date` with today nailed down. A subclass rather than a stand-in,
    because `dashboard._metrics()` also CONSTRUCTS dates (`date(y, m, 1)` for
    the month axis) through the same name it calls `today()` on.
    """

    @classmethod
    def today(cls):
        return cls(2026, 8, 16)


@pytest.fixture()
def world(client, monkeypatch, pinned_identity, golden, golden_ra, golden_dc,
          golden_dpo, golden_merged, golden_ms):
    """
    Every collection a screen page reads, held still.

    The document collections come from the print goldens' own fixtures, so the
    registers list exactly the records the printed sheets are pinned on. The
    rest — users, roles, settings, addresses, projects, employees, markings,
    charges, receipts, the draft-PO and challan series — are snapshotted,
    replaced with fixed records, and put back afterwards, because
    `conftest.client` deliberately does not clear them between tests and a
    golden cannot hash whatever the previous test left behind.

    Two things a page reads that are not records: **today**, which the
    dashboard prints and buckets by, is pinned through `dashboard.date`; and
    **the signed-in user**, whose id is minted from `uuid4()` by
    `auth.create_user()` and would otherwise change the `/users` page's hrefs
    from one process to the next, is replaced by a fixed one and the session
    repointed at it.
    """
    import address
    import dashboard

    monkeypatch.setattr(dashboard, "date", _FixedToday)

    saved = {k: dict(STORE.get(k) or {}) for k in (
        "users", "roles", "settings", "addresses", "projects", "employees",
        "attendance", "charges", "receipts")}

    # ── identity: one fixed Owner, and the session pointed at it ──────────
    STORE["users"].clear()
    STORE["users"][GOLD_USER] = {
        "id": GOLD_USER, "username": "test-owner", "display_name": "Test Owner",
        "password_hash": "not-a-hash", "role_ids": ["role-owner"],
        "active": True, "created_at": "2026-08-01 09:00", "created_by": "conftest",
    }
    STORE["roles"].clear()
    auth.ensure_builtin_roles()
    with client.session_transaction() as session:
        session[auth.SESSION_KEY] = GOLD_USER

    # ── settings: the specimen company only; every series at its default ──
    STORE["settings"].clear()
    STORE["settings"][settings_mod.RECORD_ID] = dict(DS.COMPANY)
    B.apply_settings(settings_mod.load_saved())

    # ── the address book: the six demo entries, re-seeded from scratch ────
    STORE["addresses"].clear()
    seed_baseline("addresses")
    STORE["addresses"][GOLD_SITE] = {
        "id": GOLD_SITE, "label": "Riverside site", "type": "site",
        "contact_name": "R. Surveyor", "company": "Lakeside Park",
        "line1": "Survey 21", "line2": "", "landmark": "", "city": "Bangalore",
        "state": "Karnataka", "pincode": "560066", "country": "India",
        "phone": "", "email": "", "gstin": "",
    }

    # ── projects ──────────────────────────────────────────────────────────
    STORE["projects"].clear()
    STORE["projects"][GOLD_PROJECT] = {
        "id": GOLD_PROJECT, "name": "Lakeside Offices — Fit-out",
        "norm_name": "lakeside offices — fit-out",
        "client": "Example Developers Pvt Ltd", "notes": "",
        "site_address_id": GOLD_SITE, "site_address": "Riverside site",
        "created_at": "2026-04-01 10:00", "updated_at": "2026-04-01 10:00",
    }
    STORE["projects"][GOLD_PROJECT_2] = {
        "id": GOLD_PROJECT_2, "name": "Hillview Techpark — Fit-out",
        "norm_name": "hillview techpark — fit-out",
        "client": "Hillview Techpark Pvt. Ltd.", "notes": "Phase 2 tender",
        "site_address_id": "", "site_address": "",
        "created_at": "2026-05-12 15:30", "updated_at": "2026-05-12 15:30",
    }
    STORE["boqs"]["gold-boq"]["project_id"] = GOLD_PROJECT

    # ── employees and two markings on the pinned day ──────────────────────
    STORE["employees"].clear()
    STORE["employees"][GOLD_EMP] = {
        "id": GOLD_EMP, "name": "Arun Sample", "code": "EMP-014",
        "designation": "Fitter", "site": "Riverside site",
        "site_address_id": GOLD_SITE, "site_source": "book",
        "date_joined": "2026-04-01", "day_rate": 1200.0, "active": True,
        "notes": "", "created_at": "2026-04-01 10:00", "updated_at": "2026-04-01 10:00",
    }
    STORE["employees"][GOLD_EMP_2] = {
        "id": GOLD_EMP_2, "name": "Vijay Example", "code": "EMP-015",
        "designation": "Helper", "site": "Riverside site",
        "site_address_id": GOLD_SITE, "site_source": "book",
        "date_joined": "2026-05-01", "day_rate": 800.0, "active": True,
        "notes": "", "created_at": "2026-05-01 10:00", "updated_at": "2026-05-01 10:00",
    }
    STORE["attendance"].clear()
    STORE["attendance"]["gold-att-1"] = {
        "id": "gold-att-1", "date": GOLD_DATE, "employee_id": GOLD_EMP,
        "employee_name": "Arun Sample", "employee_code": "EMP-014",
        "day_rate": 1200.0, "site": "Riverside site", "site_address_id": GOLD_SITE,
        "site_source": "book", "project_id": GOLD_PROJECT,
        "project_name": "Lakeside Offices — Fit-out",
        "status": "present", "ot_hours": 2.0, "notes": "",
        "created_at": "2026-08-16 18:00", "updated_at": "2026-08-16 18:00",
    }
    STORE["attendance"]["gold-att-2"] = {
        "id": "gold-att-2", "date": GOLD_DATE, "employee_id": GOLD_EMP_2,
        "employee_name": "Vijay Example", "employee_code": "EMP-015",
        "day_rate": 800.0, "site": "Riverside site", "site_address_id": GOLD_SITE,
        "site_source": "book", "project_id": GOLD_PROJECT,
        "project_name": "Lakeside Offices — Fit-out",
        "status": "absent", "ot_hours": 0.0, "notes": "",
        "created_at": "2026-08-16 18:00", "updated_at": "2026-08-16 18:00",
    }

    # ── a charge and a receipt ────────────────────────────────────────────
    STORE["charges"].clear()
    STORE["charges"][GOLD_CHARGE] = {
        "id": GOLD_CHARGE, "date": "2026-08-10", "person": "R. Surveyor",
        "head": "Travel", "description": "Site visit, Riverside",
        "project_id": GOLD_PROJECT, "project_name": "Lakeside Offices — Fit-out",
        "taxable_amount": 1200.0, "gst_rate": 0.0, "gst_amount": 0.0,
        "total": 1200.0, "notes": "",
        "created_at": "2026-08-10 19:00", "updated_at": "2026-08-10 19:00",
        "approval_status": "approved",
    }
    STORE["receipts"].clear()
    STORE["receipts"][GOLD_RCPT] = {
        "id": GOLD_RCPT, "ref": "DP/RCPT/26-27/0001", "fy": "26-27",
        "date": "2026-06-20", "ra_id": "gold-ra", "ra_ref": "DP/RA/26-27/0002",
        "ra_no": 2, "leg": "supply", "boq_id": "gold-boq",
        "boq_ref": "DP/BOQ/26-27/0001",
        "project_name": "Lakeside Offices — Fit-out",
        "account_name": "Example Developers Pvt Ltd",
        "amount": 100000.0, "write_off": 0.0, "mode": "neft",
        "instrument_ref": "UTR20260620", "instrument_date": "2026-06-19", "notes": "",
    }

    yield

    for k, v in saved.items():
        STORE[k].clear()
        STORE[k].update(v)
    B.apply_settings(settings_mod.load_saved())


def _check(html: str, expect_whole: str, expect_len: int, expect_blocks: dict,
           what: str):
    got_len, got_whole = len(html), _sha(html)
    if got_whole != expect_whole:
        got_blocks = _blocks(html, PAGE_BLOCKS)
        moved = [n for n in expect_blocks if got_blocks[n] != expect_blocks[n]]
        assert not moved, (
            f"{what}: these blocks changed — {moved}. "
            f"Expected {expect_blocks}, got {got_blocks}. "
            f"Whole page {expect_whole} -> {got_whole}, "
            f"{expect_len} -> {got_len} bytes.")
    assert (got_whole, got_len) == (expect_whole, expect_len), (
        f"{what}: the rendered page changed. "
        f"sha {expect_whole} -> {got_whole}, bytes {expect_len} -> {got_len}. "
        f"Every block hashed the same, so the difference is outside them — "
        f"before <head>, or between two markers.")


# ── The pages, one per blueprint that renders the app chrome ───────────────
#
# Captured 14 September 2026, against the code as it stood BEFORE `chrome.py`
# existed. `/product/` is absent because the catalogue is hidden from
# everybody (auth.HIDDEN_BLUEPRINTS) and the route answers 403; `/login` and
# `/setup` render no chrome by design; the `approval` blueprint's routes are
# refused while the ladder is off. Everything else that draws `_nav()` is here.
# ⚠ **RE-BASELINED October 2026 — the white-label product.** Every page moved
#   in `head` and `chrome`, and all but `/users` in `main`. Measured against a
#   pre-cleanup render of each page with its own pre-cleanup data pushed back
#   in, the causes are: DATA (the company name and the generated tab icon /
#   initials monogram in place of the client's logo; the seeded schedule,
#   library and address book behind every register, counter and rail badge);
#   INVISIBLE renames (`nb-fire` -> `nb-accent`, CSS / JS comments that named
#   the client); and two VISIBLE, deliberate Step-2 changes — the dashboard's
#   market-news card blurb made trade-neutral, and /settings gaining its Logo,
#   Document Numbering, Sign-in Names and Public Landing Page sections. Each
#   entry's predecessor is in the comment above it.
PAGES = {
    # (name, url): (whole sha, byte length, {block: sha})
    # was 5e225e0820d80885 / 106453 before the white-label re-baseline (October 2026)
    # was c28868da67c436a6 / 89132 before the white-label re-baseline (October 2026)
    # was 5d517edd364bbfd7 / 91306 before the Product Inquiry rename (27 Nov 2026)
    ("dashboard",       "/"):                          ("19c0765acc302822", 91294,
        {"head": "66ab60e6c7d630f9", "shell": "8a27214eeb51b76a", "chrome": "67c2c78cac5f5a40", "main": "706c0cbfe6d45d5d"}),
    # was 36d5f6af2d97f948 / 70833 before the white-label re-baseline (October 2026)
    # was 9eb6958a0365c764 / 53522 before the white-label re-baseline (October 2026)
    # was dc35355618422d26 / 55665 before the Product Inquiry rename (27 Nov 2026)
    ("quotations",      "/quotation/"):                ("c7fc7132c43ca554", 55657,
        {"head": "ba7647ada7d5801c", "shell": "8a27214eeb51b76a", "chrome": "95d3611c7e85d079", "main": "6c5e3eb84af95543"}),
    # was 7d76c8fa785a4097 / 76141 before the white-label re-baseline (October 2026)
    # was 934eca3dbe9f2e42 / 58830 before the white-label re-baseline (October 2026)
    # was 7cf3a3edcbb4eac4 / 60973 before the Product Inquiry rename (27 Nov 2026)
    ("proformas",       "/proforma/"):                 ("f7136e480e0294cb", 60965,
        {"head": "26ad1b55097b7862", "shell": "8a27214eeb51b76a", "chrome": "8230f91a490d653b", "main": "8692744de5e2d1c7"}),
    # was 838b42d5894c49c6 / 83043 / head 28aee5e42e857421 before the
    # 23 Sep 2026 cancellation overprint. ⚠ `head` ALONE moved (+1,575 bytes of
    # `.lc-*` rules in INVOICE_STYLES, which every page in this module loads);
    # `shell`, `chrome` and `main` are byte-identical, so the register itself
    # did not change at all.
    # was 36c5d2c1be5c3e01 / 84618 before the white-label re-baseline (October 2026)
    # was cbc2956a3ced50e8 / 67307 before the white-label re-baseline (October 2026)
    # was e0cd06234792a4cb / 69450 before the Product Inquiry rename (27 Nov 2026)
    ("tax invoices",    "/invoice/"):                  ("7c2f3afec6c24a7a", 69442,
        {"head": "49f622d77e9036ac", "shell": "8a27214eeb51b76a", "chrome": "8c757811be8c3199", "main": "8911f51a4148d389"}),
    # was ddd6e71e5ba97679 / 80408 before the white-label re-baseline (October 2026)
    # was 10c1d46213b80396 / 63090 before the white-label re-baseline (October 2026)
    # was d18362fda86a22b0 / 65233 before the Product Inquiry rename (27 Nov 2026)
    ("purchase orders", "/purchase/"):                 ("e0e78b5599e8f9fb", 65225,
        {"head": "17d23c0c6391fa6e", "shell": "8a27214eeb51b76a", "chrome": "82ec612cf90b8725", "main": "770a13cce5f5e749"}),
    # was f4df328387214170 / 98711 before the white-label re-baseline (October 2026)
    # was e8b824fc212c097f / 51773 before the white-label re-baseline (October 2026)
    # was b59375433f88c6f9 / 53916 before the Product Inquiry rename (27 Nov 2026)
    ("spec library",    "/spec/"):                     ("3c446e5fc9818106", 53908,
        {"head": "1f64956e49517af6", "shell": "8a27214eeb51b76a", "chrome": "1ed59b35933ccc94", "main": "5b074816f67970c6"}),
    # was da65fd57390c41ea / 87604 before the white-label re-baseline (October 2026)
    # was 068b702058c3203b / 69614 before the white-label re-baseline (October 2026)
    # was acb84bf43c52f940 / 71757 before the Product Inquiry rename (27 Nov 2026)
    ("BOQs",            "/boq/"):                      ("261b82551ecb111a", 71749,
        {"head": "46b1475120f7d5c7", "shell": "8a27214eeb51b76a", "chrome": "8cab72f5e0eec7b2", "main": "4b405bdea65a6caa"}),
    # was 3a5536d4d6af4366 / 94831 before the white-label re-baseline (October 2026)
    # was 086c68b63e5ac306 / 77516 before the white-label re-baseline (October 2026)
    # was 1a17baee3eda1b91 / 79659 before the Product Inquiry rename (27 Nov 2026)
    ("RA bills",        "/ra/"):                       ("441d10193f5c4a1f", 79651,
        {"head": "b40e623d1615d0d7", "shell": "8a27214eeb51b76a", "chrome": "acb1df4de9dd48b5", "main": "99f71b979c2d3cca"}),
    # was c8c76cbaad9ecafa / 87366 before the white-label re-baseline (October 2026)
    # was dc3a9edaa632d9a2 / 70047 before the white-label re-baseline (October 2026)
    # was 4e5ca747f26271cf / 72190 before the Product Inquiry rename (27 Nov 2026)
    ("merged RAs",      "/merged/"):                   ("069eaa35fb6243f7", 72182,
        {"head": "b3168ced85c4d3ff", "shell": "8a27214eeb51b76a", "chrome": "b50a5a94d075523f", "main": "8aaa5b569e4887ea"}),
    # was 0507f0420f7839fd / 86611 / head 2cc6952bbfa08148 before the
    # 23 Sep 2026 delete rollout. ⚠ `head` ALONE moved (+462 bytes of
    # `cascade.CASCADE_STYLES`, loaded by receipt.py's shared `_shell()` so the
    # delete confirmation can draw its impact block); `shell`, `chrome` and
    # `main` are byte-identical, so the register itself did not change.
    # was c08e0ecf87251688 / 87073 before the white-label re-baseline (October 2026)
    # was 281fe969bf3fe514 / 69754 before the white-label re-baseline (October 2026)
    # was 0912cb4b6f148771 / 71897 before the Product Inquiry rename (27 Nov 2026)
    ("receipts",        "/receipt/"):                  ("1eddcea4548f253a", 71889,
        {"head": "860c292408cbb5a7", "shell": "8a27214eeb51b76a", "chrome": "d7cd04ba8cce444a", "main": "62335835c047ac24"}),
    # was b539d6762348461b / 72469 before the white-label re-baseline (October 2026)
    # was 84cbc72de07dba16 / 55151 before the white-label re-baseline (October 2026)
    # was d8e8b98199a8f667 / 57294 before the Product Inquiry rename (27 Nov 2026)
    ("clients",         "/client/"):                   ("ea12bade6a3db60a", 57286,
        {"head": "08917bb1259e4cc8", "shell": "8a27214eeb51b76a", "chrome": "09a37f68b4cd37b9", "main": "416080f7d9edfbb3"}),
    # was fbbdae870b7c8492 / 71208 before the white-label re-baseline (October 2026)
    # was 000d5a084340b0f0 / 53884 before the white-label re-baseline (October 2026)
    # was 757847bd00afd252 / 56027 before the Product Inquiry rename (27 Nov 2026)
    ("draft POs",       "/po/"):                       ("bbaa228432103080", 56007,
        {"head": "bc13c5a30c6bd081", "shell": "8a27214eeb51b76a", "chrome": "d5d7f0c7f5237576", "main": "4dcc71d99c8106d0"}),
    # was 4ddb960f86b83e82 / 76341 before the white-label re-baseline (October 2026)
    # was fb819eb1638df401 / 59019 before the white-label re-baseline (October 2026)
    # was 456ac847a09ab607 / 61162 before the Product Inquiry rename (27 Nov 2026)
    ("challans",        "/dc/"):                       ("3654258a5a40a094", 61154,
        {"head": "05dcc562e23dd666", "shell": "8a27214eeb51b76a", "chrome": "89785eee3cc1934c", "main": "00010743d840cfac"}),
    # was 087142596310c260 / 68945 before the white-label re-baseline (October 2026)
    # was 18c2827462adfa01 / 51623 before the white-label re-baseline (October 2026)
    # was 1d4c29955771a62d / 53766 before the Product Inquiry rename (27 Nov 2026)
    ("measurements",    "/measurement/"):              ("54cb2b4c932ce2b9", 53758,
        {"head": "2dd39912087b1421", "shell": "8a27214eeb51b76a", "chrome": "049028461630482b", "main": "25fdd7e4c985b0ba"}),
    # was 1dcdc0e2798636eb / 49548 before the white-label re-baseline (October 2026)
    # was c81435618b26f7d7 / 32231 before the white-label re-baseline (October 2026)
    # was 044ec4a633b70714 / 34374 before the Product Inquiry rename (27 Nov 2026)
    ("projects",        "/projects/"):                 ("28e9691978d34a48", 34366,
        {"head": "bf5cadc91d957acf", "shell": "8a27214eeb51b76a", "chrome": "d702ec5abbcc420b", "main": "d9bb0470f4e0f231"}),
    # was 74f683d1a779159f / 76963 before the white-label re-baseline (October 2026)
    # was 9d555843bde69793 / 59652 before the white-label re-baseline (October 2026)
    # was a130561a600fa7fe / 61795 before the Product Inquiry rename (27 Nov 2026)
    # was 58b7f53b2bf1411a / 61787 before the Profit & Loss and RA-bills panels (27 Nov 2026)
    ("project page",    f"/projects/view/{GOLD_PROJECT}"): ("5a191a8307f1bc70", 67209,
        {"head": "869f4ed6e4102f76", "shell": "8a27214eeb51b76a", "chrome": "b73c7948e46bd897", "main": "443a3f40779f8899"}),
    # was fd7d40f31d63a52e / 66359 before the white-label re-baseline (October 2026)
    # was a3e368d5049fc080 / 49045 before the white-label re-baseline (October 2026)
    # was b2190c2241795900 / 51188 before the Product Inquiry rename (27 Nov 2026)
    ("employees",       "/employee/"):                 ("5bad6ce3e36ad65b", 51180,
        {"head": "8453b6f6704eafcb", "shell": "8a27214eeb51b76a", "chrome": "34c6eaefcf20360e", "main": "57d7037c60fdeb48"}),
    # was 772b3d71abb8f8ee / 72731 before the white-label re-baseline (October 2026)
    # was 4d0c86dacdebbcbe / 55416 before the white-label re-baseline (October 2026)
    # was b6bf117f7a7caf75 / 57559 before the Product Inquiry rename (27 Nov 2026)
    ("attendance",      f"/attendance/?date={GOLD_DATE}"): ("2930466215d64ae1", 57551,
        {"head": "c0d5aa122d762d49", "shell": "8a27214eeb51b76a", "chrome": "a104ecb662aa50be", "main": "2ff637b8a8fdab2a"}),
    # was 52eec3cf3cd7c8cd / 66001 before the white-label re-baseline (October 2026)
    # was 0469ebdec7ce6bf7 / 48683 before the white-label re-baseline (October 2026)
    # was ac61979355310e12 / 50826 before the Product Inquiry rename (27 Nov 2026)
    ("charges",         "/charge/"):                   ("6e1fa577cd83a3ab", 50818,
        {"head": "3570a389ec06c23c", "shell": "8a27214eeb51b76a", "chrome": "c068e2333c46cc49", "main": "8c02fcfc0de05545"}),
    # was def4ca415fbc0f49 / 75650 before the white-label re-baseline (October 2026)
    # was 6773497e89718a2f / 58068 before the white-label re-baseline (October 2026)
    # was e2c17da9faf8328b / 60211 before the Product Inquiry rename (27 Nov 2026)
    ("address book",    "/address/"):                  ("127c848585ba9f9a", 60203,
        {"head": "0155fdb201cec6ec", "shell": "8a27214eeb51b76a", "chrome": "b61977d20d217d26", "main": "cfd20bb75d6529e8"}),
    # ⚠ **RE-BASELINED 25 September 2026 — `main` ONLY, and it is the ONE
    #   golden this application's go-live hardening was always going to move.**
    #   ABOUT.md §7 gap 36 is closed by adding a **Starting Numbers** section to
    #   this form, so the page that owns every series control gains nine boxes.
    #   A gap that can only be closed by putting a control on a page cannot be
    #   closed without moving that page's digest.
    #
    #   Measured before the baseline was touched, by rendering the page twice
    #   from the same process — once as it stands, once with the new section's
    #   HTML removed:
    #
    #       +5,560 bytes · 27 lines ADDED · **0 lines REMOVED**
    #
    #   **Purely additive.** Every line of the identity, bank, draft-PO,
    #   challan, labour, charge-head and measurement-column sections is
    #   byte-identical, `head` / `shell` / `chrome` did not move, and **no
    #   print golden moved at all** — the nine printed documents are untouched,
    #   which is what the minters' scan-move to `series.py` had to prove and
    #   did.
    #
    #   The old values, kept rather than overwritten in silence:
    #       ("f12eaac1c07efbaa", 74589,
    #        {"head": "ce8721ccb87d2120", "shell": "75cda0afbae27209",
    #         "chrome": "d107029c10eb2dec", "main": "741824ea93f3b3cb"})
    # was a499293306ea5d30 / 80230 before the white-label re-baseline (October 2026)
    # was 6dc5c9c79a1632f1 / 68394 before the white-label re-baseline (October 2026)
    # was 75c66f3ae4969cec / 70537 before the Product Inquiry rename (27 Nov 2026)
    ("settings",        "/settings/"):                 ("e51b1ed47d15b2a2", 70538,
        {"head": "66b2e7a06db7605d", "shell": "8a27214eeb51b76a", "chrome": "e1753827ab127faf", "main": "87c073f00b4a938d"}),
    # ⚠ re-baselined 22 September 2026 — `head` ONLY, by the four CSS rules the
    # role picker and the empty action cell needed (`AUTH_ADMIN_STYLES`, +262
    # bytes). `main` is byte-identical and that is the measurement that matters
    # here: this page is hashed as an OWNER, who may administer every account
    # and reach `/roles`, so every link the pass made conditional is still
    # drawn. A moved `main` would have meant the Owner lost something.
    # was 6f28cf4801fb6f4c / 65758 before the white-label re-baseline (October 2026)
    # was feb5e7bfeab32ce7 / 48444 before the white-label re-baseline (October 2026)
    # was eb61b5304608fc62 / 50587 before the Product Inquiry rename (27 Nov 2026)
    ("users",           "/users"):                     ("7c2f66e3e0328f16", 50579,
        {"head": "f7f989d34971a0fa", "shell": "8a27214eeb51b76a", "chrome": "64ca8f2ed5d3cc67", "main": "645012baa0685fdd"}),
}


@pytest.mark.parametrize("name,url", list(PAGES), ids=[n for n, _u in PAGES])
def test_the_screen_page_is_unchanged(name, url, client, world):
    r = client.get(url)
    assert r.status_code == 200, f"{name}: {url} -> {r.status_code}"
    whole, length, blocks = PAGES[(name, url)]
    _check(r.get_data(as_text=True), whole, length, blocks, what=name)


def test_the_page_goldens_are_hashing_real_pages(client, world):
    """
    The control. A digest passes just as well against a refusal page, an empty
    register or a store that silently stopped seeding, so each page is checked
    for the thing it claims to show before any digest is believed.
    """
    get = lambda u: client.get(u).get_data(as_text=True)  # noqa: E731

    home = get("/")
    assert "Sunday, 16 August 2026" in home, "today is not pinned on the dashboard"
    assert "Test Owner" in home, "the fixed user is not the one signed in"
    assert "QT-0001" in home, "the golden quotation is not on the dashboard"

    assert "DP/BOQ/26-27/0001" in get("/boq/"), "the golden BOQ is not listed"
    assert "DP/RA/26-27/0002" in get("/ra/"), "the golden RA bill is not listed"
    assert "DP/RCPT/26-27/0001" in get("/receipt/"), "the receipt is not listed"
    assert "DP/DPO/0007" in get("/po/"), "the golden draft PO is not listed"
    assert "Open delivery challan 54" in get("/dc/"), "the golden challan is not listed"
    assert "DP/MS/26-27/0007" in get("/measurement/"), "the joint sheet is not listed"
    assert "DP/MI/26-27/0001" in get("/merged/"), "the merged document is not listed"
    assert "DP/PO/26-27/0001" in get("/purchase/"), "the golden PO is not listed"
    assert "DP/TI/26-27/0001" in get("/invoice/"), "the golden TI is not listed"
    assert "PI-0001" in get("/proforma/"), "the golden PI is not listed"
    assert "Hillview Techpark" in get("/projects/"), "the projects are not listed"
    assert "Arun Sample" in get("/employee/"), "the employees are not listed"
    assert "EMP-015" in get(f"/attendance/?date={GOLD_DATE}"), "the muster is empty"
    assert "Site visit, Riverside" in get("/charge/"), "the charge is not listed"
    assert "Riverside site" in get("/address/"), "the address book is not listed"
    assert "Example Developers" in get("/client/"), "the client register is empty"
    assert "2026-08-01 09:00" in get("/users"), "the fixed user's row is missing"
    assert DS.COMPANY["BANK_NAME"] in get("/settings/"), "the pinned identity is not loaded"


def test_every_pinned_page_renders_the_shared_chrome(client, world):
    """
    The shape the split relies on: every page here carries the shell's
    stylesheet, a `<nav` and a `<main`, in that order, after its `<head>`. A
    page that lost any of them has lost the chrome this file exists to measure.
    """
    for (name, url) in PAGES:
        html = client.get(url).get_data(as_text=True)
        cuts = [html.find(m) for _n, m in PAGE_BLOCKS]
        assert all(c >= 0 for c in cuts), f"{name}: a marker is missing ({cuts})"
        assert cuts == sorted(cuts), f"{name}: the markers are out of order"


def test_the_head_element_carries_none_of_the_shell(client, world):
    """
    ⚠ **What "the sidebar moved only the chrome" rests on.** The shell's
    stylesheet and script are emitted by `_nav()` in the BODY, so a page's
    `<head>` element is exactly what it was before the redesign — its own
    `<title>`, the favicon, and the style constants it always loaded. That is
    asserted two ways: nothing of the shell is inside `<head>…</head>`, and
    nothing but whitespace and the `<body>` opening sits between `</head>` and
    the shell's first byte. `chrome.BASE_STYLES` being byte-identical to the
    extraction commit's (`efa3467`) is the third leg, and it was measured in
    the sidebar commit rather than assumed.
    """
    import re

    import theme

    # The shell's first byte is the screen palette's block (October 2026),
    # which `_nav()` emits ahead of `CHROME_STYLES`.
    shell_start = theme.SCREEN_TOKENS.strip()
    for (name, url) in PAGES:
        html = client.get(url).get_data(as_text=True)
        head = html[html.index("<head>"):html.index("</head>")]
        for token in ("nav.rail", "railToggle", ".topbar", "--rail-w"):
            assert token not in head, f"{name}: {token!r} leaked into <head>"
        between = html[html.index("</head>") + len("</head>"):html.index(shell_start)]
        assert re.fullmatch(r"\s*<body[^>]*>\s*", between), (
            f"{name}: something other than <body> sits between </head> and the "
            f"shell: {between!r}")
