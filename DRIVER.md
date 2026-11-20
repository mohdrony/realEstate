# Investment scout — driver playbook (v3, 2026-11-20)

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
1. `python tests/test_metric.py` and `python tests/test_deal_v4.py` must pass before and after any change.
2. **Re-check known leads** (`data/listings.csv`): still online? price changed? new rent/Hausgeld info in the ad?
   Update the row, note it in `research_note`, record status changes in `driver_state.json → lead_history`.
3. **Search for new listings** (read-only; Claude in Chrome main profile, text reads; WebSearch/WebFetch fallback):
   follow the workbook's *Research steps* scope: €34–75k asking prices, markets that pass the *National screen*
   (population trend ≥ 0 %, vacancy ≤ 5 %, or a dated local override), Sparkasse/Volksbank portals, ImmoScout24,
   immowelt, Kleinanzeigen, ohne-makler, ZVG forced-sale portal — **work through the channel radar in §1b** (every
   "each run" channel every run, the rest on their rhythm). Rotate markets so every run covers new ground;
   keep `driver_state.json → coverage` (market → last searched date) and `→ channels` (channel → last checked,
   leads found). One unit on several portals = one lead; fill `channel` with where it was found first.
   **Unicorn hunting (v4, from 2026-11-20):** also search for flats likely to sell below value — renovation-needed
   or dated interiors (renovierungsbedürftig, sanierungsbedürftig, Modernisierungsbedarf), inheritance sales
   (Erbengemeinschaft, Nachlass), private sellers (provisionsfrei, ohne Makler), listings online for months or
   with price cuts, poor energy class priced at a discount. Value-add leads are only worth keeping within about
   75 minutes of Brühl (NRW first: Rhein-Erft, Köln, Bonn, Düsseldorf, Wuppertal, Ruhr, Aachen). Own-cash budget
   ~€28k (v4) — asking prices up to ~€75k stay in scope.
4. **Score** every new or changed row with `metric/realestate_metric.py data/listings.csv --assumptions
   metric/driver_assumptions.json --json` (v3) **and** `metric/deal_v4.py data/listings.csv --json` (v4). **Rank
   by the v4 verdict** (Unicorn > Pass > Watch > Fail); v3 stays as the asking-price check. For flats that need
   work or look underpriced, fill `market_value` (from 2–3 comparable sales or asking prices of renovated flats in
   the same area, sources in `research_note`), `renovation_cost` (rough €/m² by scope), `rent_after` (local rent
   for renovated flats) and `drive_min_from_bruehl`. Mark every such estimate as an estimate in `research_note`. A listing without a verified cold rent is "Rent missing": record it,
   and capture a rent estimate only in `research_note` (never in `cold_rent`).
5. **Market mood** (Friday runs): current 10-year fixed mortgage rates (Interhyp, Dr. Klein, Bundesbank MFI
   statistics), ECB decisions, price indices (GREIX, vdp, Europace), rent/energy law (GEG, Mietpreisbremse,
   energy certificates), transfer-tax changes by state. Append to `driver_state.json → market_mood` with sources.
6. **Opportunities**: any v4 *Unicorn*; any *Watch* whose asking price drops to its `price_self_funding`; price drop ≥ 8 %, forced sale with a date, rented below local rent with legal increase room,
   lead that moves from Fail to Pass after a price change, negotiation target (price at which BRE-01/KAI-01-type
   leads would pass the budget). Write a short case into `driver_state.json → opportunities`.
7. Update `METRIC.md` §8 results table and README status line; commit and push to `main`.

## 1b · Channel radar (from 2026-11-20)
Good deals rarely reach the big portals. The radar has two halves: channels the scout reads itself, and channels
only Rony can work (outreach — templates in `outreach/`, log in `outreach/tracker.csv`).

**A · Scout reads (read-only)**

