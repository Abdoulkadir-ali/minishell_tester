from __future__ import annotations

import csv
import difflib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Optional

@dataclass(frozen=True)
class Command:
    """Immutable representation of a test command."""
    id: int
    text: str
    kind: str = "General"


@dataclass
class ShellResult:
    """Encapsulates the result of a shell execution."""
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    def __eq__(self, other):
        if not isinstance(other, ShellResult):
            return NotImplemented
        return (self.exit_code == other.exit_code and
                self.stdout == other.stdout)


# --- Shell Abstraction ---


class Shell(ABC):
    """Abstract base class for any shell (Bash, Minishell, etc)."""

    def __init__(self, executable_path: Path, timeout: int = 5):
        self.path = Path(executable_path)
        self.timeout = timeout

    def _run_process(self, args: List[str], input_str: Optional[str] = None) -> ShellResult:
        try:
            proc = subprocess.run(
                args,
                input=input_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                errors='replace'
            )
            return ShellResult(proc.returncode, proc.stdout, proc.stderr)
        except subprocess.TimeoutExpired as e:
            return ShellResult(124, e.stdout or "", (e.stderr or "") + "\nTimeout", timed_out=True)

    @abstractmethod
    def execute(self, cmd: Command, cwd: Path) -> ShellResult:
        pass


class Bash(Shell):
    """Concrete implementation for Bash execution."""

    def __init__(self, timeout: int = 5):
        super().__init__(Path('/bin/bash'), timeout)

    def execute(self, cmd: Command, cwd: Path) -> ShellResult:
        return self._run_process([str(self.path), '--noprofile', '--norc', '-c', cmd.text], input_str=None)


class Minishell(Shell):
    """Concrete implementation for Minishell execution."""

    def __init__(self, executable_path: Path, timeout: int = 5):
        super().__init__(Path(executable_path), timeout)

    def prepare_binary(self, temp_dir: Path) -> None:
        """Copies and prepares the binary (chmod +x) into temp_dir."""
        if not self.path.exists():
            raise FileNotFoundError(f"Minishell binary not found at {self.path}")
        dest = Path(temp_dir) / 'minishell_exec'
        src = str(self.path)
        dst = str(dest)
        try:
            shutil.copy2(src, dst)
            dest.chmod(dest.stat().st_mode | 0o111)
        except PermissionError:
            try:
                st = os.stat(src)
                orig_mode = st.st_mode & 0o777
            except Exception:
                orig_mode = None
            if orig_mode is not None:
                os.chmod(src, orig_mode | 0o644)
            shutil.copy2(src, dst)
            dest.chmod(dest.stat().st_mode | 0o111)
            if orig_mode is not None:
                try:
                    os.chmod(src, orig_mode)
                except Exception:
                    pass
        self.path = dest

    def execute(self, cmd: Command, cwd: Path) -> ShellResult:
        return self._run_process([str(self.path)], input_str=cmd.text + '\n')


# --- Utilities ---


class CaseLoader:
    """Handles loading and parsing of test definitions from CSV."""

    def __init__(self, csv_path: Path):
        self.csv_path = Path(csv_path)

    def load(self) -> List[Command]:
        if not self.csv_path.exists():
            return []
        commands: List[Command] = []
        # Detect delimiter by peeking at the first line
        with self.csv_path.open(newline='', encoding='utf-8') as f:
            first = f.readline()
            if not first:
                return []
            delimiter = ';' if ';' in first else ','
            f.seek(0)
            reader = csv.reader(f, delimiter=delimiter)
            for i, row in enumerate(reader):
                if not row:
                    continue
                # skip header rows that contain 'test'
                if i == 0 and any('test' in (str(cell).lower()) for cell in row):
                    continue
                # Accept rows in either of these shapes:
                # [id, kind, test]  OR  [id, test]
                if len(row) >= 3:
                    id_str = str(row[0]).strip()
                    kind = str(row[1]).strip() or 'Uncategorized'
                    # Normalize CRLF and strip surrounding whitespace so commands
                    # don't contain stray "\r" characters which break shells
                    test_text = str(row[2]).replace('\r', '').strip()
                elif len(row) == 2:
                    id_str = str(row[0]).strip()
                    kind = 'generated'
                    test_text = str(row[1]).strip()
                else:
                    continue
                if not test_text:
                    continue
                cid = int(id_str) if id_str.isdigit() else i
                commands.append(Command(id=cid, text=test_text, kind=kind))
        return commands


class DiffGenerator:
    """Responsible for formatting failure reports."""

    @staticmethod
    def unified_diff(expected: str, actual: str) -> str:
        return ''.join(difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile='Bash',
            tofile='Minishell',
        ))
