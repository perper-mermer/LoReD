# LoReD 冻结补充实验与协议核对报告

日期：2026-10-24。本轮已完成作者指定的三项任务：测试集特征消融、HaluBench 冻结强基线、训练与阈值协议核对。只使用既有数值风险缓存和本机 CPU，没有 GPU 推理、模型下载或付费 API 调用。

## 1. 执行与复现结论

- 开发集 499 条（225 条幻觉），RAGTruth 测试集 2,700 条；输入哈希与发布包一致，开发/测试来源无交叉。
- 五个历史方法与基线（Fixed-Max、Calibrated-Max、StatLR-2、StatLR-4、正式 LoReD）在全部 2,700 条回答上逐条预测零差异。
- 本轮 15 项可比归档指标全部精确复现。此前把这些实验一概称为“未完成”不准确：HaluBench 强基线及 F0—F4 的测试结果已在本地验证目录中存在；原论文正文没有充分展示，本轮重新执行并补齐了开发选择记录、冻结模型、折分、逐条预测和统计比较。
- 所有特征、模型、阈值在评估前拟合并写入训练锁。评估后没有重新选择特征、种子、阈值或主模型。
- 实验是已知基准上的回顾性复现与诊断，不构成新增的未接触测试集验证。

## 2. 冻结测试特征消融

所有七个学习配置均使用同一开发集、相同来源五折、同一折内标准化、balanced LR(C=.1, liblinear)、同一 OOF Macro-F1 阈值选择规则。F4 是 LoReD 特征的统一协议拟合，不等于历史正式训练协议。

| 配置 | 特征 | 选定阈值 | 开发 OOF Macro-F1 (%) | 测试 Macro-F1 (%) |
|---|---|---:|---:|---:|
| F0 | max | 0.54 | 70.87 | 69.64 |
| F1 | max, max*log1p(n) | 0.57 | 71.54 | 71.73 |
| F2 | max, max*log1p(n), mean*log1p(n) | 0.54 | 75.07 | 74.63 |
| F3 | max, max*log1p(n), mean*log1p(n), run/n | 0.55 | 74.83 | 73.31 |
| F4 | max*log1p(n), mean*log1p(n), run/n | 0.49 | 74.34 | 72.73 |
| StatLR-2 | max, mean | 0.57 | 73.21 | 73.57 |
| StatLR-4 | max, mean, std(ddof=0), min | 0.56 | 74.48 | 74.32 |

其中 run/n 表示风险超过 0.5 的最长连续区间长度占句数的比例。F1 增加的是 max×log1p(n)，F2 再增加 mean×log1p(n)，F3 再增加 run/n，F4 移除未缩放 max。开发 OOF 指标参与过阈值选择，不能当成独立泛化估计。

下表差值、区间单位为百分点；七项比较作为一个 Holm 校正族。

| 比较 | 测试差值 | Bootstrap 95% CI | Holm p |
|---|---:|---|---:|
| F1 − F0 | +2.09 | [+1.09, +3.10] | 0.0014 |
| F2 − F1 | +2.90 | [+1.58, +4.20] | 0.0014 |
| F3 − F2 | -1.32 | [-2.16, -0.53] | 0.0070 |
| F4 − F3 | -0.58 | [-1.43, +0.30] | 0.3328 |
| F4 − StatLR-2 | -0.84 | [-2.02, +0.31] | 0.3328 |
| F4 − StatLR-4 | -1.59 | [-2.94, -0.26] | 0.0504 |
| F4 − Calibrated-Max | +1.89 | [+0.36, +3.38] | 0.0504 |

解释：

