"""
solar_seed.py — DEMO BRANCH ONLY: a fictional rooftop & industrial solar EPC
============================================================================
"Helios Grid Energy Pvt Ltd" — **demo data, every name and number invented** —
an office in Thane, two projects and one lead, built through the application's
OWN routes exactly the way `demo_seed.py` builds the generic demo (it reuses
that module's form driver). Nothing here is written to STORE or MySQL
directly: every record is the answer to a form a person could have posted, so
every invariant holds — `line_id` minting, document snapshots, the number
series, the C1 order of working, the over-claim guard.

This module lives on the `demo/solar-epc` branch and nowhere else. `main`
keeps `demo_seed.py` (the test suite's fixture world) untouched.

The story (dates August to November 2026)
-----------------------------------------
PROJECT 1 — Shree Ganesh Polymers, 350 kWp industrial rooftop, Bhiwandi.
  budgetary quotation (spec library) → BOQ rev 0 with the price-summary cover →
  rev 1 after negotiation → product inquiry to two module distributors → the
  winner converted to a PO → inverter and BOS POs from the BOQ → a work order
  to the installation subcontractor → three partial challans → RA1 supply
  (challan 1) → RA2 supply (challans 2 + 3, one cable line billed above the
  BOQ quantity with a reason) → joint measurement → RA3 installation →
  receipts (one net of TDS, one short) → misc charges → six site workers'
  attendance for October and November.
PROJECT 2 — Green Valley CHS, 60 kWp housing society, Panvel: BOQ issued, one
  challan, one RA.
LEAD — Konkan Cold Storage LLP, Vasai: a quotation that never converted.

Rates are plausible 2026 Indian market figures for a demo, nothing more. HSN /
SAC codes and GST rates are editable SAMPLE values, not tax advice.
"""

import io
import json

import demo_seed as DS

DEMO_DB_NAME = "qms_demo"

# =============================================================================
# THE COMPANY
# =============================================================================
COMPANY = {
    "COMPANY_NAME":      "HELIOS GRID ENERGY",
    "COMPANY_LEGAL":     "Helios Grid Energy Pvt Ltd",
    "COMPANY_TAGLINE":   "Rooftop & Industrial Solar EPC · demo data",
    "COMPANY_ADDR":      ("Office 504, Lakeview Business Centre, Ghodbunder Road, "
                          "Thane (W) - 400607, Maharashtra"),
    "COMPANY_PHONE":     "+91 22 4000 0000",
    "COMPANY_EMAIL":     "projects@heliosgrid.example",
    "COMPANY_WEB":       "www.heliosgrid.example",
    # Format-valid with the correct check character, all-zero serial: passes
    # every validator and is obviously not a real registration.
    "COMPANY_GSTIN":     "27AAACH0000H1ZD",
    "COMPANY_PAN":       "AAACH0000H",
    "COMPANY_BRANCHES":  "Thane",
    "COMPANY_SIGNATORY": "Authorised Signatory",
    "COMPANY_SHORT":     "HG",
    "BANK_NAME":         "Demo Bank",
    "BANK_ACCOUNT_NAME": "Helios Grid Energy Pvt Ltd",
    "BANK_ACCOUNT_NO":   "000000000000",
    "BANK_IFSC":         "DEMO0000001",
    "BANK_BRANCH":       "Thane West Branch",
}

LANDING = {
    "eyebrow":      "Rooftop & industrial solar EPC",
    "hero_title":   "Solar plants engineered, installed and net-metered.",
    "hero_text":    ("Helios Grid Energy designs, supplies and commissions rooftop and "
                     "industrial solar PV plants across Thane, Mumbai and Navi Mumbai."),
    "about":        ("Helios Grid Energy is a FICTIONAL solar EPC company used to demonstrate "
                     "this application. Every name, number and figure on this page is invented.\n"
                     "The team takes a plant from the bill of quantities through procurement, "
                     "dispatch, installation, measurement, billing and net metering."),
    "founder":      "A. Demo Founder",
    "service_area": "Thane, Bhiwandi, Mumbai, Navi Mumbai and Palghar",
    "hours":        "Monday to Saturday, 9:30 am to 6:30 pm",
    "services":     ("Industrial rooftop | 100 kWp to 1 MWp plants on RCC and metal-sheet roofs.\n"
                     "Housing societies | Common-area solar with DISCOM net metering.\n"
                     "Design & engineering | Shadow analysis, SLD and structure design.\n"
                     "Net-metering liaisoning | Application to commissioning with the DISCOM.\n"
                     "O&M | Cleaning, monitoring and preventive maintenance.\n"
                     "Monitoring | Remote generation monitoring with monthly reports."),
    "reasons":      ("Per-kWp clarity | Every quote broken down section by section.\n"
                     "Tier-1 makes | Modules and inverters from established brands.\n"
                     "Measured billing | Bills follow dispatches and joint measurement.\n"
                     "Trained crews | Supervised installation teams on every site.\n"
                     "Net metering handled | We file, follow up and commission.\n"
                     "After handover | Generation monitored remotely."),
    "reviews":      ("Plant Head, a polymer unit | 5 | Clear milestone bills and a plant on schedule.\n"
                     "Secretary, a housing society | 4.5 | Net metering was handled end to end.\n"
                     "Owner, a cold-storage unit | 4 | Detailed offer with per-kWp comparison."),
}

# One login per built-in role. DEMO passwords, listed in RUN_LOCAL.md — for a
# local demo database only, never a server anyone else can reach.
USERS = [
    ("owner",      "Arjun Desai",     "role-owner",            "Helios-Owner-26"),
    ("director",   "Kavita Rao",      "role-director",         "Helios-Director-26"),
    ("operations", "Rohit Patil",     "role-operation-head",   "Helios-Ops-26"),
    ("hr",         "Neha Joshi",      "role-hr",               "Helios-HR-26"),
    ("sales",      "Vikram Shah",     "role-sales-manager",    "Helios-Sales-26"),
    ("purchase",   "Sameer Kulkarni", "role-purchase-manager", "Helios-Purchase-26"),
    ("accounts",   "Pooja Iyer",      "role-accountant",       "Helios-Accounts-26"),
]

# =============================================================================
# THE TERMS LIBRARY (/settings/terms) — fictional, generic solar EPC terms
# =============================================================================
TERMS = [
    # (category, text, on by default)
    ("Payment", "30% advance with the purchase order; 60% against delivery of material to "
                "site, pro rata; 10% on commissioning.", True),
    ("Commercial", "This offer is valid for 15 days, as module prices are revised fortnightly.", True),
    ("Commercial", "Module wattage may vary by ±5 Wp at dispatch; the difference is adjusted "
                   "at the quoted per-Wp rate.", True),
    ("Scope", "Net-metering liaisoning with the DISCOM is in our scope; DISCOM fees and "
              "meter testing charges are payable by the client at actuals.", True),
    ("Site", "Clear roof access, a lockable store, construction power and water at site "
             "are in the client's scope.", True),
    ("Exclusions", "Roof structural stability certificate, civil strengthening and roof "
                   "waterproofing are excluded.", True),
    ("Warranty", "Module product warranty 12 years and linear performance warranty 30 years; "
                 "inverter warranty 5 years — as per manufacturer.", True),
    ("Warranty", "Workmanship warranty 5 years from the date of commissioning.", True),
    ("Delivery", "Material within 4 to 6 weeks of advance; installation and commissioning "
                 "within 3 weeks of complete material at site.", True),
    ("Taxes", "GST extra as applicable at the rates in force on the date of invoice.", True),
    ("Legal", "Subject to Thane jurisdiction.", False),
    ("Exclusions", "Generation guarantee is not part of this offer unless agreed separately "
                   "in writing.", False),
]

