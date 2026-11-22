# Result versions / 结果版本

Use [current_paper/](current_paper/README.md) for the tables in LoReD_Chinese_Translation10.pdf.

Current root exports:
- `canonical_main_results.csv`: full-precision cached-risk recalculation checked against Table 4.
- `frozen_parameters.json`: original coefficients/scalers with paper operating points StatLR-2=.540, StatLR-4=.510.
- `canonical_pairwise_bootstrap.csv`: current paper Table 5 reported precision; four comparisons, seed20261026; not a fresh bootstrap run.
- `canonical_matched_predictions.csv`: 2700-row export recalculated at those operating points. Input risk arrays/text are not included.
- `cross_verifier_reference.csv`: paper Tables12/17 (includes AlignScore-base), reported precision.

Unchanged historical exports: `five_seed_results_corrected.csv`, `five_seed_summary_corrected.csv`, `llm_judge_pairwise_bootstrap_corrected.csv`, `verified_efficiency_v4.csv`. They retain their original historical names/settings; the paper-facing summaries are Tables6/16 and the corresponding current tables. Historical root exports replaced during synchronization are preserved in `historical_20261026/`.

Legacy prediction-column mapping (not a multi-module contribution claim): A=Fixed-Max; L0=Tuned-Max; L3=StatLR-2; L4=StatLR-4; AB=LoReD; T2=LoReD+Task; ABC=Task-Conditioned LoReD. Internal parameter key Calibrated-Max means Tuned-Max, not probability calibration.

旧文件与新表不能混用：StatLR-2/4旧操作阈值为.570/.560，新论文为.540/.510；bootstrap的种子及比较族也不同。旧版原文件保留用于追溯，不再作为最新主表。
