# LoReD

**Learning Response-Level Hallucination Decisions from Local Factuality Risks**  
**从局部事实性风险学习回答级幻觉决策**

## Overview / 项目简介

This repository is a results and experiment-record archive for LoReD. It provides frozen parameters, archived predictions, experimental results, protocols, and provenance records. Benchmark input datasets and their split/manifest files were removed from the current branch on 2026-11-22; historical commits can still contain them.

本仓库为 LoReD 的实验结果与记录归档，提供冻结参数、归档预测、实验结果、实验协议及来源记录。实验输入数据集及配套划分、清单文件已于 2026-11-22 从当前分支移除；历史提交仍可能包含这些文件。

## Repository contents / 仓库内容

- `benchmarks/`: archived LLM judge predictions only; benchmark input datasets and their split/manifest files are no longer included.
- `results/`: canonical metrics, matched predictions, frozen parameters and archived comparisons.
- `supplementary/`: supplementary data, metrics, predictions, protocols, timing records and reports.
- `audit/`: provenance and historical release-validation records.
- `DATA.md`, `PROTOCOL.md` and supplementary Markdown files: data descriptions and experimental protocols.
- `requirements*.txt`: dependency lists documenting the historical experimental environment.

验证日志、命令示例和哈希清单记录的是对应实验或归档版本，应结合各文件的日期与适用范围阅读。

Validation logs, command examples, and hash manifests describe their respective experimental or archived versions and should be read in that context.

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

## Rights / 使用条款

Third-party data and models remain subject to their original terms. No software license has been selected by the author.

第三方数据与模型遵守原始使用条款，作者尚未选择软件许可证。
