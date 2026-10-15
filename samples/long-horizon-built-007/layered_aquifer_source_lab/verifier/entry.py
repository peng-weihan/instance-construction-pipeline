#!/usr/bin/env python3
import argparse,json,sys,traceback
from pathlib import Path
from runtime import SubmissionError,InfrastructureError,invalid,workdir,snapshot
from grader import grade

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--submission',required=True)
    ap.add_argument('--suite',choices=['feedback','audit','public'],default='feedback');a=ap.parse_args()
    try:
        with workdir() as temp:
            clean=Path(temp)/'submission'
            snapshot(Path(a.submission).resolve(),clean)
            report=grade(clean,a.suite)
        print(json.dumps(report,allow_nan=False));return 0
    except SubmissionError as e:
        print(json.dumps(invalid(str(e)),allow_nan=False));return 0
    except Exception as e:
        # Infrastructure failure is deliberately not a numeric reward.
        print(json.dumps({'status':'verifier_error','error':type(e).__name__,
                          'summary':str(e)[:500]}));traceback.print_exc(file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
