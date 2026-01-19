import pytest
from pathlib import Path

from .core import Bash, Minishell, TestCaseLoader, Command, DiffGenerator, ShellResult


# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MINISHELL_PATH = PROJECT_ROOT / "minishell"
CSV_PATH = PROJECT_ROOT / 'minishell_tester' / 'cases' / 'test_cases.csv'


@pytest.fixture(scope="session")
def loaded_test_cases():
    loader = TestCaseLoader(CSV_PATH)
    return loader.load()


@pytest.fixture(scope="session")
def bash_shell():
    return Bash()


@pytest.fixture(scope="session")
def minishell_binary(tmp_path_factory):
    bin_dir = tmp_path_factory.mktemp("bin")
    shell = Minishell(MINISHELL_PATH)
    shell.prepare_binary(bin_dir)
    return shell


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
        pytest.fail("\n".join(report), pytrace=False)

    def run_comparison(self, cmd: Command, bash: Bash, minishell: Minishell, work_dir: Path):
        bash_res = bash.execute(cmd, work_dir)
        mini_res = minishell.execute(cmd, work_dir)
        if bash_res != mini_res:
            self.fail_with_report(cmd, bash_res, mini_res)

    @pytest.mark.parametrize("cmd", TestCaseLoader(CSV_PATH).load())
    def test_command_execution(self, cmd: Command, bash_shell: Bash, minishell_binary: Minishell, tmp_path: Path):
        self.run_comparison(cmd, bash_shell, minishell_binary, tmp_path)
