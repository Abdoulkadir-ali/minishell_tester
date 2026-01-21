#!/usr/bin/env python3
from pathlib import Path
p = Path('tests/logs/test.log')
if not p.exists():
    print('NO_LOG')
    raise SystemExit(1)
text = p.read_text(encoding='utf-8', errors='replace')
parts = text.split('\n' + '='*80 + '\n')
summary = []
for part in parts:
    lines = part.strip().splitlines()
    if not lines:
        continue
    # find Test #
    tnum = None
    for l in lines[:5]:
        if l.startswith('Test #'):
            tnum = l.split('#',1)[1].strip()
            break
    if not tnum:
        for l in lines:
            if l.startswith('Test #'):
                tnum = l.split('#',1)[1].strip(); break
    if not tnum:
        continue
    # get COMMAND block
    cmd = ''
    try:
        ci = lines.index('COMMAND:')
        cmd_lines = []
        for ln in lines[ci+1:ci+10]:
            if ln.strip().startswith('---'):
                break
            cmd_lines.append(ln)
        cmd = '\n'.join(cmd_lines).strip()
    except ValueError:
        cmd = ''
    # detect stdout diff
    has_stdout_diff = ('--- DIFF (stdout) ---' in part) and ('(no stdout diff)' not in part)
    # detect exit code mismatch
    be = None; me = None
    for i,l in enumerate(lines):
        if l.startswith('--- bash ---'):
            if i+1 < len(lines) and lines[i+1].startswith('EXIT CODE:'):
                be = lines[i+1].split(':',1)[1].strip()
        if l.startswith('--- minishell ---'):
            if i+1 < len(lines) and lines[i+1].startswith('EXIT CODE:'):
                me = lines[i+1].split(':',1)[1].strip()
    exit_mismatch = (be is not None and me is not None and be != me)
    # detect stderr non-empty for minishell
    stderr_nonempty = False
    try:
        if '--- minishell ---' in lines:
            idx = lines.index('--- minishell ---')
            if 'STDERR:' in lines[idx:idx+20]:
                si = lines.index('STDERR:', idx)
                se = si+1
                sblk = []
                while se < len(lines) and not lines[se].startswith('---') and not lines[se].startswith('='):
                    sblk.append(lines[se])
                    se += 1
                stderr_nonempty = any(l.strip() for l in sblk)
    except Exception:
        stderr_nonempty = False
    # classify subsystem
    cmd_first = cmd.splitlines()[0] if cmd else ''
    subsystem = 'other'
    if cmd_first.startswith('env'):
        subsystem = 'env'
    elif cmd_first.startswith('export'):
        subsystem = 'export'
    elif cmd_first.startswith('unset'):
        subsystem = 'unset'
    elif cmd_first.startswith('echo') or '$' in cmd_first:
        subsystem = 'expansion'
    elif any(w in cmd_first for w in ['*','?','[']):
        subsystem = 'wildcard'
    elif cmd_first.startswith('cd'):
        subsystem = 'cd'
    summary.append((int(tnum), subsystem, has_stdout_diff, exit_mismatch, stderr_nonempty, cmd_first))
summary.sort()
print('COUNT', len(summary))
from collections import Counter
cnt = Counter(s[1] for s in summary)
print('BY_SUBSYSTEM', dict(cnt))
for t,sub,sd,em,se,cf in summary[:200]:
    flags = []
    if sd: flags.append('STDOUT_DIFF')
    if em: flags.append('EXIT_MISMATCH')
    if se: flags.append('STDERR')
    print(f'Test#{t}: {sub} {"|".join(flags) if flags else "OK?"} -- cmd: {cf}')