| Channel | Rhythm | How | `channel` value |
|---|---|---|---|
| **ZVG portal** (zvg-portal.de → Termine suchen) | each run | Land = Nordrhein-Westfalen first, then RLP/Saarland/Niedersachsen. Objekt = *Eigentumswohnung (1 bis 2 Zimmer)* and *(3 bis 4 Zimmer)*. All Verfahrensarten — note the type: *Aufhebung der Gemeinschaft* (Teilungsversteigerung: heirs/divorce), *Insolvenzverwalter*, *Erbe*, *Zwangsvollstreckung*. Courts within ~75 min of Brühl first (Brühl, Köln, Bonn, Siegburg, Bergheim, Kerpen, Euskirchen, Düren, Aachen, Düsseldorf, Neuss, Mönchengladbach, Leverkusen, Solingen, Wuppertal, Gummersbach …). Read the Gutachten PDF when linked. | `zvg` |
| **Private auction houses** (Westdeutsche Grundstücksauktionen AG, Köln; Deutsche Grundstücksauktionen AG; Norddeutsche / Sächsische Grundstücksauktionen; Karhausen) | each run (catalogues appear ~6 weeks before each auction) | Flats with low minimum bid (Mindestgebot). Note auction date, Mindestgebot, Hausgeld, rent, buyer premium (Aufgeld, add to `commission_rate`). | `auction-house` |
| **Bank portals** (Sparkasse Immobilien / S-Immobilien, Volksbank/Raiffeisen VR-Immobilien, Kreissparkasse Köln, Sparkasse KölnBonn) | each run | Region filter around Brühl; banks also sell repossessed (Verwertung) flats here before any other portal. | `bank` |
| **Private sellers**: Kleinanzeigen (Immobilien → Eigentumswohnungen, "privat"), ohne-makler.net, ImmoScout24 / immowelt filtered to private sellers | each run | Newest first; private listings are often under-priced, badly written and gone within a day. | `private` |
| **Big portals** (ImmoScout24, immowelt, Immonet) | each run | Keywords from §1.3 unicorn list; sort by newest and by "price reduced"; flats online > 90 days. | `portal` |
| **Local agent sites** (small agents in Rhein-Erft, Köln, Bonn) | weekly | Check "Neu im Angebot" pages; agents post here before portals. Keep a list in `driver_state.json → channels.agents`. | `agent` |
| **Public sellers** (BImA bundesimmobilien.de, city/Kreis property offices, NRW.BANK/municipal housing companies' sales) | monthly | Mostly houses/land — keep only flats, or lots that fit the later "house" plan (note, don't score). | `public` |
| **Price-drop watch** (own history) | each run | Any lead in `listings.csv` whose price fell, or that reappears after going offline. | — |

**B · Rony works (scout never contacts anyone)** — templates in `outreach/`:
Hausverwaltungen letter · agent search mandate (Suchauftrag) · wanted ad (Kleinanzeigen, Facebook groups,
Sparkasse/supermarket boards) · own bank: pre-approval (Finanzierungsbestätigung) and ask to be on their
Verwertung list. Each run, read `outreach/tracker.csv`: any lead Rony logged there (an agent's or manager's tip)
gets a `listings.csv` row and is scored like any other; remind him in the summary of follow-ups older than 3 weeks.

**Scoring forced sales and auctions** (v4 unchanged):
- ZVG: `market_value` = Verkehrswert from the Gutachten (also in the note: Gutachten date, condition, whether
  viewed inside). `price` = the realistic bid: 70 % of Verkehrswert for a first date, 50 % for a later date
  (no 5/10 or 7/10 limits). `commission_rate` = 0; leave `notary` at 2 % (court and Grundbuch fees). `rent_evidence`
  = rent in the Gutachten if the flat is let, otherwise "Rent missing" as usual.
- Auction house: `price` = Mindestgebot; `commission_rate` = buyer premium.
- **Max bid** = the v4 `price_self_funding` (and `price_unicorn` for the unicorn level) — write both into the
  opportunity case. A ZVG/auction lead goes into `opportunities` when its max bid ≥ realistic bid and the date is
  ≥ 10 days away; also put the date in the calendar as "◆ RE: Versteigerung <town> <Aktenzeichen>".
- Flag every auction lead with: not viewed inside? tenant/occupant? Hausgeld arrears (a sign of a weak WEG; the
  WEG's claims up to 5 % of Verkehrswert are paid first from the proceeds)? 10 % Sicherheitsleistung (Verkehrswert × 0.1) needed on the day.

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
