"""v4 deal screen: ties to the simulator model and checks verdict logic on the teaching examples.
Run: python tests/test_deal_v4.py"""
import math, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "metric"), str(ROOT / "simulator")]
from deal_v4 import V4_DEFAULTS, evaluate_deal, load_rows, simulate  # noqa: E402
import model  # noqa: E402


def test_matches_simulator():
    a = dict(V4_DEFAULTS, reserve=2900)
    for years in (10, 30):
        v4 = simulate(60000, 60000, 0, 400, 80, 0.065, 0, 0, a, years)
        sim = model.run(years=years)
        assert math.isclose(v4["wealth"], sim["wealth"], rel_tol=1e-9), (years, v4["wealth"], sim["wealth"])
        assert math.isclose(v4["etf"], sim["etf"], rel_tol=1e-9)
        assert math.isclose(v4["cash_m"][0], sim["cash_y1"], rel_tol=1e-9)


def test_example_verdicts():
    res = {r["id"]: evaluate_deal(r, V4_DEFAULTS) for r in load_rows(ROOT / "data" / "examples_v4.csv")}
    assert res["EX-A"]["verdict_v4"].startswith("Fail")
    assert res["EX-B"]["verdict_v4"].startswith("Pass")
    assert res["EX-C"]["verdict_v4"].startswith("Unicorn")
    assert "away" in res["EX-E"]["flags"]


if __name__ == "__main__":
    test_matches_simulator(); test_example_verdicts()
    print("OK: v4 deal screen matches simulator; example verdicts as expected")
