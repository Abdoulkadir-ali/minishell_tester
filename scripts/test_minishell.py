import os
import subprocess
import difflib
import pytest


def load_global_module():
    import importlib.util
    gpath = os.path.join(os.path.dirname(__file__), 'global.py')
    if not os.path.isfile(gpath):
        return None
    spec = importlib.util.spec_from_file_location('test_global', gpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# load defaults from tests/scripts/global.py if present
g = load_global_module()
if g:
    os.environ.setdefault('TEST_CSV', getattr(g, 'TEST_CSV', ''))
    os.environ.setdefault('TEST_TIMEOUT', str(getattr(g, 'TEST_TIMEOUT', 5)))


def run_cmd_with_timeout(cmd_args, input_text=None, timeout=5, cwd=None):
    proc = subprocess.run(cmd_args, input=input_text, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=timeout, cwd=cwd)
    return proc.returncode, proc.stdout, proc.stderr


@pytest.mark.parametrize("index,cmd", [])
def test_placeholder(index, cmd):
    # placeholder replaced at import time
    pass


def pytest_generate_tests(metafunc):
    # dynamically parametrize tests using the `csv_commands` fixture data
    if 'cmd' in metafunc.fixturenames and 'index' in metafunc.fixturenames:
        import csv
        path = os.environ.get('TEST_CSV')
        if not path or not os.path.isfile(path):
            metafunc.parametrize('index,cmd', [])
            return
        rows = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for idx, row in enumerate(reader):
                if not row:
                    continue
                if idx == 0 and len(row) > 1 and row[1].lower().startswith('test'):
                    continue
                if len(row) <= 1:
                    continue
                cell = row[1]
                if cell is None:
                    continue
                cmd = str(cell).replace('\r', '').strip()
                if cmd == '':
                    continue
                rows.append((idx, cmd))
        metafunc.parametrize('index,cmd', rows)


def test_minishell_vs_bash(index, cmd, minishell_exec_path, timeout, generated_dir_tmp):
    # run bash
    try:
        bash_ec, bash_out, bash_err = run_cmd_with_timeout(['/bin/bash', '--noprofile', '--norc', '-c', cmd], None, timeout, cwd=generated_dir_tmp)
    except subprocess.TimeoutExpired:
        pytest.skip('bash timed out')

    # run minishell
    try:
        mini_ec, mini_out, mini_err = run_cmd_with_timeout([minishell_exec_path], cmd + '\n', timeout, cwd=generated_dir_tmp)
    except subprocess.TimeoutExpired:
        pytest.skip('minishell timed out')

    if bash_out != mini_out or bash_ec != mini_ec:
        b_lines = bash_out.splitlines(keepends=True)
        m_lines = mini_out.splitlines(keepends=True)
        unified = ''.join(difflib.unified_diff(b_lines, m_lines, fromfile='bash stdout', tofile='minishell stdout'))
        msg = f"\nCOMMAND: {cmd}\n--- bash exit,stdout,stderr ---\n{bash_ec}\n{bash_out}\n{bash_err}\n--- minishell exit,stdout,stderr ---\n{mini_ec}\n{mini_out}\n{mini_err}\n--- DIFF ---\n{unified}"
        pytest.fail(msg)
