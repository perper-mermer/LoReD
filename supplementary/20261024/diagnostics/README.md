# LoReD accompanying supplementary materials

This archive supplements the original LoReD release. It contains all nine development-only parameter configurations, outer validation decisions/folds, an evidence-verified hallucination-positive case summary, and a separate CPU timing run. No model or operating point was selected from these checks. Raw source documents, full responses, weights and credentials are excluded.

Download or clone the public LoReD release first. In its existing Python environment (NumPy2.3.5 and scikit-learn1.7.2 were used), run:

```
python scripts/development_sensitivity.py --release-root /path/to/LoReD --output outputs/development_sensitivity
```

The script accepts no test argument and verifies the frozen development SHA256. Its nine reported configurations reproduce the archived numerical results. Development diagnostics do not replace the canonical test result or prove generalization.

For timing, first generate trusted local frozen models with the original release train/main command. Then, on Windows with psutil installed:

```
python scripts/decision_timing_windows.py --release-root C:/path/to/LoReD --models C:/path/to/models.joblib --output outputs/current_timing
```

Load only trusted locally generated joblib models. Timing outputs vary with hardware and load. The measured call includes lightweight method lookup/branching; the shorthand 'no dispatch' in raw scope fields means the generic all-feature dispatcher is absent, not that Python selection overhead is zero. No new performance model is fitted by timing.

Historical latency values remain separate. Do not infer historical CPU identity from the current run. The new positive example is detected by both Fixed-Max and LoReD; it is not a unique LoReD correction or an independent relabeling study. Applicable third-party data and model terms remain in force; no new license is asserted by this archive.

中文：此包补充九组仅开发集嵌套参数诊断、原始证据核对后的真阳性摘要和独立硬件计时。没有改选主模型或测试阈值；不包含原始全文、权重或密钥。参数复现脚本不接收测试集参数，计时按硬件变化。案例由两个方法共同检出，不能用作独有优势。原有发布包与各数据集、模型条款继续适用。
