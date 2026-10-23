"""Evaluate archived budget-limited LLM judges on exactly matched IDs."""
import argparse,csv,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lored import metrics_hall,paired_bootstrap_many,write_csv


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--judges',type=Path,default=Path(__file__).resolve().parents[1]/'benchmarks/llm_judge_predictions.jsonl')
    p.add_argument('--predictions',type=Path,required=True,help='Long-format predictions.csv from run.py main')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    judges=[json.loads(line) for line in a.judges.read_text().splitlines() if line.strip()]
    if len({r['response_id'] for r in judges})!=len(judges):raise ValueError('Duplicate judge response ID')
    with a.predictions.open(encoding='utf-8-sig') as f:table=list(csv.DictReader(f))
    predictions={name:{r['response_id']:r for r in table if r['method']==name} for name in ('Fixed-Max','LoReD','Task-Conditioned LoReD')}
    yy=np.asarray([r['gold_hall'] for r in judges])
    preds={'DeepSeek Direct':np.asarray([r['direct_judge'] for r in judges]),'DeepSeek Sentence-Local':np.asarray([r['sentence_local'] for r in judges])}
    for name,mapping in predictions.items():
        for row in judges:
            match=mapping[row['response_id']]
            if match['source_id']!=row['source_id'] or int(match['gold_hall'])!=row['gold_hall']:
                raise ValueError('Source/label alignment mismatch')
        preds[name]=np.asarray([int(mapping[r['response_id']]['pred_hall']) for r in judges])
    if any(not set(pred).issubset({0,1}) for pred in preds.values()):
        raise ValueError('Invalid or failed API predictions; do not convert failures to supported labels')
    a.output.mkdir(parents=True,exist_ok=True)
    write_csv(a.output/'judge_results.csv',[{'method':name,'n':len(yy),**metrics_hall(yy,pred)} for name,pred in preds.items()])
    pairs=[('LoReD vs Direct','LoReD','DeepSeek Direct'),('Task extension vs Direct','Task-Conditioned LoReD','DeepSeek Direct'),('Task extension vs LoReD','Task-Conditioned LoReD','LoReD'),('Fixed-Max vs Direct','Fixed-Max','DeepSeek Direct'),('Direct vs Sentence-Local','DeepSeek Direct','DeepSeek Sentence-Local')]
    write_csv(a.output/'judge_bootstrap.csv',paired_bootstrap_many(yy,preds,np.asarray([r['source_id'] for r in judges]),pairs))
    print(f'Evaluated {len(yy)} matched responses; these are budget-limited judges, not an official G2LDetect reproduction.')


if __name__=='__main__':main()
