# Investment scout — driver playbook (v1, 2026-11-20)

Rules for the scheduled task "Real estate investment scout" (Tue + Fri 20:23 Berlin). This repo is the ground
truth: `METRIC.md` (rules), `workbook/Germany_Apartment_Shortlist.xlsx` (reference), `metric/realestate_metric.py`
(same metric in code), `data/listings.csv` (every scored listing). Driver state: `data/driver_state.json`.

## 0 · Mandate (Rony 2026-11-20)
Buy-to-let apartment in Germany now, a house later. Claude runs the research authoritatively: keep analysing,
collect data, search for opportunities and listings, read the market mood, filter with Rony's metric, and adjust
the metric when the data says so. **Not now:** no emails, inquiries, contact forms, viewing requests, offers,
financing applications or sign-ups with personal data ("emailing comes later"). Rony's separate search for a
rental flat to live in (immowelt/Kleinanzeigen alerts, Brühl/Hürth) is not part of this.

## 1 · Each run
1. `python tests/test_metric.py` must pass before and after any change.
2. **Re-check known leads** (`data/listings.csv`): still online? price changed? new rent/Hausgeld info in the ad?
   Update the row, note it in `research_note`, record status changes in `driver_state.json → lead_history`.
3. **Search for new listings** (read-only; Claude in Chrome main profile, text reads; WebSearch/WebFetch fallback):
   follow the workbook's *Research steps* scope: €34–75k asking prices, markets that pass the *National screen*
   (population trend ≥ 0 %, vacancy ≤ 5 %, or a dated local override), Sparkasse/Volksbank portals, ImmoScout24,
   immowelt, Kleinanzeigen, ohne-makler, ZVG forced-sale portal. Rotate markets so every run covers new ground;
   keep `driver_state.json → coverage` (market → last searched date). One unit on several portals = one lead.
4. **Score** every new or changed row with `metric/realestate_metric.py data/listings.csv --assumptions
   metric/driver_assumptions.json --json`. A listing without a verified cold rent is "Rent missing": record it,
   and capture a rent estimate only in `research_note` (never in `cold_rent`).
5. **Market mood** (Friday runs): current 10-year fixed mortgage rates (Interhyp, Dr. Klein, Bundesbank MFI
   statistics), ECB decisions, price indices (GREIX, vdp, Europace), rent/energy law (GEG, Mietpreisbremse,
   energy certificates), transfer-tax changes by state. Append to `driver_state.json → market_mood` with sources.
6. **Opportunities**: price drop ≥ 8 %, forced sale with a date, rented below local rent with legal increase room,
   lead that moves from Fail to Pass after a price change, negotiation target (price at which BRE-01/KAI-01-type
   leads would pass the budget). Write a short case into `driver_state.json → opportunities`.
7. Update `METRIC.md` §8 results table and README status line; commit and push to `main`.

## 2 · Adjusting the metric
- **Assumption changes** (interest, stress rate, growth rates, owner Hausgeld default, transfer tax, budget gates):
  set them in `metric/driver_assumptions.json` (overrides `DEFAULTS`), with the evidence. Example: when the market
  10-year rate differs from the modelled 4.5 % by ≥ 0.25 pp for two Friday readings, move `interest` to the market
  rate. Log every change in `METRIC.md` §7 (date, old → new, reason, source).
- **Rule changes** (formulas, verdict logic): only when the evidence is strong (e.g. 0 passes for 3 weeks with
  the cause identified, or a rule proven wrong). Change `metric/realestate_metric.py` AND the workbook Models
  sheet the same way (openpyxl), regenerate `tests/workbook_expected.json`, tests must pass, bump the metric
  version in `METRIC.md`. If the workbook can't be updated safely, keep the change in an assumptions file and
  write the formula change as a proposal in `driver_state.json → proposals` instead.
- Never loosen a risk gate silently (budget, after-tax cash floor, spread). Any loosening appears in the summary.
- Placeholders that only Rony knows (marginal tax rate, building share, real budget) stay as they are unless he
  gives the number.

## 3 · Hard stops
No contact with sellers, agents or banks. No personal data typed anywhere. No money. No false statements.
Refused sites stay refused (blocker with retest in `driver_state.json → blockers`). Never write Rony's income or
bank data into this repo. Not financial or tax advice.

## 4 · Outputs
- Commit + push to `main` every run (message: `scout: <date> – <n> new, <n> updated, <passes>`).
- Claude Doc "Real estate log": one dated section per run (mood, top shortlist with links/verdicts, opportunities,
  metric changes).
- Calendar: only real dates, all-day "◆ RE: …" (auction dates of shortlisted forced sales, ECB decisions).
- Push summary ≤ 4 lines.
