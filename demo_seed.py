"""
demo_seed.py — THE one seed module: a fictional sample company
================================================================
Everything a demo of this application shows comes from here: the company
identity, the public landing page, a small specification library, an address
book, one project with one priced BOQ, and the documents raised from it on
both chains. **Nothing in it is anybody's real data.** Every name is invented,
every e-mail address ends in `.example`, the GSTINs are format-valid template
patterns and the bank is "Sample Bank".

HOW IT BUILDS — through the application, never around it
--------------------------------------------------------
`build()` drives the application's OWN routes with Flask's test client, signed
in as an administrator, exactly as a person at a browser would: it GETs each
create form, keeps every field the form carries (hidden ones included), sets
the fields this dataset decides, and POSTs it back. So every invariant the
application keeps holds for the seed too — `line_id` minting, the snapshots a
document takes of its parents, the document-number series, the approval
stamps, the C1 order of working, the over-claim guard. Not one record is
written to STORE or to MySQL by this module directly.

WHO CALLS IT
------------
* `tools/seed_demo.py` — the command line. It refuses unless `QMS_DEMO_DATA`
  is on AND the database is EMPTY (`emptiness_problems()`), creates the one
  administrator, runs every stage, and prints the password once.
* `tests/conftest.py` — builds the first stages once per test session as the
  fixture world every test starts from.

No application module imports this one; `tests/test_import_directions.py`
holds that. It imports the app only inside `build()`.
"""

import datetime
import io
import json
from html.parser import HTMLParser

# =============================================================================
# THE COMPANY  (the "company" settings record — /settings, Company Identity)
# =============================================================================
COMPANY = {
    "COMPANY_NAME":      "DEMO PROJECTS",
    "COMPANY_LEGAL":     "Demo Projects Pvt Ltd",
    "COMPANY_TAGLINE":   "Civil, Electrical & Plumbing Contractors",
    "COMPANY_ADDR":      "Plot 7, Demo Business Park, Sector 19, Navi Mumbai - 400705, Maharashtra",
    "COMPANY_PHONE":     "98765 43210",
    "COMPANY_EMAIL":     "info@demoprojects.example",
    "COMPANY_WEB":       "www.demoprojects.example",
    # A format-valid template GSTIN: State 27, an all-A / all-zero PAN, and the
    # official check character — so it passes every validator in the app and
    # is still obviously not a real registration.
    "COMPANY_GSTIN":     "27AAAAA0000A1Z2",
    "COMPANY_PAN":       "AAAAA0000A",
    "COMPANY_BRANCHES":  "Navi Mumbai",
    "COMPANY_SIGNATORY": "Authorised Signatory",
    "COMPANY_SHORT":     "DP",
    "BANK_NAME":         "Sample Bank",
    "BANK_ACCOUNT_NAME": "Demo Projects Pvt Ltd",
    "BANK_ACCOUNT_NO":   "000000000000",
    "BANK_IFSC":         "SMPL0000001",
    "BANK_BRANCH":       "Navi Mumbai Main Branch",
}

# The public landing page (/settings, Public Landing Page).
LANDING = {
    "eyebrow":      "Civil, electrical & plumbing contractors",
    "hero_title":   "Fit-outs and building services, delivered to schedule.",
    "hero_text":    ("Demo Projects plans, supplies and executes civil, electrical and "
                     "plumbing works for offices, retail and residential projects."),
    "about":        ("Demo Projects is a fictional contracting company used to demonstrate "
                     "this application. Every name, number and figure on this page is invented.\n"
                     "The team takes a job from the bill of quantities through supply, "
                     "installation, measurement and billing, with one set of records the "
                     "whole way."),
    "founder":      "A. N. Example",
    "service_area": "Navi Mumbai, Mumbai and Thane",
    "hours":        "Monday to Saturday, 9 am to 7 pm",
    "services":     ("Civil works | Masonry, plaster, concrete and flooring for new and refurbished spaces.\n"
                     "Interior fit-out | Partitions, ceilings and finishes for offices and retail.\n"
                     "Electrical works | Conduit, wiring, distribution boards and lighting.\n"
                     "Plumbing works | Supply and drainage piping, sanitaryware and fittings.\n"
                     "Testing & commissioning | Every system tested and handed over with records.\n"
                     "Maintenance | Planned upkeep and repairs after handover."),
    "reasons":      ("One team | Supply, installation and billing under one contract.\n"
                     "Measured billing | Every bill is backed by a joint measurement.\n"
                     "Clear paperwork | Challans, bills and receipts that reconcile.\n"
                     "Trained crews | Supervised site teams on every job.\n"
                     "On schedule | Work planned floor by floor.\n"
                     "After handover | Maintenance when you need it."),
    "reviews":      ("R. Sample, Facilities Manager | 5 | Clear bills, every one backed by a measurement sheet.\n"
                     "P. Placeholder, Project Lead | 4 | The fit-out finished floor by floor, as planned.\n"
                     "S. Demo, Store Owner | 4.5 | Responsive team and tidy handover documents."),
}

# The administrator `tools/seed_demo.py` creates (Owner + Director).
ADMIN_USERNAME = "admin"
ADMIN_DISPLAY = "Administrator"
ADMIN_ROLES = ("role-owner", "role-director")

