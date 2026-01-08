# ADR 指南（Windows-only / Godot + C#）

本指南用于维护本仓库 `docs/adr/**` 下的 ADR，并确保 Base/Overlay/Tasks 的回链一致。

约束：
- Windows 环境默认用 `py -3` 运行 Python。
- 文档统一 UTF-8（LF）。
- 脚本/校验输出统一写入 `logs/**` 作为取证。

## 1. 何时需要新增 ADR

- 变更口径/阈值/契约/安全基线/质量门禁/发布健康策略时：新增 ADR，并在新 ADR 里声明 `supersedes` 旧 ADR；旧 ADR 标记为 `Superseded`。
- 仅补充说明（不改变决策）时：更新既有 ADR 的 Context/Consequences/References，并保持 `status: Accepted` 不变。

## 2. ADR 文件与 Front-Matter 约定

- 路径：`docs/adr/ADR-xxxx-<slug>.md`
- 编码：UTF-8（LF）
- 最小字段（建议保持一致，便于脚本解析与回链）：
  - `ADR-ID`, `title`, `status`, `decision-time`, `deciders`
  - `archRefs: [CH01, CH03, ...]`（与 Base/Overlay 的章节引用对齐）
  - `verification:`（可执行校验脚本或可取证的工件路径，例如 `logs/ci/.../*.json`）
  - `depends-on`, `depended-by`, `supersedes`, `superseded-by`（如适用）

## 3. 回链（SSoT）

- Base 文档通过 front-matter 的 `adr_refs` 引用 ADR。
  - 规则：只引用 `Accepted` 的 ADR；`Superseded` 仅用于历史对照，不作为当前口径。
- 任务集通过 `adr_refs` / `chapter_refs` / `overlay_refs` 回链到 ADR/Base/Overlay。
  - 规则：这些字段视为回链 SSoT；不要在任务描述里复制阈值/策略正文。

## 4. 校验与取证（Python-only）

所有校验应把输出落盘到 `logs/**`。常用入口：

- UTF-8/疑似乱码扫描：
  - `py -3 scripts/python/check_encoding.py --root docs`
- 旧栈术语扫描（严格建议只扫 Base/入口/当前 Overlay 08；全量 docs 仅取证）：
  - `py -3 scripts/python/scan_doc_stack_terms.py --root docs/architecture/base --fail-on-hits`
- 任务/文档回链校验：
  - `py -3 scripts/python/task_links_validate.py`
  - `py -3 scripts/python/verify_task_mapping.py`
  - `py -3 scripts/python/validate_task_master_triplet.py`
- 索引重建（用于入口索引与导航文件）：
  - `py -3 scripts/python/rebuild_repo_indexes.py`

## 5. 常见故障：中文被替换为 `?×4`

这通常不是“显示问题”，而是文件内容真的被写坏（例如：通过不安全的控制台管道/错误编码把文本写回文件）。

修复建议：
- 优先从 `git` 历史恢复原文件，再用 UTF-8 编辑器保存。
- 避免用“复制/粘贴覆盖整段中文”的方式修复（容易二次损坏）。
- 用 `check_encoding.py` 做严格解码取证；必要时对 git 跟踪文件做 `?×4` 语义扫描并把证据留在 `logs/ci/<YYYY-MM-DD>/encoding/**`。
\n