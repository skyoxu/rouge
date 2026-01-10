#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ci_dir(name: str) -> Path:
    root = _repo_root()
    out_dir = root / "logs" / "ci" / dt.date.today().strftime("%Y-%m-%d") / name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    repo = _repo_root()
    tasks_back_path = repo / ".taskmaster" / "tasks" / "tasks_back.json"
    back = _load_json(tasks_back_path)
    if not isinstance(back, list):
        raise SystemExit("tasks_back.json must be a JSON array")

    changes: list[dict[str, object]] = []
    bad_re = re.compile(r"\?{5,}")

    def replace_acceptance(task_id: int, index_1based: int, new_text: str) -> None:
        for entry in back:
            if not isinstance(entry, dict):
                continue
            if entry.get("taskmaster_id") != task_id:
                continue
            acc = entry.get("acceptance") or []
            if not isinstance(acc, list) or len(acc) < index_1based:
                raise SystemExit(f"Task {task_id} acceptance[{index_1based}] not found")
            old = str(acc[index_1based - 1])
            acc[index_1based - 1] = new_text
            entry["acceptance"] = acc
            changes.append(
                {
                    "taskmaster_id": task_id,
                    "field": f"acceptance[{index_1based}]",
                    "old": old,
                    "new": new_text,
                }
            )
            return
        raise SystemExit(f"Task {task_id} not found in tasks_back.json")

    # Task 45: fix three corrupted acceptance items (must mention temp branch and evidence).
    replace_acceptance(
        45,
        3,
        "按测试策略对测试有效性做一次验证：在临时分支中对 `Game.Core` 临时引入一个最小的故意违规（例如添加 `using Godot;` 或引用某个 Godot 类型）并确认 `dotnet test` 失败；随后移除该违规并确认 `dotnet test` 恢复通过。",
    )
    replace_acceptance(
        45,
        5,
        "在按测试策略进行“故意引入最小违例”的验证时，必须留下可审计的验证证据：包含临时分支名与对应提交（或补丁摘要），以及“引入违例后 dotnet test 失败”和“移除违例后 dotnet test 恢复通过”的结果摘要；证据需落盘到 `logs/ci/<date>/architecture-tests/layer-deps-validation.md`（或等价文件）便于复查。",
    )
    replace_acceptance(
        45,
        6,
        "`Game.Core.Tests/Architecture/LayerDependencyTests.cs` 中必须以可全文检索的文字写明“故意违例验证”的复现步骤：包含临时分支操作、最小 `Godot` 依赖示例（如 `using Godot;`）、以及预期的失败信息/命中规则说明，用于证明该架构测试不是永远绿灯的空测试。",
    )

    # Task 47: replace any corrupted acceptance item with an explicit GdUnit4(headless) requirement.
    for entry in back:
        if not isinstance(entry, dict):
            continue
        if entry.get("taskmaster_id") != 47:
            continue
        acc = entry.get("acceptance") or []
        if not isinstance(acc, list):
            raise SystemExit("Task 47 acceptance must be a list")
        replacement = "无头安全信号契约测试套件必须通过 GdUnit4（headless）执行（CI 与本地一致），不得使用其他测试框架或自定义 runner 替代。"
        replaced_any = False
        for i, line in enumerate(list(acc), 1):
            if isinstance(line, str) and bad_re.search(line):
                old = line
                acc[i - 1] = replacement
                changes.append(
                    {
                        "taskmaster_id": 47,
                        "field": f"acceptance[{i}]",
                        "old": old,
                        "new": replacement,
                    }
                )
                replaced_any = True
        if not replaced_any and replacement not in [str(x) for x in acc]:
            acc.append(replacement)
            changes.append(
                {
                    "taskmaster_id": 47,
                    "field": "acceptance[append]",
                    "old": None,
                    "new": replacement,
                }
            )
        entry["acceptance"] = acc
        break

    # Task 47: ensure ADR/CH audit requirements are explicit (helps deterministic obligations coverage).
    for entry in back:
        if not isinstance(entry, dict):
            continue
        if entry.get("taskmaster_id") != 47:
            continue
        acc = [str(x) for x in (entry.get("acceptance") or [])]
        want_lines = [
            "上述 Overlay 文件（见本任务 acceptance 中列出的文件路径）中必须逐字包含 `ADR-0004`、`ADR-0019`、`ADR-0005`；CI 必须对这些文件执行文本检索，任一缺失则判定失败。",
            "上述 Overlay 文件中必须逐字包含 `CH02`、`CH04`、`CH07`；CI 必须对这些文件执行文本检索，任一缺失则判定失败。",
        ]
        for want in want_lines:
            if want not in acc:
                acc.append(want)
                changes.append({"taskmaster_id": 47, "field": "acceptance[append]", "old": None, "new": want})
        entry["acceptance"] = acc
        break

    _write_json(tasks_back_path, back)

    # Assert no corruption remains.
    remaining = []
    for entry in back:
        if not isinstance(entry, dict):
            continue
        tid = entry.get("taskmaster_id")
        acc = entry.get("acceptance") or []
        if isinstance(acc, list):
            for i, line in enumerate(acc, 1):
                if isinstance(line, str) and bad_re.search(line):
                    remaining.append({"taskmaster_id": tid, "field": f"acceptance[{i}]", "text": line})
    if remaining:
        out_dir = _ci_dir("acceptance-manual-fix")
        _write_json(out_dir / "remaining-corruption.json", remaining)
        raise SystemExit("Corrupted '?' sequences still present in tasks_back.json")

    out_dir = _ci_dir("acceptance-manual-fix")
    _write_json(out_dir / "fix-corrupted-acceptance.summary.json", {"changes": changes})
    print(f"OK: fixed acceptance corruption; changes={len(changes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
