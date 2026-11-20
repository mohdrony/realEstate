# realEstate

Central repository for the Germany buy-to-let apartment search: the screening metric, the shortlist workbook and the listing data.

## Contents

| Path | What it is |
|---|---|
| `METRIC.md` | How a listing is judged: costs, tests, verdict rules, assumptions, change log, current results |
| `workbook/Germany_Apartment_Shortlist.xlsx` | Main workbook: Shortlist, Models (all formulas), Rejected, Market evidence, Research steps, National screen (10,956 municipalities) |
| `data/listings.csv` | Inputs for every scored listing (price, rent, fees, Hausgeld, source link, research note) |
| `metric/realestate_metric.py` | Same metric in Python, for scoring new listings quickly |
| `tests/test_metric.py` | Checks the Python metric gives the same numbers as the workbook |

## Score listings

```bash
python metric/realestate_metric.py data/listings.csv
python metric/realestate_metric.py data/listings.csv --json
python metric/realestate_metric.py data/listings.csv --assumptions my_assumptions.json
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
