#!/usr/bin/env python3
"""
Check encodings for files changed today (this session) and verify they are UTF-8 decodable.
Also flag common mojibake patterns. Results are written under logs/ci/<date>/encoding/session-check.json.

Usage:
  py -3 scripts/python/check_encoding.py --since-today
  py -3 scripts/python/check_encoding.py --since "2025-11-13 00:00:00"
  py -3 scripts/python/check_encoding.py --files path1 path2 ...
"""
import argparse
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
from typing import List

TEXT_EXT = {'.md','.txt','.json','.yml','.yaml','.xml','.cs','.csproj','.sln','.gd','.tscn','.tres','.gitattributes','.gitignore','.ps1','.py','.ini','.cfg','.toml'}
# Explicit binary extensions to skip from UTF-8 validation
BINARY_EXT = {
    '.png','.jpg','.jpeg','.gif','.bmp','.ico','.webp',
    '.ogg','.wav','.mp3','.mp4','.avi','.mov',
    '.zip','.7z','.rar','.gz','.tar','.tgz',
    '.dll','.exe','.pdb','.pck','.import','.ttf','.otf',
    '.db','.sqlite','.sav',
    '.docx',
    '.pyc','.pyd',
    '.nupkg','.snupkg',
    '.lib',
    '.cache',
    '.tests',
    '.bak'
}

# Exclude vendor/test asset folders and known binaries
EXCLUDE_PATTERNS = [
    'Tests.Godot/addons/gdUnit4/src/core/assets/',
    'Tests.Godot/addons/gdUnit4/src/update/assets/',
    'Tests.Godot/addons/gdUnit4/src/reporters/html/template/css/',
    'Tests.Godot/addons/gdUnit4/src/ui/settings/',
    'gitlog/export-logs.zip',
]

# Exclude build/vendor/temporary directories from UTF-8 validation.
# These commonly contain binary artifacts that may be small enough to trip the
# "heuristic small files" fallback in is_text_file().
EXCLUDE_DIR_FRAGMENTS = (
    '/__pycache__/',
    '/.dotnet/',
    '/.venv/',
    '/bin/',
    '/obj/',
    '/TestResults/',
)


def run_cmd(args: List[str]) -> str:
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')
    out, _ = p.communicate()
    return out


def git_changed_since(since: str) -> List[str]:
    out = run_cmd(['git','log',f'--since={since}','--name-only','--pretty=format:'])
    files = [ln.strip() for ln in out.splitlines() if ln.strip() and not ln.startswith(' ')]
    return sorted(set(files))


def git_changed_today() -> List[str]:
    today = dt.date.today().strftime('%Y-%m-%d')
    return git_changed_since(today + ' 00:00:00')


def is_text_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    norm = path.replace('\\','/')
    if any(p in norm for p in EXCLUDE_PATTERNS):
        return False
    if any(seg in norm for seg in EXCLUDE_DIR_FRAGMENTS):
        return False
    if ext in BINARY_EXT:
        return False
    if ext in TEXT_EXT:
        return True
    # heuristic small files
    try:
        sz = os.path.getsize(path)
        # treat very small unknown files as text; larger files likely binary
        return sz < 128 * 1024
    except Exception:
        return False


def check_utf8(path: str):
    result = {
        'path': path,
        'utf8_ok': False,
        'has_bom': False,
        'mojibake_hits': [],
        'error': None,
    }
    try:
        raw = io.open(path, 'rb').read()
        result['has_bom'] = raw.startswith(b'\xef\xbb\xbf')
        text = raw.decode('utf-8')
        result['utf8_ok'] = True
        # common mojibake fragments when UTF-8 decoded as ANSI
        pattern = re.compile(r'[�]|Ã|Â|â€¢|â€“|â€”|â€œ|â€	d|â€˜|â€™|â€	4|â€	3|…')
        hits = pattern.findall(text)
        if hits:
            result['mojibake_hits'] = list(hits[:10])
    except UnicodeDecodeError as e:
        result['error'] = f'UnicodeDecodeError: {e}'
    except Exception as e:
        result['error'] = str(e)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=None, help='Recursively scan a root folder (e.g. docs)')
    ap.add_argument('--since-today', action='store_true')
    ap.add_argument('--since', default=None)
    ap.add_argument('--files', nargs='*')
    args = ap.parse_args()

    if args.root:
        root = args.root
        files = []
        for dirpath, dirnames, filenames in os.walk(root):
            rel = dirpath.replace('\\', '/')
            if '/.git' in rel or rel.startswith('.git'):
                continue
            if '/logs' in rel or rel.startswith('logs'):
                continue
            if '/demo' in rel or rel.startswith('demo'):
                continue
            if '/build' in rel or rel.startswith('build'):
                continue
            if '/.godot' in rel or rel.startswith('.godot'):
                continue
            if '/tmp' in rel or rel.startswith('tmp'):
                continue
            if '/_tmp' in rel or rel.startswith('_tmp'):
                continue
            if rel == '__pycache__' or rel.startswith('__pycache__/') or '/__pycache__/' in rel:
                continue
            if rel == '.dotnet' or rel.startswith('.dotnet/') or '/.dotnet/' in rel:
                continue
            if rel == '.venv' or rel.startswith('.venv/') or '/.venv/' in rel:
                continue
            if rel == 'bin' or rel.startswith('bin/') or '/bin/' in rel:
                continue
            if rel == 'obj' or rel.startswith('obj/') or '/obj/' in rel:
                continue

            for name in filenames:
                fpath = os.path.join(dirpath, name)
                if os.path.isfile(fpath) and is_text_file(fpath):
                    files.append(fpath)
    elif args.files:
        files = args.files
    elif args.since:
        files = git_changed_since(args.since)
    else:
        files = git_changed_today()

    files = [f for f in files if os.path.isfile(f) and is_text_file(f)]

    date = dt.date.today().strftime('%Y-%m-%d')
    out_dir = os.path.join('logs','ci',date,'encoding')
    os.makedirs(out_dir, exist_ok=True)

    results = []
    bad = []
    skipped = 0
    for fpath in files:
        if not is_text_file(fpath):
            skipped += 1
            continue
        r = check_utf8(fpath)
        results.append(r)
        if not r['utf8_ok']:
            bad.append(r)

    summary = {
        'scanned': len(results),
        'bad': len(bad),
        'bad_paths': [b['path'] for b in bad],
        'mojibake_paths': [r['path'] for r in results if r.get('mojibake_hits')],
        'skipped': skipped,
        'generated': dt.datetime.now().isoformat(),
    }

    suffix = 'root' if args.root else 'session'

    with io.open(os.path.join(out_dir,f'{suffix}-details.json'),'w',encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with io.open(os.path.join(out_dir,f'{suffix}-summary.json'),'w',encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"ENCODING_CHECK scanned={summary['scanned']} bad={summary['bad']} out={out_dir}")
    return 0 if summary['bad'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
