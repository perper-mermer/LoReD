# Release scope after code removal / 删除代码后的发布范围

Date / 日期: 2026-10-26  
Base commit / 基准提交: 97c6f91d69156d79a0d65f9b986ca996ff14d767

All executable Python files in the base tree have been removed from this branch. Numeric data, parameters, metrics, predictions, manifests and historical audit records are preserved byte-for-byte. README.md is updated and this status document is added. There are 90 retained files in the resulting tree.

已删除基准目录中的全部 Python 文件。数值数据、参数、指标、预测、清单和历史审计记录的文件内容均原样保留。更新 README.md，新增本说明；更新后共 90 个文件。

This is a data-and-results archive, not a runnable reproduction package. Commands and source-code paths in retained historical documentation describe earlier releases. Installing historical requirements does not recreate the missing implementation. Historical validation logs do not certify the current branch as an executable package.

当前是数据与结果归档，不是可运行复现包。保留文档中的命令及源码路径用于解释历史版本；安装依赖不能恢复缺失代码。过去的验证日志不代表当前分支仍可运行。

Git history is not rewritten; earlier commits can retain the deleted files. Local backups and previously delivered documents are not changed by this update.

未改写 Git 历史；旧提交中仍可保留已删除文件。本次不修改本地备份和已交付文档。

## Removed files / 删除清单

- `scripts/cross_verifier.py`
- `scripts/evaluate_judges.py`
- `scripts/export_paper_tables.py`
- `scripts/frozen_validation.py`
- `scripts/llm_judge.py`
- `scripts/plot_ablation.py`
- `scripts/prepare_data.py`
- `scripts/rebuild_halubench_rows.py`
- `scripts/rebuild_ragtruth_rows.py`
- `scripts/reproduce.py`
- `scripts/run.py`
- `scripts/score_factcg.py`
- `scripts/score_verifier.py`
- `scripts/verify_results.py`
- `scripts/verify_supplementary.py`
- `src/historical_stacking.py`
- `src/lored.py`
- `src/ragtruth_serialization.py`
- `src/verifier_scoring.py`
- `src/workflow.py`
- `supplementary/20261024/diagnostics/scripts/decision_timing_windows.py`
- `supplementary/20261024/diagnostics/scripts/development_sensitivity.py`
- `supplementary/20261024/frozen_validation/archive/prepare_evaluator_v2.py`
- `supplementary/20261024/frozen_validation/archive/run_validation.py`
- `supplementary/20261024/frozen_validation/archive/run_validation_v2.py`
- `tests/test_contracts.py`
- `tests/test_supplementary_release.py`

## Dataset removal / 实验数据集移除（2026-11-22）

Removed 8 numeric benchmark input datasets and 8 companion manifest/split files from the current main branch (16 files total). Frozen parameters, archived predictions, result tables and historical audit records are retained unchanged. Documentation was updated to distinguish historical dataset descriptions from current repository contents. The resulting tree has 74 files.

已从当前 main 分支移除 8 个实验输入数值数据集及 8 个配套清单、划分文件，共 16 个文件。冻结参数、归档预测、结果表和历史审计记录原样保留；更新说明文档以区分历史数据说明与当前仓库内容。更新后共 74 个文件。

This removes files only from the current branch snapshot. Git history is unchanged, deleted data remains recoverable from earlier commits, and local data/backups are untouched. This is not a full data erasure or history purge.

本次仅移除当前分支快照中的文件，未改写历史；旧提交仍可恢复这些数据，本地数据及备份不受影响，不等同于彻底清除公开历史中的数据。

Removed paths / 删除路径：
- `benchmarks/halubench_full.jsonl`
- `benchmarks/halubench_full.manifest.json`
- `benchmarks/halubench_multi.jsonl`
- `benchmarks/hhem_development.jsonl`
- `benchmarks/hhem_development.manifest.json`
- `benchmarks/hhem_test.jsonl`
- `benchmarks/hhem_test.manifest.json`
- `benchmarks/minicheck_development.jsonl`
- `benchmarks/minicheck_development.manifest.json`
- `benchmarks/minicheck_test.jsonl`
- `benchmarks/minicheck_test.manifest.json`
- `benchmarks/ragtruth_development.jsonl`
- `benchmarks/ragtruth_development.manifest.json`
- `benchmarks/ragtruth_split_manifest.json`
- `benchmarks/ragtruth_test.jsonl`
- `benchmarks/ragtruth_test.manifest.json`

## Paper synchronization / 最新论文同步（2026-11-22）

Current result exports and descriptions are aligned with the author-supplied LoReD_Chinese_Translation10.pdf. StatLR-2/4 use reported operating points .540/.510; their coefficients and other models are unchanged. Superseded root exports are preserved under results/historical_20261026/. Current paper numeric tables are indexed in results/current_paper/. Source-PDF rounded bootstrap values are labelled as reported, not newly computed. Threshold-selection provenance and source-PDF inconsistencies remain explicit. No code or benchmark input datasets are restored; local manuscripts/PDFs are untouched.

按最新论文同步主结果、冻结阈值、跨核验器、HaluBench及统计说明；旧版另存，保留负结果与来源限制。未进行新训练、GPU推理或阈值搜索。主结果和外部表已用本地缓存核对，输入数据不重新上传。
