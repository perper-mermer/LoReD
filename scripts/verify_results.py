from pathlib import Path
import csv, json, sys
import numpy as np
from sklearn.metrics import f1_score
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
from lored import lrdc_features
with (root / "results/canonical_matched_predictions.csv").open(encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
with (root / "results/canonical_main_results.csv").open(encoding="utf-8-sig") as f:
    expected = {r["method"]: float(r["macro_f1"]) for r in csv.DictReader(f)}
mapping = {"Fixed-Max": ("A", "A_fixed_max"), "Calibrated-Max": ("L0", "L0_calibrated_max"), "StatLR-2": ("L3", "L3_two_stat_lr"), "StatLR-4": ("L4", "L4_four_stat_lr"), "LoReD": ("AB", "AB_LRDC"), "LoReD + task one-hot": ("T2", "T2_LRDC_plus_task"), "Task-conditioned extension": ("ABC", "ABC_full")}
assert len(rows) == 2700
gold = [int(r["gold_hall"]) for r in rows]
output = {}
for name, (column, legacy) in mapping.items():
    value = 100 * f1_score(gold, [int(r[column + "_pred_hall"]) for r in rows], average="macro")
    assert abs(value - expected[legacy]) < 0.000002, (name, value, expected[legacy])
    output[name] = value
assert np.allclose(lrdc_features(np.array([0.2,0.8])), [0.8*np.log(3),0.5*np.log(3),0.5])
print(json.dumps({"responses": len(rows), "macro_f1_percent": output, "status": "PASS: frozen prediction replay and feature check"}, indent=2))
