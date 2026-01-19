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
- **Minishell Binary**: Built and executable in the project root.

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

### Run All Tests
```bash
python3 minishell_tester/main.py
```

### Run Specific Tests
```bash
python3 minishell_tester/main.py -k "test_name"
```

### Collect Tests Only
```bash
python3 minishell_tester/main.py --collect-only
```

### Verbose Output
```bash
python3 minishell_tester/main.py -v
```

### Options
- `-x`: Stop on first failure.
- `--tb=short`: Shorter tracebacks.
- Full pytest options: `python3 minishell_tester/main.py --help`

---

## 📁 **Project Structure**

- **`main.py`**: Entry script with environment setup.
- **`tests/`**: Core test files.
  - **`test_minishell.py`**: Main test suite.
  - **`core.py`**: Shell execution and diff utilities.
  - **`conftest.py`**: Fixtures and config.
- **`cases/`**: Test case CSVs.
- **`logs/`**: Log storage.
- **`tools/`**: Test generation scripts.

---

## 🔧 **How It Works**

1. **Path Discovery**: Searches upwards for the `minishell` binary.
2. **Binary Prep**: Copies and chmods the binary safely.
3. **Execution**: Runs commands in Minishell and Bash, compares results.
4. **Reporting**: Outputs diffs on failures.

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