# =============================================================================
# THE SPECIFICATION LIBRARY (/spec/add)
# =============================================================================
# HSN / SAC and GST rates are SAMPLE values for a demo — not tax advice.
# The library's categories are a fixed product list (`spec.CATEGORIES`) with no
# solar entry, so: modules, inverters and BOS are "Electrical", the structure
# and walkway "Mechanical", commissioning and liaisoning "Services".
# Variant tuple: (label, dimension, dim_unit, unit, supply rate, install rate)
def _spec(code, title, text, hsn, gst, variants, sac="9954", igst=18, category="Electrical"):
    return {"code": code, "category": category, "title": title, "spec_text": text,
            "supply_hsn": hsn, "supply_gst_rate": str(gst), "install_sac": sac,
            "install_gst_rate": str(igst), "variants": variants}


SPECS = [
    _spec("SOL-MOD-PERC", "Mono PERC half-cut module",
          "Mono PERC half-cut solar PV module, 144 cells, IEC 61215 / 61730, BIS listed. "
          "Make: Waaree / Adani / Vikram or equivalent.", "8541", 5,
          [("545 Wp", "545", "Wp", "Nos", "9100", "350"),
           ("550 Wp DCR", "550", "Wp", "Nos", "13750", "350")]),
    _spec("SOL-MOD-TOPCON", "TOPCon bifacial module",
          "N-type TOPCon bifacial dual-glass module, IEC 61215 / 61730, BIS listed. "
          "Make: Waaree / Adani / Premier or equivalent.", "8541", 5,
          [("575 Wp", "575", "Wp", "Nos", "10050", "380"),
           ("590 Wp", "590", "Wp", "Nos", "10300", "380")]),
    _spec("SOL-INV-STR", "String inverter, three-phase",
          "Grid-tie string inverter, three-phase, IP66, with built-in monitoring. "
          "Make: Sungrow / Growatt / Solis or equivalent.", "8504", 5,
          [("10 kW", "10", "kW", "Nos", "52000", "3000"),
           ("50 kW", "50", "kW", "Nos", "151800", "5500"),
           ("100 kW", "100", "kW", "Nos", "269500", "7500")]),
    _spec("SOL-MMS-HDG", "Module mounting structure, hot-dip galvanised",
          "Hot-dip galvanised MS module mounting structure (80 micron), designed for 150 km/h "
          "wind, with SS fasteners. Make: fabricated to our design.", "7308", 18,
          [("RCC roof", "", "", "kWp", "3600", "520"),
           ("Metal-sheet roof, rail & clamp", "", "", "kWp", "2900", "450")], category="Mechanical"),
    _spec("SOL-DC-CABLE", "Solar DC cable, 1C copper",
          "Single-core tinned copper solar DC cable, EN 50618, 1.5 kV DC. "
          "Make: Polycab / KEI or equivalent.", "8544", 18,
          [("4 sq mm", "4", "sq mm", "Mtr", "64", "14"),
           ("6 sq mm", "6", "sq mm", "Mtr", "90", "15")]),
    _spec("SOL-AC-CABLE", "AC cable, aluminium armoured",
          "3.5-core aluminium XLPE armoured cable, 1.1 kV. Make: Polycab / KEI or equivalent.",
          "8544", 18,
          [("3.5C x 50 sq mm", "50", "sq mm", "Mtr", "420", "70"),
           ("3.5C x 95 sq mm", "95", "sq mm", "Mtr", "704", "95")]),
    _spec("SOL-ACDB", "AC distribution box", "ACDB with MCCB incomer, SPD Type II and "
          "multifunction meter, IP65 enclosure.", "8537", 18,
          [("For up to 100 kW", "", "", "Set", "68000", "4000"),
           ("For 350 kW", "", "", "Set", "207200", "8000")]),
    _spec("SOL-DCDB", "DC distribution box", "DCDB 2-in-1-out with DC fuses, DC SPD Type II "
          "and isolator, IP65 enclosure.", "8537", 18,
          [("2-in 1-out", "", "", "Set", "10640", "1200")]),
    _spec("SOL-EARTH", "Earthing kit", "Maintenance-free chemical earthing electrode, 3 m, "
          "with earth pit, cover and copper strip.", "8538", 18,
          [("3 m electrode", "3", "m", "Set", "6944", "1500")]),
    _spec("SOL-LA", "Lightning arrester", "Early-streamer-emission lightning arrester with "
          "GI mast and dedicated earthing.", "8535", 18,
          [("ESE, 60 m radius", "60", "m", "Set", "42560", "4500")]),
    _spec("SOL-MC4", "MC4 connector pair", "MC4 connector pair, 1500 V DC, IP68.", "8536", 18,
          [("1500 V", "", "", "Nos", "98", "20")]),
    _spec("SOL-WALK", "Roof walkway", "FRP / GI walkway for cleaning and maintenance access.",
          "7308", 18, [("300 mm wide", "300", "mm", "Mtr", "728", "138")], category="Mechanical"),
    _spec("SOL-NETMTR", "Bi-directional net meter", "DISCOM-approved CT-operated "
          "bi-directional energy meter with test certificate.", "9028", 18,
          [("CT-operated", "", "", "Set", "46200", "3000")]),
    _spec("SOL-LOGGER", "Monitoring data logger", "Plant monitoring data logger with "
          "one-year remote portal subscription.", "8517", 18,
          [("With 1-year portal", "", "", "Nos", "32200", "3000")]),
    _spec("SOL-ITC", "Installation, testing & commissioning", "Installation, testing and "
          "commissioning of the complete PV system, with SLD and as-built drawings.", "", 18,
          [("Per kWp", "", "", "kWp", "", "1150")], category="Services"),
    _spec("SOL-LIAISON", "Net-metering liaisoning", "Net-metering application, follow-up, "
          "inspections and commissioning with the DISCOM.", "", 18,
          [("Per project", "", "", "Lot", "", "66000")], sac="9983", category="Services"),
]

# =============================================================================
# THE ADDRESS BOOK
# =============================================================================
def _addr(key, label, typ, company, contact, line1, line2, city, pin, phone, email, gstin,
          landmark=""):
    return {"key": key, "label": label, "type": typ, "company": company,
            "contact_name": contact, "line1": line1, "line2": line2, "landmark": landmark,
            "city": city, "state": "Maharashtra", "pincode": pin, "phone": phone,
            "email": email, "gstin": gstin}


