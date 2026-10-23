"""Portable MiniCheck-Flan-T5 or HHEM inference using the recorded v5 scoring functions."""
import argparse,json,sys
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verifier',choices=['minicheck','hhem'],required=True)
    p.add_argument('--model',type=Path,required=True,help='Local model snapshot, pinned to the recorded revision')
    p.add_argument('--foundation',type=Path,help='Local flan-t5-base snapshot required by HHEM config')
    p.add_argument('--rows',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--batch-size',type=int,default=4)
    p.add_argument('--block-size',type=int,default=100)
    p.add_argument('--reference-cache',type=Path)
    p.add_argument('--tolerance',type=float,default=.005)
    a=p.parse_args()
    import torch
    from transformers import AutoTokenizer,AutoConfig,AutoModelForSeq2SeqLM,AutoModelForSequenceClassification
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from lored import read_jsonl,sha256
    import verifier_scoring as scoring
    if not torch.cuda.is_available():raise RuntimeError('Recorded fp16 scoring protocol requires CUDA')
    if a.verifier=='minicheck':
        tokenizer=AutoTokenizer.from_pretrained(a.model,use_fast=True,local_files_only=True)
        model=AutoModelForSeq2SeqLM.from_pretrained(a.model,torch_dtype=torch.float16,local_files_only=True).to('cuda').eval()
        score=lambda rows:scoring.minicheck_score_rows(rows,tokenizer,model,a.batch_size)
        field='joint_score'
    else:
        if not a.foundation:p.error('--foundation is required for HHEM')
        config=AutoConfig.from_pretrained(a.model,trust_remote_code=True,local_files_only=True)
        config.foundation=str(a.foundation)
        model=AutoModelForSequenceClassification.from_pretrained(a.model,config=config,trust_remote_code=True,local_files_only=True).half().to('cuda').eval()
        score=lambda rows:scoring.hhem_score_rows(rows,model,a.batch_size)
        field='support_score'
    rows=read_jsonl(a.rows)
    if len({str(row['id']) for row in rows})!=len(rows):raise ValueError('Duplicate sentence IDs')
    expected={str(row['id']):float(row[field]) for row in read_jsonl(a.reference_cache)} if a.reference_cache else None
    a.output.parent.mkdir(parents=True,exist_ok=True)
    partial=a.output.with_suffix('.partial.jsonl')
    maxdiff=0.
    with partial.open('w',encoding='utf-8') as handle:
        for start in range(0,len(rows),a.block_size):
            block=rows[start:start+a.block_size]
            scores=score(block)
            for row in block:
                value=float(max(scores[row['id']]))
                if expected is not None:
                    maxdiff=max(maxdiff,abs(value-expected[str(row['id'])]))
                    if maxdiff>a.tolerance:raise RuntimeError(f'Reference cache drift: {maxdiff}')
                handle.write(json.dumps({'id':row['id'],field:value})+'\n')
            print(f'{min(start+a.block_size,len(rows))}/{len(rows)}',flush=True)
    partial.replace(a.output)
    manifest={'verifier':a.verifier,'model_path':str(a.model),'model_config_sha256':sha256(a.model/'config.json'),
              'rows_sha256':sha256(a.rows),'output_sha256':sha256(a.output),'precision':'fp16',
              'torch':torch.__version__,'transformers':__import__('transformers').__version__,
              'gpu':torch.cuda.get_device_name(0),'batch_size':a.batch_size,
              'max_reference_difference':maxdiff if expected is not None else None}
    a.output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')


if __name__=='__main__':main()
