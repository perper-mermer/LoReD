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
