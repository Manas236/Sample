"""Frozen print CSS from demo/solar-epc at 1d7017c. Preserve the rendered bytes."""

PRINT_BASE_STYLES = r"""
<style>
  /* Google Font — DM Sans for a clean but not-generic feel.
     @import has to be the first rule in the sheet or the browser drops it. */
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

  /* ── Reset ───────────────────────────────────────────────────────── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #F6F4F9;
    --surface:   #FFFFFF;
    --brand:     #D5121A;
    --brand-dk:  #A50D14;
    --brand-lt:  #FDECEC;
    --navy:      #2A086E;
    --navy-dk:   #1C0449;
    --navy-lt:   #EDEAF9;
    --saffron:   #F2944A;
    --text:      #1A1626;
    --muted:     #6B6478;
    --border:    #E4E0EC;
    --shadow-sm: 0 1px 3px rgba(26,22,38,.08), 0 1px 2px rgba(26,22,38,.06);
    --shadow-md: 0 6px 20px rgba(42,8,110,.14), 0 2px 6px rgba(26,22,38,.08);
    --radius:    14px;
    --font:      'DM Sans', 'Segoe UI', system-ui, sans-serif;
  }

  /* Flags an identity field that still needs the company's real data. */
  .todo-chip {
    display: inline-block;
    background: #FFF4D6;
    color: #8A5A00;
    border: 1px dashed #E0A93B;
    border-radius: 5px;
    padding: 0 .38em;
    font-size: .82em;
    font-weight: 600;
    font-style: normal;
    letter-spacing: 0;
    white-space: nowrap;
  }

  html, body {
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    font-size: 16px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  /* ── Nav ─────────────────────────────────────────────────────────── */
  nav {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: var(--shadow-sm);
  }

  .nav-brand {
    display: flex;
    align-items: center;
    gap: .6rem;
    font-weight: 700;
    font-size: 1.05rem;
    text-decoration: none;
    letter-spacing: .02em;
  }

  /* The two-tone wordmark: the name in the brand colour, its last word in navy. */
  .nav-brand .nb-word  { color: var(--brand); }
  .nav-brand .nb-accent { color: var(--navy); }
  .nav-brand:hover .nb-word { opacity: .82; }

  .nav-pill {
    background: var(--navy-lt);
    color: var(--navy);
    font-size: .72rem;
    font-weight: 600;
    padding: .2rem .65rem;
    border-radius: 20px;
    letter-spacing: .04em;
    text-transform: uppercase;
  }

  .nav-right { display: flex; align-items: center; gap: .9rem; }
  .nav-link {
    display: flex; align-items: center; gap: .3rem;
    font-size: .8rem; font-weight: 600; color: var(--muted);
    text-decoration: none; white-space: nowrap;
  }
  .nav-link:hover { color: var(--brand); }
  .nav-link svg {
    width: 15px; height: 15px; fill: none; stroke: currentColor;
    stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
  }
  /* Amber dot while any company/bank field is still blank — the documents are
     printing "add …" chips until it clears, so the nav should say so. */
  .nav-link .nl-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--saffron); flex-shrink: 0;
  }

  /* ── Persistence-down strip ──────────────────────────────────────── */
  /* Rendered by _nav(), so every page in the app carries it and no module has
     to remember to wire it up.

     Red, not the settings dot's amber, and a strip rather than a dot. Amber in
     this app means "incomplete but working" — a blank GSTIN prints a chip and
     the document still goes out. This means *nothing you type is being saved*,
     and a 7px dot cannot carry that. It clears itself the moment a retry
     succeeds, the same self-clearing contract the settings dot holds to. */
  .db-down {
    background: var(--brand);
    color: #fff;
    padding: .55rem 2rem;
    font-size: .82rem;
    line-height: 1.45;
    display: flex;
    align-items: baseline;
    gap: .6rem;
    position: sticky;
    top: 60px;          /* directly under the 60px nav, and sticky with it */
    z-index: 99;        /* below nav's 100, above the page */
  }
  .db-down-tag {
    flex-shrink: 0;
    font-size: .7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .07em;
    border: 1px solid rgba(255,255,255,.55);
    border-radius: 3px;
    padding: .05rem .4rem;
  }
  .db-down code { font-size: .78rem; opacity: .92; }

  /* App chrome, never part of a printed document. The rule that hides `nav` on
     paper lives in quotation.py's VIEW_DOC_STYLES; this strip ships its own so
     it cannot print on a sheet whose page did not happen to load that one. */
  @media print { .db-down { display: none !important; } }

  @media (max-width: 580px) {
    .db-down { padding: .5rem 1rem; flex-direction: column; gap: .25rem; }
  }

  /* ── Main Layout ─────────────────────────────────────────────────── */
  main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 3rem 1.5rem 5rem;
  }

  /* Contact strip under the footer rule */
  .foot-contact {
    margin-top: .35rem;
    font-size: .78rem;
    color: var(--muted);
  }
  .foot-contact b { color: var(--navy); font-weight: 600; }

  /* ── Card ────────────────────────────────────────────────────────── */
  /* Used by the dashboard's module strip (.mods in DASH_STYLES lays them out
     and overrides the padding). Kept here because a card is a general shape
     any future page can reach for. */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 2rem 1.75rem;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
    box-shadow: var(--shadow-sm);
    position: relative;
    overflow: hidden;
  }

  /* Subtle top accent bar that reveals on hover */
  .card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--brand);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform .25s ease;
  }

  .card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-md);
    border-color: var(--brand-lt);
  }

  .card:hover::before { transform: scaleX(1); }

  .card-icon {
    width: 48px;
    height: 48px;
    background: var(--brand-lt);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    flex-shrink: 0;
    transition: background .2s;
  }

  .card:hover .card-icon { background: var(--brand); }
  .card:hover .card-icon svg { stroke: #fff; }

  .card-icon svg {
    width: 24px;
    height: 24px;
    stroke: var(--brand);
    fill: none;
    stroke-width: 1.8;
    stroke-linecap: round;
    stroke-linejoin: round;
    transition: stroke .2s;
  }

  .card-body { flex: 1; }

  .card-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: .35rem;
  }

  .card-desc {
    font-size: .88rem;
    color: var(--muted);
    line-height: 1.55;
  }

  /* ── Button ──────────────────────────────────────────────────────── */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    background: var(--brand);
    color: #fff;
    font-family: var(--font);
    font-size: .88rem;
    font-weight: 600;
    padding: .65rem 1.4rem;
    border-radius: 8px;
    text-decoration: none;
    border: none;
    cursor: pointer;
    transition: background .15s, transform .15s;
  }

  .btn:hover { background: var(--brand-dk); transform: translateY(-1px); }
  .btn-ghost {
    background: transparent;
    color: var(--brand);
    border: 1.5px solid var(--brand);
  }
  .btn-ghost:hover { background: var(--brand-lt); transform: translateY(-1px); }

  /* ── Footer ──────────────────────────────────────────────────────── */
  footer {
    text-align: center;
    margin-top: 4rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: .8rem;
  }

  /* ── Responsive ──────────────────────────────────────────────────── */
  @media (max-width: 580px) {
    nav { padding: 0 1rem; }
    main { padding: 2rem 1rem 4rem; }
    /* The subtitle pill is decoration; the settings link is a control. On a
       narrow screen the control keeps the space. */
    .nav-pill { display: none; }
  }
</style>
"""

