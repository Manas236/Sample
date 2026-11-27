# Feature gap — Sample (product) vs Demo_Works `antigravity-dev`

Compared on 27 November 2026:

- **Sample** `main` at `161ab55` (the product snapshot, PROVENANCE.md).
- **Demo_Works** `antigravity-dev` at `e1ac14f` (fetched from the remote, not a
  local copy). The product line forked from it at `383135b`; Demo_Works has
  165 commits since then (≈92,600 lines added across 245 files, most of it
  docs and tests).

Demo_Works is **reference only**. A port here is a reimplementation against
Sample's code, never a cherry-pick: the two `boq.py`, `ra.py`, `purchase.py`
and `challan.py` have diverged since October and none of these commits apply.
Anything the client deployment carried as data (its terms, its number series,
its letterhead artwork, its sheets) stays behind; only the mechanism comes over.

Size: **S** ≈ a day or less, one module · **M** ≈ a few hundred lines across
2–4 modules · **L** ≈ a new subsystem, 1,000+ lines, or entangled with
Demo_Works-only modules that Sample does not have.

Status: **ported** (this pass, commit named in REPORT.md) · **deferred** (wanted,
not done, reason given) · **not needed** (client-specific, or Sample already
covers it).

## The ten features the brief asked for (in its order)

| # | Feature | Demo_Works commits / files | Size | Status |
|---|---|---|---|---|
| 1a | Price-summary cover page on the printed BOQ, Portrait / Landscape | `1e9bc9a` · `pricesummary.py`, `boq.py`, `settings.py` | M | see below |
| 1b | Terms & conditions library (/settings), add from library or your own | `71ea78a` · `pricesummary.py`, `tools/backfill_terms.py` | M | see below |
| 1c | Price-summary cover on the printed **quotation** | `1e9bc9a`, `71ea78a` · `quotation.py` | M | see below |
| 2a | Draft PO displayed as "Product Inquiry" | `66759ef` · `po_draft.py`, `chrome.py`, `settings.py` | S | see below |
| 2b | Product Inquiry without a BOQ, extra items, convert carries extras | `2e4f2c0` · `extraitems.py`, `po_draft.py`, `purchase.py` | M | see below |
| 2c | Product Inquiry fully editable until converted | `b0e4809` · `po_draft.py` | M | see below |
| 2d | Named reusable item pictures on the inquiry and the PO; pictures on the real PO at creation | `3eded00`, `af958a1` · `lineimage.py`, `boqpick.py`, `purchase.py`, `db.py` | L | see below |
| 3a | Delivery challan without a BOQ; extra items on any DC | `887860f` · `challan.py` | M | see below |
| 3b | Delivery challan raised from a purchase PO | `351eaf5` · `dcpo.py`, `challan.py`, `purchase.py` | M | see below |
| 4a | Every document raised straight from the BOQ (RA types, PI, TI) | `fa42e27` · `boq.py`, `invoice.py`, `proforma.py` | L | see below |
| 4b | Supply + Installation in one POST, merged tax invoice; set cancelled as one | `976010d`, `c33200c` · `raboth.py`, `ra.py`, `merged_ra.py` | L | see below |
| 4c | RA / TI quantity above the BOQ, with a required reason | `ac887bc` · `boqexcess.py`, `ra.py`, `invoice.py` | M | see below |
| 5 | Receipts as a BOQ running account with TDS / retention / other deductions | — not at `e1ac14f` | — | **deferred: not on origin** (the work exists only on the live server and was never pushed to Demo_Works) |
| 6 | Round-off to the rupee, a per-document tick, on by default | `09a028b`, `0cee4d4`, `d2e3234` · `roundoff.py` + every money module | M | see below |
| 7 | Project page: documents follow their BOQ (latest revision only), labour cost, cost pie + progress bars, planned vs actual margin | `a6ab6c4`, `19dc55d`, `7f2fd07`, `7308d26`, `456c980`, `e793dfa`, `9edba90`, `4f1360f`, `2df435e` · `pnl.py`, `pnl_chart.py`, `projtag.py`, `projectview.py` | L | see below |
| 8 | Labour attendance workbook import + payslips + pay ledger | `de9d757`, `078e1e3`, `0c397c5`, `9b3ef4c`, `8dad301` · `payimport.py`, `payroll.py`, `attendance.py` | L | see below |
| 9 | BOQ revision numbered off its root (`/0019/1`, print shows `/0019`) | `1eb36ca` · `boq.py`, `series.py`, `pipeline.py` | M | see below |
| 10 | SITC (Supply + Installation combined rate) on BOQ import | `703b93f`, `cb48811` · `boq.py`, `boqimport.py`, `proforma.py` | M–L | see below |

The status column is filled in under **Outcome** at the foot of this file, one
paragraph per row, so the reason travels with the verdict.

## Everything else Demo_Works has that Sample lacks or has older

