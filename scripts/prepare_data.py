"""Strict adapter from prepared sentence rows + verifier caches to numeric responses."""
from pathlib import Path
import argparse, json, sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from lored import read_jsonl, stable_id, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows', type=Path, required=True)
    parser.add_argument('--scores', type=Path, required=True)
    parser.add_argument('--gold', type=Path, help='Response JSONL with gold=1 supported')
    parser.add_argument('--score-field', default='score')
    parser.add_argument('--score-key', choices=['pair', 'sentence'], default='pair')
    parser.add_argument('--source-prefix', default='')
    parser.add_argument('--task-override')
    parser.add_argument('--group-by-response', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    scores = {}
    for item in read_jsonl(args.scores):
        key, value = str(item['id']), float(item[args.score_field])
        if not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f'Invalid support score: {key}')
        if key in scores and scores[key] != value:
            raise ValueError(f'Conflicting duplicate score: {key}')
        scores[key] = value
    gold = {str(r.get('response_id', r.get('id'))): int(r['gold']) for r in read_jsonl(args.gold)} if args.gold else None
    grouped = {}
    for row in read_jsonl(args.rows):
        grouped.setdefault(str(row['response_id']), []).append(row)
    output = []
    for rid in sorted(grouped):
        items = sorted(grouped[rid], key=lambda r: int(r['sentence_index']))
        if len({int(r['sentence_index']) for r in items}) != len(items):
            raise ValueError(f'Duplicate sentence index: {rid}')
        if len({str(r.get('source_id', rid)) for r in items}) != 1:
            raise ValueError(f'Inconsistent source IDs: {rid}')
        risks, words = [], []
        for row in items:
            keys = [str(row['id'])] if args.score_key == 'sentence' else [stable_id(str(row['claim']), str(e['text']).strip()) for e in row['evidence']]
            if not keys or any(k not in scores for k in keys):
                raise ValueError(f'Empty evidence or missing scores: response {rid}, sentence {row["sentence_index"]}')
            risks.append(1-max(scores[k] for k in keys))
            words.append(len(str(row['claim']).split()))
        support = gold[rid] if gold is not None else int(not any(int(r['gold_binary']) == 0 for r in items))
        if support not in (0, 1):
            raise ValueError(f'Invalid gold label: {rid}')
        source = rid if args.group_by_response else str(items[0]['source_id'])
        output.append({'response_id': rid, 'source_id': args.source_prefix + source,
                       'task': args.task_override or str(items[0].get('task_type', 'QA')),
                       'gold_hall': 1-support, 'risks': risks, 'word_counts': words})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(''.join(json.dumps(row) + '\n' for row in output), encoding='utf-8')
    paths = {'rows': args.rows, 'scores': args.scores, 'gold': args.gold}
    manifest = {'responses': len(output), 'label': 'gold_hall=1 means hallucination',
                'score_key': args.score_key, 'score_field': args.score_field,
                'input_sha256': {key: sha256(path) for key, path in paths.items() if path},
                'output_sha256': sha256(args.output)}
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
