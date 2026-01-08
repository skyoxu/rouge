#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add subtasks to selected tasks in `.taskmaster/tasks/tasks.json`.

This is intentionally conservative:
- Only adds subtasks when the task currently has no subtasks.
- Uses UTF-8 and LF newlines.
- Writes an audit report to logs/ci/<YYYY-MM-DD>/taskmaster-rouge/add_subtasks_for_tasks_json.json

Windows:
  py -3 scripts/python/add_subtasks_for_tasks_json.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASKS_JSON = ROOT / ".taskmaster" / "tasks" / "tasks.json"


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def find_task(tasks: list[dict[str, Any]], task_id: str) -> dict[str, Any] | None:
    tid = str(task_id).strip()
    for t in tasks:
        if not isinstance(t, dict):
            continue
        if str(t.get("id")) == tid:
            return t
    return None


def ensure_subtask_shape(st: dict[str, Any]) -> None:
    required = ["id", "title", "description", "dependencies", "details", "status", "testStrategy"]
    missing = [k for k in required if k not in st]
    if missing:
        raise ValueError(f"subtask missing fields: {missing}")
    if not isinstance(st["dependencies"], list):
        raise ValueError("subtask.dependencies must be a list")
    st["dependencies"] = [str(x) for x in st["dependencies"]]
    st["id"] = str(st["id"])
    st["title"] = str(st["title"])
    st["description"] = str(st["description"])
    st["details"] = str(st["details"])
    st["status"] = str(st["status"])
    st["testStrategy"] = str(st["testStrategy"])


SUBTASKS_BY_TASK_ID: dict[str, list[dict[str, Any]]] = {
    "40": [
        {
            "id": "1",
            "title": "Define release-health JSON schema and configuration surface",
            "description": "Define the release health gate inputs/outputs (env vars, thresholds, and JSON schema) for release_health_gate.py.",
            "dependencies": [],
            "details": (
                "Define required env vars and defaults:\n"
                "- SENTRY_AUTH_TOKEN / SENTRY_ORG / SENTRY_PROJECT / SENTRY_ENV\n"
                "- RELEASE_CRASHFREE_THRESHOLD (default aligned to ADR-0003)\n"
                "- RELEASE_HEALTH_WINDOW_HOURS (default 24)\n"
                "- RELEASE_HEALTH_MODE=skip|warn|require (default require in release workflows; warn/skip in PR if desired)\n"
                "Define output path and minimal schema:\n"
                "- logs/ci/<YYYY-MM-DD>/release-health.json\n"
                "- Fields: ts, mode, window_hours, threshold, crashfree_sessions, crashfree_users, status, reason, project, env\n"
                "Security: never print tokens; log only which env vars are missing."
            ),
            "status": "pending",
            "testStrategy": "Run with missing env vars and verify the failure is explicit (mode=require) and written to logs/ci/**.",
        },
        {
            "id": "2",
            "title": "Implement Sentry Sessions query (Crash-Free Sessions/Users)",
            "description": "Implement Sentry API calls and parsing to compute Crash-Free Sessions/Users over a rolling window.",
            "dependencies": ["1"],
            "details": (
                "Implement scripts/python/release_health_gate.py:\n"
                "- Query Sentry metrics for crash-free sessions/users over window_hours\n"
                "- Handle timeouts/rate limits gracefully; fail fast with context\n"
                "- Support a --dry-run / stub mode to run without network in CI smoke\n"
                "Keep logic deterministic for unit tests (use stub JSON fixtures)."
            ),
            "status": "pending",
            "testStrategy": "Add deterministic unit tests using stub responses to validate parsing and computed crash-free rates.",
        },
        {
            "id": "3",
            "title": "Implement gate decision + evidence logging",
            "description": "Compare crash-free rates with threshold, write evidence JSON, and return correct exit code per mode.",
            "dependencies": ["2"],
            "details": (
                "Gate behavior:\n"
                "- mode=require: rc!=0 on below threshold or API errors\n"
                "- mode=warn: always rc=0 but status=fail in JSON when below threshold\n"
                "- mode=skip: write a skipped JSON record (optional) and rc=0\n"
                "Always write logs/ci/<date>/release-health.json with status + reason."
            ),
            "status": "pending",
            "testStrategy": "Run dry-run for both pass/fail cases and verify JSON fields + exit codes match mode semantics.",
        },
        {
            "id": "4",
            "title": "Integrate into GitHub Actions workflows",
            "description": "Wire the release-health gate into Windows workflows with toggles and artifact upload.",
            "dependencies": ["3"],
            "details": (
                "Update workflows:\n"
                "- windows-quality-gate.yml: optional (warn/skip) mode\n"
                "- windows-release*.yml: require mode\n"
                "Ensure logs/ci/** includes release-health.json and is uploaded as artifact.\n"
                "Secrets must be provided via GitHub Secrets; do not commit any tokens."
            ),
            "status": "pending",
            "testStrategy": "In CI, verify the step can be toggled on/off via env vars and artifacts include release-health.json.",
        },
    ],
    "55": [
        {
            "id": "1",
            "title": "设计出牌交互状态机与数据绑定",
            "description": "在 BattleScreen 中定义“Idle → CardSelected → Targeting → Confirm/Cancel”的交互状态机，明确状态数据与 UI 绑定方式。",
            "dependencies": [],
            "details": (
                "定义状态与转移：\n"
                "- Idle: 未选中卡\n"
                "- CardSelected: 已选中一张卡（显示预览/可选目标）\n"
                "- Targeting: 正在选择目标（按 TargetRule 限定）\n"
                "- Confirm: 目标已选定，等待确认出牌（或直接出牌）\n"
                "约束：只在 UI 层处理输入与高亮；不要在 UI 里复制 Game.Core 的规则计算。"
            ),
            "status": "pending",
            "testStrategy": "GdUnit4：验证状态机的关键转移（选卡→选目标→取消→回到 Idle）可重复且无残留 UI 状态。",
        },
        {
            "id": "2",
            "title": "实现目标高亮/指示与选择交互",
            "description": "实现合法目标高亮（单位/格子/敌人），并提供明确的目标指示（例如箭头/连线/光圈）。",
            "dependencies": ["1"],
            "details": (
                "根据 CardDefinition.TargetRule 计算合法目标集合：\n"
                "- SingleEnemy/AllEnemies/SingleAlly/AllAllies/Random\n"
                "交互要求：\n"
                "- hover/click 可选择目标\n"
                "- 非法目标点击不会进入确认态，并给出原因提示\n"
                "实现参考（概念级）：demo/godot-card-game-framework 的 targeting 交互（不要直接复制 Godot3 代码）。"
            ),
            "status": "pending",
            "testStrategy": "GdUnit4：选卡后合法目标被高亮；点击非法目标不改变 BattleManager 状态。",
        },
        {
            "id": "3",
            "title": "实现取消/回退路径与输入一致性",
            "description": "实现取消路径（ESC/右键/空白点击等），并保证所有 UI 状态（高亮/箭头/预览）可完全回收。",
            "dependencies": ["1", "2"],
            "details": (
                "取消要求：\n"
                "- CardSelected/Targeting 任意阶段都可取消并回到 Idle\n"
                "- 取消后不保留任何目标高亮/指示节点\n"
                "- 取消不改变 Game.Core 战斗状态"
            ),
            "status": "pending",
            "testStrategy": "GdUnit4：覆盖“选卡→选目标→取消→再次选卡”循环，确保 UI 不堆积节点且状态一致。",
        },
        {
            "id": "4",
            "title": "对齐 BattleManager.PlayCard 调用与失败提示",
            "description": "把交互闭环真正接到 BattleManager.PlayCard(heroId, cardId, targetId)，并实现失败原因提示。",
            "dependencies": ["3"],
            "details": (
                "成功路径：\n"
                "- 目标有效且能量足够 → 调用 PlayCard 并刷新 UI\n"
                "失败路径：\n"
                "- 能量不足/非法目标 → 不得 mutate battle state，并显示明确 reason\n"
                "提示形式：Toast/Label/弹层均可，但必须可被 headless test 断言到。"
            ),
            "status": "pending",
            "testStrategy": "GdUnit4：覆盖能量不足/非法目标失败时的“不变性”与提示可见性。",
        },
        {
            "id": "5",
            "title": "编写 headless 集成测试 test_battle_card_input_flow.gd",
            "description": "补齐 headless GdUnit4 集成测试，覆盖 play+cancel+invalid 三段流程并产出工件。",
            "dependencies": ["4"],
            "details": (
                "实现 Tests.Godot/tests/Integration/test_battle_card_input_flow.gd：\n"
                "- play: 选择卡+选择目标+出牌成功\n"
                "- cancel: 选择卡/目标后取消，回到 Idle\n"
                "- invalid: 能量不足/非法目标，状态不变且提示出现\n"
                "CI 工件：JUnit/XML + 可选截图，统一写入 logs/e2e/**。"
            ),
            "status": "pending",
            "testStrategy": "CI/headless 跑通 GdUnit4 Integration suite，并在 logs/e2e/** 下生成报告工件。",
        },
    ],
}