ADDRESSES = [
    _addr("ganesh", "Shree Ganesh Polymers — Head Office", "billing",
          "Shree Ganesh Polymers Pvt Ltd", "Mr. P. Plant Head",
          "Plot B-27, Bhiwandi MIDC", "Kalher Road", "Bhiwandi", "421302",
          "+91 98200 10001", "accounts@ganeshpolymers.example", "27AAACS0000G1Z4"),
    _addr("ganesh_site", "Shree Ganesh Polymers — Factory Rooftop", "site",
          "Shree Ganesh Polymers Pvt Ltd", "Maintenance Engineer",
          "Plot B-27, Bhiwandi MIDC (sheds 1-3)", "Kalher Road", "Bhiwandi", "421302",
          "+91 98200 10002", "maintenance@ganeshpolymers.example", ""),
    _addr("greenvalley", "Green Valley CHS — Office", "billing",
          "Green Valley Co-operative Housing Society Ltd", "The Secretary",
          "Green Valley Complex, Sector 18", "New Panvel", "Panvel", "410206",
          "+91 98200 10003", "secretary@greenvalleychs.example", ""),
    _addr("greenvalley_site", "Green Valley CHS — Terrace A & B", "site",
          "Green Valley Co-operative Housing Society Ltd", "Society Manager",
          "Green Valley Complex, Wings A & B terrace", "Sector 18, New Panvel", "Panvel",
          "410206", "+91 98200 10004", "manager@greenvalleychs.example", ""),
    _addr("konkan", "Konkan Cold Storage — Vasai", "billing", "Konkan Cold Storage LLP",
          "Mr. K. Owner", "Gala 6, Sample Logistics Park", "Vasai East", "Vasai", "401208",
          "+91 98200 10005", "owner@konkancold.example", "27AAAFK0000C1ZE"),
    _addr("sunpeak", "SunPeak Solar Distributors", "vendor", "SunPeak Solar Distributors",
          "Mr. S. Sales", "Unit 14, Example Trade Centre", "Bhosari MIDC", "Pune", "411026",
          "+91 98200 20001", "sales@sunpeak.example", "27AAAFS0000P1ZF"),
    _addr("brightvolt", "BrightVolt Solar Traders", "vendor", "BrightVolt Solar Traders Pvt Ltd",
          "Ms. B. Accounts", "Shop 3, Sample Plaza", "Lamington Road", "Mumbai", "400007",
          "+91 98200 20002", "orders@brightvolt.example", "27AAACB0000V1ZQ"),
    _addr("powerwave", "PowerWave Inverters", "vendor", "PowerWave Inverters Pvt Ltd",
          "Mr. P. Channel", "Office 21, Example Tech Park", "Andheri East", "Mumbai", "400093",
          "+91 98200 20003", "channel@powerwave.example", "27AAACP0000W1ZA"),
    _addr("steelform", "Steelform Fabricators", "vendor", "Steelform Fabricators",
          "Mr. F. Works", "Gala 9, Example Industrial Estate", "Wagle Estate", "Thane", "400604",
          "+91 98200 20004", "works@steelform.example", "27AAAFS0000F1Z0"),
    _addr("konnect", "Konnect Cables & BOS", "vendor", "Konnect Cables & BOS Pvt Ltd",
          "Mr. C. Desk", "12 Sample Market", "Bhiwandi Road", "Kalyan", "421301",
          "+91 98200 20005", "desk@konnectbos.example", "27AAACK0000C1ZK"),
    _addr("skyline", "SkyLine Solar Installers", "vendor", "SkyLine Solar Installers",
          "Mr. L. Supervisor", "Room 4, Example Chawl Road", "Kopri", "Thane", "400603",
          "+91 98200 20006", "work@skylineinstall.example", "27AAAFS0000L1ZN"),
]

PROJECT_1 = {"name": "Shree Ganesh Polymers — 350 kWp Rooftop", "client": "Shree Ganesh Polymers Pvt Ltd",
             "notes": "DEMO DATA. 350.75 kWp industrial rooftop on three metal-sheet sheds, Bhiwandi."}
PROJECT_2 = {"name": "Green Valley CHS — 60 kWp Rooftop", "client": "Green Valley Co-operative Housing Society Ltd",
             "notes": "DEMO DATA. 60.5 kWp common-area plant, DCR modules, net metering."}

# =============================================================================
# PROJECT 1 — THE BOQ (base rate = OUR cost, escalation = margin)
# =============================================================================
_L = DS._line

BOQ1_META = {
    "project_name":   PROJECT_1["name"],
    "site_location":  "Bhiwandi MIDC, sheds 1-3",
    "date":           "2026-08-08",
    "rate_basis_label": "Helios cost sheet, Aug 2026",
    "account_name":   "Shree Ganesh Polymers Pvt Ltd",
    "contact_person": "Mr. P. Plant Head",
    "bill_addr":      "Plot B-27, Bhiwandi MIDC, Kalher Road",
    "bill_state":     "Maharashtra",
    "bill_city":      "Bhiwandi",
    "bill_pin":       "421302",
    "bill_gstin":     "27AAACS0000G1Z4",
    "ship_acct_name": "Shree Ganesh Polymers — Factory Rooftop",
    "ship_addr":      "Plot B-27, Bhiwandi MIDC (sheds 1-3), Kalher Road",
    "ship_state":     "Maharashtra",
    "ship_city":      "Bhiwandi",
    "ship_pin":       "421302",
    "payment_terms":  "30% advance, 60% against delivery pro rata, 10% on commissioning",
    "delivery_terms": "FOR site, Bhiwandi",
    "notes":          ("DEMO DATA. 350.75 kWp DC / 350 kW AC. Generation estimate on request; "
                       "net-metering timelines depend on the DISCOM."),
}

BOQ_SECTIONS = [
    {"code": "A", "title": "MODULES & INVERTERS", "areas": []},
    {"code": "B", "title": "MOUNTING STRUCTURE", "areas": []},
    {"code": "C", "title": "DC & AC BALANCE OF SYSTEM", "areas": []},
    {"code": "D", "title": "INSTALLATION, TESTING & COMMISSIONING", "areas": []},
    {"code": "E", "title": "LIAISONING & NET METERING", "areas": []},
]


