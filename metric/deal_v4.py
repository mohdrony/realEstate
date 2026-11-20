"""Deal screen v4 (2026-11-20): self-funding, discount / value-add and long-horizon comparison with an ETF.

Built on top of the v3 metric (metric/realestate_metric.py, unchanged). v3 answers "does the listing pass at
asking price?"; v4 answers "is this a deal worth chasing, and at what price?".

Extra optional columns in data/listings.csv (empty = no discount, no renovation):
    market_value        estimated value after any renovation (comparable sales); empty = price
    renovation_cost     own-cash renovation budget, EUR; empty = 0
    rent_after          expected cold rent per month after renovation / re-letting; empty = cold_rent
    drive_min_from_bruehl   driving minutes from Brühl (value-add should be within ~60-75 min)

Usage:
    python metric/deal_v4.py data/listings.csv
    python metric/deal_v4.py data/examples_v4.csv --json
"""
from __future__ import annotations

import argparse
import csv
import json
import math

V4_DEFAULTS = {
    "down": 0.20,                 # share of price paid by you; purchase costs and renovation always own cash
    "interest": 0.045, "repay": 0.02, "fixed_years": 10, "refi": 0.045,
    "notary": 0.02, "reserve": 3000,
    "owner_hausgeld_default": 80, "upkeep": 25, "management": 0, "rent_loss": 0.05,
    "rent_growth": 0.02, "value_growth": 0.01, "sell_cost": 0.06,
    "tax": 0.35, "building_share": 0.75, "afa": 0.02,
    "etf": 0.07, "etf_tax": 0.26375 * 0.7,
    # gates
    "max_own_cash": 28000,        # cash you can put in (incl. purchase costs, renovation, reserve)
    "min_after_tax_cash": 0.0,    # self-funding: year-1 cash after rent, costs, full loan payment, tax
    "min_discount": 0.15,         # unicorn: (value - price - renovation) / value
    "min_irr10": 0.10,            # unicorn: yearly return on own cash if sold after 10 years
    "max_drive_min": 75,          # value-add only: you manage the works yourself
    "overrun": 0.5,               # stress: renovation +50 %
}


def _num(x):
    x = (x or "").strip() if isinstance(x, str) else x
    return float(x) if x not in (None, "") else None


