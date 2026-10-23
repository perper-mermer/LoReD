# -*- coding: utf-8 -*-
"""Prepare HaluBench test rows for one-shot frozen-model evaluation.

Rules (frozen in FROZEN_PROTOCOL.md before any label was read):
- All test rows; label mapping per official README: "FAIL" -> 0 (hallucinated),
  every other value -> 1 (supported); the actual vocabulary is asserted and
  recorded in the audit.
- Answer split with the project standard sentence_spans rule (>=3 alnum tokens).
- Short-answer fallback (pre-registered): non-empty answer yielding 0 spans is
  scored as ONE single claim; empty/whitespace answers are excluded and counted.
- Evidence = passage chunked with the project standard chunk_text (350 words).
- Task type is QA for every row (task_QA=1); never decided from labels.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--data-jsonl", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from ragtruth_serialization import chunk_text, sentence_spans  # noqa: E402

    rows = read_jsonl(args.data_jsonl)
    required = {"id", "passage", "question", "answer", "label", "source_ds"}
    missing_fields = sorted(required - set(rows[0]))
    if missing_fields:
        raise RuntimeError(f"unexpected HaluBench schema, missing {missing_fields}; got {sorted(rows[0])}")

    vocab = sorted({str(r["label"]) for r in rows})
    if "FAIL" not in vocab:
        raise RuntimeError(f"label vocabulary has no FAIL: {vocab}")
    gold_map = {value: (0 if value == "FAIL" else 1) for value in vocab}

    sentence_rows: list[dict] = []
    response_meta: list[dict] = []
    excluded: list[dict] = []
    for row in rows:
        rid = str(row["id"])
        answer = str(row["answer"] or "").strip()
        passage = str(row["passage"] or "").strip()
        if not answer:
            excluded.append({"response_id": rid, "reason": "empty_answer",
                             "source_ds": str(row["source_ds"])})
            continue
        spans = sentence_spans(answer)
        if not spans:
            claims = [(0, answer)]
            fallback = True
        else:
            claims = [(index, text) for index, (_, _, text) in enumerate(spans)]
            fallback = False
        chunks = chunk_text(passage)
        evidence = [
            {"text": chunk, "question_index": index, "source_url": ""}
            for index, chunk in enumerate(chunks)
        ]
        for sentence_index, (_, claim) in enumerate(claims):
            sentence_rows.append({
                "id": f"halubench-{rid}-s{sentence_index}",
                "response_id": rid,
                "source_id": rid,
                "sentence_index": sentence_index,
                "claim": claim,
                "task_type": "QA",
                "generator": str(row["source_ds"]),
                "evidence": evidence,
            })
        response_meta.append({
            "response_id": rid,
            "source_id": rid,
            "source_ds": str(row["source_ds"]),
            "question": str(row["question"]),
            "passage": passage,
            "answer": answer,
            "gold": int(gold_map[str(row["label"])]),
            "label_raw": str(row["label"]),
            "n_sentences": len(claims),
            "single_claim_fallback": fallback,
            "answer_words": len(answer.split()),
            "passage_words": len(passage.split()),
            "n_evidence_chunks": len(chunks),
        })

    audit = {
        "dataset": "PatronusAI/HaluBench test",
        "source_file": str(args.data_jsonl),
        "total_rows": len(rows),
        "excluded_empty_answer": len(excluded),
        "evaluated_responses": len(response_meta),
        "sentence_rows": len(sentence_rows),
        "label_vocabulary": vocab,
        "label_to_gold_map": gold_map,
        "label_counts_evaluated": {k: int(v) for k, v in
                                   Counter(r["label_raw"] for r in response_meta).items()},
        "gold_counts": {0: sum(1 for r in response_meta if r["gold"] == 0),
                        1: sum(1 for r in response_meta if r["gold"] == 1)},
        "single_claim_fallback_responses": sum(1 for r in response_meta if r["single_claim_fallback"]),
        "source_ds_counts": {k: int(v) for k, v in
                             Counter(r["source_ds"] for r in response_meta).items()},
        "answer_words": {
            "mean": float(np.mean([r["answer_words"] for r in response_meta])),
            "median": float(np.median([r["answer_words"] for r in response_meta])),
            "p25": float(np.percentile([r["answer_words"] for r in response_meta], 25)),
            "p75": float(np.percentile([r["answer_words"] for r in response_meta], 75)),
            "max": int(max(r["answer_words"] for r in response_meta)),
        },
        "n_sentences_counts": {k: int(v) for k, v in
                               Counter(r["n_sentences"] for r in response_meta).items()},
        "rules": {
            "split": "sentence_spans (>=3 alnum tokens); non-empty 0-span answer -> single claim",
            "exclusion": "only empty/whitespace answers",
            "evidence_chunk": "chunk_text 350 words",
            "task_type": "QA for all rows",
        },
    }
    write_jsonl(args.output_dir / "halubench_sentence_rows.jsonl", sentence_rows)
    write_jsonl(args.output_dir / "halubench_responses.jsonl", response_meta)
    write_jsonl(args.output_dir / "excluded_responses.jsonl", excluded)
    (args.output_dir / "prepare_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "total_rows": audit["total_rows"],
        "evaluated_responses": audit["evaluated_responses"],
        "sentence_rows": audit["sentence_rows"],
        "excluded_empty_answer": audit["excluded_empty_answer"],
        "label_vocabulary": vocab,
        "gold_counts": audit["gold_counts"],
        "single_claim_fallback_responses": audit["single_claim_fallback_responses"],
        "source_ds_counts": audit["source_ds_counts"],
        "output": str(args.output_dir),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