1. 本次固定增量比较中，max×log1p(n) 相对单独 max 的增量为 +2.09pp，mean×log1p(n) 的后续增量为 +2.90pp，二者在本比较族校正后均有统计支持。历史“+0.67pp”是开发 OOF 的另一指标，不是本次测试增量，不能互相替换。
2. 增加 run/n 后下降 1.32pp，校正后 p=0.0070。该配置和数据下，连续风险特征未贡献收益，反而造成退化；这不是证明所有连续性建模都无效。
3. LoReD 形状的 F4 仍不优于 StatLR-2/4。相对 StatLR-4 的未校正区间低于零，但 Holm p=0.0504，按 0.05 标准不称校正后显著；这也不证明两者等效。相对调优 Max 的 Holm p 同为 0.0504，不能把四舍五入后的 0.050 写成显著。
4. F2 的 74.63% 是本次固定消融配置中的最高点估计，不能据此将它直接改名为新的主模型，或声称已经证明优于 StatLR-4：本轮未将 F2–StatLR-4 纳入预先声明的比较族，更没有独立新数据确认。
5. 这些结果对具体特征增量给出局部证据，不支持“长度越长优势越大”或“长度与连续性共同解决普遍风险累积”这一强机制叙事。

## 3. HaluBench 冻结强基线

所有参数和阈值均来自 RAGTruth 开发集。完整集 13,202 条，多句子集 803 条；子集重叠，不能当作两次独立复现。

| 方法 | 冻结阈值 | 完整集 Macro-F1 (%) | 多句子集 Macro-F1 (%) |
|---|---:|---:|---:|
| Fixed-Max | 0.50 | 79.27 | 57.33 |
| Calibrated-Max | 0.83 | 75.54 | 69.07 |
| StatLR-2 | 0.57 | 79.37 | 67.01 |
| StatLR-4 | 0.56 | 63.67 | 66.67 |
| LoReD-canonical | 0.49 | 78.86 | 68.79 |

| 数据池及比较 | 差值 (pp) | Bootstrap 95% CI | Holm p |
|---|---:|---|---:|
| halubench_full: LoReD − Fixed-Max | -0.40 | [-0.74, -0.07] | 0.0164 |
| halubench_full: LoReD − Calibrated-Max | +3.32 | [+2.76, +3.89] | 0.0008 |
| halubench_full: LoReD − StatLR-2 | -0.50 | [-0.76, -0.25] | 0.0008 |
| halubench_full: LoReD − StatLR-4 | +15.20 | [+14.33, +16.06] | 0.0008 |
| halubench_multi: LoReD − Fixed-Max | +11.46 | [+8.14, +14.82] | 0.0008 |
| halubench_multi: LoReD − Calibrated-Max | -0.27 | [-3.04, +2.45] | 0.8337 |
| halubench_multi: LoReD − StatLR-2 | +1.78 | [-0.80, +4.37] | 0.5039 |
| halubench_multi: LoReD − StatLR-4 | +2.13 | [-1.38, +5.50] | 0.5039 |

解释：

- 完整集上 LoReD 比冻结调优 Max 高 3.32pp、比 StatLR-4 高 15.20pp，有本次回答级重采样的统计支持；但比 Fixed-Max 低 0.40pp，比 StatLR-2 低 0.50pp，也有本次统计支持。不能据此主张 LoReD 是外部最优方法。
- 多句子集上，LoReD 与调优 Max 的点估计几乎相同（68.79% vs 69.07%，差 −0.27pp，区间跨零）。相对固定 Max 的大幅改善不能全部归于 LoReD 的特征设计，调阈值同样能获得类似水平。未检出差异不等于证明等效。
- 完整集的 Fixed-Max 与 Calibrated-Max 使用完全相同分数，AUROC 都为 83.62%，仅冻结阈值从 0.50 变为 0.83，Macro-F1 却从 79.27% 降到 75.54%。这直接说明：在该外部设置下，源域选择的阈值并非更好的工作点；不是重新证明核验器排序变差。
- StatLR-4 在完整集上 AUROC 仍为 82.44%，但幻觉召回只有 38.47%，预测幻觉比例21.93%，而金标幻觉比例50.42%。这是冻结映射和工作点失配的迹象，不能仅凭它断言唯一原因是阈值，也没有通过外部标签再优化阈值来“修复”。
- LoReD 完整集 AUROC 83.16%、幻觉召回75.29%；StatLR-2 AUROC 84.03%、幻觉召回77.83%。简单统计映射同样可以迁移，不能将 StatLR-4 的失败写成所有统计聚合器必然失败。

