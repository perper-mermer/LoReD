# Frozen supplementary evidence 2026-10-24

This additive release accompanies the final LoReD manuscript. It preserves the canonical 72.727037% RAGTruth Macro-F1 and all original result files. It is a retrospective reproducibility release, not an independent untouched test.

## Contents

- `frozen_validation/`: fixed test feature ablations, full external controls, all response predictions, thresholds, folds, protocol comparison and paired statistics; original evaluator repair history retained.
- `diagnostics/`: nine development-only parameter settings, separate CPU timing, verified hallucination-positive case summary and their portable reproduction scripts.
- `reproduction_reference/`: prior numeric reference rows used by the frozen evaluator; these are references, not newly fitted models.
- `canonical_length_bins.csv`: computed from **LoReD-canonical**, not F4; six-sentence Macro-F1 is 78.2088167635%.
- `sha256.json`: integrity manifest for this supplement and its new root scripts.

## Reproduction

From the repository root, install `requirements-supplementary.txt`, then run `python scripts/verify_supplementary.py` for an arithmetic/integrity replay without fitting. To regenerate frozen fits, run `python scripts/frozen_validation.py prepare --output outputs/frozen_validation`, followed by `python scripts/frozen_validation.py evaluate --output outputs/frozen_validation`. Both phases use a new local output directory. Evaluation must use its own unmodified training lock and stops on mismatches.

For parameter diagnostics: `python supplementary/20261024/diagnostics/scripts/development_sensitivity.py --release-root . --output outputs/development_sensitivity`. For current Windows timing, use its `decision_timing_windows.py` with `--release-root .`, `--models outputs/main/models.joblib`, and a new `--output` directory after generating trusted local models with the original main workflow. Timing depends on hardware and load.

Run `python scripts/export_paper_tables.py --output outputs/paper_tables` and `python scripts/plot_ablation.py --output outputs/figures/ablation.pdf` for data-derived length statistics and Figure 3. The figure uses the matched F0--F4 scores on its left and canonical length bins on its right.

## Findings and scope

The matched continuity increment is negative. F2's observed 74.63% is an ablation result, not a replacement primary model. Full HaluBench LoReD is 78.86%, below StatLR-2's 79.37% and Fixed-Max's 79.27%, while above calibrated Max and StatLR-4. The six-sentence canonical LoReD value corrects an earlier F4 substitution; the pooled primary result is unchanged. Parameter diagnostics do not select a new held-out configuration. CPU timing does not prove relative acceleration. Both Fixed-Max and LoReD detect the archived positive case.

Raw source passages, full generated responses, credentials, downloaded weights and binary fitted models are excluded. Historical lock files retain the original paths and hashes for audit purposes. Third-party terms and the original repository's license status are unchanged.

中文：本补充发布与正文证据对应，保留正式模型和全部旧结果。固定测试消融不用于换主模型；F4 与正式模型不同。完整 HaluBench 中 LoReD 并非最优。正式六句桶为 78.21%，修复旧 F4 数值误用。参数诊断只读取开发集；计时不证明相对统计基线加速；所选真阳性由两个方法共同检出。历史评估修复记录保留，原始全文、密钥、下载权重及二进制模型均不打包。
