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
