# 文档口径收敛操作手册（Base 严格 + 全量取证）

## 1. 目的与范围

本手册用于解决仓库文档中残留旧技术栈语境（例如旧桌面壳、旧前端栈、旧构建/测试工具名）导致的人与 LLM 误导问题，并给出在本仓库进行收敛的可执行步骤与验证方式。

适用范围：
- `docs/architecture/base/**`（Base-Clean 口径，硬门禁）
- `README.md`、`AGENTS.md`、`CLAUDE.md`、`docs/PROJECT_DOCUMENTATION_INDEX.md`（入口与规则文档，硬门禁）
- `docs/architecture/overlays/**/08/**`（功能纵切，硬门禁）
- `docs/migration/**`、`docs/adr/**`（历史/取证资料库，仅取证，不作为“旧栈词汇零命中”的硬门禁范围）

本手册不讨论业务 PRD 细节；只讨论文档口径收敛与可执行验证。

## 2. 止损原则（避免无穷修复）

- **硬门禁范围**：Base + 入口文档 + 当前 Overlay 08。
  - 要求：禁止旧技术栈词汇回流；必须能通过脚本门禁。
- **全量 docs 扫描仅取证**：不要把 “`docs/**` 全量扫描 hits=0” 当成硬门禁。
  - 原因：迁移资料与已标记 `Superseded` 的 ADR 可能需要保留历史语境；强行硬门禁会导致长期无穷修复与口径混乱。
- **迁移资料要中性化**：允许提及旧栈，但必须写成“历史对照/旧实现”，避免让读者误以为是当前依赖。

## 3. Windows 环境前置（必须）

- Windows 环境下请使用 `py -3` 运行 Python。不要依赖 `python`（可能指向 Microsoft Store alias）。
- 运行 PowerShell 脚本请使用：`powershell -NoProfile -ExecutionPolicy Bypass -File <script.ps1>`。
- 文档读写一律使用 UTF-8（仓库脚本均显式使用 `encoding="utf-8"`）。

## 4. 本仓库可执行脚本（SSoT）

### 4.1 Base-Clean 校验（硬门禁）

脚本：`scripts/ci/verify_base_clean.ps1`