# =============================================================================
# THE SPECIFICATION LIBRARY  (/spec/add) — trade-neutral construction clauses
# =============================================================================
# Two clauses carried at full length — a real specification paragraph runs to
# a thousand characters and more, and the picker has to carry one intact.
TILE_CLAUSE = (
    "Supply and laying of vitrified tiles of approved make and shade, in the sizes "
    "scheduled, on a cement mortar bed of 1:4 not less than 20 mm thick over the "
    "prepared base, including cutting, chamfering and grinding of edges where "
    "required, and filling the joints with matching epoxy grout.\n"
    "The work includes setting out the pattern as per the approved drawings, "
    "maintaining the levels and slopes shown, providing expansion joints at the "
    "intervals specified, and protecting the finished surface with a plastic "
    "sheet until handover.\n"
    "Tiles shall be from a single production batch per room, checked for shade "
    "variation before laying, and stacked on site on a level surface away from "
    "traffic. Broken, chipped or shaded tiles shall be rejected and replaced at "
    "no extra cost.\n"
    "The surface shall be cleaned of all mortar and grout residue, and the "
    "contractor shall hand over 2% spare tiles of each size, boxed and labelled.\n"
    "Measurement shall be for the finished area laid, deducting openings over "
    "0.5 sqm. Skirting and nosing are measured separately."
)
CPVC_CLAUSE = (
    "Supply, installation, testing and commissioning of CPVC pipes conforming to "
    "IS 15778, SDR 11, for hot and cold water supply, with all fittings — elbows, "
    "tees, reducers, unions and adaptors — of the same make, jointed with the "
    "manufacturer's solvent cement.\n"
    "Pipes shall be run concealed in wall chases or exposed on walls and ceilings "
    "as shown on the drawings, fixed with approved clamps at the spacing the "
    "manufacturer specifies, with expansion loops or offsets on long runs.\n"
    "Chasing in masonry and making good the plaster to match the adjoining surface "
    "is included. Sleeves shall be provided where pipes cross walls and slabs.\n"
    "The complete network shall be pressure tested at 1.5 times the working "
    "pressure for not less than two hours before concealment, and the test "
    "witnessed and recorded.\n"
    "All pipes and fittings shall be delivered with the manufacturer's test "
    "certificates. Damaged, discoloured or scratched pipes shall not be used. "
    "Measurement is along the centre line of the installed pipe, fittings included."
)

# variants: (label, dimension, dim_unit, unit, supply base rate, install base rate)
SPECS = [
    {"code": "CIV-BRK-MAS", "category": "Civil", "title": "Brick masonry",
     "spec_text": "Brick masonry in cement mortar 1:6 with first-class bricks, including "
                  "scaffolding, raking of joints and curing.",
     "supply_hsn": "6901", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("115 mm", "115", "mm", "Sqm", "650", "280"),
                  ("230 mm", "230", "mm", "Sqm", "1150", "420")]},
    {"code": "CIV-PLASTER", "category": "Civil", "title": "Internal cement plaster",
     "spec_text": "Internal cement plaster in CM 1:4, finished smooth, including curing.",
     "supply_hsn": "2523", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("12 mm", "12", "mm", "Sqm", "95", "165"),
                  ("15 mm", "15", "mm", "Sqm", "115", "180")]},
    {"code": "CIV-PCC-M10", "category": "Civil", "title": "Plain cement concrete M10",
     "spec_text": "Plain cement concrete M10 for flooring base, including compaction and curing.",
     "supply_hsn": "6810", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("", "", "", "Cum", "5200", "1450")]},
    {"code": "FIN-GYP-PART", "category": "Finishes", "title": "Gypsum board partition",
     "spec_text": "Gypsum board partition on a GI stud frame, both faces finished, joints taped "
                  "and ready for paint.",
     "supply_hsn": "6809", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("75 mm", "75", "mm", "Sqm", "1450", "380"),
                  ("100 mm", "100", "mm", "Sqm", "1680", "420")]},
    # A family whose FIRST size carries no supply rate (laying only, the
    # customer supplies the tiles) — and a full specification paragraph.
    {"code": "FIN-VIT-TILE", "category": "Finishes", "title": "Vitrified tile flooring",
     "spec_text": TILE_CLAUSE,
     "supply_hsn": "6907", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("Laying only, tiles by client", "", "", "Sqm", "", "180"),
                  ("600 x 600 mm", "", "", "Sqm", "1150", "210"),
                  ("800 x 800 mm", "", "", "Sqm", "1480", "240")]},
    # Four variants whose labels run to TWO LINES — the picker has to carry a
    # newline in a label through to the page and back.
    {"code": "ELE-CONDUIT", "category": "Electrical", "title": "PVC conduit",
     "spec_text": "Supply and laying of PVC conduit with bends and accessories, concealed in "
                  "wall or ceiling.",
     "supply_hsn": "3917", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("20 mm\nmedium duty", "20", "mm", "Rmt", "48", "22"),
                  ("25 mm\nmedium duty", "25", "mm", "Rmt", "62", "26"),
                  ("32 mm\nheavy duty", "32", "mm", "Rmt", "88", "30"),
                  ("40 mm\nheavy duty", "40", "mm", "Rmt", "112", "34")]},
    {"code": "ELE-WIRE-FR", "category": "Electrical", "title": "FRLS copper wire",
     "spec_text": "FRLS PVC-insulated multi-strand copper wire, 1100 V grade, drawn through "
                  "conduit.",
     "supply_hsn": "8544", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("1.5 sq mm", "1.5", "sq mm", "Rmt", "18.5", "6"),
                  ("2.5 sq mm", "2.5", "sq mm", "Rmt", "29", "7"),
                  ("4 sq mm", "4", "sq mm", "Rmt", "46", "8.5")]},
    {"code": "ELE-DB-8W", "category": "Electrical", "title": "Distribution board, 8-way TPN",
     "spec_text": "8-way TPN distribution board with incomer and MCBs, wall mounted and "
                  "connected.",
     "supply_hsn": "8537", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("", "", "", "Nos", "14500", "1800")]},
    # Eight sizes, every one priced, and a full specification paragraph.
    {"code": "PLB-CPVC", "category": "Plumbing", "title": "CPVC pipe, SDR 11",
     "spec_text": CPVC_CLAUSE,
     "supply_hsn": "39172390", "supply_gst_rate": "18", "install_sac": "995462",
     "install_gst_rate": "18",
     "variants": [("80 mm", "80", "mm", "Rmt", "980", "320"),
                  ("65 mm", "65", "mm", "Rmt", "760", "280"),
                  ("50 mm", "50", "mm", "Rmt", "540", "240"),
                  ("40 mm", "40", "mm", "Rmt", "420", "200"),
                  ("32 mm", "32", "mm", "Rmt", "310", "160"),
                  ("25 mm", "25", "mm", "Rmt", "240", "110"),
                  ("20 mm", "20", "mm", "Rmt", "185", "95"),
                  ("15 mm", "15", "mm", "Rmt", "145", "85")]},
    {"code": "PLB-EWC", "category": "Plumbing", "title": "European water closet",
     "spec_text": "European water closet with concealed cistern, seat cover and connections.",
     "supply_hsn": "6910", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("", "", "", "Nos", "18500", "2200")]},
    {"code": "HVAC-SPLIT-AC", "category": "HVAC", "title": "Split air conditioner",
     "spec_text": "Inverter split air conditioner with copper piping up to 3 m, drain line "
                  "and stand, installed and commissioned.",
     "supply_hsn": "8415", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("1.5 TR", "1.5", "TR", "Nos", "42000", "3500"),
                  ("2 TR", "2", "TR", "Nos", "52000", "4000")]},
    {"code": "MEC-EXH-FAN", "category": "Mechanical", "title": "Exhaust fan",
     "spec_text": "Wall-mounted exhaust fan with louvre and cut-out, fixed and wired.",
     "supply_hsn": "8414", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("300 mm", "300", "mm", "Nos", "2800", "450"),
                  ("450 mm", "450", "mm", "Nos", "4200", "600")]},
    {"code": "EQP-WATER-PUMP", "category": "Equipment", "title": "Domestic water pump set",
     "spec_text": "Monoblock domestic water pump set with starter, foundation and "
                  "connections.",
     "supply_hsn": "8413", "supply_gst_rate": "18", "install_sac": "9954", "install_gst_rate": "18",
     "variants": [("1 HP", "1", "HP", "Nos", "14500", "1500"),
                  ("2 HP", "2", "HP", "Nos", "21000", "2200")]},
    {"code": "OTH-DEBRIS", "category": "Other", "title": "Debris removal and site cleaning",
     "spec_text": "Removal of construction debris from site and final cleaning before handover.",
     "supply_hsn": "", "supply_gst_rate": "18", "install_sac": "9985", "install_gst_rate": "18",
     "variants": [("", "", "", "LS", "", "8000")]},
    # A SERVICE clause: no HSN and no supply rate on any variant — the
    # quotation picker must still offer it, with an empty price box.
    {"code": "SRV-TEST-COMM", "category": "Services", "title": "Testing and commissioning",
     "spec_text": "Testing and commissioning of the installed system, with test records "
                  "handed over.",
     "supply_hsn": "", "supply_gst_rate": "18", "install_sac": "9987", "install_gst_rate": "18",
     "variants": [("", "", "", "LS", "", "15000")]},
]