def boq1_lines(module_pct=8, walkway_qty=420):
    """Project 1's schedule. Rev 1 (after negotiation) passes a lower module
    escalation and a shorter walkway."""
    return [
        _L("A", "1", "TOPCon bifacial module 575 Wp, dual glass (Make: Waaree / Adani / Premier "
                     "or equivalent)", "Nos", qty=610,
           s_base=9300, s_pct=module_pct, i_base=350, i_pct=15, hsn="8541", s_gst=5),
        _L("A", "2", "Three-phase string inverter, 100 kW (Make: Sungrow / Growatt / Solis or "
                     "equivalent)", "Nos", qty=3,
           s_base=245000, s_pct=10, i_base=6500, i_pct=15, hsn="8504", s_gst=5),
        _L("A", "3", "Three-phase string inverter, 50 kW", "Nos", qty=1,
           s_base=138000, s_pct=10, i_base=5000, i_pct=10, hsn="8504", s_gst=5),
        _L("B", "1", "HDG module mounting structure for metal-sheet roof, rail & clamp, "
                     "80 micron galvanising", "kWp", qty=350.75,
           s_base=3200, s_pct=12, i_base=450, i_pct=15, hsn="7308"),
        _L("B", "2", "FRP walkway 300 mm wide for cleaning access", "Mtr", qty=walkway_qty,
           s_base=650, s_pct=12, i_base=120, i_pct=15, hsn="7308"),
        _L("C", "1", "Solar DC cable, single-core tinned copper, EN 50618, 1.5 kV DC "
                     "(Make: Polycab / KEI or equivalent)", header=True),
        _L("C", "1.1", "4 sq mm", "Mtr", parent="1", qty=4200,
           s_base=58, s_pct=10, i_base=12, i_pct=15, hsn="8544"),
        _L("C", "1.2", "6 sq mm", "Mtr", parent="1", qty=1800,
           s_base=82, s_pct=10, i_base=13, i_pct=15, hsn="8544"),
        _L("C", "2", "AC cable 3.5C x 95 sq mm Al armoured, inverter to ACDB", "Mtr", qty=180,
           s_base=640, s_pct=10, i_base=85, i_pct=12, hsn="8544"),
        _L("C", "3", "DCDB 2-in 1-out with DC fuses and SPD", "Set", qty=4,
           s_base=9500, s_pct=12, i_base=1100, i_pct=10, hsn="8537"),
        _L("C", "4", "ACDB for 350 kW with MCCB incomer, SPD and multifunction meter", "Set", qty=1,
           s_base=185000, s_pct=12, i_base=7500, i_pct=10, hsn="8537"),
        _L("C", "5", "Chemical earthing kit, 3 m electrode with pit", "Set", qty=8,
           s_base=6200, s_pct=12, i_base=1300, i_pct=15, hsn="8538"),
        _L("C", "6", "ESE lightning arrester with mast and earthing", "Set", qty=2,
           s_base=38000, s_pct=12, i_base=4000, i_pct=12, hsn="8535"),
        _L("C", "7", "MC4 connector pair, 1500 V", "Nos", qty=160,
           s_base=85, s_pct=15, i_base=18, i_pct=10, hsn="8536"),
        _L("C", "8", "Monitoring data logger with 1-year remote portal", "Nos", qty=1,
           s_base=28000, s_pct=15, i_base=2600, i_pct=15, hsn="8517"),
        _L("D", "1", "Testing & commissioning, SLD, as-built drawings and O&M manual", "Lot",
           qty=1, i_base=60000, i_pct=20, hsn="", sac="9954"),
        _L("D", "2", "Crane hire and material shifting to roof", "Lot", qty=1,
           i_base=45000, i_pct=10, hsn="", sac="9954"),
        _L("E", "1", "Net-metering liaisoning with the DISCOM: application, inspections, "
                     "commissioning", "Lot", qty=1, i_base=55000, i_pct=20, hsn="", sac="9983"),
        _L("E", "2", "Bi-directional CT-operated net meter, DISCOM approved", "Set", qty=1,
           s_base=42000, s_pct=10, i_base=3000, i_pct=10, hsn="9028"),
    ]


BOQ1_REV1_NOTE = "Revision 1 after negotiation (14 Aug 2026): module margin 8% -> 6%, walkway 420 -> 380 m."

# =============================================================================
# PROJECT 2 — 60 kWp housing society (earlier stage)
# =============================================================================
BOQ2_META = {
    "project_name":   PROJECT_2["name"],
    "site_location":  "New Panvel, terrace wings A & B",
    "date":           "2026-10-20",
    "rate_basis_label": "Helios cost sheet, Oct 2026",
    "account_name":   "Green Valley Co-operative Housing Society Ltd",
    "contact_person": "The Secretary",
    "bill_addr":      "Green Valley Complex, Sector 18, New Panvel",
    "bill_state":     "Maharashtra",
    "bill_city":      "Panvel",
    "bill_pin":       "410206",
    "bill_gstin":     "",
    "ship_acct_name": "Green Valley CHS — Terrace A & B",
    "ship_addr":      "Green Valley Complex, Wings A & B terrace, Sector 18, New Panvel",
    "ship_state":     "Maharashtra",
    "ship_city":      "Panvel",
    "ship_pin":       "410206",
    "payment_terms":  "40% advance, 50% against delivery, 10% on net-meter commissioning",
    "delivery_terms": "FOR site, New Panvel",
    "notes":          "DEMO DATA. 60.5 kWp DC with DCR modules for the society's common load.",
}

BOQ2_LINES = [
    _L("A", "1", "Mono PERC half-cut module 550 Wp, DCR (Make: Waaree / Adani / Vikram or "
                 "equivalent)", "Nos", qty=110,
       s_base=12800, s_pct=8, i_base=330, i_pct=15, hsn="8541", s_gst=5),
    _L("A", "2", "Three-phase string inverter, 50 kW", "Nos", qty=1,
       s_base=138000, s_pct=10, i_base=5000, i_pct=10, hsn="8504", s_gst=5),
    _L("A", "3", "Three-phase string inverter, 10 kW", "Nos", qty=1,
       s_base=47000, s_pct=10, i_base=2800, i_pct=10, hsn="8504", s_gst=5),
    _L("B", "1", "HDG module mounting structure for RCC terrace, elevated 1.5 m", "kWp",
       qty=60.5, s_base=3400, s_pct=12, i_base=500, i_pct=15, hsn="7308"),
    _L("C", "1", "Solar DC cable 4 sq mm, EN 50618", "Mtr", qty=900,
       s_base=58, s_pct=10, i_base=12, i_pct=15, hsn="8544"),
    _L("C", "2", "ACDB for 60 kW with MCCB, SPD and meter", "Set", qty=1,
       s_base=62000, s_pct=12, i_base=4000, i_pct=10, hsn="8537"),
    _L("C", "3", "Chemical earthing kit, 3 m electrode with pit", "Set", qty=4,
       s_base=6200, s_pct=12, i_base=1300, i_pct=15, hsn="8538"),
    _L("D", "1", "Testing & commissioning, SLD and as-built drawings", "Lot", qty=1,
       i_base=18000, i_pct=20, hsn="", sac="9954"),
    _L("E", "1", "Net-metering liaisoning with the DISCOM", "Lot", qty=1,
       i_base=30000, i_pct=20, hsn="", sac="9983"),
]

