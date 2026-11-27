# Demo script — 15 minutes for a solar EPC owner

**Branch:** `demo/solar-epc` · **Company:** Helios Grid Energy Pvt Ltd (fictional, demo data)
· **Sign in as:** `owner` / `Helios-Owner-26` (RUN_LOCAL.md §7)

The story on screen: a 350 kWp industrial rooftop for *Shree Ganesh Polymers*,
Bhiwandi, from quotation to commissioning-stage billing (Aug–Nov 2026), plus a
60 kWp housing society at an earlier stage and one lead that never converted.

## Before you start (2 minutes, off-camera)

1. Fresh data: `.\.venv\Scripts\python.exe tools\seed_demo.py --reset`
2. Start: `.\.venv\Scripts\python.exe app.py`, open the address it prints, sign in as `owner`.
3. Optional: rebrand to the prospect (below). Do it before the call, not during.
4. Browser zoom 90% reads well on a shared screen; print previews open in a new tab.

---

## 1. Dashboard (1 min)

**Click:** the app opens on the dashboard.

**Pain it solves:** one screen for what is quoted, billed, received and committed
across every plant, instead of five spreadsheets and a WhatsApp group.

**Don't click:** *Product Catalogue* in the rail (switched off in this product;
the spec library replaces it) or *Market News*.

## 2. Quotation with the price summary (2 min)

**Click:** *Bills of Quantities* → **HG/BOQ/26-27/0002** (rev 1, Shree Ganesh
Polymers) → **Print**. The first page is the **price summary**: one line per
section (modules & inverters, structure, BOS, I&C, liaisoning) with supply,
installation and total, the amount in words, and the numbered terms. Back on
the BOQ, **Price summary & terms** shows where the terms come from: ticked from
the company's library, or typed for this customer, with Portrait or Landscape.

Then *Quotations* → **QT-0001** for the quick budgetary offer built from the
spec library (modules and inverters, per-Wp priced).

**Pain it solves:** per-kWp quoting that a client can read in one page, with the
same terms every time, and no retyping when module prices move.

**Don't click:** nothing on the quotation's print expects a price-summary page —
the cover is on the BOQ print, not on the quotation print (FEATURE_GAP 1c).

## 3. BOQ — cost vs selling, margin hidden on print (2 min)

**Click:** back to **HG/BOQ/26-27/0002**. On screen each line shows the
**base rate (our cost)** and the **escalation % (our margin)**, then the
selling rate. Open **Print** again: the base rate and escalation columns are
gone; the client sees only the agreed rate. Mention rev 0 (**HG/BOQ/26-27/0001**)
is superseded: the negotiation cut module margin from 8% to 6% and the walkway
from 420 to 380 m, and rev 1 kept every line's identity so billing continues.

**Pain it solves:** knowing your margin line by line without ever sending it to
the client; revisions without losing what was already billed.

**Don't click:** **Delete** on any BOQ; **Revise** (it opens an editor — fine to
show, but don't save a third revision mid-demo).

## 4. Product inquiry to two vendors, then the PO (2 min)

**Click:** *Product Inquiries* → **HG/DPO/0001** (SunPeak) and **HG/DPO/0002**
(BrightVolt): the same 610 TOPCon modules asked of two distributors, raised
straight from the BOQ lines. Then *Purchase Orders* → **HG/PO/26-27/0001**, the
winning inquiry converted to a priced PO. The inverter, structure and BOS POs
(**0002–0004**) were raised from the BOQ at cost; **0005** is the work order to
the installation subcontractor.

**Pain it solves:** comparing distributor quotes for the same lines, then
ordering without retyping; every rupee committed is tied to the project.

**Don't click:** *Convert* on HG/DPO/0002 (it would create a second module PO),
or *Import from Excel* buttons.

## 5. Delivery challan to site (1.5 min)

**Click:** *Delivery Challans* → the challan dated **6 Oct** (lot 3) → **Print**.
Three copies print in one run — **Original / Duplicate / Triplicate**. On the
register, three partial dispatches to Bhiwandi (5 Sep, 19 Sep, 6 Oct) and what
each carried.

**Pain it solves:** partial dispatches to site that reconcile with the BOQ — you
always know what has gone out and what is still to send.

**Don't click:** *Edit* on a challan that is already billed.

## 6. RA bill + tax invoice (2 min)

**Click:** *Running Account Bills* → **HG/RA/26-27/0002** (RA 2, supply). The
amber band says one line — the 4 sq mm DC cable — was **billed above the BOQ
quantity (4,450 m against 4,200)** and shows the reason recorded. **Print**: the
running-account bill is the tax invoice (HSN-wise GST, 5% on modules and
inverters, 18% on the rest — sample rates), with its copy labels. Also show
**HG/RA/26-27/0003** (RA 3, installation, from the joint measurement sheet).

