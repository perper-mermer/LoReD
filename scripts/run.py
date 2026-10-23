"""Train, predict, or run named CPU reproduction stages."""
from pathlib import Path
import argparse, csv, json, platform, sys, time
import numpy as np
import joblib
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from workflow import read_records, disjoint, train_suite, evaluate, predict, matrix, fit_stat, export_parameters
from lored import write_csv, paired_bootstrap_many, sha256, select_threshold_hall


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['train', 'evaluate', 'predict', 'main', 'seeds', 'ablation', 'timing'])
    p.add_argument('--development', type=Path)
    p.add_argument('--test', type=Path)
    p.add_argument('--model', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--bootstrap', type=int, default=10000)
    p.add_argument('--timing-repeats', type=int, default=10)
    p.add_argument('--check-reference', action='store_true', help='Only for the original RAGTruth evaluation')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    training = a.stage in ('train', 'main', 'seeds', 'ablation')
    if training and not a.development:
        p.error('--development is required for this stage')
    if a.stage != 'train' and not a.test:
        p.error('--test is required for this stage')
    if a.stage in ('evaluate', 'predict', 'timing') and not a.model:
        p.error('--model is required for this stage; load only a trusted local joblib file')
    dev = read_records(a.development) if training else None
    test = read_records(a.test, labeled=a.stage != 'predict') if a.test else None
    if dev is not None and test is not None:
        disjoint(dev, test)
    manifest = {'stage': a.stage, 'python': sys.version, 'platform': platform.platform(),
                'numpy': np.__version__, 'sklearn': __import__('sklearn').__version__,
                'inputs': {k: sha256(v) for k,v in [('development',a.development),('test',a.test),('model',a.model)] if v},
                'protocol': 'historical-canonical' if a.stage in ('main','train') else a.stage}
    if a.stage == 'seeds':
        reports = []
        for seed in range(20261020, 20261025):
            print(f'Seed {seed}', flush=True)
            suite = train_suite(dev, seed)
            rows, _ = evaluate(suite, test)
            reports.extend({'seed': seed, **r} for r in rows if r['method'] in ('Calibrated-Max','StatLR-4','LoReD','LoReD+Task','Task-Conditioned LoReD'))
        write_csv(a.output / 'five_seed_results.csv', reports)
        summary = []
        for method in sorted({r['method'] for r in reports}):
            for metric in ('macro_f1','bacc','hall_f1','auc'):
                values = np.asarray([r[metric] for r in reports if r['method']==method])
                summary.append({'method': method, 'metric': metric, 'mean': values.mean(), 'std_sample': values.std(ddof=1), 'n_seeds':len(values)})
        write_csv(a.output / 'five_seed_summary.csv', summary)
    elif a.stage == 'ablation':
        suite = {name: fit_stat(dev, name) for name in ('Peak-only','Peak-length','Peak-length-mean','Peak-length-mean-run','LoReD')}
        reports, preds = evaluate(suite, test)
        for row in reports:
            row['development_oof_macro_f1'] = suite[row['method']]['development_oof_macro_f1']
        write_csv(a.output / 'ablation.csv', reports)
        write_csv(a.output / 'predictions.csv', preds)
        manifest['protocol'] = 'matched GroupKFold liblinear ablations; distinct from historical canonical LoReD'
    else:
        suite = train_suite(dev) if training else joblib.load(a.model)
        if training:
            joblib.dump(suite, a.output / 'models.joblib')
            (a.output / 'parameters.json').write_text(json.dumps(export_parameters(suite), indent=2), encoding='utf-8')
            folds = {name: entry['folds'] for name,entry in suite.items() if 'folds' in entry}
            (a.output / 'folds.json').write_text(json.dumps(folds, indent=2), encoding='utf-8')
            manifest['thresholds'] = {name: entry['threshold'] for name,entry in suite.items()}
        if a.stage == 'timing':
            rows=[]
            for name in ('LoReD','Task-Conditioned LoReD'):
                for row in test[:20]:
                    predict(suite[name], [row])
                for row in test:
                    times=[]
                    for _ in range(a.timing_repeats):
                        start=time.perf_counter_ns()
                        predict(suite[name], [row])
                        times.append((time.perf_counter_ns()-start)/1000)
                    rows.append({'method':name,'response_id':row['response_id'],'n_sentences':len(row['risks']),'median_us':np.median(times)})
            write_csv(a.output / 'timing.csv', rows)
            manifest['timing_scope']='cached risks, feature construction, standardization, prediction; excludes verifier inference; general release interface adds feature-dispatch overhead'
        elif a.stage == 'predict':
            predictions=[]
            for name,entry in suite.items():
                risk, pred=predict(entry,test)
                predictions.extend({'response_id':row['response_id'],'method':name,'risk':float(risk[i]),'pred_hall':int(pred[i])} for i,row in enumerate(test))
            write_csv(a.output / 'predictions.csv', predictions)
        elif a.stage != 'train':
            reports, predictions = evaluate(suite, test)
            write_csv(a.output / 'main_results.csv', reports)
            write_csv(a.output / 'predictions.csv', predictions)
            strata=[]
            masks={f'task:{task}':[r for r in test if r['task']==task] for task in sorted({r['task'] for r in test})}
            for label, lo, hi in [('length:<=5',1,5),('length:6',6,6),('length:7-9',7,9),('length:>9',10,10**9)]:
                masks[label]=[r for r in test if lo<=len(r['risks'])<=hi]
            for label,subset in masks.items():
                if subset:
                    values,_=evaluate(suite,subset)
                    strata.extend({'stratum':label,**r} for r in values)
            write_csv(a.output / 'strata.csv',strata)
            preds={name:predict(entry,test)[1] for name,entry in suite.items()}
            pairs=[('LoReD vs '+name,'LoReD',name) for name in ('Fixed-Max','Calibrated-Max','StatLR-2','StatLR-4')]
            pairs += [('Task extension vs '+name,'Task-Conditioned LoReD',name) for name in ('StatLR-4','LoReD+Task')]
            boot=paired_bootstrap_many(np.asarray([r['gold_hall'] for r in test]),preds,np.asarray([r['source_id'] for r in test]),pairs,a.bootstrap)
            write_csv(a.output / 'pairwise_bootstrap.csv',boot)
            if a.check_reference:
                reference=Path(__file__).resolve().parents[1]/'results/canonical_matched_predictions.csv'
                with reference.open(encoding='utf-8-sig') as f:
                    frozen={r['response_id']:r for r in csv.DictReader(f)}
                columns={'Fixed-Max':'A','Calibrated-Max':'L0','StatLR-2':'L3','StatLR-4':'L4','LoReD':'AB','LoReD+Task':'T2','Task-Conditioned LoReD':'ABC'}
                assert set(frozen)=={r['response_id'] for r in test}, 'Reference ID mismatch'
                errors={name:sum(int(pred[i])!=int(frozen[row['response_id']][column+'_pred_hall']) for i,row in enumerate(test)) for name,column in columns.items() for pred in [preds[name]]}
                manifest['reference_prediction_mismatches']=errors
                (a.output/'reference_check.json').write_text(json.dumps(errors,indent=2),encoding='utf-8')
                if any(errors.values()):
                    raise RuntimeError(f'Canonical prediction mismatch: {errors}; do not tune on evaluation labels')
            print(json.dumps(reports,indent=2))
    (a.output/'run_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
