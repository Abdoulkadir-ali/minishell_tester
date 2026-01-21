import pytest
from pathlib import Path
import os
from .core import Bash, Minishell, CaseLoader, Command, DiffGenerator, ShellResult


# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MINISHELL_PATH = PROJECT_ROOT / "minishell"


@pytest.fixture(scope="session")
def bash_shell():
    return Bash()


@pytest.fixture(scope="session")
def minishell_binary(tmp_path_factory):
    bin_dir = tmp_path_factory.mktemp("bin")
    shell = Minishell(MINISHELL_PATH)
    shell.prepare_binary(bin_dir)
    return shell


def pytest_generate_tests(metafunc):
    if "cmd" in metafunc.fixturenames:
        # Replicate the logic from conftest.py
        def find_project_root():
            current = Path(__file__).resolve().parent
            while current.parent != current:
                minishell_path = os.path.join(str(current), 'minishell')
                makefile_path = os.path.join(str(current), 'Makefile')
                if os.path.exists(minishell_path) and os.path.exists(makefile_path):
                    return str(current)
                current = current.parent
            raise ValueError("Could not find project root with minishell binary and Makefile")
        PROJECT_ROOT = find_project_root()
        # Derive the package directory relative to this test file so the
        # tests work whether the package folder is named
        # 'minishell-tester' or 'minishell_tester'.
        PACKAGE_DIR = str(Path(__file__).resolve().parent.parent)
        TEST_CSV = os.path.join(PACKAGE_DIR, 'cases', 'minishell_tests.csv')
        kind_filter = os.environ.get('TEST_KIND', None)
        loader = CaseLoader(Path(TEST_CSV))
        tests = loader.load()
        if kind_filter:
            tests = [t for t in tests if t.kind == kind_filter]
        metafunc.parametrize("cmd", tests)


class TestMinishellSuite:
    def fail_with_report(self, cmd: Command, bash_res: ShellResult, mini_res: ShellResult):
        diff = DiffGenerator.unified_diff(bash_res.stdout, mini_res.stdout)
        report = [
            f"\n{'='*40}",
            f"FAIL: Command ID {cmd.id} [{cmd.kind}]",
            f"INPUT: {cmd.text}",
            f"{'-'*40}",
            f"Bash Exit: {bash_res.exit_code} | Minishell Exit: {mini_res.exit_code}",
            f"{'-'*40}",
            "STDOUT DIFF:",
            diff,
            f"{'='*40}"
        ]
        if bash_res.stderr or mini_res.stderr:
            report.append(f"Bash Stderr: {bash_res.stderr.strip()}")
            report.append(f"Mini Stderr: {mini_res.stderr.strip()}")
        # Log to file
        import os
        log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'test.log')
        with open(log_path, 'a') as f:
            f.write("\n".join(report) + "\n")
        pytest.fail("\n".join(report), pytrace=False)

    def run_comparison(self, cmd: Command, bash: Bash, minishell: Minishell, work_dir: Path):
        bash_res = bash.execute(cmd, work_dir)
        mini_res = minishell.execute(cmd, work_dir)
        if bash_res != mini_res:
            self.fail_with_report(cmd, bash_res, mini_res)

    def test_command_execution(self, cmd: Command, bash_shell: Bash, minishell_binary: Minishell, tmp_path: Path):
        self.run_comparison(cmd, bash_shell, minishell_binary, tmp_path)
