"""Long-horizon flat vs ETF model (annual steps). Mirrors simulator/index.html."""
DEF = dict(size=40, price_m2=1500, rent_m2=10.0, down=0.20, interest=0.045, repay=0.02, fixed_years=10,
           refi=0.045, owner_hg_m2=2.0, upkeep_m2=0.625, mgmt=0, loss=0.05,
           rent_growth=0.02, value_growth=0.01, tax=0.35, building_share=0.75, afa=0.02,
           transfer_tax=0.065, notary=0.02, commission=0.0, sell_cost=0.06, reserve=2900,
           etf=0.07, years=30, extra_repay=0, assess=0, assess_year=15)

def run(**kw):
    p = dict(DEF); p.update(kw)
    price = p['size']*p['price_m2']; rent0 = p['size']*p['rent_m2']*12
    costs0 = (p['size']*(p['owner_hg_m2']+p['upkeep_m2'])+p['mgmt'])*12
    acq = price*(1+p['transfer_tax']+p['notary']+p['commission'])
    loan = price*(1-p['down']); own = acq-loan+p['reserve']
    afa = acq*p['building_share']*p['afa']
    bal = loan; i = p['interest']; pay = loan*(p['interest']+p['repay'])
    import math
    # original payoff term in years (annuity); after refinancing keep the same payoff date
    term = math.log(pay/(pay-loan*i))/math.log(1+i) if loan > 0 and pay > loan*i else 99
    side = p['reserve']; side_basis = p['reserve']; rows = []
    for y in range(1, p['years']+1):
        if y == p['fixed_years']+1 and bal > 0:
            i = p['refi']; n = max(term-p['fixed_years'], 1)
            pay = bal*i/(1-(1+i)**-n) if i > 0 else bal/n
        noi = rent0*(1+p['rent_growth'])**(y-1)*(1-p['loss']) - costs0*(1+p['rent_growth'])**(y-1)
        it = bal*i; pr = min(max(pay-it, 0), bal)
        extra = min(p['extra_repay'], bal-pr) if bal-pr > 0 else 0
        bal -= pr+extra
        afa_y = afa if y <= 50 else 0
        tax = (noi-it-afa_y)*p['tax']
        cash = noi-it-pr-extra-tax-(p['assess'] if y == p['assess_year'] else 0)
        side = side*(1+p['etf'])+cash; side_basis += cash
        value = price*(1+p['value_growth'])**y
        rows.append(dict(year=y, noi_m=noi/12, cash_m=cash/12, balance=bal, value=value))
    etf_tax = 0.26375*0.7
    side_after = side-max(side-side_basis, 0)*etf_tax
    wealth = value*(1-p['sell_cost'])-bal+side_after
    etf_v = own*(1+p['etf'])**p['years']; etf_after = etf_v-(etf_v-own)*etf_tax
    payoff = next((r['year'] for r in rows if r['balance'] <= 0.5), None)
    pos = next((r['year'] for r in rows if r['cash_m'] >= 0), None)
    return dict(price=price, rent_m=rent0/12, gross=rent0/price, own=own, loan=loan, cash_y1=rows[0]['cash_m'],
                first_positive=pos, payoff=payoff, wealth=wealth, etf=etf_after, rows=rows)

if __name__ == '__main__':
    r = run(); print({k: v for k, v in r.items() if k != 'rows'})
    print('cash/mo by yr', [round(x['cash_m']) for x in r['rows']][::3])
