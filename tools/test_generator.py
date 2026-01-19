#!/usr/bin/env python3
"""Grammar-based test generator (moved under tools).

This is the same generator as before, now placed in `tools` to separate
test-generation helpers from test execution code.
"""

from __future__ import annotations

import argparse
import csv
import random
import string
from pathlib import Path
from typing import List


SIMPLE_COMMANDS = [
    'echo', 'printf', 'cat', 'grep', 'wc', 'ls', 'true', 'false', 'sed', 'head', 'tail'
]


def rand_word(max_len=12):
    l = random.randint(1, max_len)
    return ''.join(random.choices(string.ascii_letters + string.digits + " _-", k=l)).strip()


def quote(s: str) -> str:
    if '"' in s and "'" not in s:
        return f"'{s}'"
    return '"' + s.replace('"', '\\"') + '"'


def make_sample_files(generated_dir: Path):
    generated_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(3):
        p = generated_dir / f'sample_{i}.txt'
        content = '\n'.join([f'line {j} {rand_word(6)}' for j in range(1, random.randint(3, 8))]) + '\n'
        p.write_text(content, encoding='utf-8')
        files.append(p)
    return files


def gen_simple_command(sample_files):
    cmd = random.choice(SIMPLE_COMMANDS)
    if cmd == 'echo':
        return f'echo {quote(rand_word(20))}'
    if cmd == 'printf':
        return f'printf {quote(rand_word(10))}\\n'
    if cmd == 'cat':
        f = random.choice(sample_files)
        return f'cat {f}'
    if cmd == 'grep':
        pat = rand_word(4)
        f = random.choice(sample_files)
        return f'grep -n {quote(pat)} {f} || true'
    if cmd == 'wc':
        f = random.choice(sample_files)
        return f'wc -l {f}'
    if cmd == 'ls':
        if random.random() < 0.8:
            return f'ls {sample_files[0].parent}'
        else:
            return 'ls /nonexistent_path'
    if cmd == 'true':
        return 'true'
    if cmd == 'false':
        return 'false'
    if cmd == 'sed':
        f = random.choice(sample_files)
        return f'sed -n 1,2p {f}'
    return 'echo ok'


def attach_redirection(cmd: str, sample_files, generated_dir: Path):
    REDIRS = ['>', '>>', '2>', '2>>']
    if random.random() < 0.25:
        r = random.choice(REDIRS)
        # use relative paths for redirection targets so generated commands are portable
        if r.startswith('2'):
            target = Path('generated') / f'err_{random.randint(0,99)}.log'
        else:
            target = Path('generated') / f'out_{random.randint(0,99)}.txt'
        return f"{cmd} {r} {target}"
    return cmd


def gen_command(sample_files, generated_dir: Path, max_parts=4):
    parts = []
    n = random.randint(1, max_parts)
    for i in range(n):
        p = gen_simple_command(sample_files)
        p = attach_redirection(p, sample_files, generated_dir)
        parts.append(p)
        if i < n - 1:
            op = random.choices(['|', '&&', '||', ';'], weights=[0.35, 0.25, 0.2, 0.2])[0]
            parts.append(op)
    cmd = ' '.join(parts)
    if random.random() < 0.05:
        cmd = f'({cmd})'
    return cmd


def generate_csv(out_path: Path, count: int, seed: int = None):
    if seed is not None:
        random.seed(seed)
    # Keep generated files next to the output CSV for portability
    generated_dir = out_path.parent / 'generated'
    sample_files = make_sample_files(generated_dir)
    # store sample file paths relative to the CSV parent so commands are portable
    sample_files = [p.relative_to(out_path.parent) for p in sample_files]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['id', 'kind', 'test'])
        for i in range(count):
            cmd = gen_command(sample_files, generated_dir)
            writer.writerow([i + 1, 'generated', cmd])
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--count', '-n', type=int, default=10)
    p.add_argument('--out', '-o', default=None, help='Write CSV to this path (relative to scripts dir)')
    p.add_argument('--seed', type=int, default=None)
    args = p.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    if args.out:
        out = (scripts_dir / args.out).resolve()
        path = generate_csv(out, args.count, args.seed)
        print(f'Wrote {args.count} cases to {path}')
    else:
        generated_dir = scripts_dir.joinpath('..', 'generated').resolve()
        sample_files = make_sample_files(generated_dir)
        for i in range(args.count):
            print(gen_command(sample_files, generated_dir))


if __name__ == '__main__':
    main()
