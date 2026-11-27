"""
tools/export_landing.py — write the public landing page to a static file.

    python tools/export_landing.py                      # -> deploy/landing/index.html
    python tools/export_landing.py --out /var/www/<site>/index.html

The application serves the same page live at `/welcome` (landing.py), built
from `/settings`. This writes that page to disk for a host that serves the
public page as a static file in front of the app (DEPLOY.md, "Public landing
page"). Re-run it after changing the identity or the landing text at /settings.

It boots the application exactly as `python app.py` does — persistence from
`.env`, then the saved identity and logo — renders `landing.render_page()` and
writes the one self-contained HTML file. Nothing is written to the database.
"""

import argparse
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(REPO / "deploy" / "landing" / "index.html"),
                    help="where to write the page (default: deploy/landing/index.html)")
    ap.add_argument("--login-url", default="/login",
                    help="the Staff Login link on the page (default: /login)")
    args = ap.parse_args(argv)

    import app  # noqa: F401 — boots persistence and applies /settings
    import landing

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(landing.render_page(login_url=args.login_url), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
