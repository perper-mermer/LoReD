"""One command for the released cached-score experiments; no GPU/API calls."""
import argparse,subprocess,sys
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('outputs/reproduction'))
    p.add_argument('--timing',action='store_true',help='Also benchmark this machine; latency will differ from reference')
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    bench=root/'benchmarks'
    def run(script,*args):
        subprocess.run([sys.executable,str(root/'scripts'/script),*map(str,args)],check=True)
    common=['--development',bench/'ragtruth_development.jsonl','--test',bench/'ragtruth_test.jsonl']
    run('verify_results.py')
    run('run.py','main',*common,'--output',a.output/'main','--check-reference')
    run('run.py','seeds',*common,'--output',a.output/'seeds')
    run('run.py','ablation',*common,'--output',a.output/'ablation')
    for verifier in ('minicheck','hhem'):
        run('cross_verifier.py','--development',bench/f'{verifier}_development.jsonl','--test',bench/f'{verifier}_test.jsonl','--verifier',verifier,'--output',a.output/verifier)
    for name in ('halubench_full','halubench_multi'):
        run('run.py','evaluate','--model',a.output/'main/models.joblib','--test',bench/f'{name}.jsonl','--output',a.output/name)
    run('evaluate_judges.py','--predictions',a.output/'main/predictions.csv','--output',a.output/'judges')
    if a.timing:
        run('run.py','timing','--model',a.output/'main/models.joblib','--test',bench/'ragtruth_test.jsonl','--output',a.output/'timing')
    print(f'Completed cached-score reproduction: {a.output.resolve()}')


if __name__=='__main__':main()
