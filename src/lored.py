from __future__ import annotations
import csv, gc, hashlib, json, math, os, platform, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
SEED_CANON_AB = 20261010
SEED_CANON_TSAC = 20261012
BOOT_SEED = 20261020
STABILITY_SEEDS = [20261020,20261021,20261022,20261023,20261024]
def stable_id(claim, evidence):
    return hashlib.sha256((claim + "\0" + evidence).encode("utf-8")).hexdigest()
def load_score_cache(path):
    with Path(path).open(encoding="utf-8-sig") as handle:
        return {row["id"]: float(row["score"]) for row in map(json.loads, filter(str.strip, handle))}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def lrdc_features(risk: np.ndarray) -> np.ndarray:
    n = len(risk)
    longest = current = 0
    for value in risk:
        current = current + 1 if value > 0.5 else 0
        longest = max(longest, current)
    return np.asarray([
        float(np.max(risk) * np.log1p(n)),
        float(np.mean(risk) * np.log1p(n)),
        float(longest / max(n, 1)),
    ], dtype=np.float64)

def structure_features(words: np.ndarray, task: str) -> np.ndarray:
    n = len(words)
    return np.asarray([
        float(n),
        float(np.log1p(n)),
        float(np.sum(words)),
        float(np.mean(words)),
        float(np.max(words)),
        float(task == "QA"),
        float(task == "Summary"),
        float(task == "Data2txt"),
    ], dtype=np.float64)

def clip_logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))

def tsac_features(upstream_risk: np.ndarray, structure: np.ndarray) -> np.ndarray:
    return np.column_stack([clip_logit(upstream_risk), structure])

def make_model(seed: int, solver: str = "lbfgs") -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("lr", LogisticRegression(
            C=0.1,
            class_weight="balanced",
            solver=solver,
            max_iter=4000,
            random_state=seed,
        )),
    ])

def risk_probability(model: Pipeline, x: np.ndarray) -> np.ndarray:
    classes = np.asarray(model.named_steps["lr"].classes_)
    idx = np.flatnonzero(classes == 0)
    if len(idx) != 1:
        raise RuntimeError(f"Expected supported-label model with hallucination class 0, got {classes}")
    return model.predict_proba(x)[:, int(idx[0])]

def load_dataset(rows_path: Path, cache_path: Path, gold_map: dict[str, int] | None = None) -> list[dict]:
    rows = read_jsonl(rows_path)
    cache = load_score_cache(cache_path)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row["response_id"])].append(row)
    output = []
    missing = []
    for rid in sorted(grouped, key=lambda x: int(x)):
        items = sorted(grouped[rid], key=lambda x: int(x["sentence_index"]))
        risks, words = [], []
        for item in items:
            keys = [stable_id(str(item["claim"]), str(e["text"]).strip()) for e in item["evidence"]]
            absent = [key for key in keys if key not in cache]
            if absent:
                missing.extend((rid, str(item.get("sentence_index")), key) for key in absent)
                continue
            support = max(float(cache[key]) for key in keys)
            if not 0 <= support <= 1 or not np.isfinite(support):
                raise ValueError(f"Invalid support score for response {rid}: {support}")
            risks.append(1.0 - support)
            words.append(len(str(item["claim"]).split()))
        if missing:
            continue
        risk = np.asarray(risks, dtype=np.float64)
        word = np.asarray(words, dtype=np.float64)
        task = str(items[0].get("task_type", "QA"))
        y_sup = int(gold_map[rid]) if gold_map is not None else int(
            not any(int(item["gold_binary"]) == 0 for item in items)
        )
        output.append({
            "rid": rid,
            "source": str(items[0]["source_id"]),
            "task": task,
            "y_sup": y_sup,
            "risk": risk,
            "words": word,
            "lrdc": lrdc_features(risk),
            "struct": structure_features(word, task),
            "max": float(risk.max()),
            "mean": float(risk.mean()),
            "std": float(risk.std()),
            "min": float(risk.min()),
            "n": len(risk),
        })
    if missing:
        sample = missing[:3]
        raise KeyError(f"Missing {len(missing)} cache entries, examples={sample}")
    return output

def arr(data: list[dict], key: str) -> np.ndarray:
    return np.asarray([row[key] for row in data])

def select_threshold_support(y_sup: np.ndarray, risk: np.ndarray) -> float:
    best = (0.5, -1.0)
    for th in np.linspace(0.10, 0.90, 81):
        score = f1_score(y_sup, (risk < th).astype(int), average="macro", zero_division=0)
        if score > best[1]:
            best = (float(th), float(score))
    return best[0]

def select_threshold_hall(y_hall: np.ndarray, risk: np.ndarray) -> float:
    best = (0.5, -1.0)
    for th in np.arange(0.10, 0.90, 0.01):
        score = f1_score(y_hall, (risk >= th).astype(int), average="macro", zero_division=0)
        if score > best[1]:
            best = (float(th), float(score))
    return best[0]

def generic_oof_support(x: np.ndarray, y_sup: np.ndarray, groups: np.ndarray, seed: int) -> np.ndarray:
    splitter = StratifiedGroupKFold(5, shuffle=True, random_state=seed)
    out = np.full(len(y_sup), np.nan)
    for fold, (tri, vai) in enumerate(splitter.split(x, y_sup, groups)):
        fitted = make_model(seed + fold).fit(x[tri], y_sup[tri])
        out[vai] = risk_probability(fitted, x[vai])
    if not np.isfinite(out).all():
        raise RuntimeError("Incomplete OOF predictions")
    return out

