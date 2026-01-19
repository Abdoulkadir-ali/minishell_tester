from pathlib import Path
import shutil
import pytest
import os

# from minishell_tester import MINISHELL, TEST_CSV, TEST_TIMEOUT, GENERATED_DIR
from .core import TestCaseLoader

# Resolve package and project locations robustly
def find_project_root():
    """Find the project root by searching upwards for the minishell binary."""
    current = Path(__file__).resolve().parent
    while current.parent != current:
        if os.path.exists(os.path.join(str(current), 'minishell')):
            return str(current)
        current = current.parent
    raise ValueError("Could not find project root with minishell binary")

PROJECT_ROOT = find_project_root()
PACKAGE_DIR = os.path.join(PROJECT_ROOT, 'minishell_tester')

# Paths are expressed as strings for simpler use from tests/scripts
MINISHELL = os.path.join(PROJECT_ROOT, 'minishell')
TEST_CSV = os.path.join(PACKAGE_DIR, 'cases', 'test_cases.csv')
TEST_LOG = os.path.join(PACKAGE_DIR, 'logs', 'test.log')
TEST_TIMEOUT = 5
GENERATED_DIR = os.path.join(PACKAGE_DIR, 'generated')


@pytest.fixture(scope='session')
def minishell_exec_path(tmp_path_factory):
    """Provide a temporary, executable copy of the minishell binary."""
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
    loader = TestCaseLoader(Path(TEST_CSV))
    tests = loader.load()
    if not tests:
        pytest.skip(f'CSV file not found or empty: {TEST_CSV}')
    return [t.text for t in tests]


@pytest.fixture
def timeout():
    return TEST_TIMEOUT


@pytest.fixture(scope='session')
def generated_dir_tmp():
    generated = GENERATED_DIR or os.environ.get('GENERATED_DIR')
    if not generated:
        pytest.skip('No GENERATED_DIR configured')
    generated = str(Path(generated).resolve())
    os.makedirs(generated, exist_ok=True)
    yield generated
    try:
        if os.path.isdir(generated):
            shutil.rmtree(generated)
    except Exception:
        pass
