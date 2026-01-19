#!/usr/bin/env python3
"""Read a CSV of tests and run them under Bash and Minishell, writing a map CSV.

Output CSV columns: id,command,bash_exit,minishell_exit,match
"""

from __future__ import annotations

import argparse
import csv
import tempfile
from pathlib import Path
import sys

from minishell_tester import TEST_CSV, GENERATED_DIR, TEST_TIMEOUT, MINISHELL
from minishell_tester.core import TestCaseLoader, Bash, Minishell


def run_tests(csv_path: Path, minishell_path: Path, out_map: Path, timeout: int = 5, max_count: int = 0):
    tests = TestCaseLoader(csv_path).load()
    if not tests:
        print('No tests found in', csv_path)
        return 2

    # prepare shells
    bash = Bash(timeout=timeout)
    mini = Minishell(minishell_path, timeout=timeout)

    with tempfile.TemporaryDirectory() as td:
        mini.prepare_binary(Path(td))

        out_map.parent.mkdir(parents=True, exist_ok=True)
        with out_map.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'command', 'bash_exit', 'minishell_exit', 'match'])
            for i, tc in enumerate(tests, start=1):
                if max_count and i > max_count:
                    break
                work_dir = Path(GENERATED_DIR) if GENERATED_DIR else None
                bash_res = bash.execute(tc, work_dir)
                mini_res = mini.execute(tc, work_dir)
                match = int(bash_res.exit_code == mini_res.exit_code and bash_res.stdout == mini_res.stdout)
                writer.writerow([tc.id, tc.text, bash_res.exit_code, mini_res.exit_code, match])

    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--csv', default=None)
    p.add_argument('--minishell', default=None)
    p.add_argument('--out', default='minishell_tester/minishell_test_map.csv')
    p.add_argument('--timeout', type=int, default=None)
    p.add_argument('--max', type=int, default=0)
    args = p.parse_args()

    csv_path = Path(args.csv) if args.csv else Path(TEST_CSV)
    minishell_path = Path(args.minishell) if args.minishell else Path(MINISHELL)
    out_map = Path(args.out)
    timeout = args.timeout if args.timeout is not None else int(TEST_TIMEOUT)

    code = run_tests(csv_path, minishell_path, out_map, timeout=timeout, max_count=args.max)
    sys.exit(code)


if __name__ == '__main__':
    main()
