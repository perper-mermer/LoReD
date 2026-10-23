"""Strict Lightning-checkpoint FactCG scoring, matching validated pair serialization."""
from pathlib import Path
import argparse, hashlib, json, sys


PROMPT = '{text_a}\n\nChoose your answer: based on the paragraph above can we conclude that "{text_b}"?\n\nOPTIONS:\n- Yes\n- No\nI think the answer is '


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rows',type=Path,required=True)
    p.add_argument('--config',required=True,help='Local tokenizer/config snapshot')
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--batch-size',type=int,default=4)
    p.add_argument('--device',default='cuda')
    p.add_argument('--precision',choices=['fp16','fp32'],default='fp16')
    p.add_argument('--reference-cache',type=Path,help='Check recomputed scores against known pair scores')
    p.add_argument('--tolerance',type=float,default=.005)
    a=p.parse_args()
    import torch
    from torch import nn
    from transformers import AutoModel,AutoConfig,AutoTokenizer,DebertaV2ForSequenceClassification
    class FactCG(nn.Module):
        def __init__(self,config):
            super().__init__()
            self.base_model=AutoModel.from_config(config)
            self.pooler=DebertaV2ForSequenceClassification(config).pooler
            self.bin_layer=nn.Linear(config.hidden_size,2)
            self.dropout=nn.Dropout(.1)
        def forward(self,**batch):
            hidden=self.base_model(input_ids=batch['input_ids'],attention_mask=batch['attention_mask'],token_type_ids=batch.get('token_type_ids')).last_hidden_state
            return self.bin_layer(self.dropout(self.pooler(hidden)))
    if a.precision=='fp16' and not a.device.startswith('cuda'):
        p.error('fp16 protocol requires CUDA; CPU inference requires --precision fp32')
    config=AutoConfig.from_pretrained(a.config,local_files_only=True)
    tokenizer=AutoTokenizer.from_pretrained(a.config,use_fast=True,local_files_only=True)
    model=FactCG(config)
    state=torch.load(a.checkpoint,map_location='cpu',mmap=True,weights_only=True)
    incompatible=model.load_state_dict(state['state_dict'],strict=True)
    del state
    model=model.to(device=a.device,dtype=torch.float16 if a.precision=='fp16' else torch.float32).eval()
    pairs={}
    for line in a.rows.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():continue
        row=json.loads(line)
        for evidence in row['evidence']:
            claim,text=str(row['claim']),str(evidence['text']).strip()
            key=hashlib.sha256((claim+'\0'+text).encode()).hexdigest()
            pairs[key]=(claim,text)
    if not pairs:raise ValueError('No evidence pairs')
    reference={}
    if a.reference_cache:
        reference={r['id']:float(r['score']) for r in map(json.loads,filter(str.strip,a.reference_cache.read_text(encoding='utf-8-sig').splitlines()))}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    temporary=a.output.with_suffix('.partial.jsonl')
    keys=list(pairs)
    max_diff=0.
    with temporary.open('w',encoding='utf-8') as handle:
        for start in range(0,len(keys),a.batch_size):
            selected=keys[start:start+a.batch_size]
            texts=[PROMPT.format(text_a=pairs[k][1],text_b=pairs[k][0]) for k in selected]
            batch=tokenizer(texts,max_length=1024,truncation=True,padding=True,return_tensors='pt')
            batch={k:v.to(a.device) for k,v in batch.items()}
            with torch.inference_mode():
                scores=torch.softmax(model(**batch).float(),dim=-1)[:,1].cpu().tolist()
            for key,score in zip(selected,scores):
                if a.reference_cache:
                    if key not in reference:raise KeyError(f'Pair absent from reference: {key}')
                    max_diff=max(max_diff,abs(score-reference[key]))
                    if max_diff>a.tolerance:raise RuntimeError(f'Cache drift exceeds tolerance: {max_diff}; partial output retained')
                handle.write(json.dumps({'id':key,'score':score})+'\n')
            print(f'{min(start+a.batch_size,len(keys))}/{len(keys)}',flush=True)
    temporary.replace(a.output)
    def digest(path):
        h=hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda:f.read(1<<20),b''):h.update(block)
        return h.hexdigest()
    report={'checkpoint_sha256':digest(a.checkpoint),'rows_sha256':digest(a.rows),'output_sha256':digest(a.output),'pairs':len(keys),'max_length':1024,'precision':a.precision,'batch_size':a.batch_size,'torch':torch.__version__,'transformers':__import__('transformers').__version__,'missing_keys':list(incompatible.missing_keys),'unexpected_keys':list(incompatible.unexpected_keys),'max_reference_difference':max_diff if a.reference_cache else None,'scope':'upstream inference only; no model training'}
    a.output.with_suffix('.manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