# =============================================================================
# THE DOCUMENTS — keyed (section, item_no), the human handle
# =============================================================================
# A quotation carries ONE GST rate (quotation.py), so each offer holds the
# modules and inverters only — 5%, the same rate — and its tax section says so.
QUOTE_P1 = {"qtn_date": "2026-08-04", "buyer_ref": "SGP/ENQ/2026/031",
            "other_ref": "Budgetary offer — 350 kWp rooftop, supply", "account": "ganesh",
            "picks": [("SOL-MOD-TOPCON", 0, 610, None), ("SOL-INV-STR", 2, 3, None),
                      ("SOL-INV-STR", 1, 1, None)]}
QUOTE_LEAD = {"qtn_date": "2026-10-14", "buyer_ref": "KCS/RFQ/07",
              "other_ref": "120 kWp rooftop — supply offer", "account": "konkan",
              "picks": [("SOL-MOD-TOPCON", 0, 209, None), ("SOL-INV-STR", 2, 1, None),
                        ("SOL-INV-STR", 0, 2, None)]}

INQUIRIES = [   # the same modules asked of two distributors
    {"date": "2026-08-17", "vendor": "sunpeak", "notes": "Please quote your best price for "
     "TOPCon 575 Wp modules, delivery to Bhiwandi in two lots."},
    {"date": "2026-08-17", "vendor": "brightvolt", "notes": "Please quote your best price for "
     "TOPCon 575 Wp modules, delivery to Bhiwandi in two lots."},
]
INQUIRY_LINES = {("A", "1"): 610}
WINNER = {"date": "2026-08-21", "rate": 9300, "vendor_ref": "SPD/Q/2608-114",
          "notes": "Converted from inquiry: lowest landed price, two-lot delivery agreed."}
PO_INVERTERS = {"date": "2026-08-24", "vendor": "powerwave", "vendor_ref": "PWI/SO/5521",
                "notes": "Inverters for the Bhiwandi 350 kWp plant.",
                "lines": {("A", "2"): 3, ("A", "3"): 1}}
PO_STRUCTURE = {"date": "2026-08-26", "vendor": "steelform", "vendor_ref": "SF/WO/0912",
                "notes": "HDG structure and walkway, fabricated to our drawing HG-SGP-ST-01.",
                "lines": {("B", "1"): 350.75, ("B", "2"): 380}}
PO_BOS = {"date": "2026-08-28", "vendor": "konnect", "vendor_ref": "KCB/PO-ACK/233",
          "notes": "DC and AC cable, DCDB, ACDB, earthing, LA, MC4, logger and net meter.",
          "lines": {("C", "1.1"): 4450, ("C", "1.2"): 1800, ("C", "2"): 180, ("C", "3"): 4,
                    ("C", "4"): 1, ("C", "5"): 8, ("C", "6"): 2, ("C", "7"): 160,
                    ("C", "8"): 1, ("E", "2"): 1}}
WORK_ORDER = {"date": "2026-09-01", "vendor": "skyline", "vendor_ref": "SKY/WO/26-14",
              "notes": "WORK ORDER — installation labour for the Bhiwandi 350 kWp plant: module "
                       "mounting, DC and AC wiring, earthing and LA.",
              "extras": [("Module mounting and DC wiring", "9954", "kWp", 350.75, 900),
                         ("AC side, earthing and lightning arrester", "9954", "Lot", 1, 45000)]}

DC1 = {"date": "2026-09-05", "notes": "Lot 1: structure, DC cable and earthing",
       "lines": {("B", "1"): 350.75, ("B", "2"): 380, ("C", "1.1"): 2500, ("C", "1.2"): 1000,
                 ("C", "5"): 8}}
DC2 = {"date": "2026-09-19", "notes": "Lot 2: modules (first lot) and two inverters",
       "lines": {("A", "1"): 360, ("A", "2"): 2}}
# Challan 3 carries the cable run that came out longer than the BOQ: 2,500 +
# 1,950 = 4,450 m of 4 sq mm against 4,200 in the schedule.
DC3 = {"date": "2026-10-06", "notes": "Lot 3: balance modules, inverters, ACDB/DCDB, LA, "
                                      "MC4, logger and the balance cable",
       "lines": {("A", "1"): 250, ("A", "2"): 1, ("A", "3"): 1, ("C", "1.1"): 1950,
                 ("C", "1.2"): 800, ("C", "2"): 180, ("C", "3"): 4, ("C", "4"): 1,
                 ("C", "6"): 2, ("C", "7"): 160, ("C", "8"): 1}}

RA1 = {"date": "2026-09-10", "notes": "RA 1 — supply against challan 1"}
RA2 = {"date": "2026-10-10", "notes": "RA 2 — supply against challans 2 and 3",
       "excess_reason": ("4 sq mm DC cable: actual routing across sheds 1-3 measured at "
                         "4,450 m against 4,200 m in the BOQ; agreed with the client's "
                         "maintenance engineer on 6 Oct 2026.")}
MEASUREMENT = {"date": "2026-11-03", "measured_by": "Site Engineer, Helios Grid Energy",
               "witnessed_by": "Maintenance Engineer, Shree Ganesh Polymers",
               "notes": "Joint measurement — installation complete on sheds 1-3",
               "system": "Rooftop solar PV, 350.75 kWp", "material": "As per BOQ rev 1",
               "area": "Sheds 1-3",
               "lines": {("A", "1"): 610, ("A", "2"): 3, ("A", "3"): 1, ("B", "1"): 350.75,
                         ("B", "2"): 380, ("C", "1.1"): 4200, ("C", "1.2"): 1800,
                         ("C", "2"): 180, ("C", "3"): 4, ("C", "4"): 1, ("C", "5"): 8,
                         ("C", "6"): 2, ("C", "7"): 160, ("C", "8"): 1, ("D", "2"): 1}}
RA3 = {"date": "2026-11-05", "notes": "RA 3 — installation, as jointly measured on 3 Nov 2026"}

# TDS: this product has no TDS field on a receipt (FEATURE_GAP.md item 5,
# deferred), so the receipt is the NET amount the client paid and the note says
# what was deducted; the TDS stays in the balance until the certificate comes.
RECEIPT_1 = {"date": "2026-09-30", "mode": "neft", "instrument_ref": "UTR-DEMO-260930-01",
             "tds_pct": 2.0, "notes": "Against RA 1. TDS u/s 194C @ 2% on the taxable value "
                                      "({tds}) deducted by the client — Form 16A awaited."}
RECEIPT_2 = {"date": "2026-10-28", "mode": "rtgs", "instrument_ref": "UTR-DEMO-261028-07",
             "fraction": 0.85, "notes": "Against RA 2 — part payment; the balance is carried "
                                        "into the next bill."}

