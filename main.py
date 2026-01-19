#!/usr/bin/env python3
"""
Main entry point for the Minishell Tester.

This script runs the pytest test suite for minishell.
"""

import sys
import os
from pathlib import Path
import subprocess


def main():
    """
    Run the minishell test suite using pytest.
    """
    package_dir = Path(__file__).parent
    tests_dir = package_dir / 'tests'
    # Run pytest as subprocess with PYTHONPATH set so imports work
    env = dict(os.environ)
    pythonpath = str(package_dir.parent)
    if 'PYTHONPATH' in env:
        pythonpath = os.pathsep.join([pythonpath, env['PYTHONPATH']])
    env['PYTHONPATH'] = pythonpath
    result = subprocess.run([sys.executable, '-m', 'pytest', '--rootdir', str(package_dir), str(tests_dir)] + sys.argv[1:], env=env, cwd=str(package_dir.parent))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()