### 分布诊断

| 数据池 | 回答数 | 幻觉比例 (%) | 单句比例 (%) | 平均句数 |
|---|---:|---:|---:|---:|
| development | 499 | 45.09 | 1.60 | 7.39 |
| ragtruth_test | 2700 | 34.93 | 3.00 | 6.85 |
| halubench_full | 13202 | 50.42 | 93.92 | 1.12 |
| halubench_multi | 803 | 48.94 | 0.00 | 2.98 |

HaluBench 的句数和类别分布与 RAGTruth 不同，完整集尤其以单句为主。分布描述与分层结果支持检查映射/阈值迁移，但没有隔离类别先验、长度、证据格式和内容难度各自的因果影响。特征分布、单句/长度分层及混淆计数见 accompanying CSV；不把 AUROC 正常当作概率已经校准的证明。

## 4. 训练与阈值协议核对

| 项目 | 历史正式 LoReD | 统一消融与 StatLR-2/4 |
|---|---|---|
| 开发样本/风险 | 同一499回答、同一风险缓存 | 完全相同 |
| 排序 | 字符串 ID | 数值 ID |
| 分组 | 外5/内4折 StratifiedGroupKFold | 同一 GroupKFold(5) |
| 标准化 | 训练折内部拟合 | 训练折内部拟合 |
| 标签与风险概率 | 支持=1，读取类别0概率 | 幻觉=1，读取类别1概率 |
| 分类器 | C=.1，balanced，lbfgs，max_iter4000 | C=.1，balanced，liblinear，max_iter2000 |
| 阈值目标 | 幻觉类F1优先，其余指标处理平局 | 汇总OOF Macro-F1，取首个最大值 |
| 阈值保留方式 | 最后外折的内层阈值0.49 | 全开发OOF所选阈值，F4约0.49 |
| 最终拟合 | 全开发集 | 全开发集 |
| 外部再拟合/调阈值 | 无 | 无 |

结论：历史主表属于同数据、同风险、同测试集的比较，但不是完全统一训练/阈值协议。统一消融中的 F4 与 StatLR-2/4 则确实共享同一协议和折分，可用于检验特征集合的相对贡献。不能把历史最后一折阈值规则误写成汇总 OOF Macro-F1 选择。

正式 LoReD 测试 Macro-F1 为72.7270%，统一 F4 为72.7345%，差仅−0.0074pp；逐条预测有2处不同。配对区间跨零（见 protocol diagnostic），本次结果未显示协议差异造成大的总体性能变化，但不能因此将两个协议说成相同，也不能把未检出差异解释为严格等效。

## 5. 统计、质量检查与执行修正

- RAGTruth 按450个来源分组配对重采样；HaluBench 按回答重采样。外部ID为 halubench:<response_id>，不是已核验的独立来源文档；若不同回答共享来源，当前外部区间可能低估依赖影响。
- 每个预先声明的比较族10,000次重采样、seed20261020、95%百分位区间、双侧plus-one符号尾概率和单调Holm校正。四个比较族分别校正，没有将全量与多句子集当独立确认。
- 参数文件、模型、折分与开发OOF预测在评估前冻结，评估后哈希一致。逐条重算所有结果的Macro-F1，独立验证混淆矩阵向量化公式，并核对Holm校正单调性。
- 首次评估在读取外部ID时被一个过严的格式断言停止：代码期望 source_id 与 response_id 字面相等，实际发布格式带 halubench: 命名空间。未产生性能输出即停止。保留原代码、原停止记录、训练锁和模型；只修正该断言，记录 evaluation_amendment.json 后继续。没有改变输入、重采样单位、特征、模型、参数、种子、阈值或样本。
- 没有把统一 F4 的72.7345%覆盖到历史正式72.7270%，没有按测试结果选择F2，没有重新运行无关任务扩展。

