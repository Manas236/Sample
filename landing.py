"""
landing.py — the public landing page
====================================
Blueprint  : landing_bp
Mounted at : /welcome  (registered in app.py) — PUBLIC, no session needed

Routes
------
  GET /welcome/   — the company's public page

Every word on this page comes from `/settings`: the identity block (name,
tagline, phone, e-mail, address, GSTIN, website, logo) and the "Public Landing
Page" record (`settings.LANDING_RECORD` — headline, about, founder, services,
reasons, reviews, hours, service area). Nothing company-specific is written in
this file. A section whose content is blank is left off the page rather than
printed empty, so a fresh install shows a short, honest page carrying only the
name and the contact details.

The one fixed line is the footer credit, which is the developer's and is not a
setting.

`tools/export_landing.py` writes the same page to `deploy/landing/index.html`
for a host that serves the public page as a static file in front of the app.

⚠ **A PUBLIC page.** It must never describe the application's internal
  documents, workflow, roles or staff — it carries only what the company itself
  chooses to publish on /settings. It reads no session and imports nothing
  that does: never `auth`, never `chrome`.

⚠ **Every value is escaped at the interpolation site** (ABOUT.md §9); the
  `tel:`, `mailto:` and website links are built from validated parts.
"""

import datetime
import re
import urllib.parse

from flask import Blueprint, url_for

import branding as B
import pipeline as P
import settings as ST
import theme as T

landing_bp = Blueprint("landing", __name__, url_prefix="/welcome")

CREDIT = "Designed &amp; developed by Manas Gawde"

# The page's colours, in ONE place.
_PALETTE = {                     # theme.py — the screen palette
    "accent":    T.PRIMARY,
    "accent_dk": T.PRIMARY_HOVER,
    "accent_lt": T.PRIMARY_SOFT,
    "ink":       T.INK,
    "ink_dk":    T.INK,
    "ink_lt":    T.PRIMARY_SOFT,
    "text":      T.TEXT,
    "muted":     T.MUTED,
    "border":    T.BORDER,
    "canvas":    T.BACKGROUND,
    "surface":   T.SURFACE,
    "star":      T.AMBER,
}

# Generic line icons (24px, stroke = currentColor), cycled over the services.
_ICONS = [
    '<path d="M22 11.1V12a10 10 0 1 1-5.9-9.1"/><path d="M22 4 12 14l-3-3"/>',
    '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z"/>',
    '<path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
]
_ICON_PHONE = ('<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 '
               '2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 '
               '6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>')
_ICON_MAIL = '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/>'
_ICON_PIN = '<path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>'
_ICON_CLOCK = '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'


def _svg(paths: str, size: int = 22) -> str:
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
            f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


def _lines(raw: str) -> list:
    return [ln.strip() for ln in str(raw or "").split("\n") if ln.strip()]


def _pairs(raw: str) -> list:
    """`Title | sentence` lines -> [(title, sentence)]."""
    out = []
    for ln in _lines(raw):
        title, _, text = ln.partition("|")
        if title.strip():
            out.append((title.strip(), text.strip()))
    return out


def _reviews(raw: str) -> list:
    """`Name | rating | quote` lines -> [(name, rating or None, quote)]."""
    out = []
    for ln in _lines(raw):
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) < 3 or not parts[2]:
            continue
        try:
            rating = max(0.0, min(5.0, float(parts[1])))
        except ValueError:
            rating = None
        out.append((parts[0], rating, " | ".join(parts[2:])))
    return out


def _tel(phone: str) -> str:
    """`tel:` target — digits and a leading + only, Indian numbers given +91."""
    digits = re.sub(r"[^0-9+]", "", str(phone or ""))
    if not digits:
        return ""
    if not digits.startswith("+") and len(digits) == 10:
        digits = "+91" + digits
    return "tel:" + digits


def _web_href(web: str) -> str:
    w = str(web or "").strip()
    if not w:
        return ""
    if not re.match(r"^https?://", w, re.I):
        w = "https://" + w
    return w if re.match(r"^https?://[^\s\"'<>]+$", w, re.I) else ""


def _web_label(web: str) -> str:
    return re.sub(r"^https?://", "", str(web or "").strip(), flags=re.I).rstrip("/")


def _stars(rating) -> str:
    if rating is None:
        return ""
    full = int(round(rating))
    return (f'<div class="stars" aria-label="Rated {rating:g} out of 5">'
            f'{"&#9733;" * full}{"&#9734;" * (5 - full)}</div>')


