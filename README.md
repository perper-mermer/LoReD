# LoReD

**Learning Response-Level Hallucination Decisions from Local Factuality Risks**  
**从局部事实性风险学习回答级幻觉决策**

Runnable CPU reproduction from sentence-risk caches, including training, matched baselines, source-grouped statistical comparisons, sensitivity, ablations and external evaluation. GPU scoring entry points are provided separately. LoReD is the core method; task conditioning is an optional extension.

本仓库支持从句级风险缓存重新训练并复现主要实验，包括匹配基线、来源分组统计检验、敏感性分析、消融与外部验证。另提供 GPU 核验器推理入口。LoReD 是主方法，任务条件化为可选扩展。

## Quick start / 快速开始

Use Python 3.11 or newer; release validation used Python 3.13.9, NumPy 2.3.5, scikit-learn 1.7.2 and joblib 1.5.2. Run from the repository root:

使用 Python 3.11 及以上版本；进入仓库根目录运行：

```sh
python -m pip install -r requirements.txt
python scripts/reproduce.py --output outputs/reproduction
```

This runs all cached-score experiments without model downloads, GPU inference or API calls. The full HaluBench bootstrap needs several GB of free RAM. Numeric benchmarks contain risks, lengths, IDs and labels; source passages and generated answers are excluded.

该命令运行全部缓存实验，不下载模型、不调用 API、不使用 GPU。全量 HaluBench bootstrap 需要预留数 GB 内存。缓存只含数值、ID 与标签，不含原始文本。

For only the principal comparison / 只复现主要比较：

```sh
python scripts/run.py main --development benchmarks/ragtruth_development.jsonl --test benchmarks/ragtruth_test.jsonl --output outputs/main --check-reference
```

`--check-reference` checks predictions by response ID. During release validation, all seven methods matched all 2,700 archived predictions with zero disagreements. AUROC may differ in the last decimals because archived risks were rounded.

`--check-reference` 按 ID 检查逐条预测。本次验证七种方法全部 2,700 条预测零差异。历史风险分数经过舍入，因此重训 AUROC 的末位可能略有不同。

## Results / 结果

| Method / 方法 | RAGTruth Macro-F1 (%) |
|---|---:|
| Fixed-Max | 61.184349 |
| Calibrated-Max | 70.842902 |
| StatLR-2 | 73.569819 |
| StatLR-4 | 74.321050 |
| LoReD | 72.727037 |
| LoReD+Task | 74.610586 |
| Task-Conditioned LoReD | 74.152859 |

The evidence does not establish universal superiority over statistical aggregation or a validated length-risk mechanism. Full HaluBench: LoReD 78.863542%, Fixed-Max 79.265360%, task-conditioned extension 42.067114%. Keep negative findings and all comparison rows. Earlier benchmark feedback informed development, so the evidence is retrospective.

这些结果不能证明普遍优于统计聚合器或长度机制成立。HaluBench 全量上 LoReD 为 78.863542%，Fixed-Max 为 79.265360%，任务条件扩展为 42.067114%。保留负面发现与完整比较；既有基准反馈曾参与开发，因此按回顾性证据解释。

## Commands / 分项命令

```sh
# Five-seed sensitivity / 五种子敏感性分析
python scripts/run.py seeds --development benchmarks/ragtruth_development.jsonl --test benchmarks/ragtruth_test.jsonl --output outputs/seeds

# Matched feature ablations / 匹配协议特征消融
python scripts/run.py ablation --development benchmarks/ragtruth_development.jsonl --test benchmarks/ragtruth_test.jsonl --output outputs/ablation

# Verifier-specific adaptation / 核验器适配
python scripts/cross_verifier.py --development benchmarks/minicheck_development.jsonl --test benchmarks/minicheck_test.jsonl --verifier MiniCheck-Flan-T5-Large --output outputs/minicheck
python scripts/cross_verifier.py --development benchmarks/hhem_development.jsonl --test benchmarks/hhem_test.jsonl --verifier HHEM-2.1-Open --output outputs/hhem

# Frozen external transfer / 冻结参数外部验证
python scripts/run.py evaluate --model outputs/main/models.joblib --test benchmarks/halubench_full.jsonl --output outputs/halubench_full
python scripts/run.py evaluate --model outputs/main/models.joblib --test benchmarks/halubench_multi.jsonl --output outputs/halubench_multi

# Matched archived judges / 同样本归档 LLM 评估
python scripts/evaluate_judges.py --predictions outputs/main/predictions.csv --output outputs/judges

# Decision-layer timing / 决策层计时
python scripts/run.py timing --model outputs/main/models.joblib --test benchmarks/ragtruth_test.jsonl --output outputs/timing

# Contract checks / 输入及分组约束检查
python -m unittest discover -s tests
```

`main` saves models, readable parameters, folds, metrics, long-format predictions, task/length strata, bootstrap comparisons and input hashes. `train` does not open test data; `predict` does not require labels. Load only trusted locally generated joblib files.