| Feature | Demo_Works commits / files | Size | Status |
|---|---|---|---|
| Work orders for petty contractors, own collection, Excel import | `54e15a3`, `d052ff9`, `dfc7d96`, `e4daa5d` · `workorder.py`, `importstage.py` | L | deferred — Sample raises a work order as a PO marked "WORK ORDER" (the demo seeds do this) |
| BOQ import: column picker with advice, escalation optional, discount and net | `2225e6a` · `boqimport.py`, `sheetimport.py` | L | deferred |
| BOQ opens "as it is" (blank stays blank, 0 stays 0) | `cd5dd64` · `boq.py`, `boqimport.py` | L | deferred |
| BOQ import: qty-0 + no-rate row left out | `1d6a171` · `boqimport.py` | S | deferred |
| Import from Excel on every typed document | `378e236` · `docimport.py` | L | deferred |
| PI / TI raised from a BOQ bill at the net rate | `4db95ca` · `boq.py`, `invoice.py`, `proforma.py` | S | deferred (needs 4a) |
| Four document deletes leave the Owner tier | `c89c173` · `auth.py` | S | not needed — a client role ruling, not a product rule |
| Preloaded signature and company stamp on every signed print | `c35b710` · `docsheet.py`, `settings.py` | M | deferred — affects the branding swap; noted in DEMO_SCRIPT.md |
| Make column on the PO and the draft PO | `02f1e10`, `d08ed3a` · `purchase.py`, `po_draft.py` | S–M | deferred |
| No browser header / footer on a printed document | `c6a385a` · print CSS | S | deferred |
| Typed document numbers, forward only (RA, receipt, sheet, WO, inquiry, PO, DC) | `8904422`, `ad9a290`, `1c90ab4`, `a359d30` · `docnum.py` | M | deferred |
| Tax invoice number settable to match an accounting package's series | `42d49db` · `tinum.py` | S–M | deferred |
| Search on the attendance pages | `2ce5d6f` · `attendance.py` | S | deferred |
| HSN editable everywhere, fill blanks only | `1fdc09e`, `17b2aba` · `hsnfill.py` | M | deferred |
| Per-login ALLOW / BLOCK access lists edited by a Director | `93c09e7` · `auth.py` | M | deferred |
| Units dropdown on every line form, with its GST UQC | `6ea528a` · `units.py` | M | deferred |
| List page table stays inside its card | `a121953` · screen CSS | S | deferred |
| PO item picker: spec library + BOQ items, short labels | `fc5f4ed`, `89fbd4a` · `buypick.py` | M | deferred |
| Every saved BOQ's items join the spec library | `d617354` · `boq.py`, `spec.py` | M | deferred |
| Resume after Back on create forms | `09a028b`, `5645457` · `formdraft.py` | M | deferred |
| Full edit after issue: proforma, TI, RA text, PO, DC, WO, BOQ in place, quotation | `f3958e3`, `b506f64`, `4f74b91`, `2eceb6e`, `27d5b9c`, `c036916`, `84a3acc` | L | deferred — the quotation edit is also a fifth unfreeze of `quotation.py`, which Sample's freeze forbids |
| Proforma with no BOQ and no quotation; Excel lines on the proforma | `c96fe71`, `f77d124` · `proforma.py` | M | deferred |
| "Edit issued invoice" permission | `41f8ecd` · `auth.py` | S | deferred (needs the TI edit) |
| Labour: estimate then actual, project per worker, overhead, unassigned screen, bulk assign | `9b3ef4c`, `8dad301`, `89e02d8`, `54a63cc`, `727e28d`, `c6cdf71`, `c987971`, `867a734` | L | deferred (needs 8) |
| One worker, one day across every marking path | `1e33de5`, `36487b1` · `attendance.py` | S–M | deferred |
| Address book: duplicate guard, merge-then-delete | `8b80a1b` · `address.py` | M | deferred |
| Qty (Mtr) and Qty (Nos) on the delivery challan | `6583ac3` · `dcqty.py` | M | deferred |
| PO "Deliver To" picked from the address book | `d38687c`, `49d9518` · `purchase.py` | S | deferred |
| Print: every title band clears the letterhead; merged RA print fixes; measurement column fit | `3e88a08`, `0c218da`, `d32b8c3`, `4654d33` | S | deferred — the title-band fix answers the client's tall letterhead banner, which Sample does not have |
| Print-clipping sweep tool (headless renders) | `717c2ba` · `tools/print_sweep/` | M | deferred |
| Letterhead banner artwork and its logo moves | `ff7e956`, `c62f96a`, `36a7e95`, `16154e7` · `assets/` | — | not needed — the client's own artwork; Sample's logo is a /settings upload |
| Landing page public phone | `6cadf67` | — | not needed — client data |

## Outcome, row by row

_Filled in as each port lands; REPORT.md on `demo/solar-epc` carries the
commit SHAs._
