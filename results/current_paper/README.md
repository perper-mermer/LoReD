# Current paper results / 当前论文结果

Source: author-supplied `LoReD_Chinese_Translation10.pdf`, synchronized 2026-11-22. PDF SHA256: `5130c7e25466fda9b5bd45bebe0d907edb74f373d3e7484da0ba8e1eb42c213a`.

Files `table02_*.csv`, `table04_*.csv` through `table17_*.csv` correspond to the numbered empirical tables. Table 1 is notation and Table 3 is a textual protocol comparison, so neither is a numeric result CSV.

These table CSVs transcribe the PDF's reported precision, not invented unrounded values. Metrics are percentages; bootstrap differences/intervals are percentage points; operating thresholds are on [0,1]. Counts, seeds, p-values, C/rho and microsecond timing are not percentages. Confidence intervals are unadjusted percentile intervals; Holm applies to p-values within each named family.

论文表格CSV按PDF精度转录，不将两位小数伪装成未舍入实验输出。表4、9、11、13（冻结模型部分）和14与本地原冻结参数、风险缓存的复算结果在报告精度内一致。输入缓存没有重新上传。表5/15的CI和p值按论文转录，本次未重跑bootstrap；明确记录种子与比较族，不与20261024旧表混合。

## Table map / 表格索引

| Table | File / subject |
|---|---|
| 2 | table02_datasets.csv — historical split counts, not dataset records |
| 4 | table04_ragtruth_main.csv |
| 5 | table05_ragtruth_bootstrap.csv — four comparisons, seed 20261026 |
| 6 | table06_five_seed.csv — separate pooled-OOF sensitivity protocol |
| 7 | table07_feature_ablation.csv — development selection diagnostics versus frozen test |
| 8 | table08_incremental_bootstrap.csv — Holm-4, seed 20261020 |
| 9 | table09_length_strata.csv |
| 10 | table10_development_sensitivity.csv — development only |
| 11 | table11_task_results.csv — task-equal versus pooled Macro-F1 |
| 12 | table12_cross_verifier.csv — FactCG, AlignScore-base, HHEM |
| 13 | table13_matched_judges.csv — 999 responses, 418 groups |
| 14 | table14_halubench_transfer.csv — overlapping full/multi pools |
| 15 | table15_halubench_bootstrap.csv — seeds 20261027/full and 20261028/multi |
| 16 | table16_efficiency.csv — historical and controlled-current runs separated |
| 17 | table17_minicheck.csv — appendix, not main cross-verifier table |

## Protocol and claim boundaries / 口径与表述边界

- StatLR-2/4 reported thresholds: 0.540/0.510; source-selection verification remains unresolved as stated in Section 4.4. No new threshold search occurred here.
- LoReD is the unified core method. Task heads remain optional. Internal legacy identifiers are mapped in the parent results README.
- Table 5: LoReD versus Tuned-Max passes the exploratory four-family Holm threshold; differences versus StatLR-2/4 do not.
- Table 15: on full HaluBench, LoReD is below Fixed-Max/StatLR-2 and above Tuned-Max/StatLR-4; on multi only the Fixed-Max contrast passes Holm 0.05.
- Earlier feedback influenced development. Multi and full HaluBench overlap. Response-ID resampling does not certify source-document independence.
- Calibration, monotonic length benefit, run-feature usefulness and universal verifier/transfer superiority are not established. Negative task and verifier results stay visible.

## Source-PDF discrepancies / 原PDF中仍需注意的事项

1. The Chinese body Table 14 reports multi-sentence StatLR-2=65.75, verified from the frozen cache. A reproduced English table embedded on PDF page 23 shows 65.86. This archive uses body Table 14, not the inconsistent embedded illustration.
2. The PDF availability paragraph still says experiment datasets are provided. Dataset inputs were removed from current main at the user's request. The current repository provides parameters, outputs, result tables and method/protocol records, not those input datasets or executable code. Git history still contains earlier data.

未修改原PDF或本地英文/中文稿件。同步范围仅为GitHub结果与说明。
