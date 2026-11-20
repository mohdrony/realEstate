# realEstate

Central repository for the Germany buy-to-let apartment search: the screening metric, the shortlist workbook and the listing data.

## Contents

| Path | What it is |
|---|---|
| `METRIC.md` | How a listing is judged: costs, tests, verdict rules, assumptions, change log, current results |
| `workbook/Germany_Apartment_Shortlist.xlsx` | Main workbook: Shortlist, Models (all formulas), Rejected, Market evidence, Research steps, National screen (10,956 municipalities) |
| `data/listings.csv` | Inputs for every scored listing (price, rent, fees, Hausgeld, source link, research note) |
| `metric/realestate_metric.py` | Same metric in Python, for scoring new listings quickly |
| `metric/deal_v4.py` | v4 deal screen: self-funding, discount / value-add, price targets, 30-yr flat vs ETF (`METRIC.md` §9) |
| `data/examples_v4.csv` | Five teaching examples for the v4 screen (not listings) |
| `tests/test_metric.py` | Checks the Python metric gives the same numbers as the workbook |
| `DRIVER.md`, `data/driver_state.json`, `metric/driver_assumptions.json` | Scheduled scout: playbook (incl. channel radar §1b), state, assumption overrides |
| `outreach/` | Templates Rony sends himself (property managers, agent search mandate, wanted ad, bank) + `tracker.csv` the scout reads |
| `simulator/index.html` | Interactive flat-vs-ETF simulator with sliders (open in a browser) |
| `simulator/model.py` | Same long-horizon model in Python; the page's JavaScript gives identical results |

## Score listings

```bash
python metric/realestate_metric.py data/listings.csv
python metric/realestate_metric.py data/listings.csv --json
python metric/realestate_metric.py data/listings.csv --assumptions my_assumptions.json
python metric/deal_v4.py data/listings.csv          # v4 verdicts and price targets
python tests/test_metric.py && python tests/test_deal_v4.py
```

An assumptions file overrides any key in `DEFAULTS`, for example:

```json
{ "tax_rate": 0.42, "self_managed": 0, "budget_total": 100000 }
```

To add a listing, append a row to `data/listings.csv`. Leave `cold_rent` empty if the rent isn't verified; leave `owner_hausgeld_verified` empty to use the €80 default.

## Keeping workbook and code in step

The workbook is the reference. If a formula changes there, change `metric/realestate_metric.py` to match, recalculate the workbook, regenerate `tests/workbook_expected.json`, and run `python tests/test_metric.py`.

## Status (13 Nov 2026)

Two numeric passes: **WUP-01** Wuppertal-Elberfeld (€29k; whole-building renovation risk) and **DOR-01** Dortmund (narrow). Kaiserslautern passes on yield but is over budget at the asking price. See `METRIC.md` §8.

Not financial or tax advice.
