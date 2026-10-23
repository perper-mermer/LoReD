"""Optional paid API rerun of the archived truncated-context judge protocol."""
import argparse,json,os,sys
from pathlib import Path

DIRECT='''You are a fact-checker. Given the source evidence and a generated response, determine if the response contains any hallucinated claims (information not supported by or contradicted by the evidence).

Source Evidence:
{evidence}

Generated Response:
{response}

Question: Is the generated response fully supported by the source evidence?
Answer with only "yes" (fully supported) or "no" (contains hallucination). Then briefly explain why.'''
LOCAL='''You are a fact-checker. Given a source evidence and one sentence from a response, determine if that sentence is supported by the evidence.

Source Evidence:
{evidence}

Sentence:
{sentence}

Question: Is this sentence supported by the evidence?
Answer with only "yes" or "no".'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rows',type=Path,required=True)
    p.add_argument('--selected',type=Path,default=Path(__file__).resolve().parents[1]/'benchmarks/llm_judge_predictions.jsonl')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model',default='deepseek-chat')
    p.add_argument('--base-url',default='https://api.deepseek.com')
    p.add_argument('--max-responses',type=int,required=True,help='Explicit spending limit; at most six calls per response')
    a=p.parse_args()
    if a.max_responses <= 0:p.error('--max-responses must be positive')
    from openai import OpenAI
    key=os.environ.get('DEEPSEEK_API_KEY')
    if not key:raise RuntimeError('Set DEEPSEEK_API_KEY in the environment')
    client=OpenAI(api_key=key,base_url=a.base_url)
    selected=[json.loads(line) for line in a.selected.read_text().splitlines() if line.strip()][:a.max_responses]
    grouped={}
    for line in a.rows.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():
            row=json.loads(line)
            grouped.setdefault(str(row['response_id']),[]).append(row)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8') as f:
        for meta in selected:
            rows=sorted(grouped[meta['response_id']],key=lambda r:int(r['sentence_index']))
            evidence=' '.join(str(e['text']) for e in rows[0]['evidence'])
            def ask(prompt,tokens):
                response=client.chat.completions.create(model=a.model,messages=[{'role':'user','content':prompt}],temperature=0,max_tokens=tokens)
                return response.choices[0].message.content.strip()
            # Deliberately preserve the recorded string parsing and truncation limits.
            direct=ask(DIRECT.format(evidence=evidence[:2000],response=' '.join(r['claim'] for r in rows)[:1000]),100)
            local=[ask(LOCAL.format(evidence=evidence[:1500],sentence=r['claim'][:300]),10) for r in rows[:5]]
            result={k:meta[k] for k in ('response_id','source_id','gold_hall')}
            result.update(direct_judge=int('no' in direct.lower()[:10]),sentence_local=int(any('no' in answer.lower()[:5] for answer in local)),model=a.model)
            f.write(json.dumps(result)+'\n');f.flush()
    # Exceptions stop the run; API failures are never silently coded as supported.
    a.output.with_suffix('.manifest.json').write_text(json.dumps({'model':a.model,'base_url':a.base_url,'responses':len(selected),'evidence_chars_direct':2000,'response_chars_direct':1000,'evidence_chars_local':1500,'sentence_chars_local':300,'local_sentence_limit':5,'temperature':0,'failure_policy':'stop; differs from legacy silent sentence-failure handling','scope':'API aliases may drift; archived outputs remain the exact historical reference'},indent=2),encoding='utf-8')


if __name__=='__main__':main()