# =============================================================================
# THE ADDRESS BOOK  (/address/add)
# =============================================================================
# 2 clients, 2 suppliers, 1 contractor — and the project's site, because a
# project's site is an address-book entry and never free text.
ADDRESSES = [
    {"key": "client_hq", "label": "Example Developers — Head Office", "type": "office",
     "company": "Example Developers Pvt Ltd", "contact_name": "Mr. A. Client",
     "line1": "Floor 5, Example Corporate Centre", "line2": "Sector 30A",
     "landmark": "Near Example Station",
     "city": "Navi Mumbai", "state": "Maharashtra", "pincode": "400703",
     "phone": "+91 98200 00001", "email": "accounts@exampledevelopers.example",
     "gstin": "27AAECE1111A1ZK"},
    {"key": "client_retail", "label": "Sample Retail — Billing", "type": "billing",
     "company": "Sample Retail LLP", "contact_name": "Ms. B. Buyer",
     "line1": "Shop 12, Sample Arcade", "line2": "Station Road",
     "city": "Mumbai", "state": "Maharashtra", "pincode": "400001",
     "phone": "+91 98200 00002", "email": "purchase@sampleretail.example",
     "gstin": "27AAKFS2222B1ZM"},
    {"key": "supplier_civil", "label": "Standard Building Supplies", "type": "vendor",
     "company": "Standard Building Supplies Pvt Ltd", "contact_name": "Mr. C. Supplier",
     "line1": "Gala 4, Example Industrial Estate", "line2": "Wagle Estate",
     "landmark": "Behind the Example Depot",
     "city": "Thane", "state": "Maharashtra", "pincode": "400604",
     "phone": "+91 98200 00003", "email": "sales@standardsupplies.example",
     "gstin": "27AADCS3333C1ZR"},
    {"key": "supplier_elec", "label": "Bright Electricals & Co.", "type": "vendor",
     "company": "Bright Electricals & Co.", "contact_name": "Mr. D. Dealer",
     "line1": "12 Sample Lane", "line2": "Camp",
     "city": "Pune", "state": "Maharashtra", "pincode": "411001",
     "phone": "+91 98200 00004", "email": "orders@brightelectricals.example",
     "gstin": "27AAJFB4444D1ZO"},
    {"key": "contractor", "label": "Prime Labour Contractors", "type": "vendor",
     "company": "Prime Labour Contractors", "contact_name": "Mr. E. Foreman",
     "line1": "Office 3, Example Plaza", "line2": "Sector 15",
     "city": "Navi Mumbai", "state": "Maharashtra", "pincode": "400705",
     "phone": "+91 98200 00005", "email": "office@primelabour.example",
     "gstin": "27AAQFP5555E1ZV"},
    {"key": "site", "label": "Tower B — Project Site", "type": "site",
     "company": "Example Developers Pvt Ltd", "contact_name": "Site Engineer",
     "line1": "Tower B, Example Business Park", "line2": "Plot 7, Sector 19",
     "landmark": "Opposite Example Park",
     "city": "Navi Mumbai", "state": "Maharashtra", "pincode": "400705",
     "phone": "+91 98200 00006", "email": "site.towerb@exampledevelopers.example",
     "gstin": ""},
]

PROJECT = {"name": "Office Fit-out, Tower B", "client": "Example Developers Pvt Ltd",
           "notes": "Fictional demo project — three floors of office fit-out."}

# =============================================================================
# THE BOQ — "Office Fit-out, Tower B"  (/boq/create)
# =============================================================================
BOQ_META = {
    "project_name":   "Office Fit-out, Tower B",
    "site_location":  "Tower B, Navi Mumbai",
    "date":           "2026-06-15",
    "rate_basis_label": "Site A Rates",
    "account_name":   "Example Developers Pvt Ltd",
    "contact_person": "Mr. A. Client",
    "bill_addr":      "Floor 5, Example Corporate Centre, Sector 30A",
    "bill_state":     "Maharashtra",
    "bill_city":      "Navi Mumbai",
    "bill_pin":       "400703",
    "bill_gstin":     "27AAECE1111A1ZK",
    "ship_acct_name": "Tower B — Project Site",
    "ship_addr":      "Tower B, Example Business Park, Plot 7, Sector 19",
    "ship_state":     "Maharashtra",
    "ship_city":      "Navi Mumbai",
    "ship_pin":       "400705",
    "payment_terms":  "40% Advance, 50% Against Delivery, 10% After Handover",
    "delivery_terms": "FOR Site",
    "notes":          ("GST extra as applicable. Power and water at site in the client's scope. "
                       "Scaffolding above 4 m not included."),
}

