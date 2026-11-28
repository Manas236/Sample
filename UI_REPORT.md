# Demo screen pass

Use a light, system-font workspace with a restrained deep copper accent beside the sun mark.  
Give the project owner one clear primary action in each page header.  
Use quiet borders, white surfaces and a warm neutral canvas to group related work.  
Align money to the right and use tabular figures for comparisons.  
Keep status text beside its colour and retain readable row density.  
Give site staff stacked summaries and horizontally scrollable line items on narrow screens.

## Baseline and decisions

- Fallback: demo/solar-epc at 1d7017ce7e0f9f84f765f4740095b25931b19299. Direct GitHub clone. No root README in this tree: gap for main. Used INTRODUCTION.md, PROVENANCE.md and REPORT.md as authorised.
- Linux, CPython 3.12.14, pytest 9.1.1, pinned requirements, in-memory tests, cache provider disabled. Baseline: 3,729 passed, 6 skipped, 0 failures (133.22 s). Windows REPORT.md: 3,731 passed, 4 skipped. Both collected 3,735.
- Four common skips: test_every_client_xls_reads_through_the_xls_path (private workbook absent), test_every_printed_sheet_hides_the_nav_at_print (BOQ line picker is a form), and test_a_blank_identity_prints_the_amber_todo_chip_rather_than_nothing (delivery challan and measurement sheet each omit statutory identity). The two extra skips are test_the_checkout_env_really_exists_so_this_file_is_not_vacuous and test_a_subprocess_with_no_overrides_DOES_read_the_checkout_env. The demo used environment variables with no checkout .env; both tests require that file.
- MariaDB 11.4.5 binary distribution, local TCP port 3307 after apt installation failed. Seed reset succeeded, 360 records loaded, Owner dashboard and Shree Ganesh Polymers project returned HTTP 200. Project HTML included Planned margin.
- Preserve the original CSS as literal values in a print-only module. This keeps the legacy font import and whitespace frozen in printed HTML. Keep the shared screen/preview stack available for non-print views; select the frozen stack at print consumers. Keep the quotation-specific import inside its view to respect the file freeze outside the permitted functions.
- Tax invoice and purchase order print from their view. The installation work order uses the PO renderer. Product inquiry, DC, RA, merged RA and measurement sheet print through the shared sheet stack. Proforma and BOQ assemble their styles inline. Quotation prints from its view with hidden screen navigation, so it must also keep its current navigation bytes when shell work proceeds. No payslip renderer exists in this branch (FEATURE_GAP item 8).
- Print isolation changes print_styles.py, docsheet.py, invoice.py, proforma.py, purchase.py, po_draft.py, challan.py, ra.py, merged_ra.py, boq.py, measurement.py and quotation.py. Neither source stylesheet nor any golden was edited. No seed changes or demo-data commits. The print isolation unit can be cherry-picked onto main.
- Screen implementation is blocked by the instruction to keep every golden unchanged. tests/test_page_golden.py::test_the_screen_page_is_unchanged hashes the complete HTML, including all inline CSS, on the dashboard, project, registers and settings. The dashboard explicitly pins 91,294 characters and digest 19c0765acc302822. A stylesheet or markup edit in the normal rendering path changes that hash. No test-only rendering path or weakened assertions were introduced.
- No demo click path changed. P0 and P1 screen work, paired screenshots, visual print comparison, repeat seed and final role sweep remain pending.
