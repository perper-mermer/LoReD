# Frozen validation protocol / 冻结补充验证协议

Scope: execute the three author-requested items only: held-out feature ablations, frozen HaluBench controls, and protocol reconciliation. No new verifier scoring, task extensions, architecture search, hyperparameter search, or test-guided selection.

本轮只执行作者指定的三项：测试集特征消融、冻结 HaluBench 强基线、训练与阈值协议核对。不重跑核验器，不新增任务扩展，不搜索结构或参数，不根据测试结果选择特征。

## Inputs and STOP gates

Use the released numeric benchmarks in `../LoReD_GitHub/benchmarks/`. Verify SHA256 against `../LoReD_GitHub/audit/benchmark_sha256.json`. Development: 499 responses; RAGTruth test: 2,700; HaluBench full: 13,202; multi: 803. Risk is 1-support; gold_hall=1 denotes hallucination. Require finite nonempty risks in [0,1], unique response IDs, development/test source and response disjointness, and multi being an identical subset of full. HaluBench group IDs are response IDs, not verified source documents.

STOP if any hash, schema, label, overlap, subset, convergence, or frozen canonical prediction check fails. Do not repair by changing features, labels, thresholds, seeds, or samples after seeing evaluation performance. Preserve logs and report the failed gate. Model parameters and thresholds must be written and hashed before evaluation data are scored. Label-free schema/hash checks may inspect evaluation records before fitting; no evaluation labels enter fitting or selection.

## Fixed feature configurations

Let m=max(r), a=mean(r), l=log1p(n), and c=longest consecutive run of r>0.5 divided by n.

| Configuration | Features |
|---|---|
| F0 / Peak-only | m |
| F1 / Peak-length | m, m*l |
| F2 / Peak-length-mean | m, m*l, a*l |
| F3 / Peak-length-mean-run | m, m*l, a*l, c |
| F4 / LoReD-shaped matched fit | m*l, a*l, c |
| StatLR-2 | m, a |
| StatLR-4 | m, a, population std(r), min(r) |

All seven learned configurations share numeric response-ID ordering, identical GroupKFold(5) source partitions, fold-fitted StandardScaler, class-balanced logistic regression C=.1, liblinear, max_iter=2000, seed=20261012, gold_hall labels. Select the first maximum of development pooled-OOF Macro-F1 over `np.arange(.10,.90,.01)`. Refit each configuration on all development data. Development selected-OOF metrics are selection diagnostics, not unbiased performance estimates. No feature set is selected as a new main model.

Fixed-Max uses threshold .5. Calibrated-Max uses raw development maximum scores and the same threshold grid/objective/tie rule; these unfitted scores need no OOF training. No thresholds are reselected externally or per subgroup.

## Historical canonical reproduction

Keep canonical LoReD separate: lexicographic ID ordering; support labels with class-0 risk; balanced LR C=.1, lbfgs, max_iter=4000; outer StratifiedGroupKFold 5, seed20261010; inner 4 folds, split seed20261010+outer_index+1; threshold grid linspace(.1,.9,81), ranking hallucination F1, Macro-F1, balanced accuracy, accuracy, proximity to .5. Retain the last outer fold's inner threshold and refit with seed20261010+999. Require its threshold .49 and all canonical evaluation predictions to match the archived reference; also require Fixed-Max, Calibrated-Max, StatLR-2 and StatLR-4 predictions to match. A mismatch stops external evaluation; never tune to restore a score.

## Evaluations

Report canonical reproduction, all F0-F4 and statistical controls on identical RAGTruth responses, task and length strata, and frozen canonical Fixed-Max/Calibrated-Max/LoReD/StatLR-2/StatLR-4 on both HaluBench pools. Record Macro-F1, balanced accuracy, hallucination/support F1, AUROC, recall, precision, confusion counts, prevalence, and predicted positive fraction. F4 matched and canonical LoReD must never be conflated.

Use paired 10,000-resample bootstrap, seed20261020. RAGTruth units: source IDs. HaluBench units: response IDs; source dependence cannot be assessed. Compute percentile 95% delta intervals and two-sided plus-one sign-tail p values; apply monotone Holm separately within each declared family. These are retrospective diagnostic comparisons, not prospective confirmation.

Families fixed before execution:

1. RAGTruth matched feature family (7): F1-F0, F2-F1, F3-F2, F4-F3, F4-StatLR-2, F4-StatLR-4, F4-Calibrated-Max.
2. RAGTruth protocol diagnostic (1): canonical LoReD minus F4 matched.
3. HaluBench full (4): canonical LoReD minus Fixed-Max, Calibrated-Max, StatLR-2, StatLR-4.
4. HaluBench multi (4): same four comparisons. This subset overlaps full; not independent replication.

All outputs go into this new directory. Existing manuscript, release code, historical numbers and archives remain immutable during this experiment. Freeze protocol/code/input hashes before fitting; freeze models before evaluation. If all gates pass, write a bilingual result report and a protocol comparison table.