PRINT_QUOTATION_STYLES = r"""
<style>
  .page-top {
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:1.75rem; flex-wrap:wrap; gap:1rem;
  }
  .page-top h1 { font-size:1.5rem; font-weight:700; letter-spacing:-.4px; }
  .page-top h1 span { color:var(--brand); }

  .alert {
    padding:.8rem 1.1rem; border-radius:8px; font-size:.87rem;
    font-weight:500; margin-bottom:1.4rem;
    display:flex; align-items:center; gap:.5rem;
  }
  .alert-error   { background:#fef2f2; color:#991b1b; border:1px solid #fecaca; }
  .alert-success { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; }

  .table-wrap {
    background:var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); overflow:hidden; box-shadow:var(--shadow-sm);
  }
  table { width:100%; border-collapse:collapse; font-size:.88rem; }
  thead { background:var(--bg); border-bottom:1px solid var(--border); }
  th {
    padding:.8rem 1.1rem; text-align:left; font-size:.73rem;
    font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--muted);
  }
  td { padding:.9rem 1.1rem; border-bottom:1px solid var(--border); vertical-align:middle; }
  tbody tr:last-child td { border-bottom:none; }
  tbody tr:hover { background:#f8fafc; }
  .td-ref   { font-family:'SFMono-Regular',Consolas,monospace; font-weight:700; color:var(--brand); }
  .td-cust  { font-weight:600; }
  .td-total { font-weight:700; color:var(--brand); }
  .td-muted { font-size:.82rem; color:var(--muted); }
  .btn-view {
    font-size:.75rem; font-weight:600; color:var(--brand); background:var(--brand-lt);
    border:1px solid #c7d2fe; border-radius:6px; padding:.28rem .7rem;
    text-decoration:none; display:inline-block; transition:background .13s;
  }
  .btn-view:hover { background:#c7d2fe; }
  .empty-state {
    text-align:center; padding:3.5rem 2rem; color:var(--muted);
    background:var(--surface); border:1px dashed var(--border); border-radius:var(--radius);
  }

  .form-section {
    background:var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); padding:1.6rem 1.9rem;
    box-shadow:var(--shadow-sm); margin-bottom:1.4rem;
  }
  .section-title {
    font-size:.73rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.09em; color:var(--brand); margin-bottom:1.2rem;
    display:flex; align-items:center; gap:.4rem;
    padding-bottom:.6rem; border-bottom:1px solid var(--border);
  }

  .fg2 { display:grid; grid-template-columns:1fr 1fr;            gap:.9rem; }
  .fg3 { display:grid; grid-template-columns:1fr 1fr 1fr;        gap:.9rem; }
  .fg4 { display:grid; grid-template-columns:1fr 1fr 1fr 1fr;    gap:.9rem; }
  .fg5 { display:grid; grid-template-columns:1fr 1fr 1fr 1fr 1fr;gap:.9rem; }
  .span2 { grid-column:span 2; }
  .span3 { grid-column:span 3; }
  .span4 { grid-column:span 4; }
  .span-all { grid-column:1/-1; }

  .form-group { display:flex; flex-direction:column; gap:.3rem; }

  /* ── Address book picker (Bill To / Ship To) ─────────────────────── */
  .addr-pick {
    display:flex; align-items:center; gap:.6rem; flex-wrap:wrap;
    margin-bottom:.8rem; padding-bottom:.8rem;
    border-bottom:1px dashed var(--border);
  }
  .addr-pick select {
    flex:1 1 260px; min-width:0;
    font-family:var(--font); font-size:.85rem; padding:.5rem .65rem;
    border:1px solid var(--border); border-radius:8px;
    background:var(--bg); color:var(--text);
  }
  .addr-pick select:focus { outline:none; border-color:var(--brand); background:var(--surface); }
  .addr-pick-link {
    font-size:.76rem; font-weight:600; color:var(--brand);
    text-decoration:none; white-space:nowrap;
  }
  .addr-pick-link:hover { text-decoration:underline; }

  label {
    font-size:.72rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.07em; color:var(--muted);
  }
  input[type="text"],
  input[type="date"],
  input[type="number"],
  input[type="email"],
  input[type="tel"],
  textarea,
  select {
    font-family:var(--font); font-size:.88rem; color:var(--text);
    background:var(--bg); border:1.5px solid var(--border);
    border-radius:7px; padding:.52rem .8rem; width:100%;
    transition:border-color .14s, box-shadow .14s; outline:none;
  }
  input:focus, textarea:focus, select:focus {
    border-color:var(--brand);
    box-shadow:0 0 0 3px rgba(79,70,229,.1); background:#fff;
  }
  input[type="checkbox"] { width:auto; cursor:pointer; accent-color:var(--brand); }
  textarea { resize:vertical; min-height:72px; }

  .check-row { display:flex; align-items:center; gap:.5rem; padding-top:.35rem; }
  .check-row label { text-transform:none; font-size:.86rem; font-weight:500; color:var(--text); letter-spacing:0; }

  .readonly-field {
    font-family:'SFMono-Regular',Consolas,monospace; font-size:.88rem;
    color:var(--brand); background:#f5f3ff; border:1.5px solid #c7d2fe;
    border-radius:7px; padding:.52rem .8rem; font-weight:700;
  }

  .addr-sub {
    border:1px solid var(--border); border-radius:8px;
    padding:1rem 1.1rem; margin-top:.75rem; background:#fafafa;
  }
  .addr-sub-title {
    font-size:.7rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.08em; color:var(--muted); margin-bottom:.8rem;
  }
  .ship-opts { display:flex; gap:1.2rem; margin-bottom:.7rem; flex-wrap:wrap; }
  .ship-opt  { display:flex; align-items:center; gap:.35rem; font-size:.84rem; font-weight:500; }

  /* Tax section */
  .tax-options { display:flex; gap:1.4rem; flex-wrap:wrap; margin-bottom:1rem; }
  .tax-opt { display:flex; align-items:center; gap:.4rem; font-size:.86rem; font-weight:500; cursor:pointer; }
  .tax-opt input[type="radio"] { accent-color:var(--brand); width:auto; }
  .tax-panel {
    display:none;
    align-items:center; flex-wrap:wrap; gap:.75rem;
    padding:.75rem 1rem; background:#f8f9ff;
    border:1px solid #e0e4ff; border-radius:8px; margin-top:.1rem;
  }
  .tax-panel.active { display:flex; }
  .tax-input-group { display:flex; flex-direction:column; gap:.3rem; }
  .tax-field-lbl {
    font-size:.68rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.07em; color:var(--muted);
  }
  .tax-field-inp {
    font-family:var(--font); font-size:1rem; font-weight:700; color:var(--brand);
    background:#fff; border:2px solid var(--brand); border-radius:7px;
    padding:.4rem .6rem; width:90px; text-align:center; outline:none;
    transition:border-color .14s, box-shadow .14s;
  }
  .tax-field-inp:focus { box-shadow:0 0 0 3px rgba(79,70,229,.15); }
  .tax-sep { font-size:1.3rem; font-weight:700; color:var(--muted); align-self:flex-end; padding-bottom:.45rem; }
  .tax-total-display {
    font-family:var(--font); font-size:1rem; font-weight:800; color:#166534;
    background:#f0fdf4; border:2px solid #86efac; border-radius:7px;
    padding:.4rem .7rem; min-width:90px; text-align:center;
  }
  .tax-hint { font-size:.78rem; color:var(--muted); align-self:center; max-width:260px; line-height:1.45; }

  /* Product picker */
  .picker-bar {
    display:grid; grid-template-columns:1fr 90px auto;
    gap:.6rem; align-items:end; margin-bottom:.75rem;
  }
  .picker-bar select, .picker-bar input { margin:0; }

  .add-error {
    font-size:.8rem; color:#b91c1c; background:#fef2f2;
    border:1px solid #fecaca; border-radius:6px;
    padding:.3rem .8rem; margin-bottom:.5rem; display:none;
  }

  #sel-container { display:flex; flex-direction:column; gap:.5rem; }
  #empty-notice {
    text-align:center; padding:1.6rem 1rem; color:var(--muted);
    font-size:.86rem; border:1.5px dashed var(--border); border-radius:8px; background:#fafafa;
  }

  .sel-root {
    border:1px solid var(--border); border-radius:9px;
    background:var(--bg); overflow:hidden;
    transition:border-color .13s;
  }
  .sel-root:hover { border-color:#a5b4fc; }

  .sel-root-head {
    display:grid; grid-template-columns:1fr auto;
    gap:.6rem; padding:.55rem .85rem; align-items:center;
  }
  .sel-root-info .sel-name  { font-size:.88rem; font-weight:700; color:var(--text); }
  .sel-root-info .sel-pno   { font-size:.72rem; color:var(--muted); font-family:'SFMono-Regular',Consolas,monospace; margin-top:1px; }
  .badge-asm {
    display:inline-block; font-size:.62rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.06em;
    background:#dbeafe; color:#1d4ed8; border-radius:10px; padding:.1rem .4rem; margin-left:.4rem;
  }

  .sel-root-ctrl { display:flex; gap:.5rem; align-items:center; flex-wrap:wrap; }
  .ctrl-block { display:flex; flex-direction:column; gap:.15rem; align-items:center; }
  .ctrl-lbl   { font-size:.65rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }
  .ctrl-input {
    font-family:var(--font); font-size:.86rem; color:var(--text);
    background:#fff; border:1.5px solid var(--border); border-radius:6px;
    padding:.35rem .5rem; outline:none; transition:border-color .14s;
  }
  .ctrl-input:focus { border-color:var(--brand); }
  .ctrl-input.w-qty   { width:70px; text-align:center; }
  .ctrl-input.w-price { width:110px; text-align:right; }
  .ctrl-check { accent-color:var(--brand); width:auto !important; cursor:pointer; }

  .btn-expand {
    font-family:var(--font); font-size:.74rem; font-weight:600;
    color:var(--brand); background:var(--brand-lt); border:1px solid #c7d2fe;
    border-radius:6px; padding:.3rem .65rem; cursor:pointer; white-space:nowrap;
    transition:background .13s;
  }
  .btn-expand:hover { background:#c7d2fe; }
  .btn-rm {
    font-family:var(--font); font-size:.96rem; font-weight:700;
    color:#ef4444; background:#fef2f2; border:1px solid #fecaca;
    border-radius:6px; cursor:pointer; width:30px; height:30px;
    display:flex; align-items:center; justify-content:center;
    flex-shrink:0; transition:background .13s;
  }
  .btn-rm:hover { background:#fee2e2; }

  .comp-area {
    border-top:1px dashed var(--border);
    background:#f8f9ff; padding:.5rem .85rem .6rem 1.5rem;
  }
  .comp-row {
    display:grid; grid-template-columns:1fr auto;
    gap:.5rem; align-items:center;
    padding:.35rem .5rem; border-radius:7px;
    border:1px solid #e8eaff; background:#fff; margin-bottom:.35rem;
  }
  .comp-row:last-of-type { margin-bottom:.5rem; }
  .comp-info .comp-name { font-size:.83rem; font-weight:600; color:var(--text); }
  .comp-info .comp-pno  { font-size:.7rem; color:var(--muted); font-family:'SFMono-Regular',Consolas,monospace; }

  .comp-ctrl { display:flex; gap:.4rem; align-items:center; flex-wrap:wrap; }

  .btn-add-comp {
    font-family:var(--font); font-size:.75rem; font-weight:600;
    color:#166534; background:#f0fdf4; border:1px dashed #86efac;
    border-radius:6px; padding:.3rem .75rem; cursor:pointer;
    transition:background .13s; display:inline-flex; align-items:center; gap:.3rem;
    margin-top:.25rem;
  }
  .btn-add-comp:hover { background:#dcfce7; }

  .comp-picker { display:flex; gap:.4rem; align-items:center; margin-top:.4rem; flex-wrap:wrap; }
  .comp-picker select { flex:1; min-width:180px; font-size:.82rem; padding:.35rem .6rem; }
  .comp-picker input  { width:70px; text-align:center; font-size:.82rem; padding:.35rem .5rem; }

  .form-actions { display:flex; gap:.75rem; margin-top:1.4rem; align-items:center; }

  /* ── Proforma links ───────────────────────────────────────────────────
     Lives here rather than in proforma.py because both sides need it: the
     deal panel lists the PIs raised against a quotation, and the convert page
     warns about the ones already issued. Every page that renders a chip
     already loads QUOTATION_STYLES. */
  .pi-block { margin-top:1.1rem; padding-top:.9rem; border-top:1px dashed var(--border); }
  .pi-lbl {
    font-size:.68rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.07em; color:var(--muted);
  }
  .pi-strip { display:flex; flex-wrap:wrap; gap:.5rem; margin-top:.5rem; }
  .pi-chip {
    font-size:.76rem; font-weight:600; text-decoration:none;
    border:1px solid var(--border); border-radius:8px;
    padding:.25rem .6rem; background:var(--surface); color:var(--navy);
    transition:border-color .13s;
  }
  .pi-chip:hover { border-color:var(--navy); }

  /* ── Job costing / purchase-order links ───────────────────────────────
     Same reasoning as the proforma chips above, one pipeline over: the deal
     panel here renders what a job is costing on the BUY side, and purchase.py
     renders the chips too. purchase.py imports *this* module for the document
     formatters, so the class cannot live there — it would be a cycle. Every
     page that renders one already loads QUOTATION_STYLES. */
  .jobcost-grid {
    display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
    gap:.7rem; margin-top:.5rem;
  }
  .jc-cell {
    background:var(--bg); border:1px solid var(--border);
    border-radius:9px; padding:.55rem .7rem;
  }
  .jc-lbl {
    font-size:.68rem; text-transform:uppercase; letter-spacing:.05em;
    color:var(--muted); font-weight:700;
  }
  .jc-val {
    font-size:1rem; font-weight:700; font-variant-numeric:tabular-nums;
    margin-top:.15rem;
  }
  /* Margin is the one figure here that carries good/bad meaning, so it is the
     only one that takes colour — and it never carries it alone: the percentage
     sits under it in words. */
  .jc-val.good { color:#166534; }
  .jc-val.bad  { color:var(--brand); }
  .jc-sub { font-size:.72rem; color:var(--muted); margin-top:.1rem; }
  .po-strip { display:flex; flex-wrap:wrap; gap:.5rem; margin-top:.6rem; }
  .po-chip {
    font-size:.76rem; font-weight:600; text-decoration:none;
    border:1px solid var(--border); border-radius:8px;
    padding:.25rem .6rem; background:var(--surface); color:var(--navy);
    transition:border-color .13s;
  }
  .po-chip:hover { border-color:var(--navy); }

  @media(max-width:800px){
    .fg2,.fg3,.fg4,.fg5 { grid-template-columns:1fr 1fr; }
    .span3,.span4,.span-all { grid-column:1/-1; }
    .picker-bar { grid-template-columns:1fr; }
    .sel-root-ctrl { gap:.35rem; }
    td,th { padding:.6rem .75rem; }
    .col-h { display:none; }
  }
  @media(max-width:520px){
    .fg2,.fg3,.fg4,.fg5 { grid-template-columns:1fr; }
  }
</style>
"""
