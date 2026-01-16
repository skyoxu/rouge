# overlays 编写与维护指南（本项目口径）

本指南的目标是：让 `docs/architecture/overlays/**` **自己可维护、可检索、可避免误用**。

## 非 SSoT 声明

- overlays 不是任务的单一事实源（SSoT）。
- 任务真相以任务文件为准：`.taskmaster/tasks/tasks.json` 与视图任务文件（例如 `.taskmaster/tasks/tasks_gameplay.json`）。
- PRD 仅作参考；overlays 不承载任务拆分、排期或实现细节。

## 适用范围

- 本指南只覆盖 overlays 的写作与维护，不规定代码实现方式。
- 08 章只写在 overlays：`docs/architecture/overlays/<PRD-ID>/08/`。

## 目录结构（固定）

每个 PRD-ID 一套 overlays（建议只维护一个 08 目录）：

```text
docs/
  architecture/
    overlays/
      <PRD-ID>/
        08/
          _index.md
          ACCEPTANCE_CHECKLIST.md
          08-Feature-Slice-*.md
          08-Contracts-*.md
```

命名约定：

- 文件名使用英文（路径稳定，降低 Windows/CI 的编码与差异比较风险）。
- 正文用中文（便于团队阅读）。

## 每页最小结构（必须）

每个 `08/*.md` 页面必须包含以下 Front-Matter 字段（允许空数组，但字段必须存在）：

- `PRD-ID`
- `Title`
- `Status`（只允许 `Active` / `Proposed` / `Template`）
- `ADR-Refs`（可为空）
- `Arch-Refs`（可为空）
- `Test-Refs`（可为空）

并且正文开头固定三节（防误用）：

- `## Scope`：本页负责什么
- `## Non-goals`：本页不负责什么（避免被当成 SSoT 或实现手册）
- `## References`：只写 ADR/CH 与同目录关联页（禁止复制 Base/ADR 阈值与策略，允许引用）

## Status 三态（必须收敛）

- `Active`：当前 PRD 真正在用、需要被阅读/遵循的页
- `Proposed`：存在但允许不完整/演进中的页
- `Template`：模板页，不代表当前 PRD 的真实口径

## 编辑纪律（最小规则）

- 新增/删除/重命名任一 `08/*.md`：必须同步更新 `08/_index.md` 的 `## Catalog`（导航不漂移）。
- 修改任一页面口径：必须复核其 Front-Matter 的 `Status/ADR-Refs/Arch-Refs/Test-Refs` 是否仍准确。
- 提交前必须运行 overlays 自检，并把结果留痕到 `logs/ci/<YYYY-MM-DD>/overlay-08-audit/`。

推荐命令（Windows）：

```bat
py -3 scripts/python/generate_overlay_08_audit.py --prd-id PRD-rouge-manager
```

## 常见误用（必须避免）

- 把 overlays 当成任务清单或排期文档。
- 在 08 页复制 Base/ADR 的阈值与策略（只允许引用）。
- `_index.md` 不更新导致目录失效，逼迫读者全文搜索。
