# LoReD

**Learning Response-Level Hallucination Decisions from Local Factuality Risks**  
**从局部事实性风险学习回答级幻觉决策**

## Current paper version / 当前论文版本

Results and descriptions are synchronized to the author-supplied `LoReD_Chinese_Translation10.pdf` on 2026-11-22. See [current paper tables](results/current_paper/README.md) for table numbers, precision, provenance and remaining caveats. This is a results-and-records archive, not executable software.

当前结果与表述按作者提供的最新论文同步，见[论文结果索引](results/current_paper/README.md)。仓库不含实现代码或可执行复现脚本。实验输入数据集及配套清单已从当前分支删除；历史提交仍可能包含这些数据。

## Method and evidence / 方法与证据

LoReD is one response-level decision method using frozen verifier risks. Its four-parameter logistic classifier uses length-scaled maximum risk, length-scaled mean risk and a high-risk-run statistic. Task-aware heads are optional variants, not required parts of core LoReD. Choosing a classification threshold is not evidence of probability calibration.

LoReD 从冻结核验风险学习响应级决策；任务感知头单独作为可选变体。阈值收益不等同于排序能力或概率校准收益。连续段特征未显示独立正增益，不宣称存在已验证的普遍长度机制。

## RAGTruth test / RAGTruth测试结果

Percentages; current paper Table 4. Full-precision values verified from local frozen coefficients/caches are in [canonical_main_results.csv](results/canonical_main_results.csv).

| Method | Macro-F1 | BAcc | AUROC |
|---|---:|---:|---:|
| Fixed-Max | 61.18 | 69.21 | 81.18 |
| Tuned-Max | 70.84 | 73.62 | 81.18 |
| StatLR-2 | 72.39 | 74.88 | 81.14 |
| StatLR-4 | 72.04 | 74.88 | 83.16 |
| LoReD | 72.73 | 75.04 | 82.14 |
| LoReD+Task | 74.61 | 76.63 | 84.41 |
| Task-Conditioned LoReD | 74.15 | 76.59 | 84.90 |

Core LoReD has the highest task-independent Macro-F1 point estimate in this comparison. Its +0.34/+0.68 pp differences against StatLR-2/4 are not statistically significant after Holm correction. The +1.8841 pp difference against Tuned-Max has exploratory Holm p=0.041996 in the paper's four-comparison family. Earlier benchmark feedback informed development; these are retrospective, exploratory results, not a new untouched test.

核心 LoReD 为本表无任务信息方法中的最高宏平均F1点估计，但相对两种 StatLR 的差异未获显著支持。任务头提高汇总分数并不代表跨任务稳定改善：LoReD+Task 的 Data2txt 为47.70%，任务等权宏平均F1为61.94%，均低于核心模型对应值59.18%与64.40%。

## Frozen transfer / 冻结迁移

Full HaluBench (13,202): LoReD Macro-F1=78.86%, below Fixed-Max (79.27%) and StatLR-2 (79.50%). Multi-sentence subset (803): LoReD=68.79%, Tuned-Max=69.07%; only the LoReD versus Fixed-Max difference is significant in the four-comparison Holm family. Full and multi-sentence pools overlap. All external task indicators remain QA. Task heads show substantial negative transfer on the full set; AUROC and thresholded F1 must be interpreted separately.

完整HaluBench上不宣称LoReD最优；803条多句集上，LoReD仅相对Fixed-Max的优势在该比较族内显著。保留任务头负迁移、统计对照和全部比较，见表14–15。

## Verifier and efficiency boundaries / 核验器与效率边界

AlignScore-base: LoReD=70.15% Macro-F1 versus Tuned-Max=66.91%. HHEM: LoReD=69.25% versus Tuned-Max=70.86%. MiniCheck appendix: LoReD=71.93% versus Tuned-Max=72.81%. Gains depend on the verifier. Current controlled CPU decision latency is 113.80 microseconds/response, excluding verifier inference; StatLR-2/4 are not slower than LoReD in that run.

## Repository contents / 仓库内容

- `results/current_paper/`: paper Tables 2 and 4–17, with explicit reported-value provenance.
- `results/`: current main results, frozen parameters, comparisons, prediction export and verifier summary; historical-only files are identified in its README.
- `results/historical_20261026/` and `supplementary/20261024/`: preserved earlier versions, not interchangeable with current tables.
- `benchmarks/`: archived LLM-judge predictions only, not benchmark input datasets.
- `audit/`: current synchronization checks plus historical audit/hash records.
- `requirements*.txt`: historical environment documentation, not an executable package.

## Threshold and availability caveats / 阈值与可用性说明

StatLR-2/4 use the paper-reported operating points 0.540/0.510. Their coefficients are unchanged. The paper explicitly notes that rerunning the stated development search on available caches yields different optima; exact selection provenance still needs the corresponding fold/OOF exports. Do not describe those values as newly verified OOF maxima. No fitting or threshold search was performed for this synchronization.

实验数据集已于2026-11-22从当前分支移除，但模型输出、标签、样本ID和历史提交中的材料仍保留。这不是完整的数据擦除或历史清除。

Third-party data/models remain subject to their original terms. No software license has been selected by the author.