def main() -> int:
    if not TASKS_JSON.exists():
        print(f"ERROR: missing {TASKS_JSON}")
        return 2

    data = load_json(TASKS_JSON)
    master = data.get("master")
    if not isinstance(master, dict):
        print("ERROR: tasks.json missing master object")
        return 2
    tasks = master.get("tasks")
    if not isinstance(tasks, list):
        print("ERROR: tasks.json master.tasks is not a list")
        return 2

    report: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "file": str(TASKS_JSON.relative_to(ROOT)).replace("\\", "/"),
        "updated": [],
        "skipped": [],
        "missing": [],
    }

    for tid, subtasks in SUBTASKS_BY_TASK_ID.items():
        t = find_task(tasks, tid)
        if not t:
            report["missing"].append(tid)
            continue

        existing = t.get("subtasks")
        existing_n = len(existing) if isinstance(existing, list) else 0
        if existing_n > 0:
            report["skipped"].append({"id": tid, "reason": "already_has_subtasks", "count": existing_n})
            continue

        # Validate shape
        for st in subtasks:
            ensure_subtask_shape(st)

        t["subtasks"] = subtasks
        t["recommendedSubtasks"] = len(subtasks)
        report["updated"].append({"id": tid, "subtasks": len(subtasks)})

    dump_json(TASKS_JSON, data)

    out = ROOT / "logs" / "ci" / today_str() / "taskmaster-rouge" / "add_subtasks_for_tasks_json.json"
    write_json(out, report)

    status = "ok" if not report["missing"] else "warn"
    print(
        f"TASK_SUBTASKS_ADD status={status} "
        f"updated={len(report['updated'])} skipped={len(report['skipped'])} missing={len(report['missing'])} out={out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

