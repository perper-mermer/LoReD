"""Portable cached-risk training and evaluation; no text or GPU dependency."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from lored import (lrdc_features, structure_features, tsac_features, make_model,
                   risk_probability, generic_oof_support, select_threshold_hall,
                   select_threshold_support, metrics_hall)


def read_records(path, labeled=True):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    ids = set()
    for row in rows:
        rid = str(row['response_id'])
        if rid in ids:
            raise ValueError(f'Duplicate response_id: {rid}')
        ids.add(rid)
        row['response_id'] = rid
        row['source_id'] = str(row['source_id'])
        risk = np.asarray(row['risks'], float)
        words = np.asarray(row['word_counts'], float)
        if risk.ndim != 1 or len(risk) == 0 or len(risk) != len(words):
            raise ValueError(f'Empty or inconsistent sentence arrays: {rid}')
        if not np.isfinite(risk).all() or np.any((risk < 0) | (risk > 1)):
            raise ValueError(f'Invalid risk: {rid}')
        if not np.isfinite(words).all() or np.any(words < 0):
            raise ValueError(f'Invalid word counts: {rid}')
        if labeled and row.get('gold_hall') not in (0, 1):
            raise ValueError(f'Expected gold_hall in {{0,1}}: {rid}')
    if not rows:
        raise ValueError('Empty dataset')
    return rows


def matrix(rows, kind):
    out = []
    for row in rows:
        risk = np.asarray(row['risks'], float)
        peak, mean = np.max(risk), np.mean(risk)
        local = lrdc_features(risk)
        features = {
            'LoReD': local,
            'StatLR-2': [peak, mean],
            'StatLR-4': [peak, mean, np.std(risk), np.min(risk)],
            'Peak-only': [peak],
            'Peak-length': [peak, local[0]],
            'Peak-length-mean': [peak, local[0], local[1]],
            'Peak-length-mean-run': [peak, *local],
            'Structure': structure_features(np.asarray(row['word_counts']), row['task']),
        }
        out.append(features[kind])
    return np.asarray(out, float)


def disjoint(train, test):
    if {r['response_id'] for r in train} & {r['response_id'] for r in test}:
        raise ValueError('Development/evaluation response overlap')
    if {r['source_id'] for r in train} & {r['source_id'] for r in test}:
        raise ValueError('Development/evaluation source overlap; namespace external source IDs')


def split_audit(rows, x, y, splitter):
    groups = np.asarray([r['source_id'] for r in rows])
    result = []
    for fold, (tri, vai) in enumerate(splitter.split(x, y, groups)):
        assert not set(groups[tri]) & set(groups[vai])
        result.append({'fold': fold, 'train_ids': [rows[i]['response_id'] for i in tri],
                       'validation_ids': [rows[i]['response_id'] for i in vai], 'source_overlap': 0})
    return result


def historical_core_threshold(x, y_support, groups):
    """Exact original protocol: last outer fold's inner-selected threshold.

    Preserve this unusual historical choice for numerical reproduction only;
    seed sensitivity separately uses pooled OOF Macro-F1 selection.
    """
    seed = 20261010
    outer = StratifiedGroupKFold(5, shuffle=True, random_state=seed)
    audits = []
    for fold, (tri, vai) in enumerate(outer.split(x, y_support, groups)):
        inner = StratifiedGroupKFold(4, shuffle=True, random_state=seed + fold + 1)
        oof = np.full(len(tri), np.nan)
        for inner_fold, (it, iv) in enumerate(inner.split(x[tri], y_support[tri], groups[tri])):
            assert not set(groups[tri][it]) & set(groups[tri][iv])
            fitted = make_model(seed + fold * 100 + inner_fold).fit(x[tri][it], y_support[tri][it])
            oof[iv] = risk_probability(fitted, x[tri][iv])
        assert np.isfinite(oof).all()
        candidates = []
        for threshold in np.linspace(.1, .9, 81):
            pred = (oof < threshold).astype(int)
            key = (f1_score(y_support[tri], pred, pos_label=0),
                   f1_score(y_support[tri], pred, average='macro'),
                   balanced_accuracy_score(y_support[tri], pred),
                   accuracy_score(y_support[tri], pred), -abs(threshold - .5))
            candidates.append((key, float(threshold)))
        threshold = max(candidates, key=lambda z: z[0])[1]
        audits.append({'fold': fold, 'threshold': threshold,
                       'train_sources': sorted(set(groups[tri])),
                       'validation_sources': sorted(set(groups[vai]))})
    return audits[-1]['threshold'], audits


def fit_stat(rows, feature, seed=20261012, sensitivity=False):
    rows = sorted(rows, key=lambda r: int(r['response_id']))
    x = matrix(rows, feature)
    y = np.asarray([r['gold_hall'] for r in rows])
    groups = np.asarray([r['source_id'] for r in rows])
    def estimator(s):
        return Pipeline([('scale', StandardScaler()), ('lr', LogisticRegression(
            C=.1, class_weight='balanced', solver='liblinear', max_iter=2000, random_state=s))])
    splitter = StratifiedGroupKFold(5, shuffle=True, random_state=seed) if sensitivity else GroupKFold(5)
    oof = np.full(len(rows), np.nan)
    for fold, (tri, vai) in enumerate(splitter.split(x, y, groups)):
        assert not set(groups[tri]) & set(groups[vai])
        oof[vai] = estimator(seed + fold if sensitivity else seed).fit(x[tri], y[tri]).predict_proba(x[vai])[:, 1]
    assert np.isfinite(oof).all()
    threshold = select_threshold_hall(y, oof)
    return {'feature': feature, 'model': estimator(seed).fit(x, y),
            'threshold': threshold, 'label': 'hall',
            'development_oof_macro_f1': float(f1_score(y, (oof >= threshold).astype(int), average='macro')),
            'folds': split_audit(rows, x, y, splitter)}


def train_suite(rows, sensitivity_seed=None):
    canonical = sensitivity_seed is None
    # Original LoReD uses lexicographic IDs; corrected sensitivity uses numeric IDs.
    core_rows = sorted(rows, key=(lambda r: r['response_id']) if canonical else (lambda r: int(r['response_id'])))
    x = matrix(core_rows, 'LoReD')
    y = 1 - np.asarray([r['gold_hall'] for r in core_rows])
    groups = np.asarray([r['source_id'] for r in core_rows])
    if canonical:
        threshold, audit = historical_core_threshold(x, y, groups)
        core = make_model(20261010 + 999).fit(x, y)
    else:
        seed = sensitivity_seed
        oof = generic_oof_support(x, y, groups, seed)
        threshold = select_threshold_support(y, oof)
        core = make_model(seed).fit(x, y)
        audit = split_audit(core_rows, x, y, StratifiedGroupKFold(5, shuffle=True, random_state=seed))
    numeric = sorted(rows, key=lambda r: int(r['response_id']))
    max_risk = np.asarray([max(r['risks']) for r in numeric])
    hall = np.asarray([r['gold_hall'] for r in numeric])
    suite = {
        'Fixed-Max': {'threshold': .5, 'pool': 'max'},
        'Calibrated-Max': {'threshold': select_threshold_hall(hall, max_risk), 'pool': 'max'},
        'LoReD': {'feature': 'LoReD', 'model': core, 'threshold': threshold, 'label': 'support', 'folds': audit},
    }
    for feature in ('StatLR-2', 'StatLR-4'):
        suite[feature] = fit_stat(rows, feature, sensitivity_seed or 20261012, not canonical)
    # The canonical task one-hot control uses numeric IDs in the corrected evaluator.
    xx = matrix(numeric, 'LoReD')
    structure = matrix(numeric, 'Structure')
    yy = 1 - hall
    gg = np.asarray([r['source_id'] for r in numeric])
    seed = sensitivity_seed or 20261012
    upstream_oof = generic_oof_support(xx, yy, gg, seed)
    upstream = make_model(seed).fit(xx, yy)
    head_x = np.column_stack([np.log(np.clip(upstream_oof, 1e-6, 1-1e-6) / (1-np.clip(upstream_oof, 1e-6, 1-1e-6))), structure[:, 5:8]])
    head_seed = seed + 1000 if not canonical else seed
    head_oof = generic_oof_support(head_x, yy, gg, head_seed)
    suite['LoReD+Task'] = {'upstream': upstream, 'model': make_model(head_seed).fit(head_x, yy),
                           'threshold': select_threshold_support(yy, head_oof), 'label': 'support', 'task_only': True}
    # Historical extension uses nested 4x3 grouped cross-fitting from the source code.
    from historical_stacking import stacked_inner_oof, crossfit_b, select_threshold
    if canonical:
        sx = matrix(core_rows, 'Structure')
        extension_oof = stacked_inner_oof(x, sx, y, groups, 20261012 + 50)
        extension_threshold = select_threshold(y, extension_oof)[0]
        upstream_for_head = crossfit_b(x, y, groups, 5, 20261012 + 60)
        suite['Task-Conditioned LoReD'] = {
            'upstream': make_model(20261012 + 20).fit(x, y),
            'model': make_model(20261012 + 70).fit(tsac_features(upstream_for_head, sx), y),
            'threshold': extension_threshold, 'label': 'support', 'task_only': False}
    else:
        from lored import stacked_oof_support
        extension_oof = stacked_oof_support(xx, structure, yy, gg, seed + 2000)
        upstream_for_head = generic_oof_support(xx, yy, gg, seed + 3000)
        suite['Task-Conditioned LoReD'] = {
            'upstream': make_model(seed + 5000).fit(xx, yy),
            'model': make_model(seed + 4000).fit(tsac_features(upstream_for_head, structure), yy),
            'threshold': select_threshold_support(yy, extension_oof), 'label': 'support', 'task_only': False}
    return suite


def export_parameters(suite):
    def parameters(model):
        scaler = model.named_steps['scale']
        classifier = model.named_steps['lr']
        return {'mean': scaler.mean_.tolist(), 'scale': scaler.scale_.tolist(),
                'classes': classifier.classes_.tolist(), 'coefficient': classifier.coef_.tolist(),
                'intercept': classifier.intercept_.tolist()}
    output = {}
    for name, entry in suite.items():
        record = {k:v for k,v in entry.items() if k in ('threshold','feature','label','pool','task_only')}
        for key in ('model','upstream'):
            if key in entry:
                record[key] = parameters(entry[key])
        output[name] = record
    return output


def predict(entry, rows):
    if 'pool' in entry:
        scores = np.asarray([max(r['risks']) if entry['pool'] == 'max' else
                             np.mean(r['risks']) if entry['pool'] == 'mean' else
                             1-np.prod(1-np.asarray(r['risks'])) for r in rows])
    elif 'upstream' in entry:
        upstream = risk_probability(entry['upstream'], matrix(rows, 'LoReD'))
        sx = matrix(rows, 'Structure')
        feat = tsac_features(upstream, sx[:, 5:8] if entry['task_only'] else sx)
        scores = risk_probability(entry['model'], feat)
    else:
        x = matrix(rows, entry['feature'])
        scores = risk_probability(entry['model'], x) if entry['label'] == 'support' else entry['model'].predict_proba(x)[:, 1]
    return scores, (scores >= entry['threshold']).astype(int)


def evaluate(suite, rows):
    y = np.asarray([r['gold_hall'] for r in rows])
    reports, predictions = [], []
    for name, entry in suite.items():
        risk, pred = predict(entry, rows)
        report = metrics_hall(y, pred, risk) if len(np.unique(y)) == 2 else metrics_hall(y, pred)
        reports.append({'method': name, 'n': len(rows), 'threshold': entry['threshold'], **report})
        for i, row in enumerate(rows):
            predictions.append({'response_id': row['response_id'], 'source_id': row['source_id'],
                                'task': row['task'], 'gold_hall': int(y[i]), 'method': name,
                                'risk': float(risk[i]), 'pred_hall': int(pred[i])})
    return reports, predictions
