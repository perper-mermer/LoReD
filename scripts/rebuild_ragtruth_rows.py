"""Rebuild sentence/evidence serialization from official RAGTruth JSONL and frozen IDs."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ragtruth_serialization import sentence_spans,chunk_text,source_text


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--responses',type=Path,required=True)
    p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--split-manifest',type=Path,required=True,help='Frozen benchmark response IDs')
    p.add_argument('--partition',choices=['development','test'],required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    manifest=json.loads(a.split_manifest.read_text(encoding='utf-8'))[a.partition]
    selected={str(row['response_id']):row for row in manifest}
    sources={str(row['source_id']):row for row in read(a.sources)}
    responses={str(row['id']):row for row in read(a.responses)}
    rows=[]
    for rid,expected in selected.items():
        response=responses[rid]
        source=sources[str(response['source_id'])]
        evidence=[{'text':text,'question_index':i,'source_url':''} for i,text in enumerate(chunk_text(source_text(source)))]
        labels=response.get('labels',[])
        for index,(start,end,claim) in enumerate(sentence_spans(str(response['response']))):
            hall=any(int(label['start'])<end and int(label['end'])>start for label in labels)
            rows.append({'id':f'ragtruth-full-{rid}-s{index}','source_id':str(response['source_id']),
                         'response_id':rid,'sentence_index':index,'claim':claim,
                         'task_type':source.get('task_type','unknown'),'evidence':evidence,'gold_binary':int(not hall)})
        if int(bool(labels))!=expected['gold_hall']:
            raise RuntimeError(f'Gold mismatch for response {rid}')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    print(f'Wrote {len(rows)} sentence rows. Compare pair hashes to the benchmark manifests before claiming exact upstream reproduction.')


if __name__=='__main__':main()
