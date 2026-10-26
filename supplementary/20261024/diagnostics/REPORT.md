# 开发集敏感性 真实幻觉案例与硬件计时补强

2026-10-24。有限检查全部完成。没有将参数变体用于测试集或HaluBench评价，没有更换主模型或正式数字。

## 开发集敏感性

固定499条开发回答，字符串ID排序，来源分组外5/内4折嵌套分析。内层OOF只在各外折训练部分选择阈值，随后评价对应外折验证部分。汇总所有外层留出决策得到下表；不是测试集结果，也不同于汇总OOF五种子协议。所有九个预设配置均报告，不从中选择新主模型。

| C | 连续风险截止值ρ | 嵌套开发Macro-F1 (%) | BAcc (%) | 内选阈值范围 |
|---:|---:|---:|---:|---|
| 0.01 | 0.5 | 72.92 | 73.38 | 0.49–0.51 |
| 0.03 | 0.5 | 73.54 | 74.12 | 0.48–0.50 |
| 0.1 | 0.5 | 73.94 | 74.49 | 0.48–0.49 |
| 0.3 | 0.5 | 68.85 | 70.13 | 0.28–0.50 |
| 1 | 0.5 | 71.12 | 72.13 | 0.36–0.49 |
| 0.1 | 0.3 | 70.30 | 71.40 | 0.34–0.48 |
| 0.1 | 0.4 | 73.93 | 74.41 | 0.48–0.51 |
| 0.1 | 0.6 | 73.15 | 73.88 | 0.41–0.51 |
| 0.1 | 0.7 | 72.14 | 73.01 | 0.43–0.49 |

默认配置为73.94%。固定ρ=0.5时，C扫描范围68.85%–73.94%；固定C=0.1时，ρ扫描范围70.30%–73.94%。C=0.3出现最低Macro-F1及[0.28,0.50]内选阈值范围，不能宣称参数不敏感。相近AUROC与阈值波动不能单独确立原因。默认配置五折内选阈值[0.48,0.49,0.48,0.49,0.49]与归档一致；此处使用各外折阈值评价开发留出部分，不等于全开发拟合后采用最后一折阈值的正式模型。不将73.94%写成测试成绩。

## 幻觉真阳性案例

回答68，来源15604，Summary测试样本。原文为批评Rand Paul的第一人称评论，没有提及Elizabeth Warren；回答却将评论归给“Senator Elizabeth Warren”。原标注将字符[0,24)标为Evident Baseless Info，已核对来源、回答、偏移、分句和缓存顺序。

最大风险0.975507，LoReD风险0.615486，分别超过阈值0.50和0.49，两者均正确检出。预设“仅LoReD检出”的候选为空，按协议转用两者均检出的首个递增ID候选；不声称LoReD纠正了最大值漏检。现有三个支持类案例保留。该案例不构成独立重标或频率估计，原始全文只保留在本地研究归档。

## 当前硬件冻结计时

实际CPU为Intel Core i7-14700HX，20物理核、28逻辑核、约32GiB内存，Windows11；Python3.13.9、NumPy2.3.5、scikit-learn1.7.2。BLAS/OpenMP设为单线程并核验。五方法2700条预测与冻结参考零差异。

预热200条，每条10次重复，关闭GC，方法顺序按预设循环交错。统计2700条回答各自重复中位数的Median/P95，吞吐从其中均值折算，非并发实测吞吐。含直接推理调用的轻量方法分支、特征构造、预测与阈值判断；不含读取、数组构造、通用全特征分派器或核验器推理。

| 方法 | 中位延迟μs | P95 μs | 均值折算回答/秒 |
|---|---:|---:|---:|
| Fixed-Max | 1.70 | 1.85 | 581,345 |
| Calibrated-Max | 1.20 | 1.20 | 850,420 |
| StatLR-2 | 100.03 | 104.25 | 10,012 |
| StatLR-4 | 111.40 | 116.60 | 8,975 |
| LoReD | 113.80 | 119.95 | 8,777 |

LoReD新增决策成本较低，但没有比StatLR-2/4更快。最大值规则约1–2μs；两种最大值方法的微小差异不应解释为方法级加速。原114.90/237.95μs归档保留，本次硬件身份不能补造历史环境；本次作为单独运行报告。

## English summary

All nine predeclared configurations were evaluated only through nested source-grouped development validation. Macro-F1 ranged from68.85% to73.94% over C and from70.30% to73.94% over the run cutoff. This reveals parameter sensitivity rather than a new test improvement. No model was selected.

The added positive case is Summary response68: the response names Elizabeth Warren although the source does not. The unsupported attribution and raw annotation were checked. Both Fixed-Max and LoReD detect it; no unique LoReD correction is claimed.

A separate frozen timing run on an Intel Core i7-14700HX with one BLAS thread gives LoReD a113.80μs median, StatLR-2 100.03μs and StatLR-4 111.40μs. This supports low added cost, not a speed advantage. All historical results remain unchanged.
