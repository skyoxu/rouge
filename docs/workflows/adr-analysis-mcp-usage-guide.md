# ADR Analysis MCP 使用指南

## 配置说明

### 1. 目录配置修正

**问题**: MCP 服务器默认配置 ADR 目录为 `docs/adrs`（有 s）
**实际**: 本项目使用 `docs/adr`（无 s）

### 2. 配置方案

#### 方案 A: 项目环境变量（推荐）✅

已创建配置文件：`.env.mcp`

```env
PROJECT_PATH=F:\rouge
ADR_DIRECTORY=docs/adr
ENABLE_AI_EXECUTION=true
ENABLE_MEMORY_INTEGRATION=true
```

#### 方案 B: 工具调用时显式指定参数

每次调用 adr-analysis MCP 工具时，显式指定正确的目录：

```javascript
{
  "adrDirectory": "docs/adr",
  "projectPath": "F:\\rouge"
}
```

### 3. 使用前提条件检查清单

#### ✅ 已满足的条件

- [x] 项目根目录：`F:\rouge`
- [x] ADR 文件存在：23 个 ADR 文件（ADR-0001 至 ADR-0024）
- [x] 目录结构完整：
  - `docs/adr/` - ADR 文件
  - `docs/architecture/base/` - 基础架构文档
  - `docs/architecture/overlays/` - PRD 特定覆盖
  - `docs/prd/` - PRD 文档
  - `tasks/tasks.json` - Taskmaster 任务
- [x] Windows 环境配置
- [x] Python 3.x 可用

#### ⚠️ 需要注意的问题

1. **MCP 服务器依赖问题**:
   - 缺少 `openai` 包（影响 AI 增强功能）
   - 编译依赖需要 Visual Studio C++ 工具（非必需）

2. **配置生效方式**:
   - `.env.mcp` 文件需要 MCP 服务器重启后生效
   - 或在每次工具调用时显式指定参数

### 4. 推荐使用流程

#### 步骤 1: 发现和索引现有 ADR

```javascript
mcp__adr-analysis__discover_existing_adrs({
  "adrDirectory": "docs/adr",
  "includeContent": true
})
```

#### 步骤 2: 获取架构上下文

```javascript
mcp__adr-analysis__get_architectural_context({
  "conversationContext": {
    "humanRequest": "了解项目架构决策",
    "userGoals": ["理解现有 ADR", "评估架构一致性"]
  }
})
```

#### 步骤 3: 验证 ADR 完整性

```javascript
mcp__adr-analysis__validate_all_adrs({
  "adrDirectory": "docs/adr",
  "projectPath": "F:\\rouge",
  "includeEnvironmentCheck": true
})
```

#### 步骤 4: 分析 ADR 实现进度

```javascript
mcp__adr-analysis__compare_adr_progress({
  "adrDirectory": "docs/adr",
  "todoPath": "TODO.md",
  "projectPath": "F:\\rouge",
  "strictMode": true
})
```

### 5. 常用工具参考

#### ADR 管理工具

- `discover_existing_adrs` - 发现和编目现有 ADR
- `validate_adr` - 验证单个 ADR
- `validate_all_adrs` - 验证所有 ADR
- `review_existing_adrs` - 审查 ADR 质量和完整性
- `suggest_adrs` - 基于项目分析建议新 ADR
- `generate_adr_from_decision` - 从决策生成 ADR

#### 分析工具

- `analyze_project_ecosystem` - 分析完整项目生态系统
- `get_architectural_context` - 获取架构上下文
- `compare_adr_progress` - 对比 ADR 实施进度

#### 部署工具

- `deployment_readiness` - 评估部署就绪度
- `generate_deployment_guidance` - 生成部署指导

### 6. 最佳实践

1. **始终指定 adrDirectory 参数**:
   ```javascript
   { "adrDirectory": "docs/adr" }
   ```

2. **提供丰富的对话上下文**:
   ```javascript
   {
     "conversationContext": {
       "humanRequest": "原始需求描述",
       "userGoals": ["目标1", "目标2"],
       "focusAreas": ["security", "performance"]
     }
   }
   ```

3. **启用内存集成**（提升分析质量）:
   ```javascript
   { "enableMemoryIntegration": true }
   ```

4. **使用服务器上下文文件**:
   ```
   @.mcp-server-context.md
   ```

### 7. 故障排除

#### 问题: MCP 工具返回错误"Cannot find package 'openai'"

**原因**: MCP 服务器缺少 AI 执行依赖

**解决方案**:
- 方案 A: 暂时禁用 AI 增强功能
  ```javascript
  { "enhancedMode": false, "knowledgeEnhancement": false }
  ```
- 方案 B: 等待依赖修复后重新安装服务器

#### 问题: 找不到 ADR 文件

**原因**: 默认目录配置不正确

**解决方案**: 显式指定正确目录
```javascript
{ "adrDirectory": "docs/adr" }
```

### 8. 参考资源

- MCP 服务器上下文: `@.mcp-server-context.md`
- ADR 文件位置: `docs/adr/ADR-*.md`
- 架构文档索引: `@architecture_base.index`
- PRD 索引: `@prd_chunks.index`

---

**更新时间**: 2025-12-20
**版本**: 1.0
**维护者**: Claude Code AI Assistant