`main` 保存模型、可读参数、折分、指标、逐条预测、任务/长度分层、统计比较与哈希。`train` 不读取测试集，`predict` 不要求标签。joblib 文件只从可信来源加载。

```sh
python scripts/run.py train --development benchmarks/ragtruth_development.jsonl --output outputs/train_only
python scripts/run.py predict --model outputs/train_only/models.joblib --test benchmarks/ragtruth_test.jsonl --output outputs/predictions
```

Timing excludes sentence verification and depends on hardware. The portable feature-dispatch interface adds overhead relative to the original specialized harness; archived latency should not be expected exactly. Use `reproduce.py --timing` to include timing.

计时不含句级核验，受硬件影响。通用特征接口相比原专用测速程序存在额外开销，不能要求精确复现旧延迟。

## Upstream inference / 上游推理

See [DATA.md](DATA.md) for original sources, schemas and preprocessing. Rebuilding RAGTruth text preparation and applying the original caches produced byte-identical numeric inputs for 499 development and 2,700 test responses. The fixed development sample is listed in the split manifest; it is not all training data.

原始来源、格式和预处理见 [DATA.md](DATA.md)。本次从原始 RAGTruth 文件重建后应用原缓存，499 条开发回答与 2,700 条测试回答的数值输入完全一致。开发样本 ID 已固定，不代表全部训练数据。

```sh
python scripts/rebuild_ragtruth_rows.py --responses data/ragtruth/response.jsonl --sources data/ragtruth/source_info.jsonl --split-manifest benchmarks/ragtruth_split_manifest.json --partition development --output data/development_rows.jsonl
python scripts/rebuild_ragtruth_rows.py --responses data/ragtruth/response.jsonl --sources data/ragtruth/source_info.jsonl --split-manifest benchmarks/ragtruth_split_manifest.json --partition test --output data/test_rows.jsonl
python -m pip install -r requirements-inference.txt
python scripts/score_factcg.py --rows data/development_rows.jsonl --config models/factcg_config --checkpoint models/factcg_stage2.ckpt --output data/development_factcg.jsonl
python scripts/prepare_data.py --rows data/development_rows.jsonl --scores data/development_factcg.jsonl --output data/development.jsonl
python scripts/score_factcg.py --rows data/test_rows.jsonl --config models/factcg_config --checkpoint models/factcg_stage2.ckpt --output data/test_factcg.jsonl
python scripts/prepare_data.py --rows data/test_rows.jsonl --scores data/test_factcg.jsonl --output data/test.jsonl
python scripts/run.py main --development data/development.jsonl --test data/test.jsonl --output outputs/from_text
```

FactCG requires the original stage-2 Lightning checkpoint and config/tokenizer revision `0430e3509dbd28d2dff7a117c0eae25359ff3e80`. Its loader rejects missing/unexpected keys. MiniCheck revision: `96eafd01cee2d16cf81aaa2fb226b14f422a37b3`; HHEM revision: `de9a5e6ba9ba49531a022dba17e35ffeb2a6fad8`. No third-party weights are included. Install a CUDA-compatible PyTorch build for your machine.

FactCG 必须使用原 stage-2 Lightning 权重；加载时严格检查 key。第三方权重不打包。GPU 入口在本次发布中完成语法/CLI 检查，未重新执行完整 GPU 推理；CPU 缓存实验已实际运行。

## LLM judges / LLM 判断

The archived 999-response judges are budget-limited baselines, not official G2LDetect or MASE reproductions. Direct judging truncates evidence/response to 2,000/1,000 characters; local judging checks at most five sentences with 1,500 evidence characters and 300 characters per sentence. API reruns are optional and may drift with the model alias:

归档判断基线受预算限制，不能称作 G2LDetect 或 MASE 的官方复现。API 入口保留截断和解析规则，但遇到请求失败即停止，避免将失败当作支持标签。

```sh
python -m pip install -r requirements-api.txt
# Set DEEPSEEK_API_KEY in the environment / 先设置环境变量密钥
python scripts/llm_judge.py --rows data/test_rows.jsonl --max-responses 10 --output outputs/api/judges.jsonl
```

## Protocol and rights / 协议与权利

Read [PROTOCOL.md](PROTOCOL.md): historical canonical LoReD uses the final outer fold's inner-selected threshold, not pooled OOF Macro-F1 selection. This historical choice is preserved explicitly. Grouping/cross-fitting does not remove adaptive benchmark reuse.

请阅读 [PROTOCOL.md](PROTOCOL.md)：正式历史 LoReD 使用最后一个外层折的内层阈值，不是汇总 OOF 后最大化 Macro-F1。代码明确保留该规则。分组/cross-fitting 不会消除自适应使用基准造成的影响。

No software license has been selected by the author. Third-party data and models remain governed by their original terms. No credentials, manuscript, raw passages or downloaded weights are included.

作者尚未选择软件许可证；第三方数据和模型遵守原条款。不包含密钥、论文稿件、原始段落或下载权重。