BOQ_SECTIONS = [
    {"code": "A", "title": "CIVIL WORKS", "areas": ["Ground Floor", "First Floor"]},
    {"code": "B", "title": "ELECTRICAL WORKS", "areas": ["Ground Floor"]},
    {"code": "C", "title": "PLUMBING WORKS", "areas": []},
]


def _line(section, item, desc, unit="", *, qty=None, areas=None, parent="",
          s_base=None, s_pct=None, s_rate=None, i_base=None, i_pct=None, i_rate=None,
          hsn="", sac="9954", s_gst=18, i_gst=18, header=False, remark=""):
    """One `boq_json` line, in the editor's own shape."""
    if header:
        return {"section": section, "item_no": item, "is_header": True,
                "parent_item_no": parent, "description": desc}
    li = {"section": section, "item_no": item, "parent_item_no": parent,
          "description": desc, "unit": unit, "remark": remark,
          "supply_hsn": hsn, "install_sac": sac,
          "supply_gst_rate": s_gst, "install_gst_rate": i_gst}
    if areas is not None:
        li["area_qty"] = dict(areas)
    else:
        li["total_qty"] = qty
    for key, val in (("supply_base_rate", s_base), ("supply_escalation_pct", s_pct),
                     ("supply_rate", s_rate), ("install_base_rate", i_base),
                     ("install_escalation_pct", i_pct), ("install_rate", i_rate)):
        if val is not None:
            li[key] = val
    return li


# Item numbers RESTART in every section — exactly as real schedules do — so
# item "1" exists in A, B and C, and "2" in all three. An item number is a
# label; `line_id` is the key. Rates left out of a line are DERIVED by the save
# from base x (1 + escalation %); a NEGATIVE escalation is how this schedule
# carries a discount (A item 4).
BOQ_LINES = [
    # ── A. Civil works — measured by floor ──
    _line("A", "1", "Brick masonry in cement mortar 1:6 with first-class bricks, including "
                    "scaffolding, raking of joints and curing.", header=True),
    _line("A", "1.1", "115 mm thick partition wall", "Sqm", parent="1",
          areas={"Ground Floor": 120, "First Floor": 80},
          s_base=650, s_pct=10, i_base=308, i_pct=0, hsn="6901", s_gst=12),
    _line("A", "1.2", "230 mm thick wall", "Sqm", parent="1",
          areas={"Ground Floor": 40, "First Floor": 30},
          s_base=1150, s_pct=10, i_base=462, i_pct=0, hsn="6901", s_gst=12),
    _line("A", "2", "Internal cement plaster 12 mm thick in CM 1:4, finished smooth", "Sqm",
          areas={"Ground Floor": 300, "First Floor": 220},
          s_base=95, s_pct=5, i_base=173.25, i_pct=0, hsn="2523"),
    _line("A", "3", "Plain cement concrete M10 for flooring base", "Cum",
          areas={"Ground Floor": 12.5}, s_rate=5200, i_rate=1450, hsn="6810"),
    _line("A", "4", "Gypsum board partition, 75 mm, both faces finished — 10% project discount "
                    "on supply", "Sqm",
          areas={"First Floor": 90}, s_base=1450, s_pct=-10, i_base=380, i_pct=0, hsn="6809"),
    _line("A", "5", "Vitrified tile flooring 600 x 600 mm on mortar bed", "Sqm",
          areas={"Ground Floor": 260, "First Floor": 210}, s_rate=1150, i_rate=210, hsn="6907"),
    # ── B. Electrical works ──
    _line("B", "1", "Supply and laying of PVC conduit with bends and accessories, concealed in "
                    "wall or ceiling.", header=True),
    _line("B", "1.1", "20 mm medium duty conduit", "Rmt", parent="1", areas={"Ground Floor": 600},
          s_base=48, s_pct=8, i_base=23.76, i_pct=0, hsn="3917"),
    _line("B", "1.2", "25 mm medium duty conduit", "Rmt", parent="1", areas={"Ground Floor": 350},
          s_base=62, s_pct=8, i_base=28.08, i_pct=0, hsn="3917"),
    _line("B", "2", "FRLS PVC-insulated multi-strand copper wire, 1100 V grade, drawn through "
                    "conduit.", header=True),
    _line("B", "2.1", "1.5 sq mm", "Rmt", parent="2", areas={"Ground Floor": 2400}, s_rate=18.5, i_rate=6, hsn="8544"),
    _line("B", "2.2", "2.5 sq mm", "Rmt", parent="2", areas={"Ground Floor": 1800}, s_rate=29, i_rate=7, hsn="8544"),
    _line("B", "2.3", "4 sq mm", "Rmt", parent="2", areas={"Ground Floor": 600}, s_rate=46, i_rate=8.5, hsn="8544"),
    # The agreed rate is NOT base x (1 + escalation): the remark says why, and
    # the save keeps the rate as entered rather than re-deriving it.
    _line("B", "3", "8-way TPN distribution board with incomer and MCBs", "Nos", areas={"Ground Floor": 6},
          s_base=12500, s_pct=0, s_rate=14500, i_rate=1800, hsn="8537",
          remark="Includes 2,000/nos extra for the incomer MCCB"),
    _line("B", "4", "LED panel light 2 x 2 ft, 36 W, recessed", "Nos", areas={"Ground Floor": 64},
          s_rate=2350, i_rate=250, hsn="9405"),
    # ── C. Plumbing works ──
    # The header carries the library's full clause, as a real schedule carries
    # the specification paragraph: over 1,000 characters, four paragraphs.
    _line("C", "1", CPVC_CLAUSE, header=True),
    _line("C", "1.1", "15 mm CPVC pipe", "Rmt", parent="1", qty=180,
          s_base=145, s_pct=5, i_base=89.25, i_pct=0, hsn="3917"),
    _line("C", "1.2", "20 mm CPVC pipe", "Rmt", parent="1", qty=120,
          s_base=185, s_pct=5, i_base=99.75, i_pct=0, hsn="3917"),
    _line("C", "2", "European water closet with concealed cistern", "Nos", qty=8,
          s_rate=18500, i_rate=2200, hsn="6910"),
    # ⚠ Item "3" TWICE in one section — exactly as it stands on the customer's
    #   sheet. A label, not a key: `line_id` tells the two apart. /boq/view
    #   shows an amber note about it and blocks nothing.
    _line("C", "3", "Kitchen sink with sink mixer", "Nos", qty=2,
          s_rate=9200, i_rate=1200, hsn="7324"),
    _line("C", "3", "Wash basin with pillar cock and bottle trap", "Nos", qty=10,
          s_rate=6400, i_rate=950, hsn="6910"),
    _line("C", "4", "Testing and commissioning of the plumbing system", "LS", qty=1,
          i_rate=15000, hsn="", sac="9987"),
    # NIL-PRICED: a quantity and no rate on either track — priced inside C 2,
    # which is a valid state, not an error.
    _line("C", "5", "Shifting of existing sanitaryware — rate included in item 2", "LS",
          qty=1, hsn="", sac="9954"),
]