def stacked_oof_support(
    bx: np.ndarray,
    struct: np.ndarray,
    y_sup: np.ndarray,
    groups: np.ndarray,
    seed: int,
) -> np.ndarray:
    splitter = StratifiedGroupKFold(5, shuffle=True, random_state=seed)
    out = np.full(len(y_sup), np.nan)
    for fold, (tri, vai) in enumerate(splitter.split(bx, y_sup, groups)):
        inner = StratifiedGroupKFold(3, shuffle=True, random_state=seed + 100 + fold)
        b_inner = np.full(len(tri), np.nan)
        for inner_fold, (it, iv) in enumerate(inner.split(bx[tri], y_sup[tri], groups[tri])):
            bm = make_model(seed + 200 + fold * 10 + inner_fold).fit(bx[tri][it], y_sup[tri][it])
            b_inner[iv] = risk_probability(bm, bx[tri][iv])
        cm = make_model(seed + 300 + fold).fit(tsac_features(b_inner, struct[tri]), y_sup[tri])
        bm = make_model(seed + 400 + fold).fit(bx[tri], y_sup[tri])
        b_valid = risk_probability(bm, bx[vai])
        out[vai] = risk_probability(cm, tsac_features(b_valid, struct[vai]))
    if not np.isfinite(out).all():
        raise RuntimeError("Incomplete stacked OOF predictions")
    return out

def metrics_hall(y_hall: np.ndarray, pred_hall: np.ndarray, risk: np.ndarray | None = None) -> dict:
    result = {
        "macro_f1": f1_score(y_hall, pred_hall, average="macro", zero_division=0) * 100,
        "bacc": balanced_accuracy_score(y_hall, pred_hall) * 100,
        "hall_f1": f1_score(y_hall, pred_hall, pos_label=1, zero_division=0) * 100,
        "sup_f1": f1_score(y_hall, pred_hall, pos_label=0, zero_division=0) * 100,
    }
    if risk is not None:
        result["auc"] = roc_auc_score(y_hall, risk) * 100
    return result

def macro_f1_from_cm(cm: np.ndarray) -> np.ndarray:
    f0_den = 2 * cm[:, :, 0, 0] + cm[:, :, 1, 0] + cm[:, :, 0, 1]
    f1_den = 2 * cm[:, :, 1, 1] + cm[:, :, 0, 1] + cm[:, :, 1, 0]
    f0 = np.divide(2 * cm[:, :, 0, 0], f0_den, out=np.zeros_like(f0_den), where=f0_den != 0)
    f1 = np.divide(2 * cm[:, :, 1, 1], f1_den, out=np.zeros_like(f1_den), where=f1_den != 0)
    return (f0 + f1) / 2

def paired_bootstrap_many(
    y_hall: np.ndarray,
    predictions: dict[str, np.ndarray],
    groups: np.ndarray,
    comparisons: list[tuple[str, str, str]],
    repetitions: int = 10_000,
    seed: int = BOOT_SEED,
) -> list[dict]:
    names = list(predictions)
    name_idx = {name: i for i, name in enumerate(names)}
    unique = np.unique(groups)
    cms = np.zeros((len(unique), len(names), 2, 2), dtype=np.float64)
    for gi, group in enumerate(unique):
        idx = np.flatnonzero(groups == group)
        for mi, name in enumerate(names):
            cms[gi, mi] = confusion_matrix(y_hall[idx], predictions[name][idx], labels=[0, 1])
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(len(unique), np.full(len(unique), 1 / len(unique)), size=repetitions)
    sampled = np.einsum("rg,gmij->rmij", weights, cms, optimize=True)
    sampled_mf1 = macro_f1_from_cm(sampled)
    rows = []
    for label, a, b in comparisons:
        delta = sampled_mf1[:, name_idx[a]] - sampled_mf1[:, name_idx[b]]
        point = (
            f1_score(y_hall, predictions[a], average="macro")
            - f1_score(y_hall, predictions[b], average="macro")
        ) * 100
        n_le = int(np.sum(delta <= 0))
        n_ge = int(np.sum(delta >= 0))
        p = min(1.0, 2 * (min(n_le, n_ge) + 1) / (repetitions + 1))
        rows.append({
            "comparison": label,
            "method_a": a,
            "method_b": b,
            "delta_macro_f1_pp": point,
            "ci95_low_pp": np.percentile(delta, 2.5) * 100,
            "ci95_high_pp": np.percentile(delta, 97.5) * 100,
            "prob_gt_zero": float(np.mean(delta > 0)),
            "p_plus_one": p,
            "n_sources": len(unique),
            "n_bootstrap": repetitions,
            "seed": seed,
        })
    # Correct Holm: sort, multiply, then cumulative maximum.
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p_plus_one"])
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = min(1.0, rows[idx]["p_plus_one"] * (len(rows) - rank))
        running = max(running, candidate)
        rows[idx]["p_holm"] = running
    return rows

def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)




def length_bin(n: int) -> str:
    if n <= 5:
        return "short_le5"
    if n == 6:
        return "six"
    if n <= 9:
        return "medium_7_9"
    return "long_gt9"
