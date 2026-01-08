#!/usr/bin/env python3
"""
CI pipeline driver (Python): dotnet tests+coverage (soft gate), Godot self-check, encoding scan.

Usage (Windows):
  py -3 scripts/python/ci_pipeline.py all \
    --solution Game.sln --configuration Debug \
    --godot-bin "C:\\Godot\\Godot_v4.5.1-stable_mono_win64_console.exe" \
    --build-solutions

Exit codes:
  0  success (or only soft gates failed)
  1  hard failure (dotnet tests failed or self-check failed)
"""
import argparse
import datetime as dt
import io
import json
import os
import subprocess
import sys


def run_cmd(args, cwd=None, timeout=900_000):
    p = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding='utf-8', errors='ignore')
    try:
        out, _ = p.communicate(timeout=timeout/1000.0)
    except subprocess.TimeoutExpired:
        p.kill()
        out, _ = p.communicate()
        return 124, out
    return p.returncode, out


def read_json(path):
    try:
        with io.open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    ap_all = sub.add_parser('all')
    ap_all.add_argument('--solution', default='Game.sln')
    ap_all.add_argument('--configuration', default='Debug')
    ap_all.add_argument('--godot-bin', required=True)
    ap_all.add_argument('--project', default='project.godot')
    ap_all.add_argument('--build-solutions', action='store_true')

    args = ap.parse_args()
    if args.cmd != 'all':
        print('Unsupported command')
        return 1

    root = os.getcwd()
    date = dt.date.today().strftime('%Y-%m-%d')
    ci_dir = os.path.join('logs', 'ci', date)
    os.makedirs(ci_dir, exist_ok=True)

    summary = {
        'dotnet': {},
        'eventbus_audit': {},
        'selfcheck': {},
        'encoding': {},
        'doc_stack': {},
        'task_semantics': {},
        'status': 'ok'
    }
    hard_fail = False

    # 1) Dotnet tests + coverage (soft gate on coverage)
    rc, out = run_cmd(['py', '-3', 'scripts/python/run_dotnet.py',
                       '--solution', args.solution,
                       '--configuration', args.configuration], cwd=root)
    dotnet_sum = read_json(os.path.join('logs', 'unit', date, 'summary.json')) or {}
    summary['dotnet'] = {
        'rc': rc,
        'line_pct': (dotnet_sum.get('coverage') or {}).get('line_pct'),
        'branch_pct': (dotnet_sum.get('coverage') or {}).get('branch_pct'),
        'status': dotnet_sum.get('status')
    }
    if rc not in (0, 2) or summary['dotnet']['status'] == 'tests_failed':
        hard_fail = True

    # 1b) EventBus handler exception audit (hard gate)
    eb_dir = os.path.join('logs', 'ci', date, 'eventbus-audit-gate')
    os.makedirs(eb_dir, exist_ok=True)
    eb_out = os.path.join(eb_dir, 'summary.json')
    rc_eb, out_eb = run_cmd(['py', '-3', 'scripts/python/eventbus_audit_gate.py', '--out', eb_out], cwd=root)
    with io.open(os.path.join(eb_dir, 'stdout.txt'), 'w', encoding='utf-8') as f:
        f.write(out_eb)
    eb_sum = read_json(eb_out) or {}
    summary['eventbus_audit'] = {
        'rc': rc_eb,
        'ok': eb_sum.get('ok'),
        'selected': ((eb_sum.get('runtime') or {}).get('selected') or {}).get('path'),
        'out': eb_out,
    }
    if rc_eb != 0 or not summary['eventbus_audit']['ok']:
        hard_fail = True

    # 2) Godot self-check (hard gate)
    # ensure autoload fixed (explicit project path)
    _ = run_cmd(['py', '-3', 'scripts/python/godot_selfcheck.py', 'fix-autoload', '--project', args.project], cwd=root)
    sc_args = ['py', '-3', 'scripts/python/godot_selfcheck.py', 'run', '--godot-bin', args.godot_bin, '--project', args.project]
    if args.build_solutions:
        sc_args.append('--build-solutions')
    rc2, out2 = run_cmd(sc_args, cwd=root, timeout=600_000)
    # persist raw stdout for diagnosis
    os.makedirs(os.path.join('logs', 'ci', date), exist_ok=True)
    with io.open(os.path.join('logs', 'ci', date, 'selfcheck-stdout.txt'), 'w', encoding='utf-8') as f:
        f.write(out2)
    sc_sum = read_json(os.path.join('logs', 'e2e', date, 'selfcheck-summary.json')) or {}
    # fallback: parse status from stdout if summary missing
    if not sc_sum:
        import re
        m = re.search(r"SELF_CHECK status=([a-z]+).*? out=([^\r\n]+)", out2)
        if m:
            sc_status = m.group(1)
            sc_out = m.group(2)
            sc_sum = {'status': sc_status, 'out': sc_out, 'note': 'parsed-from-stdout'}
    # as ultimate fallback, trust process rc (0==ok)
    # Copy Godot selfcheck raw console/stderr into ci logs if present
    try:
        e2e_dir = os.path.join('logs', 'e2e', date)
        ci_dir = os.path.join('logs', 'ci', date)
        cons = [p for p in os.listdir(e2e_dir) if p.startswith('godot-selfcheck-console-')]
        if cons:
            cons.sort()
            src = os.path.join(e2e_dir, cons[-1])
            with io.open(src, 'r', encoding='utf-8', errors='ignore') as rf, io.open(os.path.join(ci_dir, 'selfcheck-console.txt'), 'w', encoding='utf-8') as wf:
                wf.write(rf.read())
        errs = [p for p in os.listdir(e2e_dir) if p.startswith('godot-selfcheck-stderr-')]
        if errs:
            errs.sort()
            src = os.path.join(e2e_dir, errs[-1])
            with io.open(src, 'r', encoding='utf-8', errors='ignore') as rf, io.open(os.path.join(ci_dir, 'selfcheck-stderr.txt'), 'w', encoding='utf-8') as wf:
                wf.write(rf.read())
    except Exception:
        pass

    sc_ok = (sc_sum.get('status') == 'ok') or (rc2 == 0)
    summary['selfcheck'] = sc_sum or {'status': 'fail', 'note': 'no-summary'}
    if not sc_ok:
        hard_fail = True

    # 3) Encoding scan (soft gate)
    rc3, out3 = run_cmd(['py', '-3', 'scripts/python/check_encoding.py', '--since-today'], cwd=root)
    enc_sum = read_json(os.path.join('logs', 'ci', date, 'encoding', 'session-summary.json')) or {}
    summary['encoding'] = enc_sum

    # 3b) Doc stack terminology scan
    # Hard gate: Base + entry docs + current Overlay/08 must not contain legacy stack terms.
    # Soft evidence: full docs scan records hits but does not fail (except bad UTF-8).
    doc_stack = {"strict": [], "full": {}}

    def run_doc_stack_scan(root_arg: str, out_dir: str, fail_on_hits: bool) -> tuple[int, dict]:
        cmd = ['py', '-3', 'scripts/python/scan_doc_stack_terms.py', '--root', root_arg, '--out', out_dir]
        if fail_on_hits:
            cmd.append('--fail-on-hits')
        rc, _out = run_cmd(cmd, cwd=root)
        s = read_json(os.path.join(out_dir, 'summary.json')) or {}
        return rc, s

    strict_roots = [
        'docs/architecture/base',
        'docs/architecture/overlays/PRD-rouge-manager/08',
        'README.md',
        'AGENTS.md',
        'CLAUDE.md',
        'docs/PROJECT_DOCUMENTATION_INDEX.md',
    ]

    for root_arg in strict_roots:
        if not os.path.exists(root_arg):
            continue
        slug = root_arg.replace('\\', '_').replace('/', '_').replace(':', '').replace('.', '_')
        out_dir = os.path.join('logs', 'ci', date, 'doc-stack-scan', 'strict', slug)
        rc_ds, ds_sum = run_doc_stack_scan(root_arg, out_dir, fail_on_hits=True)
        doc_stack['strict'].append(
            {
                'root': root_arg,
                'out': out_dir,
                'rc': rc_ds,
                'hits': ds_sum.get('hits'),
                'bad_utf8_files': len(ds_sum.get('bad_utf8_files') or []),
                'summary_json': os.path.join(out_dir, 'summary.json'),
            }
        )
        if rc_ds != 0:
            hard_fail = True

    # Soft evidence scan for full docs (do not fail on hits).
    if os.path.exists('docs'):
        out_dir = os.path.join('logs', 'ci', date, 'doc-stack-scan', 'full')
        rc_ds, ds_sum = run_doc_stack_scan('docs', out_dir, fail_on_hits=False)
        doc_stack['full'] = {
            'root': 'docs',
            'out': out_dir,
            'rc': rc_ds,
            'hits': ds_sum.get('hits'),
            'bad_utf8_files': len(ds_sum.get('bad_utf8_files') or []),
            'summary_json': os.path.join(out_dir, 'summary.json'),
        }
        if rc_ds == 2:
            hard_fail = True

    summary['doc_stack'] = doc_stack

    # 4) Task semantics (hard gate): prevent drifted event-like names in tasks
    task_sem_dir = os.path.join('logs', 'ci', date, 'task-semantic')
    os.makedirs(task_sem_dir, exist_ok=True)
    task_sem_out = os.path.join(task_sem_dir, 'task-event-drift.json')
    rc4, out4 = run_cmd(['py', '-3', 'scripts/python/check_task_event_drift.py', '--out', task_sem_out], cwd=root)
    sem_sum = read_json(task_sem_out) or {}
    summary['task_semantics'] = {
        'rc': rc4,
        'status': sem_sum.get('status'),
        'master_hits': len(((sem_sum.get('master') or {}).get('hits') or [])),
        'gameplay_hits': len(((sem_sum.get('tasks_gameplay') or {}).get('hits') or [])),
    }
    if rc4 != 0:
        hard_fail = True

    summary['status'] = 'ok' if not hard_fail else 'fail'
    with io.open(os.path.join(ci_dir, 'ci-pipeline-summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(
        f"CI_PIPELINE status={summary['status']} dotnet={summary['dotnet'].get('status')} "
        f"selfcheck={summary['selfcheck'].get('status')} encoding_bad={summary['encoding'].get('bad', 'n/a')} "
        f"task_semantics={summary['task_semantics'].get('status')}"
    )
    return 0 if not hard_fail else 1


if __name__ == '__main__':
    sys.exit(main())
