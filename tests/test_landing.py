"""
`landing.py` — the PUBLIC landing page at /welcome (white-label, October 2026).

Built only from what /settings publishes: the company identity and the landing
text. What this file holds:

1. it is reachable WITHOUT a session, and it is the only company page that is;
2. it names the company from /settings, and a blank install still renders
   (the app name, no empty sections, no broken separators);
3. every landing field is user text and is ESCAPED;
4. the footer credit is fixed in code, whatever /settings says;
5. it wears the screen palette, never the print one.
"""

import pytest

import branding as B
import demo_seed as DS
import landing
import settings as ST
import theme as T
from store import STORE

PAYLOAD = '<script>alert("x")</script>'


@pytest.fixture()
def with_landing(client):
    saved = STORE["settings"].get(ST.LANDING_RECORD)
    ST.save_landing(dict(DS.LANDING))
    yield
    if saved is None:
        STORE["settings"].pop(ST.LANDING_RECORD, None)
    else:
        STORE["settings"][ST.LANDING_RECORD] = saved


def test_the_page_is_public(anon_client):
    r = anon_client.get("/welcome/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "<html" in html and "/login" in html, "a visitor needs the way in"


def test_it_names_the_company_from_settings(client, with_landing):
    html = client.get("/welcome/").get_data(as_text=True)
    assert B.COMPANY_NAME == DS.COMPANY["COMPANY_NAME"]
    assert "DEMO" in html and DS.COMPANY["COMPANY_PHONE"] in html
    assert DS.LANDING["hero_title"].split()[0] in html


def test_a_blank_install_renders_and_omits_the_empty_sections(client):
    saved = {k: STORE["settings"].get(k) for k in (ST.RECORD_ID, ST.LANDING_RECORD)}
    try:
        STORE["settings"].pop(ST.RECORD_ID, None)
        STORE["settings"].pop(ST.LANDING_RECORD, None)
        B.apply_settings(ST.load_saved())
        html = landing.render_page()
        assert "<html" in html
        assert B.APP_NAME in html, "a blank install names the app"
        for heading in ("Why choose us", "Client reviews"):
            assert heading not in html, f"an empty {heading!r} section was drawn"
        assert "&middot; &middot;" not in html and "| |" not in html
    finally:
        for k, v in saved.items():
            if v is None:
                STORE["settings"].pop(k, None)
            else:
                STORE["settings"][k] = v
        B.apply_settings(ST.load_saved())


def test_every_landing_field_is_escaped(client):
    saved = STORE["settings"].get(ST.LANDING_RECORD)
    try:
        STORE["settings"][ST.LANDING_RECORD] = {
            k: (f"{PAYLOAD} | 5 | {PAYLOAD}" if k == "reviews" else
                f"{PAYLOAD} | {PAYLOAD}" if k in ("services", "reasons") else PAYLOAD)
            for k, *_ in ST.LANDING_FIELDS}
        html = landing.render_page()
        assert PAYLOAD not in html
        assert "&lt;script&gt;" in html
    finally:
        if saved is None:
            STORE["settings"].pop(ST.LANDING_RECORD, None)
        else:
            STORE["settings"][ST.LANDING_RECORD] = saved


def test_the_credit_is_fixed_in_code(client, with_landing):
    html = client.get("/welcome/").get_data(as_text=True)
    assert landing.CREDIT == "Designed &amp; developed by Manas Gawde"
    assert landing.CREDIT in html
    assert all("credit" not in k for k, *_ in ST.LANDING_FIELDS), \
        "the credit must not become a /settings field"


def test_the_page_wears_the_screen_palette(client, with_landing):
    html = client.get("/welcome/").get_data(as_text=True)
    assert T.PRIMARY in html
    assert B.RED not in html, "the print red reached the public page"