CHARGES = [
    {"date": "2026-09-05", "person": "Site Engineer", "head": "Transport / Freight",
     "description": "Truck hire, structure and cable lot to Bhiwandi", "taxable_amount": "14500",
     "gst_rate": "12"},
    {"date": "2026-09-20", "person": "Site Engineer", "head": "Site Expenses",
     "description": "Crane hire, two days, module lifting to sheds 1-2", "taxable_amount": "36000",
     "gst_rate": "18"},
    {"date": "2026-10-07", "person": "Site Supervisor", "head": "Transport / Freight",
     "description": "Truck hire, lot 3 to Bhiwandi", "taxable_amount": "12800", "gst_rate": "12"},
    {"date": "2026-10-16", "person": "Site Supervisor", "head": "Site Expenses",
     "description": "Safety harnesses, lifelines and first-aid kit", "taxable_amount": "18600",
     "gst_rate": "18"},
    {"date": "2026-11-02", "person": "Store Keeper", "head": "Consumables",
     "description": "Cable ties, lugs, glands and sealant", "taxable_amount": "9450",
     "gst_rate": "18"},
]

EMPLOYEES = [
    {"name": "Ramesh Kale", "code": "HG-101", "designation": "Site Supervisor", "day_rate": "1400"},
    {"name": "Sunil Pawar", "code": "HG-102", "designation": "Electrician", "day_rate": "1100"},
    {"name": "Mahesh Gaikwad", "code": "HG-103", "designation": "Electrician", "day_rate": "1050"},
    {"name": "Imran Shaikh", "code": "HG-104", "designation": "Fitter", "day_rate": "900"},
    {"name": "Deepak Yadav", "code": "HG-105", "designation": "Helper", "day_rate": "700"},
    {"name": "Santosh Jadhav", "code": "HG-106", "designation": "Helper", "day_rate": "700"},
]

P2_DC = {"date": "2026-11-10", "notes": "Lot 1: modules, structure and DC cable",
         "lines": {("A", "1"): 110, ("B", "1"): 60.5, ("C", "1"): 900}}
P2_RA = {"date": "2026-11-14", "notes": "RA 1 — supply against challan 1"}

STAGES = ("settings", "masters", "project1_boq", "project1_buy", "project1_chain",
          "project1_costs", "people", "project2", "lead")


# =============================================================================
# THE SUN MARK — a generated logo (base64 PNG once logo.py re-encodes it)
# =============================================================================
def sun_png(size: int = 512) -> bytes:
    """A simple sun: an amber disc with twelve rays, on transparency."""
    import math
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    for k in range(12):
        a = 2 * math.pi * k / 12
        r1, r2, w = size * 0.30, size * 0.47, size * 0.035
        x1, y1 = c + r1 * math.cos(a), c + r1 * math.sin(a)
        x2, y2 = c + r2 * math.cos(a), c + r2 * math.sin(a)
        d.line([(x1, y1), (x2, y2)], fill=(245, 158, 11, 255), width=int(w))
    r = size * 0.24
    d.ellipse([c - r, c - r, c + r, c + r], fill=(245, 158, 11, 255))
    r2 = size * 0.15
    d.ellipse([c - r2, c - r2, c + r2, c + r2], fill=(252, 211, 77, 255))
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


# =============================================================================
# THE STAGES
# =============================================================================
def _post_form(d, url: str, contains: str, over: dict, files: dict = None):
    """GET a singleton form, post its own fields with `over` — for the forms
    that edit a record rather than create one."""
    from werkzeug.datastructures import MultiDict
    f = d.form(url, contains)
    over = dict(over)
    data = MultiDict()
    for name, value in f["fields"]:
        if name in over:
            v = over.pop(name)
            for item in (v if isinstance(v, list) else [v]):
                data.add(name, item)
        else:
            data.add(name, value)
    for name, v in over.items():
        for item in (v if isinstance(v, list) else [v]):
            data.add(name, item)
    for name, fobj in (files or {}).items():
        data.add(name, fobj)
    r = d.c.post(f["action"] or url, data=data,
                 content_type="multipart/form-data" if files else None)
    if r.status_code not in (200, 302):
        raise DS.SeedError(f"POST {url} answered {r.status_code}")
    return r


def _stage_settings(d, ids):
    over = dict(COMPANY)
    over.update({f"landing_{k}": v for k, v in LANDING.items()})
    # The challan book's prefix (blank by default — a paper book has none).
    over.update({"dc_prefix": "HG/DC/", "dc_next_no": "1"})
    r = _post_form(d, "/settings/", "COMPANY_NAME", over,
                   files={"logo_file": (io.BytesIO(sun_png()), "helios-sun.png", "image/png")})
    company = (d.store.get("settings") or {}).get("company") or {}
    if r.status_code != 302 or company.get("COMPANY_NAME") != COMPANY["COMPANY_NAME"]:
        raise DS.SeedError(f"/settings/ did not save: {DS._error_of(r.get_data(as_text=True))}")
    if not (d.store.get("settings") or {}).get("logo"):
        raise DS.SeedError("/settings/ did not take the logo")
    # The terms library: on-by-default first, then the rest, one post each way.
    for flag in (True, False):
        group = [t for t in TERMS if t[2] is flag]
        for cat in dict.fromkeys(c for c, _t, _o in group):
            from werkzeug.datastructures import MultiDict
            import pricesummary as PS
            lib = PS.library()
            data = MultiDict([("title", ""), ("tax_line", ""), ("new_category", cat),
                              ("new_terms", "\n".join(t for c, t, _o in group if c == cat))])
            if flag:
                data.add("new_on", "1")
            for e in lib:
                data.add("lib_id", e["id"]); data.add("lib_text", e["text"])
                data.add("lib_cat", e["category"])
                if e["on"]:
                    data.add("lib_on", e["id"])
            d.post("/settings/terms", data)
    import pricesummary as PS
    if len(PS.library()) != len(TERMS):
        raise DS.SeedError(f"terms library holds {len(PS.library())}, expected {len(TERMS)}")


def _stage_masters(d, ids):
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
    ids["project1"] = d.submit("/projects/create", "name", {
        **PROJECT_1, "site_address_id": ids["addresses"]["ganesh_site"]}, "projects")
    ids["project2"] = d.submit("/projects/create", "name", {
        **PROJECT_2, "site_address_id": ids["addresses"]["greenvalley_site"]}, "projects")


def _lines_of(store, bid):
    return {(li["section"], li["item_no"]): li for li in store["boqs"][bid]["line_items"]
            if not li.get("is_header")}


def _rows(lines: dict, qty_by_key: dict, rate: str = "") -> list:
    """Picker rows. `rate`: "supply" / "install" (the BOQ's selling rate),
    "cost" (the supply BASE rate — what we pay a vendor), or "" (none)."""
    out = []
    for key, qty in qty_by_key.items():
        li = lines[key]
        row = {"line_id": li["line_id"], "qty": qty}
        if rate == "supply":
            row["rate"] = li["supply_rate"]
        elif rate == "install":
            row["rate"] = li["install_rate"]
        elif rate == "cost":
            row["rate"] = li.get("supply_base_rate") or li["supply_rate"]
        out.append(row)
    return out


def _summary(d, bid, orientation="landscape"):
    import pricesummary as PS
    picks = [e["id"] for e in PS.library() if e["on"]]
    d.post(f"/boq/summary/{bid}", {PS.FIELD_ON: "1", PS.FIELD_ORIENT: orientation,
                                   "lib_pick": picks, "own_terms": ""})
    if not d.store["boqs"][bid].get(PS.FIELD_ON):
        raise DS.SeedError(f"/boq/summary/{bid} did not save")


