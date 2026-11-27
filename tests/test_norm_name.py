"""
`pipeline.norm_name` — a characterisation test for a function that MOVED.

`boq._norm_identity()` was lifted out of `boq.py` and became
`pipeline.norm_name()` so that `client.py` could group BOQs by the same key
`boq_identity()` uses. Nothing checked that the behaviour survived the move,
and `boq_identity()` is not a formatting helper: it is **duplicate BOQ
detection**. It decides which schedules `/boq/create?revise=` will offer as a
predecessor, and `POST /boq/create` refuses a predecessor whose identity does
not match. A quiet drift there does not raise anything — it makes a revision
refusable, or offerable, for reasons nobody can see.

So this file does two things:

  1. **pins the exact output** for a table of realistic inputs — trailing
     whitespace, doubled internal spaces, mixed case, empty, None, punctuation,
     unicode spaces;
  2. **pins `boq_identity()` on the seeded BOQ**, which is the actual consumer.

The literals below are the observed behaviour of the function as it stands, not
a specification of what it ought to do. If a change makes one of them fail,
that is the test doing its job: say what moved and why before changing a number
here.
"""

import pytest

import boq as BQ
import demo_seed as DS
import pipeline as P
from conftest import demo_boq_id


# (input, expected output) — read the second column as "what it does today".
CASES = [
    # ── The ordinary path ──────────────────────────────────────────────────
    ("Example Developers Pvt Ltd", "example developers pvt ltd"),
    ("example developers pvt ltd", "example developers pvt ltd"),
    ("EXAMPLE DEVELOPERS PVT LTD", "example developers pvt ltd"),
    ("ExAmPlE DeVeLoPeRs", "example developers"),

    # ── Whitespace: collapsed internally, stripped at both ends ────────────
    ("  Example Developers  ", "example developers"),
    ("Example    Developers", "example developers"),
    ("\tExample\tDevelopers\n", "example developers"),
    ("Example\nDevelopers", "example developers"),
    ("Example   Developers", "example developers"),   # NBSP — str.split() eats it
    ("Example Developers", "example developers"),     # thin space, likewise

    # ── Empty and near-empty ───────────────────────────────────────────────
    ("", ""),
    ("   ", ""),
    ("\n\t ", ""),
    (None, ""),
    # `str(value or "")` short-circuits on anything falsy, so 0 and False both
    # come out empty rather than as "0"/"False". Worth pinning: a quantity of
    # zero is a real value elsewhere in this app, and somebody reaching for
    # this helper on a numeric field would get "" and not notice.
    (0, ""),
    (False, ""),

    # ── Punctuation is KEPT, and that is the point ────────────────────────
    # `Pvt Ltd` and `Pvt. Ltd.` stay two different keys. Collapsing them would
    # be this app deciding two typed names are one party, which it cannot know
    # (DOMAIN.md §6). `client._base_name()` strips punctuation SEPARATELY, and
    # only to raise a near-duplicate warning that merges nothing.
    ("Example Developers Pvt. Ltd.", "example developers pvt. ltd."),
    ("Example-Developers", "example-developers"),
    ("Example & Co.", "example & co."),
    ("M/s Example Developers", "m/s example developers"),

    # ── casefold(), not lower() ───────────────────────────────────────────
    # The German sharp s folds to "ss"; `lower()` would leave it alone. Nothing
    # in a typical register needs this, but it is what the function does and a
    # future change from casefold to lower would be a silent behaviour change.
    ("STRASSE", "strasse"),
    ("Straße", "strasse"),

    # ── Non-strings arrive from a hand-edited record ──────────────────────
    (12345, "12345"),
    (12.5, "12.5"),
]


@pytest.mark.parametrize("raw,expected", CASES)
def test_norm_name_output_is_exactly_this(raw, expected):
    assert P.norm_name(raw) == expected


def test_norm_name_is_idempotent():
    """Normalising a normalised name changes nothing. Cheap, and load-bearing:
    `boq_identity()` is compared against values that have been through it."""
    for raw, _expected in CASES:
        once = P.norm_name(raw)
        assert P.norm_name(once) == once, raw


def test_the_two_names_the_duplicate_warning_exists_for_stay_apart():
    """
    The behaviour `client.py`'s near-duplicate band depends on. If `norm_name`
    ever started stripping punctuation, these would collapse into one group and
    the warning would have nothing to warn about — it would have silently
    become a merge.
    """
    assert P.norm_name("Example Developers Pvt Ltd") != \
           P.norm_name("Example Developers Pvt. Ltd.")


def test_the_names_that_SHOULD_collapse_do():
    """The other half: case and spacing are noise, and must not split a group."""
    assert P.norm_name("Example Developers Pvt Ltd") == \
           P.norm_name("  example   DEVELOPERS pvt ltd ")


# ═══ The consumer: boq_identity() on the real seeded schedule ══════════════

def test_boq_identity_on_the_seeded_boq_is_unchanged_by_the_move(client):
    """
    The identity `boq_identity()` produces for the seeded BOQ, pinned as a
    literal. This is the value `revision_candidates()` filters on and that
    `POST /boq/create` compares a named predecessor against.

    Captured from the function after `_norm_identity` became
    `pipeline.norm_name`, and identical to what the original produced: the body
    moved verbatim — `" ".join(str(value or "").split()).casefold()` — so this
    records "no drift" rather than "here is the new behaviour".
    """
    client.get("/boq/")
    boq = STORE_boq()
    assert BQ.boq_identity(boq) == (
        "office fit-out, tower b",
        "example developers pvt ltd",
    )


def test_boq_identity_survives_the_name_being_retyped_differently(client):
    """
    What the normalisation is FOR. A revision is written months later and the
    party is re-typed; the identity has to survive that, or the predecessor
    disappears from the selector and `POST` refuses the revision.
    """
    client.get("/boq/")
    boq = STORE_boq()
    retyped = dict(boq,
                   project_name="  " + boq["project_name"].upper() + " ",
                   account_name=boq["account_name"].replace(" ", "   "))
    assert BQ.boq_identity(retyped) == BQ.boq_identity(boq)


def test_boq_identity_is_project_AND_party_never_one_of_them(client):
    """
    `account_name` alone is too broad — one contractor, many sites.
    `project_name` alone is too loose — "Tower B" belongs to somebody. Both
    halves have to move the identity, or the revision selector offers the wrong
    schedules.
    """
    client.get("/boq/")
    boq = STORE_boq()
    assert BQ.boq_identity(dict(boq, project_name="A different project")) \
        != BQ.boq_identity(boq)
    assert BQ.boq_identity(dict(boq, account_name="A different contractor")) \
        != BQ.boq_identity(boq)


def STORE_boq():
    from store import STORE
    return STORE["boqs"][demo_boq_id()]
