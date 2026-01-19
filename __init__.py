from pathlib import Path

# Resolve package and project locations so paths work whether imported or run
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent

# Paths are expressed as strings for simpler use from tests/scripts
MINISHELL = str(PROJECT_ROOT / 'minishell')
TEST_CSV = str(PACKAGE_DIR / 'cases' / 'test_cases.csv')
TEST_LOG = str(PACKAGE_DIR / 'logs' / 'test.log')
TEST_TIMEOUT = 5
GENERATED_DIR = str(PACKAGE_DIR / 'generated')

__all__ = [
	'MINISHELL', 'TEST_CSV', 'TEST_LOG', 'TEST_TIMEOUT', 'GENERATED_DIR',
]
