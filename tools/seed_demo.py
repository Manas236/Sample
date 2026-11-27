"""
tools/seed_demo.py — DEMO BRANCH: build the fictional solar EPC into the DEMO database.

    python tools/seed_demo.py            # seed (or report that it is already seeded)
    python tools/seed_demo.py --check    # report the database's state; change nothing
    python tools/seed_demo.py --reset    # dated backup, DROP + CREATE the demo DB, seed

On the `demo/solar-epc` branch this builds "Helios Grid Energy Pvt Ltd" from
`solar_seed.py` — demo data, every name and number invented — through the
application's own routes and its own `auth.create_user`, so every invariant the
application keeps holds for the demo too. `main` keeps the generic
`demo_seed.py` company and its own version of this tool.

REFUSALS, all before anything is written
----------------------------------------
1. **`QMS_DEMO_DATA` must be true** (the code default is false).
2. **The configured database must be the demo database**, `qms_demo`
   (`solar_seed.DEMO_DB_NAME`). Nothing here will seed, drop or recreate a
   database with any other name — `--reset` least of all.
3. **Persistence must be live** — a seed into an in-memory store vanishes.
4. Without `--reset`, **the database must be empty or already hold this
   demo**. Already seeded: it prints the record counts and changes NOTHING, so
   running it twice is a no-op the second time. Holding anything else: it
   refuses and says what is there.

`--reset`
---------
Takes a dated backup first with `tools/backup_db.py` (the SQL dump and the
attachments archive, into `backups/`, which is gitignored), and only then
DROPs and CREATEs `qms_demo`. A failed backup stops it before the drop.

Logins: one per built-in role, with the DEMO passwords listed in RUN_LOCAL.md.
They are public in this branch's history, so this database must never be
reachable by anyone else.
"""

import argparse
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def _counts(store, collections) -> dict:
    return {c: len(store.get(c) or {}) for c in collections}


def _print_counts(title: str, counts: dict) -> None:
    print(title)
    for coll, n in counts.items():
        if n:
            print(f"  {coll:20s} {n}")


def _reset(db, SS) -> int:
    """Back up, then DROP and CREATE the demo database. Uses db's own config."""
    name = db.CONFIG["name"]
    if name != SS.DEMO_DB_NAME:          # belt and braces: main() checked already
        print(f"REFUSED: --reset only ever touches {SS.DEMO_DB_NAME!r}; DB_NAME is {name!r}.")
        return 2
    conn = db._connect(with_db=False)
    cur = conn.cursor()
    cur.execute("SHOW DATABASES LIKE %s", (name,))
    exists = cur.fetchone() is not None
    if exists:
        import importlib.util
        spec = importlib.util.spec_from_file_location("backup_db", REPO / "tools" / "backup_db.py")
        bk = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bk)
        sql_path, zip_path = bk.backup("pre-demo-reset")   # raises SystemExit on failure
        print(f"backup taken: {sql_path.name}" + (f" + {zip_path.name}" if zip_path else ""))
        cur.execute(f"DROP DATABASE `{name}`")
        print(f"dropped {name}")
    cur.execute(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"created {name}")
    conn.close()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="report and exit")
    ap.add_argument("--reset", action="store_true",
                    help="dated backup, then DROP + CREATE the demo database, then seed")
    args = ap.parse_args(argv)

    # db, auth and solar_seed are safe to import before the app: none boots it.
    # db FIRST — importing it loads .env, which auth.demo_data_on() then reads.
    import db
    import auth
    import solar_seed as SS

    if not auth.demo_data_on():
        print("REFUSED: QMS_DEMO_DATA is not true. Set it in .env (a demo box only) — "
              "the code default is false so production is never seeded.")
        return 2
    wrong_name = db.CONFIG["name"] != SS.DEMO_DB_NAME
    name_refusal = (f"REFUSED: DB_NAME is {db.CONFIG['name']!r}. This tool only works on "
                    f"the demo database {SS.DEMO_DB_NAME!r} — set DB_NAME="
                    f"{SS.DEMO_DB_NAME} in .env.")
    if args.reset and args.check:
        print("REFUSED: --check changes nothing; it cannot be combined with --reset.")
        return 2
    if args.reset:
        # The name guard runs BEFORE anything is dropped, and before the app
        # boots: the app would create tables in whatever database it found.
        if wrong_name:
            print(name_refusal)
            return 2
        rc = _reset(db, SS)
        if rc:
            return rc

    import app as A          # boots persistence from .env and loads the store
    from store import STORE

    if not db.is_live():
        print(f"REFUSED: persistence is not live ({db.status()}). A seed into an "
              f"in-memory store would vanish at exit.")
        return 2
    if wrong_name:
        print(name_refusal)
        return 2

    if SS.is_seeded(STORE):
        _print_counts(f"Already seeded: {db.CONFIG['name']} holds the solar demo "
                      f"({SS.COMPANY['COMPANY_LEGAL']}). Nothing added. Records:",
                      _counts(STORE, db.COLLECTIONS))
        return 0
    import demo_seed as DS
    problems = DS.emptiness_problems(STORE)
    if problems:
        print("REFUSED: the database is not empty and does not hold the solar demo. "
              "Use --reset to back it up and start again:")
        for line in problems:
            print(f"  - {line}")
        return 3
    if args.check:
        print(f"The database ({db.CONFIG['name']}) is empty: a seed may run.")
        return 0

    auth.ensure_builtin_roles()
    SS.create_users(auth)
    owner = auth.find_user(SS.USERS[0][0])
    A.app.config["TESTING"] = False
    client = A.app.test_client()
    with client.session_transaction() as sess:
        sess[auth.SESSION_KEY] = owner["id"]
    ids = SS.build(client, STORE)
    db.sync(STORE)

    _print_counts(f"Seeded {db.CONFIG['name']} with the solar demo "
                  f"({SS.COMPANY['COMPANY_LEGAL']}, demo data). Records:",
                  _counts(STORE, db.COLLECTIONS))
    print(f"  Project 1 BOQ id     {ids['boq1']}")
    print()
    print("  Logins (DEMO passwords — see RUN_LOCAL.md):")
    for username, display, role, password in SS.USERS:
        print(f"    {username:11s} {password:20s} {role}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