**Pain it solves:** milestone billing straight from what was dispatched and
measured; the cumulative claim is tracked per line, and going over the BOQ needs
a written reason instead of a quiet overbill.

**Don't click:** *Merge* on the RA register (it raises a new merged tax invoice),
*Cancel*, or *Issue* on Project 2's draft RA.

## 7. Receipt with TDS (1.5 min)

**Click:** *Receipts* → **HG/RCPT/26-27/0001**: RA 1 paid net of **TDS @ 2%**,
the note says how much was deducted. **HG/RCPT/26-27/0002**: RA 2 short-paid.
Open **RA 3** again: its **previous balance** carries what RA 1 and RA 2 still
owe onto the next bill.

**Pain it solves:** chasing payments — every bill knows what is still owed,
and the next bill reminds the client in writing.

**Note honestly if asked:** TDS sits in the receipt's note and in the balance; a
dedicated TDS / retention field is on the roadmap (FEATURE_GAP 5).

**Don't click:** *New receipt* (it would change the balances you just showed).

## 8. Project page — the real margin (2 min)

**Click:** *Projects* → **Shree Ganesh Polymers — 350 kWp Rooftop**. The
**Profit & Loss** panel at the top:

- **Contract value** ≈ ₹1.04 crore (rev 1 only — rev 0 is named under the BOQ
  table as superseded and is not added in).
- **Billed to date** ≈ ₹1.02 crore (98% of contract, three issued RA bills).
- **Still owed** ≈ ₹20.9 lakh — the TDS and the short payment, with GST.
- **Planned margin** ≈ ₹8.1 lakh (7.8%) from the BOQ's base rates, against
  **actual margin to date** ≈ ₹6.5 lakh: purchase and work orders, expenses
  (transport, crane hire, safety kit) and the six workers' wages.
- A **cost-split** donut and three bars: billed vs contract, received vs billed,
  cost vs planned cost. Below it, every **RA bill** with what was received
  against it, then the BOQ, POs, expenses and the site labour.

Open **Green Valley CHS — 60 kWp** for contrast: BOQ issued, one challan, a
draft RA — nothing billed yet.

**Pain it solves:** knowing the real margin per project while the job is still
running, not at year-end — and seeing at once that cost is tracking the plan.

**Say if asked:** planned uses our BOQ cost, actual uses what was actually
ordered and paid on site; GST is left out of the margin. Signed in as
`accounts`, the labour wages are withheld and the panel says so.

**Don't click:** links into documents you have not shown yet; keep it to this page.

## 9. Labour attendance (1 min)

**Click:** *Attendance*: six site workers for October and November, booked to
Project 1, with overtime on Saturdays. *Employees* shows each worker's day rate.

**Pain it solves:** site muster and day-rate labour cost per project, not a
paper register at the gate.

**Don't click / don't promise:** **payslips** — not in this build (FEATURE_GAP 8,
deferred). Attendance import from Excel is also deferred.

---

## Avoid everywhere

- Any **Delete** button; **Users & Access** edits; **/settings Save** during the
  demo (it rebrands every document at once — do it before, below).
- *Product Catalogue* and the approvals pages: switched off in this product.
- Anything marked *deferred* in FEATURE_GAP.md: a delivery challan or product
  inquiry **without a BOQ**, item pictures, payslips, the round-off tick, the
  SITC import option, proforma / tax invoice raised from a BOQ.

## Rebrand before the demo (5 minutes)

Verified by `tests/test_solar_seed.py::test_a_rebrand_in_settings_reaches_every_printed_document`:
the new identity reaches every printed BOQ, RA bill / tax invoice, challan,
product inquiry, measurement sheet, quotation and PO, and the old one appears
on none of them.

1. Sign in as `owner` → **Settings** (foot of the rail).
2. **Company Identity:** company name, legal name, tagline, registered address,
   phone, e-mail, web, **GSTIN**, PAN, branches, **authorised signatory**,
   document prefix (1–4 letters or digits; it applies to NEW document numbers only).
3. **Bank Details:** bank name, account name, account number, IFSC, branch.
4. **Logo:** choose the prospect's PNG/JPG (re-encoded and fitted; transparent
   PNG looks best), or tick *remove*.
5. **Public Landing Page:** optional.
6. **Save Details.** Open any BOQ / RA print to check.

**Signature and stamp images:** this build has no upload for them (FEATURE_GAP,
"Preloaded signature and company stamp", deferred). The printed signature block
shows *For &lt;company&gt;* and the signatory's name from step 2.

To go back to Helios: `.\.venv\Scripts\python.exe tools\seed_demo.py --reset`.