def _quotation(d, ids, q):
    a = next(x for x in ADDRESSES if x["key"] == q["account"])
    picks = []
    for code, vidx, qty, price in q["picks"]:
        sid = ids["specs"][code]
        spec = d.store["specs"][sid]
        rate = price if price is not None else spec["variants"][vidx]["default_supply_base_rate"]
        picks.append({"sid": sid, "vidx": vidx, "qty": qty, "price": rate, "show_price": True})
    return d.submit("/quotation/create", "selections_json", {
        "selections_json": json.dumps(picks), "qtn_date": q["qtn_date"],
        "qtn_type": "Supply Only", "buyer_ref": q["buyer_ref"], "other_ref": q["other_ref"],
        "company_branch": COMPANY["COMPANY_NAME"], "auth_signatory": "Authorised Signatory",
        "lead_owner": "Sales", "assigned_to": "Sales", "account_name": a["company"],
        "contact_person": a["contact_name"], "bill_addr": f"{a['line1']}, {a['line2']}",
        "bill_state": a["state"], "bill_city": a["city"], "bill_pin": a["pincode"],
        "bill_phone": a["phone"], "bill_gstin": a["gstin"], "ship_type": "same",
        "tax_type": "cgst_sgst", "tax_cgst": "2.5", "tax_sgst": "2.5"}, "quotations")


def _stage_project1_boq(d, ids):
    ids["quote_p1"] = _quotation(d, ids, QUOTE_P1)
    payload = json.dumps({"sections": BOQ_SECTIONS, "lines": boq1_lines()})
    ids["boq1_r0"] = d.submit(f"/boq/create?project_id={ids['project1']}", "boq_json", {
        **BOQ1_META, "boq_json": payload, "rev_no": "0", "supersedes": "",
        "project_id": ids["project1"]}, "boqs")
    _summary(d, ids["boq1_r0"])
    # Revision 1 — the same lines (same line_ids), renegotiated.
    r0 = d.store["boqs"][ids["boq1_r0"]]
    by_key = _lines_of(d.store, ids["boq1_r0"])
    new = boq1_lines(module_pct=6, walkway_qty=380)
    for li in new:
        if not li.get("is_header"):
            li["line_id"] = by_key[(li["section"], li["item_no"])]["line_id"]
        else:
            hdr = next(x for x in r0["line_items"] if x.get("is_header")
                       and x["section"] == li["section"] and x["item_no"] == li["item_no"])
            li["line_id"] = hdr["line_id"]
    meta = dict(BOQ1_META, date="2026-08-14", notes=BOQ1_META["notes"] + " " + BOQ1_REV1_NOTE)
    ids["boq1"] = d.submit(f"/boq/create?project_id={ids['project1']}", "boq_json", {
        **meta, "boq_json": json.dumps({"sections": BOQ_SECTIONS, "lines": new}),
        "rev_no": "1", "supersedes": ids["boq1_r0"], "project_id": ids["project1"]}, "boqs")


def _stage_project1_buy(d, ids):
    bid = ids["boq1"]
    lines = _lines_of(d.store, bid)
    ids["inquiries"] = []
    for inq in INQUIRIES:
        ids["inquiries"].append(d.submit(f"/po/create?boq={bid}", "po_json", {
            "po_json": json.dumps({"lines": _rows(lines, INQUIRY_LINES)}),
            "vendor_id": ids["addresses"][inq["vendor"]], "date": inq["date"],
            "delivery_to": "Shree Ganesh Polymers — Factory Rooftop, Bhiwandi",
            "notes": inq["notes"]}, "purchase_orders"))
    # The winner (the first distributor) converted to a real PO, priced.
    win = ids["inquiries"][0]
    f = d.form(f"/purchase/from-draft/{win}", "dl_line_id")
    n = sum(1 for k, _v in f["fields"] if k == "dl_line_id")
    ids["po_modules"] = d.submit(f"/purchase/from-draft/{win}", "dl_line_id", {
        "dl_rate": [str(WINNER["rate"])] * n, "date": WINNER["date"], "status": "Issued",
        "vendor_ref": WINNER["vendor_ref"], "notes": WINNER["notes"],
        "project_id": ids["project1"]}, "purchases")
    for key, po in (("po_inverters", PO_INVERTERS), ("po_structure", PO_STRUCTURE),
                    ("po_bos", PO_BOS)):
        ids[key] = d.submit(f"/purchase/from-boq/{bid}", "po_json", {
            "po_json": json.dumps({"lines": _rows(lines, po["lines"], "cost")}),
            "vendor_id": ids["addresses"][po["vendor"]], "date": po["date"],
            "status": "Issued", "vendor_ref": po["vendor_ref"], "notes": po["notes"],
            "project_id": ids["project1"]}, "purchases")
    ex = WORK_ORDER["extras"]
    ids["work_order"] = d.submit("/purchase/create", "vendor_id", {
        "vendor_id": ids["addresses"][WORK_ORDER["vendor"]], "date": WORK_ORDER["date"],
        "status": "Issued", "vendor_ref": WORK_ORDER["vendor_ref"], "notes": WORK_ORDER["notes"],
        "project_id": ids["project1"],
        "extra_desc": [e[0] for e in ex] + [""], "extra_hsn": [e[1] for e in ex] + [""],
        "extra_unit": [e[2] for e in ex] + [""], "extra_qty": [str(e[3]) for e in ex] + [""],
        "extra_rate": [str(e[4]) for e in ex] + [""], "extra_discount": [""] * (len(ex) + 1)},
        "purchases")


def _dc(d, bid, lines, dc, consignee, to):
    return d.submit(f"/dc/create?boq={bid}", "dc_json", {
        "dc_json": json.dumps({"lines": _rows(lines, dc["lines"])}),
        "date": dc["date"], "dispatch_mode": "Transport", "notes": dc["notes"],
        "consignee_name": consignee, "dispatch_to": to}, "delivery_challans")


def _issue(d, rid):
    d.post(f"/ra/issue/{rid}")
    if d.store["ra_bills"][rid].get("status") != "issued":
        raise DS.SeedError(f"RA {rid} did not issue")


