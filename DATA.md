# Data and preprocessing / 数据与预处理

`benchmarks/` contains derived numeric risks, word counts, IDs, task tags, labels, splits and archived judge predictions. No passages, claims or answers are included. File hashes: `audit/benchmark_sha256.json`. Original datasets and weights must be acquired separately under their original terms.

缓存仅含派生数值与元数据，无原始段落、claim 或回答。原始数据和权重按原条款另行获取。

## Sources / 来源

- RAGTruth: https://github.com/CodingLL/RAGTruth (`dataset/response.jsonl`, `dataset/source_info.jsonl`).
- HaluBench: https://huggingface.co/datasets/PatronusAI/HaluBench .
- FactCG: https://github.com/yaxili96/FactCG and https://huggingface.co/yaxili96/FactCG-DeBERTa-v3-Large . A config snapshot alone is not the original stage-2 checkpoint.
- MiniCheck: https://huggingface.co/lytang/MiniCheck-Flan-T5-Large .
- HHEM: https://huggingface.co/vectara/hallucination_evaluation_model .

Fixed RAGTruth sample: 499 development responses, 2,700 test responses/450 test sources. The exact IDs are in `ragtruth_split_manifest.json`. HaluBench includes 13,202 non-empty eligible responses and an 803-response multi-sentence subset.

开发样本为固定的 499 条回答，而非全部训练集。HaluBench 全量 13,202 条，多句子集 803 条。

## Numeric schema / 数值格式

```json
{"response_id":"example-1","source_id":"source-1","task":"QA","gold_hall":1,"risks":[0.2,0.8],"word_counts":[12,15]}
```

`gold_hall` is optional only for prediction. Arrays must be nonempty, aligned and ordered. Risks must be finite in [0,1]. Namespace external source IDs.

纯预测可不提供标签；风险和词数数组必须非空、对齐并保持句序。

## Sentence and cache schema / 句级与缓存格式

```json
{"id":"sentence-1","response_id":"example-1","source_id":"source-1","sentence_index":0,"claim":"A sentence.","task_type":"QA","gold_binary":0,"evidence":[{"text":"Evidence."}]}
```

`gold_binary=0` means hallucination. Optionally supply `--gold` as JSONL `{"response_id":"example-1","gold":0}`; this historical `gold` uses 1=supported, unlike `gold_hall`.

FactCG cache: `{"id":"pair_sha256","score":0.9}`, with key SHA256(claim + NUL + evidence.strip()). The adapter maximizes support over evidence chunks and rejects missing scores.

历史 `gold` 为支持标签，与 `gold_hall` 方向相反。FactCG 缓存以 claim、NUL 与去边缘空白后的证据计算 SHA256；缺失分数直接报错。

```sh
python scripts/prepare_data.py --rows data/development_rows.jsonl --scores data/development_factcg.jsonl --output data/development.jsonl
```

For MiniCheck/HHEM use sentence IDs and the recorded score field. Repeat both scoring and preparation for the test rows with separate output names. Never mix model revisions across development and test.

MiniCheck/HHEM 使用句子 ID；开发、测试必须使用相同版本和序列化协议。

```sh
python scripts/score_verifier.py --verifier minicheck --model models/minicheck --rows data/development_rows.jsonl --output data/minicheck_scores.jsonl --batch-size 8
python scripts/prepare_data.py --rows data/development_rows.jsonl --scores data/minicheck_scores.jsonl --score-key sentence --score-field joint_score --output data/minicheck_development.jsonl
python scripts/score_verifier.py --verifier hhem --model models/hhem --foundation models/flan-t5-base --rows data/development_rows.jsonl --output data/hhem_scores.jsonl --batch-size 8
python scripts/prepare_data.py --rows data/development_rows.jsonl --scores data/hhem_scores.jsonl --score-key sentence --score-field support_score --output data/hhem_development.jsonl
```

## HaluBench / 外部数据

Export original test records to JSONL without changing text/labels:

```sh
python scripts/rebuild_halubench_rows.py --data-jsonl data/halubench_test.jsonl --output-dir data/halubench
python scripts/score_factcg.py --rows data/halubench/halubench_sentence_rows.jsonl --config models/factcg_config --checkpoint models/factcg_stage2.ckpt --output data/halubench/factcg_scores.jsonl
python scripts/prepare_data.py --rows data/halubench/halubench_sentence_rows.jsonl --scores data/halubench/factcg_scores.jsonl --gold data/halubench/halubench_responses.jsonl --task-override QA --group-by-response --source-prefix halubench: --output data/halubench_full.jsonl
```

Historical preparation maps FAIL to hallucination, excludes empty answers and retains non-empty short answers as one claim when ordinary sentence splitting returns none. The preparation audit records label vocabulary, exclusions and fallback counts. Check it before interpreting data from a changed revision.

历史处理将 FAIL 映射为幻觉，排除空回答，无法正常分句的非空短回答保留为一条 claim；准备审计记录词表、排除数量及回退数量。
