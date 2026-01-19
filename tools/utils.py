from __future__ import annotations

import csv
import difflib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


@dataclass
class TestCase:
    id: int
    command: str
    kind: Optional[str] = None


def load_tests(csv_path: Optional[str]) -> List[TestCase]:
    """Load tests from CSV supporting both `id,test` and `id;kind;test` formats.

    Detects `;` vs `,` delimiter by peeking at the first line. Returns empty
    list when path missing or file empty.
    """
    if not csv_path:
        return []
    p = Path(csv_path)
    if not p.is_file():
        return []
    rows: List[TestCase] = []
    with p.open(newline='', encoding='utf-8') as f:
        first = f.readline()
        if not first:
            return []
        delimiter = ';' if ';' in first else ','
        f.seek(0)
        reader = csv.reader(f, delimiter=delimiter)
        for idx, row in enumerate(reader):
            if not row:
                continue
            # skip header rows that contain 'test'
            if idx == 0 and any('test' in (str(cell).lower()) for cell in row):
                continue
            if len(row) >= 3:
                id_str = str(row[0]).strip()
                kind = str(row[1]).strip() or 'Uncategorized'
                cmd = str(row[2]).replace('\r', '').strip()
            elif len(row) == 2:
                id_str = str(row[0]).strip()
                kind = 'generated'
                cmd = str(row[1]).replace('\r', '').strip()
            else:
                continue
            if not cmd:
                continue
            try:
                tid = int(id_str) if id_str and id_str.isdigit() else idx
            except Exception:
                tid = idx
            rows.append(TestCase(tid, cmd, kind))
    return rows


def run_cmd(cmd_args: Iterable[str], input_text: Optional[str] = None, timeout: int = 5, cwd: Optional[str] = None) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(list(cmd_args), input=input_text, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, cwd=cwd)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ''
        err = (e.stderr or '') + f"\n[timeout after {timeout}s]"
        return 124, out, err


def get_unified_diff(a: str, b: str, fromfile: str = 'a', tofile: str = 'b') -> str:
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)
    return ''.join(difflib.unified_diff(a_lines, b_lines, fromfile=fromfile, tofile=tofile))


def ensure_text(x) -> str:
    if isinstance(x, bytes):
        try:
            return x.decode('utf-8', errors='replace')
        except Exception:
            return str(x)
    return x if x is not None else ''