def _stage_project1_chain(d, ids):
    bid = ids["boq1"]
    lines = _lines_of(d.store, bid)
    cons = "Shree Ganesh Polymers Pvt Ltd"
    to = "Plot B-27, Bhiwandi MIDC (sheds 1-3), Kalher Road, Bhiwandi 421302"
    ids["dc"] = [_dc(d, bid, lines, dc, cons, to) for dc in (DC1, DC2, DC3)]

    ids["ra1"] = d.submit(f"/ra/create?boq={bid}&leg=supply&dc={ids['dc'][0]}", "ra_json", {
        "ra_json": json.dumps({"lines": _rows(lines, DC1["lines"], "supply")}),
        "date": RA1["date"], "notes": RA1["notes"]}, "ra_bills")
    _issue(d, ids["ra1"])

    bill = d.store["ra_bills"][ids["ra1"]]
    gross = float(bill.get("grand_total") or 0.0)
    tds = round(float(bill.get("claim_subtotal") or 0.0) * RECEIPT_1["tds_pct"] / 100, 0)
    ids["receipt1"] = d.submit(f"/receipt/new?ra={ids['ra1']}", "amount", {
        "amount": f"{gross - tds:.2f}", "date": RECEIPT_1["date"], "mode": RECEIPT_1["mode"],
        "instrument_ref": RECEIPT_1["instrument_ref"], "instrument_date": RECEIPT_1["date"],
        "notes": RECEIPT_1["notes"].format(tds=f"Rs {tds:,.0f}")}, "receipts")

    both = {}
    for dc in (DC2, DC3):
        for k, q in dc["lines"].items():
            both[k] = both.get(k, 0) + q
    ids["ra2"] = d.submit(
        f"/ra/create?boq={bid}&leg=supply&dc={ids['dc'][1]}&dc={ids['dc'][2]}", "ra_json", {
            "ra_json": json.dumps({"lines": _rows(lines, both, "supply")}),
            "date": RA2["date"], "notes": RA2["notes"],
            "excess_reason": RA2["excess_reason"]}, "ra_bills")
    _issue(d, ids["ra2"])

    bill = d.store["ra_bills"][ids["ra2"]]
    amount = round(float(bill.get("grand_total") or 0.0) * RECEIPT_2["fraction"], -3)
    ids["receipt2"] = d.submit(f"/receipt/new?ra={ids['ra2']}", "amount", {
        "amount": f"{amount:.2f}", "date": RECEIPT_2["date"], "mode": RECEIPT_2["mode"],
        "instrument_ref": RECEIPT_2["instrument_ref"], "instrument_date": RECEIPT_2["date"],
        "notes": RECEIPT_2["notes"]}, "receipts")

    ids["measurement"] = d.submit(f"/measurement/create?boq={bid}", "ms_json", {
        "ms_json": json.dumps({"lines": _rows(lines, MEASUREMENT["lines"])}),
        **{k: v for k, v in MEASUREMENT.items() if k != "lines"},
        "counterparty_name": BOQ1_META["account_name"]}, "measurements")
    ids["ra3"] = d.submit(f"/ra/create?ms={ids['measurement']}", "ra_json", {
        "ra_json": json.dumps({"lines": _rows(lines, MEASUREMENT["lines"], "install")}),
        "date": RA3["date"], "notes": RA3["notes"]}, "ra_bills")
    _issue(d, ids["ra3"])


def _stage_project1_costs(d, ids):
    ids["charges"] = []
    for i, ch in enumerate(CHARGES, start=1):
        ids["charges"].append(d.submit("/charge/new", "head", {
            **ch, "project_id": ids["project1"]}, "charges",
            files={"attachment": (io.BytesIO(DS._pdf(f"Demo bill {i} - Helios Grid Energy")),
                                  f"demo-bill-{i}.pdf", "application/pdf")}))


def _workdays(year: int, month: int, last: int):
    import datetime
    for day in range(1, last + 1):
        dt = datetime.date(year, month, day)
        if dt.weekday() != 6:   # Sunday off
            yield dt.isoformat()


def _stage_people(d, ids):
    site = ids["addresses"]["ganesh_site"]
    ids["employees"] = [d.submit("/employee/new", "name", {
        **e, "site_id": site, "date_joined": "2026-08-01", "active": "1"}, "employees")
        for e in EMPLOYEES]
    ids["attendance"] = []
    days = list(_workdays(2026, 10, 31)) + list(_workdays(2026, 11, 21))
    for n_day, day in enumerate(days):
        for n, eid in enumerate(ids["employees"]):
            # A fixed, readable pattern: everyone present, one absence a week
            # rotating through the crew, the supervisor's overtime on Saturdays.
            absent = (n_day % 6 == n) and n_day % 2 == 0
            import datetime
            saturday = datetime.date.fromisoformat(day).weekday() == 5
            over = {"date": day, "employee_id": eid, "site_id": site,
                    "project_id": ids["project1"],
                    "status": "absent" if absent else "present",
                    "hours": "0" if absent else "8",
                    "ot_hours": "2" if (saturday and n < 3 and not absent) else "0"}
            ids["attendance"].append(d.submit("/attendance/mark", "employee_id", over,
                                              "attendance"))


def _stage_project2(d, ids):
    payload = json.dumps({"sections": BOQ_SECTIONS, "lines": BOQ2_LINES})
    ids["boq2"] = d.submit(f"/boq/create?project_id={ids['project2']}", "boq_json", {
        **BOQ2_META, "boq_json": payload, "rev_no": "0", "supersedes": "",
        "project_id": ids["project2"]}, "boqs")
    _summary(d, ids["boq2"], orientation="portrait")
    lines = _lines_of(d.store, ids["boq2"])
    ids["p2_dc"] = _dc(d, ids["boq2"], lines, P2_DC, BOQ2_META["account_name"],
                       "Green Valley Complex, Wings A & B, Sector 18, New Panvel 410206")
    ids["p2_ra"] = d.submit(f"/ra/create?boq={ids['boq2']}&leg=supply&dc={ids['p2_dc']}",
                            "ra_json", {
        "ra_json": json.dumps({"lines": _rows(lines, P2_DC["lines"], "supply")}),
        "date": P2_RA["date"], "notes": P2_RA["notes"]}, "ra_bills")


def _stage_lead(d, ids):
    ids["quote_lead"] = _quotation(d, ids, QUOTE_LEAD)


_STAGE_FUNCS = {"settings": _stage_settings, "masters": _stage_masters,
                "project1_boq": _stage_project1_boq, "project1_buy": _stage_project1_buy,
                "project1_chain": _stage_project1_chain, "project1_costs": _stage_project1_costs,
                "people": _stage_people, "project2": _stage_project2, "lead": _stage_lead}


def build(client, store, stages=STAGES) -> dict:
    """Run `stages` through `client` (signed in as an Owner); return the ids."""
    ids = {}
    d = DS._Driver(client, store)
    for name in [s for s in STAGES if s in stages]:
        _STAGE_FUNCS[name](d, ids)
    return ids


def create_users(auth) -> list:
    """One login per built-in role, through `auth.create_user` — the app's own
    create function. Skips a username that already exists."""
    made = []
    for username, display, role, password in USERS:
        if auth.find_user(username) is None:
            auth.create_user(username, display, password, [role],
                             created_by="tools/seed_demo.py (solar demo)")
            made.append(username)
    return made


def is_seeded(store) -> bool:
    """True when the store already holds this demo: the company AND Project 1's BOQ."""
    company = ((store.get("settings") or {}).get("company") or {})
    return (company.get("COMPANY_LEGAL") == COMPANY["COMPANY_LEGAL"]
            and any(b.get("project_name") == PROJECT_1["name"]
                    for b in (store.get("boqs") or {}).values()))
