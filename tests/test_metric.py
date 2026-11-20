"""Checks the Python metric against values recalculated from the workbook.

Run: python -m pytest tests   (or: python tests/test_metric.py)
If you change a formula in the workbook, change it in metric/realestate_metric.py too,
then regenerate tests/workbook_expected.json from the recalculated workbook.
"""
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "metric"))
from realestate_metric import DEFAULTS, evaluate, load_listings  # noqa: E402


def test_matches_workbook():
    expected = json.loads((ROOT / "tests" / "workbook_expected.json").read_text(encoding="utf-8"))
    results = {r["id"]: r for r in (evaluate(l, DEFAULTS) for l in load_listings(ROOT / "data" / "listings.csv"))}
    for pid, exp in expected.items():
        got = results[pid]
        for key, val in exp.items():
            if isinstance(val, (int, float)):
                assert math.isclose(got[key], val, rel_tol=1e-6, abs_tol=1e-6), (pid, key, got[key], val)
            elif val == "n.a.":
                assert got.get(key) is None, (pid, key, got.get(key))
            else:
                assert got[key] == val, (pid, key, got[key], val)


if __name__ == "__main__":
    test_matches_workbook()
    print("OK: Python metric matches workbook")
