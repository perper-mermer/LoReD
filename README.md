# LoReD

**Learning Response-Level Hallucination Decisions from Local Factuality Risks**  
**从局部事实性风险学习回答级幻觉决策**

## Current release / 当前发布范围

This branch contains numeric benchmark caches, frozen parameters, archived predictions, results, protocols, and audit records. All 27 Python source files, including training, threshold selection, inference, evaluation, plotting, tests, and historical supplementary scripts, were removed on 2026-10-26. This branch no longer provides executable reproduction code.

当前分支仅保留数值数据缓存、冻结参数、归档预测、实验结果、协议与审计说明。2026 年 10 月 26 日已删除全部 27 个 Python 文件，包括训练、阈值搜索、推理、评估、绘图、测试与补充目录历史脚本。当前版本不再提供可执行复现代码。

See [RELEASE_STATUS.md](RELEASE_STATUS.md) for the removal inventory and preservation scope. Existing protocol documents, command examples, dependency lists and validation records describe historical releases; references to deleted scripts are not runnable instructions for this branch. Historical hash manifests may include removed files or earlier document versions and are retained as provenance records, not current whole-tree checksums.

完整删除清单及保留范围见 [RELEASE_STATUS.md](RELEASE_STATUS.md)。其他文档中的运行命令、依赖清单与验证结果属于历史版本记录，引用的脚本在当前分支已不存在。历史哈希清单可能包含已删除文件或旧文档版本，仅用于追溯，不能作为当前完整目录校验清单。

## Retained materials / 保留材料

- `benchmarks/`: numeric sentence risks, lengths, sample IDs, labels, split manifests and archived judge outputs; no raw passages or generated-answer text.
- `results/`: canonical metrics, matched predictions, frozen parameters and archived comparisons.
- `supplementary/`: supplementary data, metrics, predictions, protocol descriptions, timing records and audit reports; Python scripts removed.
- `audit/`: historical provenance and release-validation records.
- `DATA.md`, `PROTOCOL.md` and supplementary Markdown files: historical data and experiment descriptions.
- `requirements*.txt`: historical dependency lists only; they do not restore the deleted implementation.

上述数据、参数与结果文件未修改。删除代码不意味着所有数据与参数已删除，也不保证他人无法依据公开材料重新实现方法。

## Archived main results / 归档主结果

| Method / 方法 | RAGTruth Macro-F1 (%) |
|---|---:|
| Fixed-Max | 61.184349 |
| Calibrated-Max | 70.842902 |
| StatLR-2 | 73.569819 |
| StatLR-4 | 74.321050 |
| LoReD | 72.727037 |
| LoReD+Task | 74.610586 |
| Task-Conditioned LoReD | 74.152859 |

These archived results do not establish universal superiority over statistical aggregation or a validated length-risk mechanism. Full HaluBench: LoReD 78.863542%, Fixed-Max 79.265360%, task-conditioned extension 42.067114%. Earlier benchmark feedback informed development, so the evidence is retrospective.

这些结果不能证明普遍优于统计聚合器或长度机制成立。HaluBench 全量上 LoReD 为 78.863542%，Fixed-Max 为 79.265360%，任务条件扩展为 42.067114%。既有基准反馈曾参与开发，因此按回顾性证据解释。

## History and rights / 历史与权利

This update removes files from the current branch without rewriting Git history. Earlier commits may still contain the source code. Third-party data and models remain subject to their original terms. No software license has been selected by the author.

本次仅删除当前分支的代码文件，不改写 Git 历史；旧提交仍可能包含源码。第三方数据与模型继续遵守原条款，作者尚未选择软件许可证。
