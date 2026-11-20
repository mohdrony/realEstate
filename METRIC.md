# Screening metric (v3, 13 Nov 2026)

How a small German buy-to-let apartment is judged. The workbook (`workbook/Germany_Apartment_Shortlist.xlsx`, sheet **Models**) and the Python version (`metric/realestate_metric.py`) implement the same formulas; `tests/test_metric.py` checks they agree.

## 1. Costs

| Item | Formula |
|---|---|
| Acquisition cost | price × (1 + transfer tax + 2% notary + commission rate) + fixed commission |
| Total incl. reserve | acquisition cost + €5,000 reserve, used **only** for the €70k budget check |
| Owner Hausgeld | verified seller split if known, otherwise €80/month |
| Monthly net operating income (NOI) | cold rent × (1 − 5% rent loss) − owner Hausgeld − €25 upkeep − €30 management (dropped when self-managed) |

## 2. Main tests

| Test | Formula | Pass when |
|---|---|---|
| **Budget** | total incl. reserve | ≤ €70,000 |
| **Net yield vs loan rate** (leverage spread) | NOI × 12 ÷ acquisition cost − 4.5% | ≥ 0 |
| **After-tax cash** | NOI − interest − repayment + tax effect | ≥ €0/month |
| **10-yr total return vs after-tax loan cost** | IRR of cash purchase − 4.5% × (1 − tax rate) | ≥ 0 |

Tax effect = −(NOI − interest − depreciation) × marginal tax rate. Depreciation (AfA) = acquisition cost × building share × 2% ÷ 12. A negative result is a refund against salary income.

Repayment is shown as cash out but it builds equity; it is not a cost.

## 3. Verdict

1. **Fail: over total budget** if total incl. reserve > budget.
2. **Rent missing** if no verified cold rent.
3. **Fail: yield and total return below loan rate** if the net yield is below the loan rate **and** the 10-year total return is below the after-tax loan cost.
4. **Warning: negative carry; total return covers loan** if only the net yield is below the loan rate.
5. **Warning: after-tax cash below floor** if monthly after-tax cash is below €0.
6. **Pass; documents pending** otherwise. A pass is numeric only: lease, WEG minutes, planned works and Hausgeld statement must be checked.

## 4. 10-year total return

- Rent and running costs grow 2% a year; property value grows 1% a year; 6% selling costs at exit.
- Loan: 80% of price, 4.5% interest, 2% initial repayment (annuity), balance repaid from the sale.
- Exit after 10 years is tax-free for private owners (§23 EStG); reserve returned at exit.
- Two views: **financed** (IRR on own cash) and **cash purchase** (unlevered IRR).

## 5. Stress checks (information, not vetoes)

Refinancing at 6.5%, three vacant months in a year, a €10k special assessment, rent 10% lower.

## 6. Placeholders to replace with your own numbers

Marginal tax rate (35%), building share (75%), AfA rate (2%, or 2.5% for pre-1925 buildings), self-managed switch (on), growth rates. Not tax or financial advice; check tax treatment with a Steuerberater.

## 7. Changes over time

- **v1 (Oct 2026):** pass if financed pre-tax cash ≥ €50/month, with repayment counted as a cost.
- **v2 (13 Nov):** leverage spread and after-tax cash replaced the €50 target; tax line added.
- **v3 (13 Nov):** reserve taken out of yields; management fee optional; 10-year total return added; fail vs warning split; total return compared with the *after-tax* loan cost.
- **v4 deal screen (20 Nov):** added on top of v3 (v3 unchanged): self-funding as the main test, purchase discount and renovation (value-add), own-cash budget instead of a total budget, 10-year return on own cash, 30-year flat vs ETF, price targets. See §9.

## 8. Results at v3 defaults

| ID | Total incl. reserve | Net yield | Spread | After-tax €/mo | IRR financed | IRR cash | Screen |
|---|---|---|---|---|---|---|---|
| MAN-01 | 69,200 | 3.4% | −1.1% | −52 | 1.7% | 2.5% | Fail: yield and total return |
| SAA-01 | 62,820 | 4.2% | −0.3% | −6 | 1.6% | 2.4% | Fail: yield and total return |
| HER-01 | 64,938 | – | – | – | – | – | Rent missing |
| LEI-01 | 66,089 | – | – | – | – | – | Rent missing |
| BRE-01 | 71,087 | 4.4% | −0.1% | −9 | 2.7% | 2.8% | Fail: over budget |
| KAI-01 | 73,448 | 5.1% | +0.6% | +23 | 3.5% | 3.1% | Fail: over budget |
| WUP-01 | 37,845 | 6.6% | +2.1% | +36 | 5.2% | 3.9% | Pass (renovation risk) |
| DOR-01 | 58,794 | 4.7% | +0.2% | +1 | 2.9% | 2.9% | Pass (narrow) |
| LUN-01 | 71,990 | 4.1% | −0.4% | −15 | 1.8% | 2.5% | Fail: over budget |

## 9. Deal screen v4 (20 Nov 2026) — `metric/deal_v4.py`

v3 asks *does this listing pass at asking price?* v4 asks *is this a deal worth chasing, and at what price?* It follows the plan agreed on 20 Nov: keep an ETF savings plan running, and buy one flat only when it pays for itself, ideally bought below value or improved by renovation.

**Inputs** (optional columns in `data/listings.csv`; empty = no discount, no renovation): `market_value` (value after any renovation, from comparable sales), `renovation_cost`, `rent_after` (cold rent after renovation or re-letting), `drive_min_from_bruehl`.

**Model:** annual steps, identical to `simulator/model.py` (checked by `tests/test_deal_v4.py`). 20% down; purchase costs, renovation and a €3,000 reserve from own cash; renovation depreciated with the purchase; 4.5% interest, 2% repayment, refinanced after 10 years and paid off on the original date; rent and costs +2%/yr, value +1%/yr; 35% tax; monthly surpluses invested in the ETF (7%).

| Test | Rule |
|---|---|
| **Self-funding** | Year-1 cash after rent, costs, full loan payment and tax ≥ €0 |
| **Own cash** | Down payment + purchase costs + renovation + reserve ≤ €28,000 |
| **Discount** | (market value − price − renovation) ÷ market value |
| **Return on own cash** | IRR if sold after 10 years (sale tax-free after 10 years) |
| **Long run** | Wealth after 30 years (sale − loan + invested surpluses) vs the same own cash in an ETF |
| **Stress (value-add)** | Renovation +50% and value −5%: 10-year IRR should stay ≥ 5% |
| **Distance (value-add)** | ≤ 75 minutes from Brühl, so the works can be managed in person |

**Verdicts**

1. **Unicorn:** self-funding, discount ≥ 15%, 10-year IRR ≥ 10%, own cash within budget.
2. **Pass:** self-funding, beats the ETF over 30 years, own cash within budget.
3. **Watch:** self-funding but loses to the ETF over 30 years, or becomes self-funding at a price ≤ 15% below asking (`price_self_funding` = negotiation target).
4. **Fail:** needs more own cash, or not self-funding even 15% below asking.

Each row also gets `price_unicorn` (highest price that would make it a unicorn) and flags (budget, distance, overrun).

Rule of thumb behind it: at 20% down and 4.5% interest, a flat pays for itself when yearly cold rent is about 7.7% of the purchase price (8.5% at 10% down, 6.9% at 30%, 5.3% at 50%). Returns of 10–15% on own cash come from the purchase discount, not from the loan.

`data/examples_v4.csv` holds the five teaching cases from 20 Nov (typical, self-funding, 20% below value, value-add near and far). They are examples, not listings.
