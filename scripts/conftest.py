import os
import shutil
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


# Load defaults from tests/scripts/global.py if available
g = load_global_module()
MINISHELL = getattr(g, 'MINISHELL', None) if g else os.environ.get('MINISHELL')
TEST_CSV = getattr(g, 'TEST_CSV', None) if g else os.environ.get('TEST_CSV')
TEST_TIMEOUT = int((getattr(g, 'TEST_TIMEOUT', None) if g else None) or os.environ.get('TEST_TIMEOUT', '5'))


@pytest.fixture(scope='session')
def minishell_exec_path(tmp_path_factory):
    """Provide a temporary, executable copy of the minishell binary.

    This avoids modifying the repository file permissions and handles cases
    where the source binary is not executable.
    """
    src = MINISHELL
    if not os.path.exists(src):
        pytest.skip(f'minishell binary not found: {src}')
    tmpdir = tmp_path_factory.mktemp("minishell_run")
    dst = os.path.join(tmpdir, 'minishell_exec')
    try:
        shutil.copy2(src, dst)
        os.chmod(dst, 0o755)
    except PermissionError:
        try:
            st = os.stat(src)
            orig_mode = st.st_mode & 0o777
        except Exception:
            orig_mode = None
        if orig_mode is not None:
            os.chmod(src, orig_mode | 0o644)
        shutil.copy2(src, dst)
        os.chmod(dst, 0o755)
        if orig_mode is not None:
            try:
                os.chmod(src, orig_mode)
            except Exception:
                pass
    return dst


@pytest.fixture(scope='session')
def csv_commands():
    path = TEST_CSV
    if not os.path.isfile(path):
        pytest.skip(f'CSV file not found: {path}')
    cmds = []
    import csv
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
            cmds.append(cmd)
    return cmds


@pytest.fixture
def timeout():
    return TEST_TIMEOUT


@pytest.fixture(scope='session')
def generated_dir_tmp():
    # provide a dedicated directory for tests to create files, then clean it up after session
    g = load_global_module()
    generated = (getattr(g, 'GENERATED_DIR', None) if g else None) or os.environ.get('GENERATED_DIR')
    if not generated:
        pytest.skip('No GENERATED_DIR configured')
    # ensure directory exists and is inside project
    os.makedirs(generated, exist_ok=True)
    yield generated
    # cleanup after session
    try:
        if os.path.isdir(generated):
            shutil.rmtree(generated)
    except Exception:
        pass
