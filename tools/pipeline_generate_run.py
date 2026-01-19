#!/usr/bin/env python3
"""Generate tests using the generator then run them and write a map CSV.

This pipeline composes the generator and the run-from-csv pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from minishell_tester import TEST_CSV
from minishell_tester.tools.test_generator import generate_csv
from minishell_tester.tools.pipeline_run_csv import run_tests


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--count', '-n', type=int, default=200)
    p.add_argument('--out', default=None, help='CSV output path (overrides package TEST_CSV)')
    p.add_argument('--map', default='minishell_tester/minishell_test_map.csv')
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--max', type=int, default=0)
    args = p.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    out_csv = Path(args.out) if args.out else Path(TEST_CSV)
    # ensure parent exists
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    # generate CSV
    generate_csv(out_csv, args.count, args.seed)

    # run tests and write map
    rc = run_tests(out_csv, None, Path(args.map), max_count=args.max)
    sys.exit(rc)


if __name__ == '__main__':
    main()
