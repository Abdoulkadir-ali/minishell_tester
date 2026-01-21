"""Utilities to canonicalize and filter log text for tests.

This reduces noise from environment dumps (IDE vars, PATH order, long single-line values)
before computing diffs or writing to logs.
"""
import re
from typing import List


DEFAULT_MASK_REGEX = [
    r'^VSCODE_',
    r'^BUNDLED_DEBUGPY_',
    r'^VSCODE_',
    r'^PYDEVD_',
    r'^DBUS_',
    r'^SSH_AUTH_SOCK$',
    r'^GPG_AGENT_INFO$',
    r'^XDG_.*',
]


def _is_env_like(text: str) -> bool:
    if not text:
        return False
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return False
    count_eq = sum(1 for l in lines if '=' in l)
    return count_eq >= max(1, len(lines) // 2)


def canonicalize_env_text(text: str, max_lines: int = 200, max_chars: int = 10000,
                          mask_regex: List[str] = None, path_keep: int = 5) -> str:
    """Return a canonicalized version of env-like text or a truncated version otherwise.

    - If text looks like an environment dump, split into KEY=VAL lines,
      drop keys matching mask_regex, normalize PATH (keep first N entries),
      replace LS_COLORS/LSCOLORS values with a short placeholder, truncate long values,
      and sort keys.
    - Otherwise, fallback to simple truncation by chars/lines.
    """
    if text is None:
        return ''
    s = str(text)
    try:
        mrs = [re.compile(r) for r in (mask_regex or DEFAULT_MASK_REGEX)]
    except re.error:
        mrs = [re.compile(r) for r in DEFAULT_MASK_REGEX]

    def _mask_key(k: str) -> bool:
        for rx in mrs:
            if rx.search(k):
                return True
        return False

    if _is_env_like(s):
        lines = [l for l in s.splitlines() if l.strip()]
        kv = []
        for l in lines:
            if '=' not in l:
                continue
            k, v = l.split('=', 1)
            k = k.strip()
            if _mask_key(k):
                continue
            if k in ('LS_COLORS', 'LSCOLORS'):
                v = '<LS_COLORS_MASKED>'
            elif k == 'PATH':
                parts = v.split(':') if v else []
                if len(parts) > path_keep:
                    v = ':'.join(parts[:path_keep]) + ':...'
            # truncate very long values
            if max_chars is not None and len(v) > max_chars:
                v = v[:max_chars] + '...'
            kv.append((k, v))

        kv.sort(key=lambda x: x[0])
        out_lines = [f"{k}={v}" for k, v in kv]
        if max_lines is not None and len(out_lines) > max_lines:
            out_lines = out_lines[:max_lines]
            out_lines.append('... [truncated - exceeded lines limit] ...')
        return '\n'.join(out_lines) + ('\n' if out_lines else '')

    # fallback: truncate by chars then lines
    if max_chars is not None and len(s) > max_chars:
        s = s[:max_chars] + '\n... [truncated - exceeded chars limit] ...\n'
    if max_lines is not None:
        lines = s.splitlines(True)
        if len(lines) > max_lines:
            s = ''.join(lines[:max_lines]) + '\n... [truncated - exceeded lines limit] ...\n'
    return s