# =============================================================================
# THE DOCUMENTS RAISED FROM IT — keyed (section, item_no), the human handle
# =============================================================================
# Challan 1 is billed (RA supply 1 is raised FROM it and issued); challan 2 is
# not billed yet.
DC1 = {"date": "2026-07-20", "dispatch_mode": "Transport", "notes": "First dispatch to site",
       "lines": {("A", "1.1"): 200, ("A", "1.2"): 70, ("B", "1.1"): 300, ("B", "2.1"): 1200,
                 ("C", "1.1"): 90}}
DC2 = {"date": "2026-09-25", "dispatch_mode": "Transport", "notes": "Second dispatch to site",
       "lines": {("A", "5"): 200, ("B", "3"): 6, ("B", "4"): 32, ("C", "2"): 8}}
# The joint measurement — installation measured so far.
MEASUREMENT = {"date": "2026-09-20", "measured_by": "Site Engineer, Demo Projects",
               "witnessed_by": "Mr. A. Client", "notes": "Joint measurement — ground floor",
               "system": "Civil and electrical works", "material": "As per BOQ",
               "area": "Ground Floor",
               "lines": {("A", "1.1"): 120, ("A", "1.2"): 40, ("A", "2"): 300, ("A", "3"): 12.5,
                         ("B", "1.1"): 300, ("B", "2.1"): 1200, ("C", "1.1"): 60}}
RA_SUPPLY = {"date": "2026-08-05", "notes": "RA 1 — supply against challan 1"}
RA_INSTALL = {"date": "2026-10-01", "notes": "RA 1 — installation, ground floor (draft)"}
RECEIPT = {"date": "2026-09-10", "mode": "neft", "instrument_ref": "NEFT-DEMO-0001",
           "notes": "Part payment against RA 1 (supply)", "fraction": 0.5}
PO_DRAFT = {"date": "2026-06-25", "vendor": "supplier_civil",
            "delivery_to": "Tower B — Project Site",
            "notes": "Please quote your best rates for the civil materials below.",
            "lines": {("A", "1.1"): 200, ("A", "1.2"): 70, ("A", "5"): 470}}
PO = {"date": "2026-07-02", "vendor": "supplier_elec", "status": "Issued",
      "vendor_ref": "BE/Q/0412", "notes": "Electrical materials for Tower B.",
      "lines": {("B", "1.1"): 600, ("B", "1.2"): 350, ("B", "2.1"): 2400, ("B", "2.2"): 1800}}
WORK_ORDER = {"date": "2026-07-05", "vendor": "contractor", "status": "Issued",
              "vendor_ref": "WO-TOWERB-01",
              "notes": "WORK ORDER — installation labour for Tower B, civil and plumbing.",
              "extras": [("Labour — brick masonry and plaster (civil)", "9954", "Sqm", 790, 120),
                         ("Labour — CPVC piping and sanitaryware", "9954", "LS", 1, 45000)]}
CHARGES = [
    {"date": "2026-07-03", "person": "Site Engineer", "head": "Travel",
     "description": "Site visits, Tower B (July)", "taxable_amount": "2400", "gst_rate": "0"},
    {"date": "2026-07-18", "person": "Site Supervisor", "head": "Food & Meals",
     "description": "Crew meals during slab work", "taxable_amount": "3150", "gst_rate": "5"},
    {"date": "2026-08-02", "person": "Store Keeper", "head": "Consumables",
     "description": "Cutting discs, sealant and fixings", "taxable_amount": "4870", "gst_rate": "18"},
    {"date": "2026-08-21", "person": "Site Engineer", "head": "Transport / Freight",
     "description": "Tempo hire for second dispatch", "taxable_amount": "6500", "gst_rate": "12"},
    {"date": "2026-09-12", "person": "Site Supervisor", "head": "Site Expenses",
     "description": "Temporary lighting and barricading", "taxable_amount": "3900", "gst_rate": "18"},
]
EMPLOYEES = [
    {"name": "R. Example", "code": "EMP-001", "designation": "Site Supervisor", "day_rate": "1200"},
    {"name": "S. Sample", "code": "EMP-002", "designation": "Electrician", "day_rate": "900"},
    {"name": "T. Placeholder", "code": "EMP-003", "designation": "Plumber", "day_rate": "850"},
]
ATTENDANCE_DATES = ("2026-10-12", "2026-10-13", "2026-10-14")

# The sell chain: quotation -> proforma -> tax invoice, written from the spec
# library (Supply only) for the second client.
QUOTATION = {"qtn_date": "2026-09-01", "buyer_ref": "SR/RFQ/0007",
             "other_ref": "Store refurbishment — electrical supply",
             "account": "client_retail",
             "picks": [("ELE-DB-8W", 0, 2, None), ("ELE-WIRE-FR", 1, 500, None),
                       ("ELE-CONDUIT", 0, 300, None)]}
PROFORMA = {"date": "2026-09-08", "po_number": "SR/PO/0042", "po_date": "2026-09-05",
            "notes": "Proforma against your PO SR/PO/0042."}