def _brand_mark(px: int) -> str:
    """The logo when one is set, else the initials square — never an empty box."""
    return B.monogram_html(px)


def _styles() -> str:
    c = _PALETTE
    return f"""<style>
:root{{
  --accent:{c['accent']}; --accent-dk:{c['accent_dk']}; --accent-lt:{c['accent_lt']};
  --ink:{c['ink']}; --ink-dk:{c['ink_dk']}; --ink-lt:{c['ink_lt']};
  --text:{c['text']}; --muted:{c['muted']}; --border:{c['border']};
  --canvas:{c['canvas']}; --surface:{c['surface']}; --star:{c['star']};
  --r:12px; --max:1160px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:"Segoe UI",Roboto,"Helvetica Neue",Arial,system-ui,sans-serif;color:var(--text);
  background:var(--surface);line-height:1.6;-webkit-font-smoothing:antialiased}}
a{{color:inherit}}
.wrap{{max-width:var(--max);margin:0 auto;padding:0 20px}}
.eyebrow{{font-size:.78rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}}
h1,h2,h3{{line-height:1.15;color:var(--ink-dk)}}
h2{{font-size:clamp(1.7rem,3.4vw,2.4rem);margin:.5rem 0 1rem;letter-spacing:-.01em}}
.lead{{font-size:1.08rem;color:var(--muted);max-width:640px}}
.btn{{white-space:nowrap;display:inline-flex;align-items:center;gap:.5rem;font-weight:700;font-size:.95rem;
  text-decoration:none;border-radius:999px;padding:.8rem 1.35rem;border:2px solid transparent;
  transition:background .15s,color .15s,border-color .15s}}
.btn-solid{{background:var(--accent);color:#fff}}
.btn-solid:hover{{background:var(--accent-dk)}}
.btn-line{{border-color:rgba(255,255,255,.6);color:#fff}}
.btn-line:hover{{background:rgba(255,255,255,.12);border-color:#fff}}
.btn-ink{{border-color:var(--ink);color:var(--ink)}}
.btn-ink:hover{{background:var(--ink);color:#fff}}
.topbar{{background:var(--ink-dk);color:#E5E9F2;font-size:.82rem}}
.topbar .wrap{{display:flex;justify-content:space-between;gap:1rem;padding-top:.45rem;padding-bottom:.45rem;flex-wrap:wrap}}
.topbar a{{text-decoration:none;color:#fff;font-weight:600}}
header{{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.97);border-bottom:1px solid var(--border)}}
header .wrap{{display:flex;align-items:center;justify-content:space-between;gap:1rem;height:70px}}
.brand{{display:flex;align-items:center;gap:.7rem;text-decoration:none}}
.brand b{{white-space:nowrap;display:block;font-size:1.08rem;letter-spacing:.06em;color:var(--ink-dk);line-height:1.1}}
.brand small{{display:block;font-size:.68rem;letter-spacing:.12em;color:var(--muted);font-weight:700;text-transform:uppercase}}
nav.links{{display:flex;align-items:center;gap:1.6rem}}
nav.links a{{text-decoration:none;font-weight:600;font-size:.93rem}}
nav.links a:hover{{color:var(--accent)}}
.login{{padding:.55rem 1.05rem;font-size:.88rem}}
.hero{{color:#fff;background:linear-gradient(135deg,var(--ink-dk),var(--ink) 70%)}}
.hero .wrap{{display:grid;grid-template-columns:1.25fr .9fr;gap:3rem;align-items:center;padding-top:5rem;padding-bottom:5rem}}
.hero .eyebrow{{color:#fff;opacity:.85}}
.hero h1{{color:#fff;font-size:clamp(2.1rem,5vw,3.4rem);letter-spacing:-.02em;margin:.8rem 0 1.2rem}}
.hero p{{font-size:1.1rem;color:#E5E9F2;max-width:560px}}
.cta{{display:flex;flex-wrap:wrap;gap:.8rem;margin-top:2rem}}
.hero-card{{justify-self:end;width:min(100%,340px);aspect-ratio:1;display:grid;place-items:center;
  border-radius:50%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18)}}
.hero-card .disc{{width:52%;aspect-ratio:1;border-radius:50%;background:#fff;display:grid;place-items:center;
  box-shadow:0 24px 60px rgba(0,0,0,.35)}}
section{{padding:5rem 0}}
.about .wrap{{display:grid;grid-template-columns:1.2fr 1fr;gap:3.5rem;align-items:start}}
.about p{{color:var(--text);margin-bottom:1rem}}
.pillars{{display:grid;gap:1rem}}
.pillar{{display:flex;gap:1rem;padding:1.2rem 1.25rem;border:1px solid var(--border);border-radius:var(--r);background:#fff}}
.pillar .ic{{flex:none;width:44px;height:44px;border-radius:12px;background:var(--accent-lt);color:var(--accent);display:grid;place-items:center}}
.pillar h3{{font-size:1.02rem;margin-bottom:.15rem}}
.pillar p{{font-size:.93rem;color:var(--muted);margin:0}}
.services{{background:var(--canvas)}}
.head{{margin-bottom:2.5rem}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:1.25rem}}
.svc{{background:#fff;border:1px solid var(--border);border-top:3px solid var(--accent);border-radius:var(--r);padding:1.6rem}}
.svc .ic{{width:52px;height:52px;border-radius:14px;background:var(--ink-lt);color:var(--ink);display:grid;place-items:center;margin-bottom:1.1rem}}
.svc h3{{font-size:1.12rem;margin-bottom:.45rem}}
.svc p{{font-size:.95rem;color:var(--muted)}}
.why-item{{display:flex;gap:.9rem;align-items:flex-start;padding:1.1rem 0;border-bottom:1px solid var(--border)}}
.why-item b{{flex:none;width:34px;height:34px;border-radius:50%;background:var(--accent);color:#fff;display:grid;place-items:center;font-size:.85rem}}
.why-item h3{{font-size:1rem;margin-bottom:.15rem}}
.why-item p{{font-size:.92rem;color:var(--muted)}}
.reviews{{background:var(--canvas)}}
.quote{{background:#fff;border:1px solid var(--border);border-radius:var(--r);padding:1.6rem;display:flex;flex-direction:column;gap:1rem}}
.stars{{color:var(--star);letter-spacing:.15em}}
.quote cite{{font-style:normal;font-weight:700;color:var(--ink);font-size:.92rem;margin-top:auto}}
.contact{{background:var(--ink-dk);color:#E5E9F2}}
.contact h2{{color:#fff}}
.contact .wrap{{display:grid;grid-template-columns:1.1fr 1fr;gap:3rem;align-items:start}}
.contact .lead{{color:#D3D9E4}}
.contact .eyebrow{{color:#fff;opacity:.85}}
.cards{{display:grid;gap:.9rem}}
.cc{{display:flex;gap:1rem;align-items:flex-start;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);
  border-radius:var(--r);padding:1.1rem 1.2rem;text-decoration:none}}
a.cc:hover{{background:rgba(255,255,255,.1)}}
.cc .ic{{flex:none;width:42px;height:42px;border-radius:12px;background:var(--accent);color:#fff;display:grid;place-items:center}}
.cc small{{display:block;font-size:.74rem;letter-spacing:.12em;text-transform:uppercase;color:#C9D1DE;font-weight:700}}
.cc span{{color:#fff;font-weight:600}}
footer{{background:#0B1320;color:#C9D1DE;font-size:.86rem}}
footer .wrap{{display:flex;justify-content:space-between;align-items:center;gap:1rem 2rem;flex-wrap:wrap;padding-top:1.6rem;padding-bottom:1.6rem}}
footer a{{color:#fff;text-decoration:none;font-weight:600}}
.credit{{width:100%;font-size:.76rem;color:#AEB8C8;border-top:1px solid rgba(255,255,255,.1);padding-top:1rem}}
@media (max-width:960px){{
  .hero .wrap,.about .wrap,.contact .wrap{{grid-template-columns:1fr}}
  .hero-card{{justify-self:center;width:min(70%,280px)}}
  .grid3{{grid-template-columns:1fr 1fr}}
}}
@media (max-width:720px){{
  nav.links a:not(.login){{display:none}}
  .topbar .area{{display:none}}
  section{{padding:3.5rem 0}}
  .grid3{{grid-template-columns:1fr}}
  .brand small{{display:none}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important;scroll-behavior:auto}}}}
</style>"""


