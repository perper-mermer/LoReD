# Current experimental protocols / 当前实验口径

Synchronized to LoReD_Chinese_Translation10.pdf on 2026-11-22. Historical protocols inside supplementary/20261024 remain dated archives, not current table definitions.

## Labels, features and canonical fitting

Hallucination risk is 1 minus maximum sentence support over evidence chunks. gold_hall=1 denotes hallucination. Missing scores are errors, not neutral defaults. LoReD uses max risk*log1p(n), mean risk*log1p(n), and longest run of risk>0.5 divided by n. The 0.5 run cutoff is a feature definition, not the response operating threshold.

Canonical fitting retains lexicographic response-ID order, StandardScaler + balanced LR(C=.1, lbfgs, max_iter=4000), source-grouped outer5/inner4 splits with base seed20261010, hallucination-F1-first threshold selection with recorded tie breakers, and the last outer fold's inner threshold .49. The final classifier refits all499 development responses with seed20261010+999. This unusual historical rule is not pooled-OOF Macro-F1 selection.

## Statistical controls and operating-point provenance

Fixed-Max=.500, Tuned-Max=.830. StatLR-2=max/mean; StatLR-4 additionally uses population std/min. The recorded fitting protocol uses numeric IDs, unshuffled GroupKFold(5) by source, StandardScaler, balanced liblinear LR(C=.1,max_iter=2000,seed20261012), and a .10-to-.90-exclusive .01 grid with the first OOF Macro-F1 maximum.

The current paper evaluates StatLR-2/4 at .540/.510. At these operating points archived development OOF Macro-F1 is72.529204/74.147881%. Section4.4 explicitly says rerunning the stated search on currently available caches yields different optima. The exact selection provenance still requires corresponding original fold/OOF exports. These values must not be presented as newly verified maxima. Synchronization changes only those two stored thresholds, not coefficients, scalers or other methods.

StatLR阈值来源问题保留为未解决事项；本次只按论文报告点同步，不据测试或外部成绩重新选阈值。

## Optional task variants

LoReD+Task uses clipped upstream OOF risk logits plus three task indicators and threshold .480. Its historical two-stage grouped construction does not nest every upstream fit inside every downstream head-validation fold. Task-Conditioned LoReD retains the nested4x3 historical construction and threshold .460. Neither is required for core LoReD; both assume known task identity. All HaluBench records map toQA. Task-level negative transfer must be reported.

## Current statistical families

All use10,000 paired multinomial bootstrap samples, percentile95% intervals and the two-sided plus-one p=min(1,2*(min(N_le_zero,N_ge_zero)+1)/(B+1)). Confidence intervals are unadjusted; p-values receive monotone Holm correction within the named family.

- Table5: four LoReD versus Fixed-Max/Tuned-Max/StatLR-2/StatLR-4 contrasts;450 RAGTruth source groups;seed20261026.
- Table15/full: same four contrasts;13,202 response IDs;seed20261027.
- Table15/multi: same four contrasts;803 response IDs;seed20261028; overlap with full.
- Table8: F1-F0,F2-F1,F3-F2,F4-F3 form a separate Holm-4 family;450 source groups;seed20261020. Do not copy Holm-7 values from older archives.
- Archived judge comparisons:418 source groups;seed20261020;the paper's five-comparison family.
- Cross-verifier comparisons:seed20261022;exploratory unadjusted p-values, not Holm-significant claims.

For a one-response-per-group external pool, aggregating identical joint truth/prediction patterns has the exact response-level multinomial bootstrap distribution. It does not establish independent underlying source documents. These bootstrap tables were transcribed from the PDF during this update, not recomputed. Historical seed20261020 HaluBench intervals must not be mixed with current tables.

Earlier benchmark feedback informed development. All model-comparison inference is retrospective/exploratory; grouping does not remove adaptive benchmark reuse.

## Sensitivity, verification and efficiency

Five-seed sensitivity (20261020–24) uses its separate pooled-OOF Macro-F1 design; do not select a best seed. Matched F0–F4 fits differ from canonical fitting and distinguish selected development diagnostics from frozen test results. The run feature has no established positive independent contribution.

FactCG is the main verifier. AlignScore-base and HHEM are in Table12, MiniCheck in AppendixA/Table17. Adaptation fits use their own development risks and grouped OOF procedure; compare methods within each verifier, not as equal-cost verifier rankings. Current controlled CPU timing is decision-layer-only, excluding sentence verification;113.80us is not end-to-end throughput or a demonstrated speed advantage over StatLR-2/4.

## Repository scope

No implementation code or benchmark input datasets are provided in current main. Historical commands, validation logs and hash manifests describe previous releases. Outputs/predictions and historical commits still retain sample IDs and labels; dataset removal is not a privacy/history purge. Local input caches used for checking current paper Tables4/9/11/13/14 were not uploaded.
