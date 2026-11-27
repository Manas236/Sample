"""
tools/seed_demo.py — build the fictional sample company into an EMPTY database.

    python tools/seed_demo.py            # seed, then print the admin password ONCE
    python tools/seed_demo.py --check    # say whether the database is empty; change nothing

Everything it creates comes from `demo_seed.py` — the one seed module — and is
built through the application's own routes, signed in as the administrator it
creates first, so every invariant the application keeps holds for the demo too.

THREE REFUSALS, all before anything is written
----------------------------------------------
1. **`QMS_DEMO_DATA` must be true.** The code default is false, so a production
   box where nobody set it can never be seeded by accident.
2. **Persistence must be live.** A seed into an in-memory store would vanish
   at exit and report success.
3. **The database must be EMPTY** — `demo_seed.emptiness_problems()`: no users,
   no record in any data collection, nothing in settings but the genuine
   defaults the application writes itself. A second run therefore adds nothing:
   it finds the first run's records and stops.

The administrator is `admin` (Owner + Director) with a random 12-character
password printed once, here, and stored nowhere but as a hash. Change it at
/account after the first sign-in, or reset it with `tools/set_password.py`.
"""

import argparse
import pathlib
import secrets
import string
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def _password(n: int = 12) -> str:
    """Random letters and digits, at least one of each kind."""
    alphabet = string.ascii_letters + string.digits
    while True:
        p = "".join(secrets.choice(alphabet) for _ in range(n))
        if (any(c.islower() for c in p) and any(c.isupper() for c in p)
                and any(c.isdigit() for c in p)):
            return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="report whether the database is empty and exit")
    args = ap.parse_args(argv)

    import app as A          # boots persistence from .env and loads the store
    import auth
    import db
    import demo_seed as DS
    from store import STORE

    if not auth.demo_data_on():
        print("REFUSED: QMS_DEMO_DATA is not true. Set it in .env (a demo box "
              "only) — the code default is false so production is never seeded.")
        return 2
    if not db.is_live():
        print(f"REFUSED: persistence is not live ({db.status()}). A seed into an "
              f"in-memory store would vanish at exit.")
        return 2

    problems = DS.emptiness_problems(STORE)
    if problems:
        seeded = (((STORE.get("settings") or {}).get("company") or {})
                  .get("COMPANY_NAME") == DS.COMPANY["COMPANY_NAME"]
                  and DS.find_boq_id(STORE))
        if seeded:
            print("Already seeded: the database holds the demo company. Nothing added.")
            return 0
        print("REFUSED: the database is not empty, so the demo will not be mixed "
              "into it:")
        for line in problems:
            print(f"  - {line}")
        return 3
    if args.check:
        print(f"The database ({db.CONFIG['name']}) is empty: a seed may run.")
        return 0

    auth.ensure_builtin_roles()
    password = _password()
    user = auth.create_user(DS.ADMIN_USERNAME, DS.ADMIN_DISPLAY, password,
                            list(DS.ADMIN_ROLES), created_by="tools/seed_demo.py")
    A.app.config["TESTING"] = False
    client = A.app.test_client()
    with client.session_transaction() as sess:
        sess[auth.SESSION_KEY] = user["id"]
    ids = DS.build(client, STORE)
    db.sync(STORE)

    counts = {c: len(STORE.get(c) or {}) for c in db.COLLECTIONS}
    print(f"Seeded {db.CONFIG['name']} with the demo company "
          f"({DS.COMPANY['COMPANY_LEGAL']}):")
    for coll, n in counts.items():
        if n:
            print(f"  {coll:20s} {n}")
    print(f"  BOQ id               {ids['boq']}")
    print()
    print(f"  Sign in as  : {DS.ADMIN_USERNAME}")
    print(f"  Password    : {password}")
    print("  (shown once — it is stored only as a hash)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