def render_page(login_url: str = "/login") -> str:
    """The whole public page as one self-contained HTML string."""
    c = ST.landing_content()
    esc = P.esc
    name = B.name_text()                      # escaped inside
    tagline = esc(B.COMPANY_TAGLINE)
    phone, email = str(B.COMPANY_PHONE or "").strip(), str(B.COMPANY_EMAIL or "").strip()
    tel, mail = _tel(phone), (f"mailto:{email}" if "@" in email else "")
    web_href, web_label = _web_href(B.COMPANY_WEB), _web_label(B.COMPANY_WEB)
    addr = str(B.COMPANY_ADDR or "").strip()
    maps = ("https://www.google.com/maps/search/?api=1&query="
            + urllib.parse.quote_plus(" ".join(addr.split()))) if addr else ""
    year = datetime.date.today().year

    # ── top bar ──
    contact_bits = []
    if tel:
        contact_bits.append(f'<a href="{esc(tel)}">{esc(phone)}</a>')
    if mail:
        contact_bits.append(f'<a href="{esc(mail)}">{esc(email)}</a>')
    area = (f'<span class="area">Serving {esc(c["service_area"])}</span>'
            if c["service_area"] else '<span class="area"></span>')
    topbar = (f'<div class="topbar"><div class="wrap">{area}'
              f'<span>{" &nbsp;&middot;&nbsp; ".join(contact_bits)}</span></div></div>'
              if contact_bits or c["service_area"] else "")

    # ── header ──
    nav_links = []
    if c["about"]:
        nav_links.append('<a href="#about">About</a>')
    if _pairs(c["services"]):
        nav_links.append('<a href="#services">Services</a>')
    nav_links.append('<a href="#contact">Contact</a>')
    header = f"""<header><div class="wrap">
  <a class="brand" href="#top" aria-label="{name} home">
    {_brand_mark(40)}
    <span><b>{name}</b>{f'<small>{tagline}</small>' if tagline else ''}</span>
  </a>
  <nav class="links" aria-label="Main">
    {"".join(nav_links)}
    <a class="btn btn-ink login" href="{esc(login_url)}">Staff Login</a>
  </nav>
</div></header>"""

    # ── hero ──
    eyebrow = esc(c["eyebrow"]) or tagline
    title = esc(c["hero_title"]) or name
    hero_text = esc(c["hero_text"])
    cta = []
    if tel:
        cta.append(f'<a class="btn btn-solid" href="{esc(tel)}">{_svg(_ICON_PHONE, 18)} Call {esc(phone)}</a>')
    if _pairs(c["services"]):
        cta.append('<a class="btn btn-line" href="#services">Our services</a>')
    elif mail:
        cta.append(f'<a class="btn btn-line" href="{esc(mail)}">Send an email</a>')
    hero = f"""<section class="hero" style="padding:0"><div class="wrap">
  <div>
    {f'<div class="eyebrow">{eyebrow}</div>' if eyebrow else ''}
    <h1>{title}</h1>
    {f'<p>{hero_text}</p>' if hero_text else ''}
    {f'<div class="cta">{"".join(cta)}</div>' if cta else ''}
  </div>
  <div class="hero-card" aria-hidden="true"><div class="disc">{_brand_mark(96)}</div></div>
</div></section>"""

    # ── about ──
    about = ""
    paras = _lines(c["about"])
    if paras:
        pillars = []
        if c["founder"]:
            pillars.append(("Founded by", esc(c["founder"]), _ICONS[4]))
        if c["service_area"]:
            pillars.append(("Where we work", esc(c["service_area"]), _ICONS[2]))
        if B.COMPANY_GSTIN:
            pillars.append(("Registered business",
                            f"GSTIN {esc(B.COMPANY_GSTIN)}", _ICONS[0]))
        pill_html = "".join(
            f'<div class="pillar"><div class="ic">{_svg(ic)}</div>'
            f'<div><h3>{h}</h3><p>{t}</p></div></div>' for h, t, ic in pillars)
        web_btn = (f'<p style="margin-top:1.4rem"><a class="btn btn-ink" href="{esc(web_href)}" '
                   f'rel="noopener">Visit {esc(web_label)}</a></p>') if web_href else ""
        about = f"""<section class="about" id="about"><div class="wrap">
  <div>
    <div class="eyebrow">About us</div>
    <h2>{name}</h2>
    {"".join(f"<p>{esc(p)}</p>" for p in paras)}
    {web_btn}
  </div>
  {f'<div class="pillars">{pill_html}</div>' if pill_html else '<div></div>'}
</div></section>"""

    # ── services ──
    services = ""
    svc = _pairs(c["services"])
    if svc:
        cards = "".join(
            f'<div class="svc"><div class="ic">{_svg(_ICONS[i % len(_ICONS)], 26)}</div>'
            f'<h3>{esc(t)}</h3>{f"<p>{esc(s)}</p>" if s else ""}</div>'
            for i, (t, s) in enumerate(svc))
        services = f"""<section class="services" id="services"><div class="wrap">
  <div class="head"><div class="eyebrow">Our services</div><h2>What we do.</h2></div>
  <div class="grid3">{cards}</div>
</div></section>"""

    # ── why ──
    why = ""
    reasons = _pairs(c["reasons"])
    if reasons:
        items = "".join(
            f'<div class="why-item"><b>{i + 1:02d}</b><div><h3>{esc(t)}</h3>'
            f'{f"<p>{esc(s)}</p>" if s else ""}</div></div>'
            for i, (t, s) in enumerate(reasons))
        why = f"""<section class="why"><div class="wrap">
  <div class="head"><div class="eyebrow">Why choose us</div><h2>Why clients work with us.</h2></div>
  <div class="grid3">{items}</div>
</div></section>"""

    # ── reviews ──
    reviews = ""
    revs = _reviews(c["reviews"])
    if revs:
        figs = "".join(
            f'<figure class="quote">{_stars(r)}<blockquote>{esc(q)}</blockquote>'
            f'<cite>{esc(n)}</cite></figure>' for n, r, q in revs)
        reviews = f"""<section class="reviews"><div class="wrap">
  <div class="head"><div class="eyebrow">What clients say</div><h2>In their words.</h2></div>
  <div class="grid3">{figs}</div>
</div></section>"""

    # ── contact ──
    cards = []
    if tel:
        cards.append(f'<a class="cc" href="{esc(tel)}"><div class="ic">{_svg(_ICON_PHONE, 20)}</div>'
                     f'<div><small>Phone</small><span>{esc(phone)}</span></div></a>')
    if mail:
        cards.append(f'<a class="cc" href="{esc(mail)}"><div class="ic">{_svg(_ICON_MAIL, 20)}</div>'
                     f'<div><small>Email</small><span>{esc(email)}</span></div></a>')
    if addr:
        cards.append(f'<a class="cc" href="{esc(maps)}" rel="noopener"><div class="ic">{_svg(_ICON_PIN, 20)}</div>'
                     f'<div><small>Office</small><span>{esc(addr)}</span></div></a>')
    if c["hours"]:
        cards.append(f'<div class="cc"><div class="ic">{_svg(_ICON_CLOCK, 20)}</div>'
                     f'<div><small>Hours</small><span>{esc(c["hours"])}</span></div></div>')
    contact_cta = []
    if tel:
        contact_cta.append(f'<a class="btn btn-solid" href="{esc(tel)}">Call now</a>')
    if mail:
        contact_cta.append(f'<a class="btn btn-line" href="{esc(mail)}">Send an email</a>')
    contact = f"""<section class="contact" id="contact"><div class="wrap">
  <div>
    <div class="eyebrow">Contact</div>
    <h2>Talk to us about your project.</h2>
    {f'<p class="lead">We work {esc(c["hours"])}.</p>' if c["hours"] else ''}
    {f'<div class="cta">{"".join(contact_cta)}</div>' if contact_cta else ''}
  </div>
  <div class="cards">{"".join(cards)}</div>
</div></section>"""

    # ── footer ── (the credit line is fixed and is not a setting)
    gst = f" &middot; GSTIN {esc(B.COMPANY_GSTIN)}" if B.COMPANY_GSTIN else ""
    web_link = (f'<a href="{esc(web_href)}" rel="noopener">{esc(web_label)}</a> &nbsp;&middot;&nbsp; '
                if web_href else "")
    footer = f"""<footer><div class="wrap">
  <span>&copy; {year} {name}{gst}</span>
  <span>{web_link}<a href="{esc(login_url)}">Staff Login</a></span>
  <div class="credit">{CREDIT}</div>
</div></footer>"""

    desc = esc(c["hero_text"] or B.COMPANY_TAGLINE or "")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(B.APP_NAME)}{f" | {tagline}" if tagline else ""}</title>
{f'<meta name="description" content="{desc}">' if desc else ''}
<meta name="theme-color" content="{_PALETTE['ink_dk']}">
{B.HEAD_ICON}
{_styles()}
</head>
<body>
{topbar}
{header}
<main id="top">
{hero}
{about}
{services}
{why}
{reviews}
{contact}
</main>
{footer}
</body>
</html>
"""


@landing_bp.route("/", methods=["GET"])
def index():
    return render_page(login_url=url_for("auth.login"))
