"""Reproduce v5 verifier-specific grouped-OOF adaptation from numeric risks."""
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from workflow import read_records, disjoint, matrix
from lored import generic_oof_support, make_model, risk_probability, metrics_hall, paired_bootstrap_many, write_csv, sha256
from sklearn.metrics import f1_score


def choose(y, risk):
    return max((float(f1_score(y,(risk<t).astype(int),average='macro',zero_division=0)),-abs(float(t)-.5),float(t)) for t in np.linspace(.1,.9,81))[2]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--development',type=Path,required=True)
    p.add_argument('--test',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verifier',required=True)
    a=p.parse_args()
    dev=sorted(read_records(a.development),key=lambda r:int(r['response_id']))
    test=sorted(read_records(a.test),key=lambda r:int(r['response_id']))
    disjoint(dev,test)
    x,xx=matrix(dev,'LoReD'),matrix(test,'LoReD')
    y=1-np.asarray([r['gold_hall'] for r in dev])
    yy=np.asarray([r['gold_hall'] for r in test])
    groups=np.asarray([r['source_id'] for r in dev])
    seed=20261022
    oof=generic_oof_support(x,y,groups,seed)
    threshold=choose(y,oof)
    fitted=make_model(seed).fit(x,y)
    score=risk_probability(fitted,xx)
    maxtr=np.asarray([max(r['risks']) for r in dev])
    maxtest=np.asarray([max(r['risks']) for r in test])
    maxth=choose(y,maxtr)
    risks={'LoReD':score,'Calibrated-Max':maxtest,'Fixed-Max':maxtest}
    thresholds={'LoReD':threshold,'Calibrated-Max':maxth,'Fixed-Max':.5}
    preds={name:(value>=thresholds[name]).astype(int) for name,value in risks.items()}
    a.output.mkdir(parents=True,exist_ok=True)
    reports=[{'verifier':a.verifier,'method':name,'threshold':thresholds[name],**metrics_hall(yy,preds[name],value)} for name,value in risks.items()]
    write_csv(a.output/'results.csv',reports)
    pairs=[('LoReD vs '+name,'LoReD',name) for name in ('Calibrated-Max','Fixed-Max')]
    write_csv(a.output/'bootstrap.csv',paired_bootstrap_many(yy,preds,np.asarray([r['source_id'] for r in test]),pairs,seed=20261022))
    (a.output/'manifest.json').write_text(json.dumps({'seed':seed,'development_sha256':sha256(a.development),'test_sha256':sha256(a.test),'threshold_ties':'nearest .5, then larger threshold','scope':'v5 verifier-specific protocol; distinct from canonical FactCG'},indent=2),encoding='utf-8')
    print(json.dumps(reports,indent=2))


if __name__=='__main__':
    main()
