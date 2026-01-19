# 🧪 **Minishell Tester** - *Automated Shell Testing Suite*

> **A robust testing framework for Minishell.**  
> Compares Minishell behavior against Bash using pytest for reliable validation.

![Language](https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Framework](https://img.shields.io/badge/Framework-pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Status](https://img.shields.io/badge/Status-Ready-green?style=for-the-badge)

---

## 📖 **Overview**

**Minishell Tester** is an automated testing suite designed for the Minishell project. It runs a series of commands in both Minishell and Bash, comparing outputs, exit codes, and errors to ensure compatibility. Built with Python and pytest, it provides detailed diffs for easy debugging.

---

## ✨ **Features**

### 🔍 **Testing Capabilities**
- **Automated Comparisons**: Executes 20+ test cases against Minishell and Bash.
- **Output Validation**: Checks stdout, stderr, and exit codes for exact matches.
- **Diff Reports**: Generates unified diffs for mismatches.
- **Robust Handling**: Manages paths, permissions, and environments dynamically.

### 🛠️ **Technical Features**
- **Dynamic Path Resolution**: Locates Minishell binary and files without hardcoded paths.
- **Permission Management**: Handles binary copying with automatic permission adjustments.
- **Cross-Platform**: Uses OS modules for reliable file and subprocess operations.

---

## 📋 **Requirements**

- **Python 3.8+**
- **pytest** (`pip install pytest`)
- **Minishell Binary**: Built and executable in the project root (`make`).

---

## 🚀 **Setup**

1. **Build Minishell**:
   ```bash
   cd /path/to/minishell  # Project root
   make  # Or your build command
   ```

2. **Install Dependencies**:
   ```bash
   pip install pytest
   ```

3. **Run from Project Root**:
   - Execute from the directory containing the `minishell` binary.

---

## 📖 **Usage**

### Run All Tests (Default: Generated + Manual)
```bash
python3 minishell_tester/main.py
```
- Runs all tests from `cases/minishell_tests.csv` (both "generated" and "manual" kinds, 1000+ tests).

### Run Specific Kinds
```bash
TEST_KIND=manual python3 minishell_tester/main.py    # Only manual tests
TEST_KIND=generated python3 minishell_tester/main.py # Only generated tests
```

### Other Options
```bash
python3 minishell_tester/main.py -v              # Verbose output
python3 minishell_tester/main.py -x              # Stop on first failure
python3 minishell_tester/main.py --tb=short      # Shorter tracebacks
python3 minishell_tester/main.py --collect-only  # Collect without running
python3 minishell_tester/main.py -k "cmd7"       # Run specific test by ID
```
- Failed tests are logged to `logs/test.log` with detailed diffs.

### Generate Custom Tests
Use the built-in generator for random test cases:
```bash
cd minishell_tester
python3 tools/test_generator.py --count 500 --out ../cases/test_cases.csv --seed 42
```
- `--count`: Number of tests to generate.
- `--out`: Output CSV path.
- `--seed`: For reproducible generation.
- Overwrites `test_cases.csv` with generated tests (kind="generated").

### Using Large Test Sets
- The tester now uses `cases/minishell_tests.csv` by default, containing 1000+ tests (manual + generated).
- For smaller sets, you can generate custom tests or switch back to `test_cases.csv` by editing `conftest.py`.

---

## 📁 **Project Structure**

- **`main.py`**: Entry script with environment setup.
- **`tests/`**: Core test files.
  - **`test_minishell.py`**: Main test suite.
  - **`core.py`**: Shell execution and diff utilities.
  - **`conftest.py`**: Fixtures and config.
- **`cases/`**: Test case CSVs.
- **`logs/`**: Log storage (failed test reports).
- **`tools/`**: Test generation scripts.

---

## 🔧 **How It Works**

1. **Path Discovery**: Searches for `minishell` binary dynamically.
2. **Test Loading**: Parses CSV (format: `id;kind;test`), filters by `TEST_KIND` if set.
3. **Execution**: Runs each command in Minishell and Bash, compares results.
4. **Reporting**: Outputs diffs on failures.

CSV Kinds:
- **generated**: Auto-generated random commands.
- **manual**: Hand-written test cases.

---

## 🐛 **Troubleshooting**

- **Import Errors**: Run from project root; `PYTHONPATH` is auto-set.
- **Permissions**: Tester handles them, but verify `minishell` is executable.
- **Binary Missing**: Ensure `minishell` is built.
- **Failures**: Review diffs; Minishell must match Bash exactly.

---

## 🤝 **Contributing**

- Add tests to `cases/test_cases.csv` (format: `id;kind;command`).
- Update fixtures in `conftest.py`.
- Preserve path and permission robustness.

For more, see the main Minishell README.