INVOICE = {"date": "2026-09-15", "dispatch_through": "By Road Transport",
           "dispatch_doc_no": "LR-DEMO-0101", "vehicle_no": "MH43XX0000",
           "notes": "Supplied against PO SR/PO/0042."}

STAGES = ("settings", "masters", "boq", "chain", "sell", "people")
# What the test suite starts every test from: identity, library, book, project
# and the schedule — the documents downstream of it are each test's own.
TEST_BASELINE = ("settings", "masters", "boq")

# Collections that must be empty before a seed may run, and the two that may
# not be: the builtin roles (the application writes them itself) and the
# settings records the application seeds as GENUINE defaults.
GENUINE_SETTINGS = {"charge_heads"}


def emptiness_problems(store) -> list:
    """
    Why this store is NOT an empty database, one sentence per reason — `[]`
    when the seed may run. Roles and the genuine-default settings records do
    not count: the application writes those itself on its first boot.
    """
    import db
    problems = []
    for coll in db.COLLECTIONS:
        rows = store.get(coll) or {}
        if coll == "roles":
            continue
        if coll == "settings":
            extra = sorted(k for k in rows if k not in GENUINE_SETTINGS)
            if extra:
                problems.append(f"settings already holds {', '.join(extra)}")
            continue
        if rows:
            problems.append(f"{coll} holds {len(rows)} record(s)")
    return problems


# =============================================================================
# THE DRIVER — a browser's view of the application, in-process
# =============================================================================