def irr(flows):
    npv = lambda r: sum(c / (1 + r) ** t for t, c in enumerate(flows))
    lo, hi = -0.95, 3.0
    if npv(lo) * npv(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def simulate(price, value, reno, rent_m, owner_hg, transfer_tax, commission_rate, commission_fixed,
             a, years):
    """Annual model, same mechanics as simulator/model.py. Returns own cash, cash rows, IRR, wealth, ETF."""
    acq = price * (1 + transfer_tax + a["notary"] + commission_rate) + commission_fixed
    loan = price * (1 - a["down"])
    own = acq - loan + reno + a["reserve"]
    afa = (acq + reno) * a["building_share"] * a["afa"]   # renovation soon after purchase is depreciated
    costs0 = (owner_hg + a["upkeep"] + a["management"]) * 12
    bal, i = loan, a["interest"]
    pay = loan * (a["interest"] + a["repay"])
    term = math.log(pay / (pay - loan * i)) / math.log(1 + i) if loan > 0 and pay > loan * i else 99
    side, basis = a["reserve"], a["reserve"]
    flows, cash_m = [-own], []
    for y in range(1, years + 1):
        if y == a["fixed_years"] + 1 and bal > 0:
            i = a["refi"]
            n = max(term - a["fixed_years"], 1)
            pay = bal * i / (1 - (1 + i) ** -n) if i > 0 else bal / n
        g = (1 + a["rent_growth"]) ** (y - 1)
        noi = rent_m * 12 * g * (1 - a["rent_loss"]) - costs0 * g
        it = bal * i
        pr = min(max(pay - it, 0), bal)
        bal -= pr
        cash = noi - it - pr - (noi - it - afa) * a["tax"]
        cash_m.append(cash / 12)
        side = side * (1 + a["etf"]) + cash
        basis += cash
        flows.append(cash)
    exit_net = value * (1 + a["value_growth"]) ** years * (1 - a["sell_cost"]) - bal
    flows[-1] += exit_net + a["reserve"]
    side_after = side - max(side - basis, 0) * a["etf_tax"]
    wealth = exit_net + side_after
    ev = own * (1 + a["etf"]) ** years
    etf = ev - (ev - own) * a["etf_tax"]
    return dict(own=own, cash_m=cash_m, irr=irr(flows), wealth=wealth, etf=etf, loan=loan, acq=acq)


def _price_for(target_fn, hi):
    """Highest price (to the euro) at which target_fn(price) is True, searching 0..hi."""
    if target_fn(hi):
        return hi
    lo = 0.0
    if not target_fn(lo + 1):
        return None
    for _ in range(40):
        mid = (lo + hi) / 2
        if target_fn(mid):
            lo = mid
        else:
            hi = mid
    return lo


def evaluate_deal(row: dict, a: dict) -> dict:
    price = _num(row.get("price"))
    value = _num(row.get("market_value")) or price
    reno = _num(row.get("renovation_cost")) or 0.0
    rent = _num(row.get("rent_after")) or _num(row.get("cold_rent"))
    owner = _num(row.get("owner_hausgeld_verified")) or a["owner_hausgeld_default"]
    tt = _num(row.get("transfer_tax_rate")) or 0.0
    cr = _num(row.get("commission_rate")) or 0.0
    cf = _num(row.get("commission_fixed")) or 0.0
    drive = _num(row.get("drive_min_from_bruehl"))
    out = {"id": row.get("id"), "location": row.get("location"), "price": price, "market_value": value,
           "renovation_cost": reno, "rent_used": rent}
    if rent is None:
        out["verdict_v4"] = "Rent missing"
        return out

    sim = lambda p, v=value, r=reno, yrs=10: simulate(p, v, r, rent, owner, tt, cr, cf, a, yrs)
    s10, s30 = sim(price), sim(price, yrs=30)
    stress = sim(price, value * 0.95, reno * (1 + a["overrun"]))
    discount = (value - price - reno) / value if value else 0.0
    all_in = price * (1 + tt + a["notary"] + cr) + cf + reno
    self_funding = s10["cash_m"][0] >= a["min_after_tax_cash"]

    p_self = _price_for(lambda p: sim(p)["cash_m"][0] >= a["min_after_tax_cash"], price * 1.5)
    p_unicorn = _price_for(lambda p: (sim(p)["cash_m"][0] >= a["min_after_tax_cash"]
                                      and (value - p - reno) / value >= a["min_discount"]
                                      and (sim(p)["irr"] or -1) >= a["min_irr10"]), price * 1.5)

    flags = []
    if s10["own"] > a["max_own_cash"]:
        flags.append(f"own cash €{s10['own']:,.0f} > €{a['max_own_cash']:,.0f}")
    if reno > 0 and drive is not None and drive > a["max_drive_min"]:
        flags.append(f"value-add {drive:.0f} min away")
    if reno > 0 and (stress["irr"] or -1) < 0.05:
        flags.append("renovation overrun breaks it")

    budget_ok = s10["own"] <= a["max_own_cash"]
    unicorn = (self_funding and discount >= a["min_discount"] and (s10["irr"] or -1) >= a["min_irr10"]
               and budget_ok)
    if unicorn:
        verdict = "Unicorn: discount + self-funding"
    elif self_funding and s30["wealth"] >= s30["etf"] and budget_ok:
        verdict = "Pass: self-funding, beats ETF over 30 yrs"
    elif self_funding and budget_ok:
        verdict = "Watch: self-funding but loses to ETF over 30 yrs"
    elif p_self and p_self >= price * 0.85:
        verdict = f"Watch: self-funding at ≤ €{p_self:,.0f}"
    elif not budget_ok:
        verdict = "Fail: needs more own cash"
    else:
        verdict = "Fail: not self-funding"

    out.update(
        own_cash=s10["own"], all_in_cost=all_in, gross_yield_all_in=rent * 12 / all_in,
        discount=discount, cash_y1=s10["cash_m"][0], irr10=s10["irr"], irr30=s30["irr"],
        wealth30=s30["wealth"], etf30=s30["etf"], irr10_overrun=stress["irr"],
        price_self_funding=p_self, price_unicorn=p_unicorn, flags="; ".join(flags), verdict_v4=verdict)
    return out


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("listings")
    p.add_argument("--assumptions", help="JSON overriding V4_DEFAULTS keys")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    a = dict(V4_DEFAULTS)
    if args.assumptions:
        with open(args.assumptions, encoding="utf-8") as f:
            a.update({k: v for k, v in json.load(f).items() if k in V4_DEFAULTS})
    res = [evaluate_deal(r, a) for r in load_rows(args.listings)]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return
    pct = lambda x: f"{x*100:5.1f}%" if isinstance(x, float) else "  n.a."
    eur = lambda x: f"€{x:,.0f}" if isinstance(x, (int, float)) else "n.a."
    print(f"{'ID':8} {'Own cash':>9} {'Disc.':>6} {'€/mo y1':>8} {'IRR10':>6} {'30y flat/ETF':>15} {'Self-fund ≤':>12}  Verdict")
    for r in res:
        if "own_cash" not in r:
            print(f"{r['id']:8} {'':>9} {'':>6} {'':>8} {'':>6} {'':>15} {'':>12}  {r['verdict_v4']}")
            continue
        print(f"{r['id']:8} {eur(r['own_cash']):>9} {pct(r['discount'])} {r['cash_y1']:8.0f} {pct(r['irr10'])} "
              f"{eur(r['wealth30'])+'/'+eur(r['etf30']):>15} {eur(r['price_self_funding']):>12}  {r['verdict_v4']}"
              + (f"  [{r['flags']}]" if r['flags'] else ""))


if __name__ == "__main__":
    main()
