"""Buy-to-let screening metric for small German apartments.

Python mirror of the "Models" sheet in workbook/Germany_Apartment_Shortlist.xlsx.
The workbook and this module must give the same numbers; tests/test_metric.py
checks that against values recalculated from the workbook.

Usage:
    python metric/realestate_metric.py data/listings.csv
    python metric/realestate_metric.py data/listings.csv --assumptions my.json
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field, asdict

# ---------------------------------------------------------------------------
# Assumptions (all editable; mirror Models!C5:C18, C65:C70, C89:C92)
# ---------------------------------------------------------------------------
DEFAULTS = {
    "budget_total": 70000,          # total cash + loan budget incl. costs and reserve
    "notary_rate": 0.02,            # notary and land register, share of price
    "reserve": 5000,                # initial repair / cash reserve (budget only, not in yields)
    "rent_loss_rate": 0.05,         # provision for vacancy / arrears
    "upkeep_monthly": 25,           # interior upkeep, owner's own
    "management_monthly": 30,       # external letting management
    "self_managed": 1,              # 1 = you manage yourself (management fee dropped)
    "owner_hausgeld_default": 80,   # non-recoverable Hausgeld if split unknown
    "ltv": 0.80,                    # loan / purchase price
    "interest": 0.045,              # initial loan interest
    "repayment": 0.02,              # initial annual repayment
    "stress_interest": 0.065,       # refinancing stress rate
    "stress_vacant_months": 3,
    "special_assessment": 10000,
    "building_share": 0.75,         # depreciable building share of acquisition cost (placeholder)
    "afa_rate": 0.02,               # 2% for buildings 1925-2022, 2.5% if pre-1925
    "tax_rate": 0.35,               # marginal income tax rate (placeholder)
    "min_spread": 0.0,              # net yield must be >= interest + this
    "min_after_tax_cash": 0.0,      # €/month after interest, repayment, tax effect
    "growth_rent": 0.02,            # rent and running-cost growth p.a.
    "growth_value": 0.01,           # property value growth p.a.
    "selling_cost": 0.06,           # at exit
    "hold_years": 10,               # fixed: private sale tax-free after 10 years
}


@dataclass
class Listing:
    id: str
    location: str
    price: float
    area_m2: float | None
    cold_rent: float | None
    transfer_tax_rate: float
    commission_rate: float
    commission_fixed: float
    hausgeld_total: float | None
    owner_hausgeld_verified: float | None
    extra: dict = field(default_factory=dict)


def _num(x):
    if x is None:
        return None
    x = str(x).strip()
    return float(x) if x else None


def load_listings(path: str) -> list[Listing]:
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append(Listing(
                id=r["id"], location=r["location"], price=_num(r["price"]),
                area_m2=_num(r.get("area_m2")), cold_rent=_num(r.get("cold_rent")),
                transfer_tax_rate=_num(r["transfer_tax_rate"]) or 0.0,
                commission_rate=_num(r.get("commission_rate")) or 0.0,
                commission_fixed=_num(r.get("commission_fixed")) or 0.0,
                hausgeld_total=_num(r.get("hausgeld_total")),
                owner_hausgeld_verified=_num(r.get("owner_hausgeld_verified")),
                extra={k: r.get(k) for k in ("rent_evidence", "source_url", "research_note")},
            ))
    return out


def irr(flows: list[float], lo=-0.99, hi=1.0, tol=1e-10) -> float | None:
    """Bisection IRR (one sign change expected: outflow first, inflows later)."""
    def npv(rate):
        return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < tol:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def evaluate(l: Listing, a: dict) -> dict:
    mgmt = a["management_monthly"] * (1 - a["self_managed"])
    owner_hg = l.owner_hausgeld_verified if l.owner_hausgeld_verified is not None else a["owner_hausgeld_default"]

    transfer_tax = l.price * l.transfer_tax_rate
    notary = l.price * a["notary_rate"]
    commission = l.price * l.commission_rate + l.commission_fixed
    acquisition = l.price + transfer_tax + notary + commission        # excl. reserve
    total_incl_reserve = acquisition + a["reserve"]                   # budget check

    loan = l.price * a["ltv"]
    debt_monthly = loan * (a["interest"] + a["repayment"]) / 12
    interest_monthly = loan * a["interest"] / 12
    repayment_monthly = loan * a["repayment"] / 12
    afa_monthly = acquisition * a["building_share"] * a["afa_rate"] / 12

    r = {"id": l.id, "location": l.location, "price": l.price,
         "total_incl_reserve": total_incl_reserve,
         "max_price_for_budget": (a["budget_total"] - a["reserve"] - l.commission_fixed)
                                 / (1 + l.transfer_tax_rate + a["notary_rate"] + l.commission_rate)}

    if l.cold_rent is None:
        r.update(screen="Fail: over total budget" if total_incl_reserve > a["budget_total"] else "Rent missing")
        return r

    noi_m = l.cold_rent * (1 - a["rent_loss_rate"]) - owner_hg - a["upkeep_monthly"] - mgmt
    net_yield = noi_m * 12 / acquisition
    spread = net_yield - a["interest"]
    cash_after_debt = noi_m - debt_monthly
    taxable_m = noi_m - interest_monthly - afa_monthly
    tax_effect_m = -taxable_m * a["tax_rate"]
    after_tax_cash = cash_after_debt + tax_effect_m
    stressed_cash = noi_m - loan * (a["stress_interest"] + a["repayment"]) / 12
    stressed_after_tax = stressed_cash - (noi_m - loan * a["stress_interest"] / 12 - afa_monthly) * a["tax_rate"]
    max_price_pos_lev = (noi_m * 12 / (a["interest"] + a["min_spread"]) - l.commission_fixed) / (
        1 + l.transfer_tax_rate + a["notary_rate"] + l.commission_rate)

    # 10-year total return (annual, after tax on rent; exit tax-free after 10 years)
    i, g, vg, tr = a["interest"], a["growth_rent"], a["growth_value"], a["tax_rate"]
    noi_y1, afa_y, pay_y = noi_m * 12, afa_monthly * 12, debt_monthly * 12
    n = 10
    value_exit = l.price * (1 + vg) ** n
    bal = lambda t: loan * (1 + i) ** t - pay_y * ((1 + i) ** t - 1) / i
    lev = [-(total_incl_reserve - loan)]
    unl = [-total_incl_reserve]
    for t in range(1, n + 1):
        noi_t = noi_y1 * (1 + g) ** (t - 1)
        int_t = bal(t - 1) * i
        lev.append(noi_t - pay_y - (noi_t - int_t - afa_y) * tr
                   + (value_exit * (1 - a["selling_cost"]) - bal(n) + a["reserve"] if t == n else 0))
        unl.append(noi_t - (noi_t - afa_y) * tr
                   + (value_exit * (1 - a["selling_cost"]) + a["reserve"] if t == n else 0))
    irr_fin, irr_cash = irr(lev), irr(unl)
    tr_vs_loan = irr_cash - i * (1 - tr) if irr_cash is not None else None

    if total_incl_reserve > a["budget_total"]:
        screen = "Fail: over total budget"
    elif spread < a["min_spread"] and (tr_vs_loan is None or tr_vs_loan < 0):
        screen = "Fail: yield and total return below loan rate"
    elif spread < a["min_spread"]:
        screen = "Warning: negative carry; total return covers loan"
    elif after_tax_cash < a["min_after_tax_cash"]:
        screen = "Warning: after-tax cash below floor"
    else:
        screen = "Pass; documents pending"

    r.update(cold_rent=l.cold_rent, owner_hausgeld=owner_hg, noi_monthly=noi_m,
             gross_yield=l.cold_rent * 12 / acquisition, net_yield=net_yield, spread=spread,
             cash_after_debt=cash_after_debt, cash_after_interest=noi_m - interest_monthly,
             after_tax_cash=after_tax_cash, stressed_after_tax_cash=stressed_after_tax,
             vacancy_year_cash=(l.cold_rent * (12 - a["stress_vacant_months"])
                                - (owner_hg + a["upkeep_monthly"] + mgmt + debt_monthly) * 12
                                - max((l.hausgeld_total or 0) - owner_hg, 0) * a["stress_vacant_months"])
                               if l.hausgeld_total is not None else None,
             assessment_year_cash=cash_after_debt * 12 - a["special_assessment"],
             max_price_positive_leverage=max_price_pos_lev,
             irr_financed=irr_fin, irr_cash=irr_cash, total_return_vs_after_tax_loan=tr_vs_loan,
             screen=screen)
    return r


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("listings")
    p.add_argument("--assumptions", help="JSON file overriding DEFAULTS keys")
    p.add_argument("--json", action="store_true", help="print full results as JSON")
    args = p.parse_args()
    a = dict(DEFAULTS)
    if args.assumptions:
        with open(args.assumptions, encoding="utf-8") as f:
            a.update(json.load(f))
    results = [evaluate(l, a) for l in load_listings(args.listings)]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    pct = lambda x: f"{x*100:5.1f}%" if isinstance(x, float) else "   n.a."
    eur = lambda x: f"{x:8.0f}" if isinstance(x, (int, float)) else "    n.a."
    print(f"{'ID':7} {'Total':>8} {'NetYld':>7} {'Spread':>7} {'€/mo AT':>8} {'IRR fin':>7} {'IRR cash':>8}  Screen")
    for r in results:
        print(f"{r['id']:7} {eur(r['total_incl_reserve'])} {pct(r.get('net_yield'))} {pct(r.get('spread'))} "
              f"{eur(r.get('after_tax_cash'))} {pct(r.get('irr_financed'))} {pct(r.get('irr_cash'))}   {r['screen']}")


if __name__ == "__main__":
    main()
