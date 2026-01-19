#!/usr/bin/env python3
"""
Simple CSV-driven test runner for minishell.

Reads commands from `tests/scripts/test_cases.csv` (second column), runs each command
under `/bin/bash` and under a temporary copy of `./minishell`, prints
per-test status `[OK/KO] -- <command>` and shows a simplified, colorized
ndiff when KO. Failed tests are also written to `tests/logs/test.log`.

Usage:
    python3 tests/scripts/run_tests.py --csv tests/scripts/test_cases.csv --minishell ./minishell --max 20
"""

import argparse
import csv
import difflib
import os
import shutil
import subprocess
import sys
import tempfile


GREEN = '\033[32m'
RED = '\033[31m'
RESET = '\033[0m'


def load_global_module():
    # load tests/scripts/global.py as a module without relying on package import
    import importlib.util
    gpath = os.path.join(os.path.dirname(__file__), 'global.py')
    if not os.path.isfile(gpath):
        return None
    spec = importlib.util.spec_from_file_location('test_global', gpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_commands(csv_path, col=1):
    cmds = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if not row:
                continue
            if idx == 0 and len(row) > col and row[col].lower().startswith('test'):
                continue
            if len(row) <= col:
                continue
            cell = row[col]
            if cell is None:
                continue
            cmd = str(cell).replace('\r', '').strip()
            if cmd == '':
                continue
            cmds.append(cmd)
    return cmds


def run_with_timeout(cmd_args, input_text=None, timeout=5, cwd=None):
    try:
        proc = subprocess.run(cmd_args, input=input_text, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=timeout, cwd=cwd)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ''
        err = (e.stderr or '') + f"\n[timeout after {timeout}s]"
        return 124, out, err


def ensure_text(s):
    if isinstance(s, bytes):
        try:
            return s.decode('utf-8', errors='replace')
        except Exception:
            return str(s)
    return s


def run_bash(cmd, timeout=5, cwd=None):
    return run_with_timeout(['/bin/bash', '--noprofile', '--norc', '-c', cmd], None, timeout, cwd=cwd)


def run_minishell(mini_path, cmd, timeout=5, cwd=None):
    return run_with_timeout([mini_path], input_text=cmd + '\n', timeout=timeout, cwd=cwd)


def format_simple_diff(b_lines, m_lines, color=True):
    out = []
    for line in difflib.ndiff(b_lines, m_lines):
        if line.startswith('?'):
            continue
        if color:
            if line.startswith('- '):
                out.append(RED + line.rstrip('\n') + RESET + '\n')
            elif line.startswith('+ '):
                out.append(GREEN + line.rstrip('\n') + RESET + '\n')
            else:
                out.append('  ' + line[2:].rstrip('\n') + '\n')
        else:
            out.append(line)
    return ''.join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default=None, help='Path to CSV with test commands')
    parser.add_argument('--minishell', default=None, help='Path to minishell binary')
    parser.add_argument('--log', default=None, help='Path to failure log file')
    parser.add_argument('--timeout', type=int, default=None, help='Per-test timeout (s)')
    parser.add_argument('--max', type=int, default=0)
    args = parser.parse_args()

    # load defaults from tests/scripts/global.py (if present)
    g = load_global_module()
    csv_path = args.csv or (getattr(g, 'TEST_CSV', None) if g else None) or os.environ.get('TEST_CSV')
    minishell_src = args.minishell or (getattr(g, 'MINISHELL', None) if g else None) or os.environ.get('MINISHELL')
    log_path = args.log or (getattr(g, 'TEST_LOG', None) if g else None) or os.environ.get('TEST_LOG')
    timeout = args.timeout if args.timeout is not None else int((getattr(g, 'TEST_TIMEOUT', None) if g else None) or os.environ.get('TEST_TIMEOUT', '5'))

    if not csv_path or not os.path.isfile(csv_path):
        print(f'CSV file not found: {csv_path}', file=sys.stderr)
        sys.exit(2)
    if not minishell_src or not os.path.exists(minishell_src):
        print(f'minishell binary not found: {minishell_src}', file=sys.stderr)
        sys.exit(2)
    if os.path.isdir(minishell_src):
        print(f'Error: {minishell_src} is a directory', file=sys.stderr)
        sys.exit(2)

    cmds = load_commands(csv_path)
    if not cmds:
        print('No commands found in CSV.', file=sys.stderr)
        sys.exit(2)

    if not log_path:
        print('No log path specified (use --log or set TEST_LOG in tests/scripts/global.py)', file=sys.stderr)
        sys.exit(2)
    log_dir = os.path.dirname(log_path) or '.'
    os.makedirs(log_dir, exist_ok=True)

    # optional generated files directory (for easier cleanup)
    generated_dir = (getattr(g, 'GENERATED_DIR', None) if g else None) or os.environ.get('GENERATED_DIR')
    if generated_dir:
        os.makedirs(generated_dir, exist_ok=True)

    total = 0
    failures = 0

    with tempfile.TemporaryDirectory() as run_tmp:
        mini_copy = os.path.join(run_tmp, 'minishell_exec')
        try:
            shutil.copy2(minishell_src, mini_copy)
            os.chmod(mini_copy, 0o755)
        except PermissionError:
            try:
                st = os.stat(minishell_src)
                orig_mode = st.st_mode & 0o777
            except Exception:
                orig_mode = None
            try:
                if orig_mode is not None:
                    os.chmod(minishell_src, orig_mode | 0o644)
                shutil.copy2(minishell_src, mini_copy)
                os.chmod(mini_copy, 0o755)
            except Exception as e:
                print(f'Error preparing temp copy: {e}', file=sys.stderr)
                try:
                    if orig_mode is not None:
                        os.chmod(minishell_src, orig_mode)
                except Exception:
                    pass
                sys.exit(2)
            else:
                try:
                    if orig_mode is not None:
                        os.chmod(minishell_src, orig_mode)
                except Exception:
                    pass
        except Exception as e:
            print(f'Error preparing temp copy: {e}', file=sys.stderr)
            sys.exit(2)

        with open(log_path, 'w', encoding='utf-8') as log:
            try:
                for i, cmd in enumerate(cmds, start=1):
                    if args.max and i > args.max:
                        break
                    total += 1

                    # run both bash and minishell in the generated directory (isolated)
                    cwd = generated_dir or None
                    bash_ec, bash_out, bash_err = run_bash(cmd, timeout=timeout, cwd=cwd)
                    bash_out = ensure_text(bash_out)
                    bash_err = ensure_text(bash_err)
                    try:
                        mini_ec, mini_out, mini_err = run_minishell(mini_copy, cmd, timeout=timeout, cwd=cwd)
                        mini_out = ensure_text(mini_out)
                        mini_err = ensure_text(mini_err)
                    except PermissionError as pe:
                        st = None
                        try:
                            st = os.stat(minishell_src)
                        except Exception:
                            pass
                        print(f'PermissionError running minishell: {pe}', file=sys.stderr)
                        if st is not None:
                            print(f'minishell mode: {oct(st.st_mode & 0o777)}', file=sys.stderr)
                        raise

                    ok = True
                    unified_diff = ''
                    simple_diff = ''
                    if bash_out != mini_out:
                        ok = False
                        b_lines = bash_out.splitlines()
                        m_lines = mini_out.splitlines()
                        unified_diff = ''.join(difflib.unified_diff([l + '\n' for l in b_lines],
                                                                    [l + '\n' for l in m_lines],
                                                                    fromfile='bash stdout',
                                                                    tofile='minishell stdout'))
                        simple_diff = format_simple_diff(b_lines, m_lines, color=True)
                    if bash_ec != mini_ec:
                        ok = False

                    if not ok:
                        failures += 1
                        log.write('\n' + '=' * 80 + '\n')
                        log.write(f'Test #{i}\n')
                        log.write('COMMAND:\n')
                        log.write(cmd + '\n')
                        log.write('\n--- bash ---\n')
                        log.write(f'EXIT CODE: {bash_ec}\n')
                        log.write('STDOUT:\n')
                        log.write(bash_out if bash_out is not None else '')
                        log.write('\nSTDERR:\n')
                        log.write(bash_err if bash_err is not None else '')
                        log.write('\n--- minishell ---\n')
                        log.write(f'EXIT CODE: {mini_ec}\n')
                        log.write('STDOUT:\n')
                        log.write(mini_out if mini_out is not None else '')
                        log.write('\nSTDERR:\n')
                        log.write(mini_err if mini_err is not None else '')
                        log.write('\n--- DIFF (stdout) ---\n')
                        if unified_diff:
                            log.write(unified_diff)
                        else:
                            log.write('(no stdout diff)\n')
                        log.write('\n' + '=' * 80 + '\n')

                    # print status and optional diff
                    cmd_display = cmd.replace('\n', ' ').strip()
                    if len(cmd_display) > 120:
                        cmd_display = cmd_display[:117] + '...'
                    status_plain = 'OK' if ok else 'KO'
                    status_colored = f"{GREEN}{status_plain}{RESET}" if ok else f"{RED}{status_plain}{RESET}"
                    print(f"[{status_colored}] -- {cmd_display}", flush=True)
                    if not ok:
                        if simple_diff:
                            print('\n--- DIFF (bash -> minishell) ---')
                            print(simple_diff)
                        else:
                            print('\n(no stdout diff)')

            except KeyboardInterrupt:
                print('\nInterrupted by user; exiting early')
            print(f'Ran {total} tests, {failures} failures (partial)')
            print(f'See {log_path} for details on failures so far')

            # copy log into generated dir for easier cleanup if requested
            try:
                if generated_dir:
                    dst = os.path.join(generated_dir, os.path.basename(log_path))
                    shutil.copy2(log_path, dst)
            except Exception:
                pass

            # cleanup generated files after run for a clean workspace
            try:
                if generated_dir and os.path.isdir(generated_dir):
                    # remove and recreate to ensure cleanup
                    shutil.rmtree(generated_dir)
                    os.makedirs(generated_dir, exist_ok=True)
            except Exception:
                pass

    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()