class _Forms(HTMLParser):
    """Every `<form>` on a page with all its named controls — a browser's view:
    a select gives its selected (or first) option, an unchecked box gives
    nothing, a textarea gives its text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms, self._f, self._sel, self._opt, self._ta = [], None, None, None, None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if tag == "form":
            self._f = {"action": a.get("action", ""), "fields": []}
        elif self._f is None:
            return
        elif tag == "input" and a.get("name"):
            t = (a.get("type") or "text").lower()
            if t in ("submit", "button", "image", "reset", "file"):
                return
            if t in ("checkbox", "radio") and "checked" not in a:
                return
            self._f["fields"].append((a["name"], a.get("value", "")))
        elif tag == "select":
            self._sel = {"name": a.get("name"), "value": None, "first": None}
        elif tag == "option" and self._sel is not None:
            self._opt = {"value": a.get("value"), "selected": "selected" in a, "text": ""}
        elif tag == "textarea":
            self._ta = {"name": a.get("name"), "text": ""}

    def handle_data(self, data):
        if self._opt is not None:
            self._opt["text"] += data
        elif self._ta is not None:
            self._ta["text"] += data

    def handle_endtag(self, tag):
        if tag == "form" and self._f is not None:
            self.forms.append(self._f)
            self._f = None
        elif tag == "option" and self._opt is not None and self._sel is not None:
            val = self._opt["value"] if self._opt["value"] is not None else self._opt["text"].strip()
            if self._sel["first"] is None:
                self._sel["first"] = val
            if self._opt["selected"]:
                self._sel["value"] = val
            self._opt = None
        elif tag == "select" and self._sel is not None:
            if self._f is not None and self._sel["name"]:
                v = self._sel["value"]
                self._f["fields"].append((self._sel["name"], self._sel["first"] if v is None else v))
            self._sel = None
        elif tag == "textarea" and self._ta is not None:
            if self._f is not None and self._ta["name"]:
                self._f["fields"].append((self._ta["name"], self._ta["text"]))
            self._ta = None


class SeedError(RuntimeError):
    """A route refused what the seed posted — the message says which and why."""


class _Driver:
    def __init__(self, client, store):
        self.c = client
        self.store = store

    def form(self, url: str, contains: str) -> dict:
        r = self.c.get(url)
        if r.status_code != 200:
            raise SeedError(f"GET {url} answered {r.status_code} {r.headers.get('Location', '')}")
        p = _Forms()
        p.feed(r.get_data(as_text=True))
        for f in p.forms:
            if any(n == contains for n, _ in f["fields"]):
                return f
        raise SeedError(f"GET {url}: no form carries a {contains!r} field")

    def submit(self, url: str, contains: str, overrides: dict, collection: str,
               files: dict = None, drop: tuple = ()) -> str:
        """GET the form, post its own fields with `overrides`, return the ONE new
        record's id in `collection` — or raise with the page's own error."""
        from werkzeug.datastructures import MultiDict
        f = self.form(url, contains)
        over = dict(overrides)
        done = set()
        data = MultiDict()
        for name, value in f["fields"]:
            if name in drop or name in done:
                continue
            if name in over:
                # An override replaces EVERY occurrence of a repeated field
                # (variant rows, PO lines) with its own list, in order.
                v = over.pop(name)
                for item in (v if isinstance(v, list) else [v]):
                    data.add(name, item)
                done.add(name)
            else:
                data.add(name, value)
        for name, v in over.items():
            for item in (v if isinstance(v, list) else [v]):
                data.add(name, item)
        for name, fobj in (files or {}).items():
            data.add(name, fobj)
        before = set((self.store.get(collection) or {}).keys())
        r = self.c.post(f["action"] or url, data=data,
                        content_type="multipart/form-data" if files else None)
        new = [k for k in (self.store.get(collection) or {}) if k not in before]
        if len(new) != 1:
            body = r.get_data(as_text=True)
            raise SeedError(f"POST {url} created {len(new)} record(s) in {collection} "
                            f"(status {r.status_code}): {_error_of(body)}")
        return new[0]

    def post(self, url: str, data=None):
        r = self.c.post(url, data=data or {})
        if r.status_code not in (200, 302):
            raise SeedError(f"POST {url} answered {r.status_code}")
        return r





def _error_of(html: str) -> str:
    """The first error band on a page, as text — what a person would read."""
    import re
    m = re.search(r'class="alert alert-error"[^>]*>(.*?)</div>', html, re.S)
    text = m.group(1) if m else html[:300]
    return re.sub(r"<[^>]+>", " ", text).replace("&#10007;", "").strip()[:300]


def _pdf(title: str) -> bytes:
    """A tiny but REAL one-page PDF — attachment.py sniffs the leading bytes."""
    body = (f"BT /F1 12 Tf 72 720 Td ({title}) Tj ET").encode("latin-1", "replace")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length " + str(len(body)).encode() + b" >>\nstream\n" + body + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, o in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + o + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


# =============================================================================
# THE STAGES
# =============================================================================

def _stage_settings(d: _Driver, ids: dict) -> None:
    over = dict(COMPANY)
    over.update({f"landing_{k}": v for k, v in LANDING.items()})
    # /settings/ edits a singleton, so there is no NEW record to find — post it
    # and check the identity took.
    f = d.form("/settings/", "COMPANY_NAME")
    from werkzeug.datastructures import MultiDict
    data = MultiDict()
    for name, value in f["fields"]:
        data.add(name, over.pop(name) if name in over else value)
    for name, value in over.items():
        data.add(name, value)
    r = d.c.post(f["action"] or "/settings/", data=data)
    company = (d.store.get("settings") or {}).get("company") or {}
    if r.status_code != 302 or company.get("COMPANY_NAME") != COMPANY["COMPANY_NAME"]:
        raise SeedError(f"/settings/ did not save: {_error_of(r.get_data(as_text=True))}")


def _stage_masters(d: _Driver, ids: dict) -> None:
    ids["specs"] = {}
    for s in SPECS:
        over = {k: s[k] for k in ("code", "category", "title", "spec_text", "supply_hsn",
                                  "supply_gst_rate", "install_sac", "install_gst_rate")}
        cols = list(zip(*s["variants"]))
        for name, values in zip(("var_label", "var_dimension", "var_dim_unit",
                                 "var_unit", "var_supply", "var_install"), cols):
            over[name] = list(values)
        ids["specs"][s["code"]] = d.submit("/spec/add", "code", over, "specs")

    ids["addresses"] = {}
    for a in ADDRESSES:
        over = {k: v for k, v in a.items() if k != "key"}
        ids["addresses"][a["key"]] = d.submit("/address/add", "label", over, "addresses")

    ids["project"] = d.submit("/projects/create", "name", {
        **PROJECT, "site_address_id": ids["addresses"]["site"]}, "projects")


def _stage_boq(d: _Driver, ids: dict) -> None:
    payload = json.dumps({"sections": BOQ_SECTIONS, "lines": BOQ_LINES})
    url = f"/boq/create?project_id={ids['project']}"
    ids["boq"] = d.submit(url, "boq_json", {
        **BOQ_META, "boq_json": payload, "rev_no": "0", "supersedes": "",
        "project_id": ids["project"]}, "boqs")
    boq = d.store["boqs"][ids["boq"]]
    ids["lines"] = {(li["section"], li["item_no"]): li["line_id"]
                    for li in boq["line_items"] if not li.get("is_header")}


def _rows(ids: dict, qty_by_key: dict, track: str = "") -> list:
    boq = ids["_boq"]
    by_id = {li["line_id"]: li for li in boq["line_items"]}
    out = []
    for key, qty in qty_by_key.items():
        lid = ids["lines"][key]
        row = {"line_id": lid, "qty": qty}
        if track:
            row["rate"] = by_id[lid][f"{track}_rate"]
        out.append(row)
    return out


def _stage_chain(d: _Driver, ids: dict) -> None:
    bid = ids["boq"]
    ids["_boq"] = d.store["boqs"][bid]

    # The joint measurement — the installation ceiling.
    ids["measurement"] = d.submit(f"/measurement/create?boq={bid}", "ms_json", {
        "ms_json": json.dumps({"lines": _rows(ids, MEASUREMENT["lines"])}),
        **{k: v for k, v in MEASUREMENT.items() if k != "lines"},
        "counterparty_name": BOQ_META["account_name"]}, "measurements")

    # Two challans.
    ids["dc"] = []
    for dc in (DC1, DC2):
        ids["dc"].append(d.submit(f"/dc/create?boq={bid}", "dc_json", {
            "dc_json": json.dumps({"lines": _rows(ids, dc["lines"])}),
            "date": dc["date"], "dispatch_mode": dc["dispatch_mode"], "notes": dc["notes"],
            "consignee_name": COMPANY["COMPANY_LEGAL"],
            "dispatch_to": "Tower B, Example Business Park, Navi Mumbai"},
            "delivery_challans"))

    # RA supply 1, raised FROM challan 1 (which marks challan 1 billed), issued.
    dc1 = ids["dc"][0]
    ids["ra_supply"] = d.submit(f"/ra/create?boq={bid}&leg=supply&dc={dc1}", "ra_json", {
        "ra_json": json.dumps({"lines": _rows(ids, DC1["lines"], "supply")}),
        "date": RA_SUPPLY["date"], "notes": RA_SUPPLY["notes"]}, "ra_bills")
    d.post(f"/ra/issue/{ids['ra_supply']}")
    if d.store["ra_bills"][ids["ra_supply"]].get("status") != "issued":
        raise SeedError("RA supply 1 did not issue")

    # RA installation 1, raised FROM the measurement — left a draft.
    ms = ids["measurement"]
    ids["ra_install"] = d.submit(f"/ra/create?ms={ms}", "ra_json", {
        "ra_json": json.dumps({"lines": _rows(ids, MEASUREMENT["lines"], "install")}),
        "date": RA_INSTALL["date"], "notes": RA_INSTALL["notes"]}, "ra_bills")

    # A receipt for half of the issued bill.
    bill = d.store["ra_bills"][ids["ra_supply"]]
    gross = float(bill.get("grand_total") or bill.get("net_payable") or 0.0)
    amount = round(gross * RECEIPT["fraction"], 2)
    ids["receipt"] = d.submit(f"/receipt/new?ra={ids['ra_supply']}", "amount", {
        "amount": f"{amount:.2f}", "date": RECEIPT["date"], "mode": RECEIPT["mode"],
        "instrument_ref": RECEIPT["instrument_ref"], "notes": RECEIPT["notes"]}, "receipts")

    # A draft PO (rates left to the supplier).
    v = ids["addresses"][PO_DRAFT["vendor"]]
    ids["po_draft"] = d.submit(f"/po/create?boq={bid}", "po_json", {
        "po_json": json.dumps({"lines": _rows(ids, PO_DRAFT["lines"])}),
        "vendor_id": v, "date": PO_DRAFT["date"], "delivery_to": PO_DRAFT["delivery_to"],
        "notes": PO_DRAFT["notes"]}, "purchase_orders")

    # A purchase order raised from the BOQ, priced, issued.
    v = ids["addresses"][PO["vendor"]]
    ids["po"] = d.submit(f"/purchase/from-boq/{bid}", "po_json", {
        "po_json": json.dumps({"lines": _rows(ids, PO["lines"], "supply")}),
        "vendor_id": v, "date": PO["date"], "status": PO["status"],
        "vendor_ref": PO["vendor_ref"], "notes": PO["notes"],
        "project_id": ids["project"]}, "purchases")

    # A WORK ORDER — this application has no separate work-order document, so
    # it is a purchase order on the contractor for labour, said so in its notes.
    v = ids["addresses"][WORK_ORDER["vendor"]]
    ex = WORK_ORDER["extras"]
    ids["work_order"] = d.submit("/purchase/create", "vendor_id", {
        "vendor_id": v, "date": WORK_ORDER["date"], "status": WORK_ORDER["status"],
        "vendor_ref": WORK_ORDER["vendor_ref"], "notes": WORK_ORDER["notes"],
        "project_id": ids["project"],
        "extra_desc": [e[0] for e in ex] + [""], "extra_hsn": [e[1] for e in ex] + [""],
        "extra_unit": [e[2] for e in ex] + [""], "extra_qty": [str(e[3]) for e in ex] + [""],
        "extra_rate": [str(e[4]) for e in ex] + [""], "extra_discount": ["", "", ""]},
        "purchases")

    # Charges — every one carries its bill, because a charge must.
    ids["charges"] = []
    for i, ch in enumerate(CHARGES, start=1):
        ids["charges"].append(d.submit("/charge/new", "head", {
            **ch, "project_id": ids["project"]}, "charges",
            files={"attachment": (io.BytesIO(_pdf(f"Demo bill {i}")),
                                  f"demo-bill-{i}.pdf", "application/pdf")}))


def _stage_sell(d: _Driver, ids: dict) -> None:
    a = next(x for x in ADDRESSES if x["key"] == QUOTATION["account"])
    picks = []
    for code, vidx, qty, price in QUOTATION["picks"]:
        sid = ids["specs"][code]
        spec = d.store["specs"][sid]
        rate = price if price is not None else spec["variants"][vidx]["default_supply_base_rate"]
        picks.append({"sid": sid, "vidx": vidx, "qty": qty, "price": rate, "show_price": True})
    ids["quotation"] = d.submit("/quotation/create", "selections_json", {
        "selections_json": json.dumps(picks), "qtn_date": QUOTATION["qtn_date"],
        "qtn_type": "Supply Only", "buyer_ref": QUOTATION["buyer_ref"],
        "other_ref": QUOTATION["other_ref"], "company_branch": COMPANY["COMPANY_NAME"],
        "auth_signatory": "Authorised Signatory", "lead_owner": "Sales",
        "assigned_to": "Sales", "account_name": a["company"],
        "contact_person": a["contact_name"],
        "bill_addr": f"{a['line1']}, {a['line2']}", "bill_state": a["state"],
        "bill_city": a["city"], "bill_pin": a["pincode"], "bill_phone": a["phone"],
        "bill_gstin": a["gstin"], "ship_type": "same"}, "quotations")
    ids["proforma"] = d.submit(f"/proforma/from/{ids['quotation']}", "date", {
        "date": PROFORMA["date"], "po_number": PROFORMA["po_number"],
        "po_date": PROFORMA["po_date"], "notes": PROFORMA["notes"]}, "proformas")
    ids["invoice"] = d.submit(f"/invoice/from/{ids['proforma']}", "date", {
        "date": INVOICE["date"], "po_number": PROFORMA["po_number"],
        "po_date": PROFORMA["po_date"], "dispatch_through": INVOICE["dispatch_through"],
        "dispatch_doc_no": INVOICE["dispatch_doc_no"], "vehicle_no": INVOICE["vehicle_no"],
        "notes": INVOICE["notes"]}, "invoices")


def _stage_people(d: _Driver, ids: dict) -> None:
    ids["employees"] = []
    site = ids["addresses"]["site"]
    for e in EMPLOYEES:
        ids["employees"].append(d.submit("/employee/new", "name", {
            **e, "site_id": site, "date_joined": "2026-06-01", "active": "1"}, "employees"))
    ids["attendance"] = []
    for day in ATTENDANCE_DATES:
        for n, eid in enumerate(ids["employees"]):
            present = not (day == ATTENDANCE_DATES[-1] and n == 2)   # one absentee
            over = {"date": day, "employee_id": eid, "site_id": site,
                    "project_id": ids["project"],
                    "status": "present" if present else "absent",
                    "hours": "8" if present else "0", "ot_hours": "1" if n == 0 and present else "0"}
            ids["attendance"].append(d.submit("/attendance/mark", "employee_id", over,
                                              "attendance"))


_STAGE_FUNCS = {"settings": _stage_settings, "masters": _stage_masters, "boq": _stage_boq,
                "chain": _stage_chain, "sell": _stage_sell, "people": _stage_people}


def build(client, store, stages=STAGES) -> dict:
    """
    Run `stages` in order through `client` — a Flask test client ALREADY
    signed in as an administrator — and return the ids it created, keyed by
    role. Raises `SeedError` the moment a route refuses, naming the route and
    quoting the page's own error band.
    """
    ids = {}
    d = _Driver(client, store)
    order = [s for s in STAGES if s in stages]
    for name in order:
        _STAGE_FUNCS[name](d, ids)
    ids.pop("_boq", None)
    return ids


def find_boq_id(store) -> str:
    """The id of the seeded BOQ (revision 0 of "Office Fit-out, Tower B")."""
    for bid, b in (store.get("boqs") or {}).items():
        if b.get("project_name") == BOQ_META["project_name"] and not int(b.get("rev_no") or 0):
            return bid
    return ""


def line_id(store, section: str, item_no: str, boq_id: str = "") -> str:
    """The `line_id` of one seeded line — `(section, item_no)` is how a person
    names it; the id is what everything keys on."""
    boq = (store.get("boqs") or {}).get(boq_id or find_boq_id(store)) or {}
    for li in boq.get("line_items") or []:
        if li.get("section") == section and li.get("item_no") == item_no:
            return li.get("line_id", "")
    return ""


def today() -> str:
    return datetime.date.today().isoformat()