运行命令：
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ci\verify_base_clean.ps1`

产出位置：
- `logs/ci/<run>/base-clean/summary.json`

### 4.2 UTF-8 与疑似乱码扫描（取证 + 门禁前置）

脚本：`scripts/python/check_encoding.py`

运行命令：
- `py -3 scripts/python/check_encoding.py --root docs`

产出位置：
- `logs/ci/<YYYY-MM-DD>/encoding/**`

### 4.3 旧技术栈术语扫描（硬门禁 + 取证）

脚本：`scripts/python/scan_doc_stack_terms.py`

说明：
- 严格模式（硬门禁）：对 Base/入口/Overlay 08 扫描并启用 `--fail-on-hits`。
- 取证模式：对 `docs/**` 全量扫描但不阻断（不使用 `--fail-on-hits`），用于趋势观察与排障定位。

严格模式（示例）：
- Base：`py -3 scripts/python/scan_doc_stack_terms.py --root docs/architecture/base --fail-on-hits --out logs/ci/<YYYY-MM-DD>/doc-stack-scan/strict/base`
- 入口文档（逐个文件扫）：
  - `py -3 scripts/python/scan_doc_stack_terms.py --root README.md --fail-on-hits --out logs/ci/<YYYY-MM-DD>/doc-stack-scan/strict/README`
  - `py -3 scripts/python/scan_doc_stack_terms.py --root AGENTS.md --fail-on-hits --out logs/ci/<YYYY-MM-DD>/doc-stack-scan/strict/AGENTS`
  - `py -3 scripts/python/scan_doc_stack_terms.py --root CLAUDE.md --fail-on-hits --out logs/ci/<YYYY-MM-DD>/doc-stack-scan/strict/CLAUDE`
  - `py -3 scripts/python/scan_doc_stack_terms.py --root docs/PROJECT_DOCUMENTATION_INDEX.md --fail-on-hits --out logs/ci/<YYYY-MM-DD>/doc-stack-scan/strict/INDEX`
- 当前 Overlay 08：`py -3 scripts/python/scan_doc_stack_terms.py --root docs/architecture/overlays --fail-on-hits --out logs/ci/<YYYY-MM-DD>/doc-stack-scan/strict/overlays-08`

取证模式（全量 docs，不阻断）：
- `py -3 scripts/python/scan_doc_stack_terms.py --root docs --out logs/ci/<YYYY-MM-DD>/doc-stack-scan/full`

产出位置：
- `logs/ci/<YYYY-MM-DD>/doc-stack-scan/**/summary.json`
- `logs/ci/<YYYY-MM-DD>/doc-stack-scan/**/scan.json`

> 说明：CI 已通过 `scripts/python/ci_pipeline.py` 封装了“严格 + 取证”两类扫描，产物统一落盘到 `logs/ci/<date>/doc-stack-scan/**`。

### 4.4 旧术语中性化替换（可选，全量收敛工具）

脚本：`scripts/python/sanitize_legacy_stack_terms.py`

运行命令（写回）：
- `py -3 scripts/python/sanitize_legacy_stack_terms.py --root docs --write`

产出位置：
- `logs/ci/<YYYY-MM-DD>/legacy-term-sanitize/**`

### 4.5 文档去符号清理（可选但推荐）

脚本：`scripts/python/sanitize_docs_no_emoji.py`

运行命令（写回）：
- `py -3 scripts/python/sanitize_docs_no_emoji.py --root docs --extra README.md AGENTS.md CLAUDE.md --write`

产出位置：
- `logs/ci/<YYYY-MM-DD>/emoji-sanitize.json`

## 5. 推荐步骤（按顺序）

### Step 1：先做编码与疑似乱码扫描（取证）

- `py -3 scripts/python/check_encoding.py --root docs`

若 `bad>0`：
- 优先用编辑器按 UTF-8 重新保存（不要用控制台 copy/paste 修复）。
- 再复跑脚本确认 `bad=0`。

### Step 2：先做严格扫描（硬门禁范围）

- Base：`py -3 scripts/python/scan_doc_stack_terms.py --root docs/architecture/base --fail-on-hits`
- 入口文档：逐个文件用 `--root <file>` + `--fail-on-hits` 扫描
- Overlay 08：`py -3 scripts/python/scan_doc_stack_terms.py --root docs/architecture/overlays --fail-on-hits`

### Step 3：全量 docs 扫描（取证，不阻断）

- `py -3 scripts/python/scan_doc_stack_terms.py --root docs --out logs/ci/<YYYY-MM-DD>/doc-stack-scan/full`

如果 Top files 命中落在 Base/入口/Overlay 08：必须修复。
如果命中主要落在 `docs/migration/**` 或 `Superseded` ADR：优先做中性化（避免被误读为当前依赖），但不要把“全量 hits=0”当硬门禁。

### Step 4：复跑 Base-Clean（硬门禁）

- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ci\verify_base_clean.ps1`

### Step 5：形成最终取证（落 logs）

- `py -3 scripts/python/check_encoding.py --root docs`
- 严格扫描：Base/入口/Overlay 08
- 全量取证扫描：`docs/**`

## 6. 最小验证清单（建议作为 CI 门禁）

- Base-Clean：`scripts/ci/verify_base_clean.ps1`
- UTF-8/疑似乱码：`py -3 scripts/python/check_encoding.py --root docs`
- 旧栈术语严格扫描：Base + 入口文档 + Overlay 08（`--fail-on-hits`）

## 7. 常见坑与排查

- **终端显示乱码不等于文件乱码**：以 `check_encoding.py` 的严格解码结果与 `logs/**` JSON 报告为准。
- **避免用管道/复制粘贴覆盖中文内容**：建议通过脚本或编辑器以 UTF-8 保存。
- **PowerShell 与 UTF-8**：如果需要向外部进程通过管道传中文（例如 `py -3 -`），建议先设置：
  - `$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)`
  - 并使用 `py -3 -X utf8`。
