# Experimental protocols / 实验协议

## Labels and scores / 标签与分数

Numeric records use `gold_hall=1` for hallucination, `0` for support. FactCG maximizes sentence support over prepared evidence chunks, then uses risk `1-support`. Some historical training functions fit `y_sup=1` for support and explicitly select class-0 probability. A response is hallucinated when `risk >= threshold`. Missing scores are errors, not 0.5 defaults.

数值记录中 1 表示幻觉。历史支持标签训练明确读取类别 0 的概率；缺失分数直接报错，不以 0.5 填充。

## Canonical core / 历史正式主方法

Feature order: max risk × log1p(n), mean risk × log1p(n), longest consecutive run of risk > 0.5 divided by n. Development IDs are lexicographically sorted. StandardScaler + balanced logistic regression uses C=0.1, lbfgs, max_iter=4000.

Outer StratifiedGroupKFold has 5 folds, seed 20261010. Each outer training fold uses 4-fold inner OOF, split seed 20261010+fold+1. Candidate thresholds: np.linspace(.1,.9,81). The ranking maximizes hallucination F1, then Macro-F1, balanced accuracy, accuracy, proximity to .5. The final classifier refits all development data with seed 20261010+999 and uses the **last outer fold's inner-selected threshold**, .49. This unusual historical rule is preserved for exact reproduction; it is not pooled-OOF Macro-F1 optimization.

主方法保留字符串 ID 排序及外 5、内 4 折。阈值先最大化幻觉类 F1，再用其他指标处理平局；全开发集重拟合后采用最后一个外层折的内层阈值 0.49。该历史规则与汇总 OOF 最大化 Macro-F1 不同，应据此描述。

## Matched controls / 匹配控制

Corrected controls use numeric ID order. Fixed-Max threshold=.5. Calibrated-Max directly tunes the development max-risk threshold. Statistical controls use GroupKFold(5), StandardScaler, balanced LR(C=.1, liblinear, max_iter=2000, seed=20261012), grouped OOF, and the first Macro-F1-maximizing threshold in np.arange(.1,.9,.01). StatLR-2 features: max, mean. StatLR-4 adds population std and min.

控制方法保留数值 ID 排序与 GroupKFold/liblinear 协议；Calibrated-Max 的原始分数无需拟合，不应称作学习模型的 OOF 分数。应保留完整结果，包括更强的统计基线。

## Task extensions / 任务条件扩展

The corrected task one-hot control uses numeric IDs and seed 20261012. Five-fold upstream grouped OOF risks are transformed to clipped logits and concatenated with three task indicators. A second grouped OOF stage chooses its threshold. This historical two-stage construction does not nest every upstream fit inside every head-validation fold.

The task-conditioned extension uses lexicographic IDs and the extracted historical nested 4×3 protocol, with seed 20261012+50. Threshold ranking prioritizes Macro-F1 with original tie breakers. Its final head uses five-fold upstream cross-fitted risks (seed+60), eight structural/task features, head seed+70 and upstream seed+20; threshold=.46.

任务 one-hot 控制保留历史两阶段 OOF，不能称作逐层完全嵌套。任务条件扩展保留原嵌套 4×3 协议，阈值 0.46，作为可选变体报告。

## Sensitivity and ablations / 敏感性与消融

Five seeds 20261020–20261024 use numeric IDs, seed-specific stratified grouped OOF and Macro-F1 threshold selection. This reproduces corrected v4 sensitivity, separately from the canonical final-fold threshold. Do not choose the best seed.

Ablations share the statistical-control GroupKFold/liblinear protocol. Development OOF Macro-F1 and test Macro-F1 are separate fields. LoReD-shaped features fitted in this matched ablation may differ slightly from canonical LoReD. The historical approximate +0.67pp length-interaction difference (about +0.66pp from unrounded metrics) is a development OOF comparison, not a test gain.

五种子与正式冻结协议分开。匹配消融区分开发 OOF 和测试指标；长度交互的旧近似 +0.67pp（未舍入指标约 +0.66pp）来源于开发 OOF，不能写成测试集提升。

MiniCheck/HHEM adaptation uses seed 20261022, five-fold StratifiedGroupKFold, Macro-F1 threshold selection with ties resolved toward .5 then the larger threshold. Supplied HHEM development/test scores are the same-version v5 rerun, not the old drifted cache.

核验器适配使用其固定种子与平局规则；HHEM 使用同版本开发/测试重算缓存。

## Transfer and statistics / 迁移与统计

External evaluation loads frozen development-fitted models and thresholds without refitting. HaluBench metadata is QA; its groups are response IDs, not verified independent source documents. Paired bootstrap uses source groups for RAGTruth and response IDs for HaluBench, 10,000 multinomial resamples, seed 20261020, percentile 95% intervals, two-sided plus-one p values and monotone Holm correction over each stated comparison family. Verifier adaptation retains bootstrap seed 20261022.

外部验证不重调参数；RAGTruth bootstrap 以来源分组，HaluBench 以回答 ID 重采样（来源独立性未核验），10,000 次，双侧 plus-one 与 Holm 校正。核验器适配保留其种子。

Earlier benchmarks influenced development. Reproducing implementation and arithmetic does not create an untouched independent test set.

复现确认实现和计算一致，不等于增加一个未参与开发的独立测试集。

## Frozen supplementary validation / 冻结补充验证

The 2026-10-24 supplement documents fixed F0--F4/StatLR-2/StatLR-4 matched fits, seven matched-feature comparisons, one canonical-versus-F4 diagnostic and four comparisons per HaluBench pool. Holm correction is within each stated family. Full and multi-sentence HaluBench pools overlap. Canonical LoReD and F4 differ on two RAGTruth binary predictions; a small pooled difference does not establish equivalent training protocols. No best ablation configuration or sensitivity setting replaced the canonical model.

Detailed predeclared rules and evaluation-repair history are retained in `supplementary/20261024/frozen_validation/`. Development sensitivity never evaluates a parameter variant on held-out data. Current CPU timing is recorded separately from historical timing and does not establish a speed advantage over StatLR-2/4. The positive-case summary is detected by both Fixed-Max and LoReD.