## 6. 对论文结论的直接影响

可以强化：在固定设置下，学习回答级决策能够优于固定阈值Max；某些长度和均值特征的固定增量有测试支持；LoReD相对冻结StatLR-4在外部完整集表现更稳健。

必须收敛：连续风险特征在本次匹配增量中退化；LoReD不是RAGTruth统计基线最优，也不是HaluBench整体最优；多句子集的大幅Fixed-Max提升同样可由开发阈值选择达到类似水平；不主张普遍长度机制、普遍跨核验器增益或所有统计聚合器迁移失败。

这轮实验主要补齐并核验已有证据，也发现了旧稿件对档案覆盖情况的判断遗漏；不能把“重跑确认”包装成新的独立验证。尚未执行与本任务无关的参数扫描、最新方法官方复现或新数据收集。

## English summary

The three requested checks are complete. Five canonical methods reproduced all 2,700 RAGTruth predictions with zero disagreements. Fifteen comparable archived metrics reproduced exactly. Seven feature configurations were fitted using identical source-grouped folds, fold-local scaling, balanced logistic regression, and development-only OOF Macro-F1 threshold selection. Models and thresholds were frozen before evaluation.

On RAGTruth, F0–F4 achieved 69.64%, 71.73%, 74.63%, 73.31%, and 72.73% Macro-F1. Adding the normalized longest run to F2 reduced performance by 1.32 points (95% CI [−2.16, −0.53], Holm p=.0070). The matched LoReD feature map did not outperform StatLR-2 or StatLR-4. The selected F2 configuration is not promoted to a new main method based on these test results.

On full HaluBench, frozen Fixed-Max, Calibrated-Max, StatLR-2, StatLR-4, and canonical LoReD achieved 79.27%, 75.54%, 79.37%, 63.67%, and 78.86%, respectively. LoReD exceeded the tuned maximum and four-statistic learner but remained below Fixed-Max and the two-statistic learner. On the overlapping multi-sentence subset, LoReD (68.79%) did not significantly differ from Calibrated-Max (69.07%). Thus, the large gain over the fixed rule does not establish a unique aggregation benefit.

Historical canonical LoReD and the statistical baselines differ in ordering, cross-validation, label encoding, solver, and threshold objective. The additional matched panel controls these choices. Canonical versus matched F4 differs by only 0.0074 Macro-F1 points here, without establishing procedural equivalence. HaluBench bootstrap units are responses, not verified independent source documents. These findings are retrospective and do not create an untouched test set.

## Files

- `PROTOCOL.md`: protocol fixed before fitting.
- `test_feature_ablation.csv`: all seven matched feature configurations with development/test results.
- `halubench_frozen_controls.csv`: all frozen external controls, both pools.
- `pairwise_bootstrap.csv`: 16 predeclared comparisons in four families.
- `protocol_comparison.csv`: explicit historical/matched/threshold-only protocol differences.
- `protocol_prediction_diagnostic.json`: canonical versus matched prediction differences.
- `predictions.csv`, `development_oof_predictions.csv`, `parameters.json`, `models.joblib`, `folds.json`: full evaluation and development audit trail.
- `dataset_composition.csv`, `feature_distribution_diagnostics.csv`, `task_length_strata.csv`: descriptive distribution diagnostics.
- `canonical_prediction_check.json`, `archive_reproduction_check.csv`, `evaluation_complete.json`, `qa_check.json`: completion and quality checks.
- `pre_fit_lock.json`, `training_lock.json`, `evaluation_amendment.json`, `STOP_evaluate.json`: frozen provenance and retained schema correction history.
