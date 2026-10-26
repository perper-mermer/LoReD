# Archive scope

These numeric outputs and protocol records are byte-identical copies of the completed frozen validation. Original JSON locks contain historical local paths and a hash of the locally generated `models.joblib`; the binary model is intentionally not shipped. Use `scripts/frozen_validation.py prepare` to regenerate trusted local models in a new output directory, followed by its separate `evaluate` phase.

The initial stopped evaluator and the corrected evaluator are retained in `archive/`. The correction fixed evaluation bookkeeping without refitting models. `evaluation_amendment.json` records its scope. Run the portable entry point, not these historical workspace-specific scripts.

中文：本目录保留已完成冻结验证的原始数值结果及修复历史。历史锁文件含原运行路径和未打包的本地模型哈希；它们是审计记录，不是当前机器可直接执行的路径。请通过仓库根目录的可移植入口在新输出目录中重建模型，再单独评价。原实验目录未修改。
