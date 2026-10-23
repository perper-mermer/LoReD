"""Historical task-extension numerical protocol, extracted without experiment execution."""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, matthews_corrcoef, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
def model(seed: int) -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("lr", LogisticRegression(
            C=0.1,
            class_weight="balanced",
            max_iter=4000,
            random_state=seed,
        )),
    ])

def risk_probability(fitted: Pipeline, x: np.ndarray) -> np.ndarray:
    classes = np.asarray(fitted.named_steps["lr"].classes_)
    class_zero = np.flatnonzero(classes == 0)
    if len(class_zero) != 1:
        raise RuntimeError(f"expected hallucination class 0, got {classes.tolist()}")
    return fitted.predict_proba(x)[:, int(class_zero[0])]

def clip_logit(probability: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(probability, dtype=np.float64), 1e-6, 1.0 - 1e-6)
    return np.log(p / (1.0 - p))

def tsac_features(upstream_risk: np.ndarray, structure: np.ndarray) -> np.ndarray:
    return np.column_stack([clip_logit(upstream_risk), structure])

def metrics(y: np.ndarray, pred: np.ndarray, risk: np.ndarray) -> dict:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, pred, labels=[0, 1], zero_division=0
    )
    return {
        "n": int(len(y)),
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro")),
        "hallucination_precision": float(precision[0]),
        "hallucination_recall": float(recall[0]),
        "hallucination_f1": float(f1[0]),
        "support_f1": float(f1[1]),
        "mcc": float(matthews_corrcoef(y, pred)),
        "roc_auc_hallucination": float(roc_auc_score(y == 0, risk)),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }

def select_threshold(y: np.ndarray, risk: np.ndarray) -> tuple[float, dict]:
    candidates = []
    for threshold in np.linspace(0.10, 0.90, 81):
        pred = (risk < threshold).astype(np.int64)
        report = metrics(y, pred, risk)
        candidates.append((float(threshold), report))
    return max(candidates, key=lambda item: (
        item[1]["macro_f1"],
        item[1]["balanced_accuracy"],
        item[1]["hallucination_f1"],
        item[1]["accuracy"],
        -abs(item[0] - 0.5),
    ))

def assert_disjoint(groups: np.ndarray, train_idx: np.ndarray, test_idx: np.ndarray, label: str) -> None:
    overlap = set(groups[train_idx]) & set(groups[test_idx])
    if overlap:
        raise RuntimeError(f"group leakage in {label}: {sorted(overlap)[:3]}")

def crossfit_b(
    b_x: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int,
    seed: int,
) -> np.ndarray:
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    out = np.full(len(y), np.nan, dtype=np.float64)
    for fold, (train_idx, valid_idx) in enumerate(splitter.split(b_x, y, groups)):
        assert_disjoint(groups, train_idx, valid_idx, f"B-crossfit-{fold}")
        fitted = model(seed + fold).fit(b_x[train_idx], y[train_idx])
        out[valid_idx] = risk_probability(fitted, b_x[valid_idx])
    if not np.isfinite(out).all():
        raise RuntimeError("incomplete B cross-fitted probabilities")
    return out

def stacked_inner_oof(
    b_x: np.ndarray,
    structure: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    seed: int,
) -> np.ndarray:
    """OOF risk for the full B->C pipeline inside one outer training fold."""
    splitter = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=seed)
    out = np.full(len(y), np.nan, dtype=np.float64)
    for fold, (train_idx, valid_idx) in enumerate(splitter.split(b_x, y, groups)):
        assert_disjoint(groups, train_idx, valid_idx, f"stack-inner-{fold}")

        # C training inputs for inner-train are produced by B models that did
        # not see those samples.  This is the key anti-leakage step.
        b_oof_train = crossfit_b(
            b_x[train_idx], y[train_idx], groups[train_idx],
            n_splits=3, seed=seed + 100 + fold * 10,
        )
        c_train_x = tsac_features(b_oof_train, structure[train_idx])
        c_model = model(seed + 200 + fold).fit(c_train_x, y[train_idx])

        b_model = model(seed + 300 + fold).fit(b_x[train_idx], y[train_idx])
        b_valid = risk_probability(b_model, b_x[valid_idx])
        c_valid_x = tsac_features(b_valid, structure[valid_idx])
        out[valid_idx] = risk_probability(c_model, c_valid_x)

    if not np.isfinite(out).all():
        raise RuntimeError("incomplete stacked inner OOF")
    return out
