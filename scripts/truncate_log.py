#!/usr/bin/env python3
"""Truncate long sections in a test log file.

Usage: python3 tests/scripts/truncate_log.py [log_path]

Creates a backup of the original file with a .bak suffix.
"""
import os
import re
import sys
import time


def truncate_text(text, max_lines=200, max_chars=10000):
    if text is None:
        return text
    s = str(text)
    if max_chars is not None and len(s) > max_chars:
        s = s[:max_chars] + '\n... [truncated - exceeded chars limit] ...\n'
    if max_lines is not None:
        lines = s.splitlines(True)
        if len(lines) > max_lines:
            s = ''.join(lines[:max_lines]) + '\n... [truncated - exceeded lines limit] ...\n'
    return s


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'tests/logs/test.log'
    if not os.path.isfile(path):
        print(f'Log file not found: {path}', file=sys.stderr)
        sys.exit(2)
    try:
        max_lines = int(os.environ.get('TRUNCATE_MAX_LINES', '200'))
    except Exception:
        max_lines = 200
    try:
        max_chars = int(os.environ.get('TRUNCATE_MAX_CHARS', '10000'))
    except Exception:
        max_chars = 10000

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern_stdout = re.compile(r'(STDOUT:\n)(.*?)(\nSTDERR:\n)', re.S)
    content = pattern_stdout.sub(lambda m: m.group(1) + truncate_text(m.group(2), max_lines, max_chars) + m.group(3), content)
    pattern_stderr = re.compile(r'(STDERR:\n)(.*?)(\n(?:(?:--- )|={80}\n)|$)', re.S)
    content = pattern_stderr.sub(lambda m: m.group(1) + truncate_text(m.group(2), max_lines, max_chars) + (m.group(3) or ''), content)
    pattern_diff = re.compile(r'((?:--- DIFF[^\n]*\n))(.*?)(\n={80}\n|$)', re.S)
    content = pattern_diff.sub(lambda m: m.group(1) + truncate_text(m.group(2), max_lines, max_chars) + (m.group(3) or ''), content)
    bak = path + f'.bak.{int(time.time())}'
    try:
        os.rename(path, bak)
    except Exception as e:
        print(f'Failed to create backup: {e}', file=sys.stderr)
        sys.exit(2)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Log truncated and written to: {path}')
    print(f'Backup saved as: {bak}')


if __name__ == '__main__':
    main()
