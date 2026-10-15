"""Read-only, matched-budget calibration on original cases, never training export."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from pathlib import Path
import statistics

from .calibrate import write_json
from .contract import official_score, read_instance
from .generator import family_of, features
from .reference import solve_reference


def calibrate_original(source, output, iterations=1000, long_iterations=6000):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    with ProcessPoolExecutor(max_workers=3) as pool:
        for path in sorted(Path(source).glob('*.txt')):
            case = read_instance(path)
            jobs = [pool.submit(solve_reference, case, iterations=budget, seed=seed)
                    for budget, seed in [(iterations, 0), (long_iterations, 0), (long_iterations, 1)]]
            short, long, repeat = [f.result() for f in jobs]
            feasible = [r for r in [short, long, repeat] if r['valid']]
            best = min(feasible, key=lambda r: (r['nv'], r['td'])) if feasible else None
            record = {'name': case['name'], 'family': family_of(case['name']),
                      'features': features(case), 'reference': best,
                      'short_score': official_score(short, best) if best else 0,
                      'short_nv_gap': short['nv'] - best['nv'] if best and short['valid'] else None,
                      'runs': [short, long, repeat]}
            records.append(record)
            write_json(output / 'results.json', {'complete': False, 'records': records})
            print(case['name'], round(record['short_score'], 2), flush=True)
    write_json(output / 'results.json', {'complete': True, 'training_export': False,
        'iterations': iterations, 'long_iterations': long_iterations,
        'metric': 'original rounded Euclidean; both pools anchored to best of same three solver runs',
        'records': records})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='data/routing_alignment/original_judge/internal/cases/raw')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    calibrate_original(args.source, args.output)
