# Acceptance 贫血治理方法论（SSoT）

> 目标：把“done”从主观判断，收敛为**可审计、可复核、可自动化证据链**，并避免 acceptance 被无关条款稀释导致“语义验收缺失”。

本仓库以 `.taskmaster/tasks/tasks_back.json` 与 `.taskmaster/tasks/tasks_gameplay.json` 的任务视图为语义验收口径来源（允许缺一侧但至少存在一侧）。其中：

- `acceptance[]`：**任务语义验收条款**（必须可被测试证据证明）。
- `test_refs[]`：**任务证据清单**（验收条款与测试文件的聚合索引）。
- `test_strategy[] / details`：**实施策略与过程信息**（不作为硬验收口径）。

## 执行：如何选择 Task 号

本仓库的确定性门禁以 `scripts/sc/acceptance_check.py` 为准。为了避免跑偏与证据链断裂，Task 号的选择建议如下：

- 本地：建议总是显式传 `--task-id <id>`。
- CI：若没有显式指定，工作流会从 `.taskmaster/tasks/tasks.json` 中选择第一个 `status=in-progress` 的任务来运行验收门禁。
- （可选）提交绑定：如果你希望把提交历史与任务绑定，建议在 commit message 中包含 `Task [<id>]`（供部分工具做“锁定提交”）。

## 1. 为什么会出现“done 不真实”

常见根因不是代码没写，而是“语义没有固化为可验证条款”：

- `acceptance[]` 只剩“Core 不依赖 Godot”这种**跨任务通用约束**，没有任务独有行为/不变式。
- `acceptance[]` 混入本地 demo 路径、学习资料、CI 事实、操作步骤，导致真正的验收条款被挤掉。
- `Refs:` 指向不存在文件，或 `test_refs[]` 不包含全部 `Refs:`，导致证据链断裂。
- `ACC:T<id>.<n>` anchor 只是“文件出现过”，但没有绑定到具体测试方法，形成“可通过但不可审计”的假阳性。

## 2. acceptance 的最小语义集（建议）

每个任务的 `acceptance[]` 至少应包含以下 3 类中的 2 类（越靠前越推荐）：

1) **行为（Behavior）**：输入/条件 → 产出/副作用（含事件/状态变化）

- 例：完成一个地图节点会更新 Run 状态，并发布 `core.map.node.completed`。

2) **不变式（Invariant）**：始终成立的约束（唯一写入口、范围约束、幂等等）

- 例：伤害数值不得为负；非法输入应抛出 `ArgumentOutOfRangeException`。

3) **失败语义（Failure Semantics）**：失败时系统如何表现（抛异常/返回 false/回滚/不中断循环）

- 例：事件 handler 抛异常不影响其他 handler；Publish 失败是否回滚并抛出。

说明：

- “Core 不依赖 Godot API”属于通用约束，只在该任务确实新增/引入 Core 类型时才放入 acceptance；否则应放到 `test_strategy[]` 或由全局质量门禁覆盖。
- UI/场景类任务应把“可见性/信号/事件驱动 UI 更新”等写成 acceptance，并通过 GdUnit4/headless 产证据。

## 2.5 Obligations：避免 acceptance 变成 no-op

这一步的目标是：把任务的“语义义务”显式化，避免 acceptance 只有通用约束，从而出现“done 不真实”。

- “语义义务（obligations）”：完成任务必须满足的行为/不变式/失败语义。
- “可选提示（optional hints）”：学习资料、参考实现、本地 demo 路径、加固建议等；不应作为硬验收条款，应迁移到视图任务文件的 `test_strategy[]`，并统一以 `Optional:` 前缀记录。

可选（LLM 辅助，仍以确定性门禁为准）：

- 提取义务：`py -3 scripts/sc/llm_extract_task_obligations.py --task-id <id>`
  - 输入来源：
    - `.taskmaster/tasks/tasks.json` 的 `master.details` / `master.testStrategy` / `subtasks[]`
    - 任务视图：`.taskmaster/tasks/tasks_back.json` / `.taskmaster/tasks/tasks_gameplay.json` 的 `acceptance[]`
  - 输出证据：`logs/ci/<YYYY-MM-DD>/sc-llm-obligations-task-<id>/verdict.json` 与 `report.md`

治理判定（止损规则）：

- 若 obligations 明确但 acceptance 缺失/Refs 断链：必须补齐 acceptance + `Refs:`，并在对应测试方法附近加入 `ACC:T<id>.<n>` anchor。
- 若 obligations 实际属于“可选提示”（参考/学习/演示路径/加固建议）：必须改写为 `Optional:` 并迁移到视图的 `test_strategy[]`，避免污染 acceptance。
- 对 `pending/in-progress`：允许 append-only 补齐（不改写既有条款语义）；对 `done`：禁止自动重写语义，只能增补并保持可审计。

## 3. 禁止项：哪些内容不应留在 acceptance

下列条款应迁移到 `test_strategy[]` 或 `details`：

- `Local demo references:` 或任何外部绝对路径（例如 `C:\...`）。
- 学习资料、参考项目、实施步骤、命令行说明。
- CI 事实类条款（例如“覆盖率达标”“测试存在并通过”）。
- “可能/建议/可选”类条款（除非明确转为硬验收并提供测试证据）。

## 4. Refs 与 anchors：把条款绑定到证据

本仓库约束以 `docs/testing-framework.md` 为准，核心原则如下：

- `acceptance[]` 的**每条**必须以 `Refs: <repo-relative-test-path>[, ...]` 结尾。
- `test_refs[]` 必须至少包含该任务所有 acceptance `Refs:` 的并集。
- `ACC:T<id>.<n>` 作为语义绑定 anchor：第 `n` 条 acceptance 的 `Refs:` 指向测试文件中，必须出现 `ACC:T<id>.<n>`。
- anchors 建议作为注释贴近具体测试方法（xUnit `[Fact]` 或 GdUnit4 `func test_...`），避免“文件出现过但不可归因”。

## 5. 迁移优先、补齐为辅：治理流程（可重复）

1) **清洗**：把非确定性/过程条款从 `acceptance[]` 迁移到 `test_strategy[] / details`。
2) **补齐**：为每个任务写 2–6 条“可被测试证明”的 acceptance（行为/不变式/失败语义）。
3) **绑定**：每条 acceptance 填 `Refs:`，并在对应测试方法附近补 `ACC:T<id>.<n>`。
4) **汇总**：更新 `test_refs[]`（替换模式优先，避免历史漂移）。
5) **验收**：在 `refactor` 阶段启用硬门禁（Refs 文件存在、Refs 必须包含于 test_refs、anchors 绑定通过）。

## 6. 产物与取证

所有自动化输出统一落 `logs/ci/<YYYY-MM-DD>/`（详见 `AGENTS.md` 的 6.3），用于：

- 复盘 “为何 fail-fast”
- 对比治理前后差异
- 作为 PR 证据链的一部分
