# Claude Code Skill 完全指南

## 分享大纲

1. 什么是 Skill？
2. Skill 的核心组件
3. 如何创建一个 Skill
4. 实战演示
5. 最佳实践

---

## 1. 什么是 Skill？

Skill 是 Claude Code 的扩展机制，用于：
- 封装专业知识和工作流程
- 提供特定领域的能力增强
- 自动匹配用户意图并激活相应功能

### 为什么需要 Skill？

```
问题：
- 重复性任务需要反复描述
- 专业领域知识难以固化
- 用户意图识别不够精准

解决：
Skill 提供了一种结构化的方式来封装和复用能力
```

---

## 2. Skill 的核心组件

### 必需组件

| 组件 | 说明 | 示例 |
|------|------|------|
| **name** | skill 名称 | `code-reviewer` |
| **description** | 功能描述（用于自动匹配） | "专业代码审查助手" |
| **instructions** | 核心执行指令 | 详细的执行步骤 |

### 推荐组件

| 组件 | 说明 | 示例 |
|------|------|------|
| **triggers** | 触发关键词 | `review code`, `代码审查` |
| **tools** | 需要的工具 | `Read`, `Grep`, `Glob` |
| **reference** | 参考文档 | `reference.md` |
| **context** | 上下文说明 | 额外的背景信息 |

### 文件结构

```
.claude/
└── skills/
    └── {skill-name}/
        ├── skill.md          # 主文件（必需）
        ├── reference.md       # 参考文档（可选）
        └── examples.md       # 示例文档（可选）
```

---

## 3. 如何创建一个 Skill

### 步骤 1: 定义 Skill 目标

明确你要解决的问题：
- 这个 Skill 做什么？
- 用户会如何触发它？
- 需要什么专业知识？

### 步骤 2: 编写 skill.md

```markdown
# {Skill Name} Skill

## Description
[功能描述 - 用于自动匹配用户意图]

## Triggers
- `trigger1`, `trigger2`, `中文触发词`

## Instructions
[核心执行指令 - 告诉 Claude 如何执行]

## Tools
[需要的工具列表]

## Reference
[参考文档路径]
```

### 步骤 3: 添加参考文档

reference.md 包含：
- 详细的知识库
- 检查清单
- 模板和示例

### 步骤 4: 测试和迭代

使用触发词测试，根据结果调整。

---

## 4. 实战演示：Code Reviewer Skill

### 创建的文件

```
.claude/skills/code-reviewer/
├── skill.md        # 核心定义
├── reference.md    # 知识库
└── examples.md     # 触发示例
```

### skill.md 核心内容

```markdown
## Description
Professional code review assistant that analyzes code for quality,
security vulnerabilities, performance issues, and best practices.

## Triggers
- `code review`, `review code`, `代码审查`
- `check code`, `检查代码`
- `security review`, `安全审查`
- `pr review`

## Instructions
1. Understand Context
2. Perform Analysis (quality, security, performance)
3. Provide Structured Feedback
4. Offer Fixes
```

### 触发示例

| 用户输入 | Skill 响应 |
|---------|-----------|
| `review my code` | 激活 skill，全面审查 |
| `安全检查` | 激活 skill，安全焦点 |
| `pr review` | 激活 skill，PR 审查模式 |

---

## 5. 最佳实践

### 描述清晰
```
✅ 好: "Professional code review assistant that analyzes code for
       quality, security vulnerabilities, performance issues, and
       best practices."

❌ 差: "Does code review."
```

### 触发词覆盖多语言
```
triggers:
- code review (英文)
- 代码审查 (中文)
- レビュー (日文)
```

### Instructions 结构化
```
1. 理解上下文
2. 执行分析
3. 提供反馈
4. 提供修复建议
```

### Reference 内容丰富
- 检查清单
- 代码示例
- 分类模板
- 知识库

### 保持专注
- 一个 Skill 做一件事
- 避免功能膨胀
- 清晰的边界

---

## Skill 组件详解

### name
```yaml
# 命名规范
- 使用小写字母
- 用连字符分隔
- 简洁描述性强
# 好例子
code-reviewer, pdf-parser, api-tester
# 坏例子
CodeReviewer, code_reviewer, my-skill-v1
```

### description
```markdown
# 用途：自动匹配用户意图
# 要求：
- 清晰说明功能
- 包含关键能力
- 控制在 2-3 句话

# 示例
"Professional code review assistant for analyzing code quality,
security vulnerabilities, and performance issues. Provides
actionable feedback with severity levels and fix suggestions."
```

### triggers
```markdown
# 触发关键词
- 英文关键词
- 中文关键词
- 常见变体

# 示例
- code review, review code
- 代码审查, 代码评审
- check code, 检查代码
```

### instructions
```markdown
# 核心执行逻辑
# 包含：
1. 角色定义（你是...）
2. 执行步骤（第一步...）
3. 输出格式（结构化输出）
4. 行为约束（不要...）

# 示例
You are a senior code reviewer...

### Review Process
1. Understand Context
2. Perform Analysis
3. Provide Feedback
4. Offer Fixes
```

### tools
```markdown
# 声明需要的工具
# 常用工具：
- Read: 读取文件
- Grep: 搜索内容
- Glob: 查找文件
- Bash: 执行命令
- WebFetch: 获取网页

# 示例
## Tools
- Read: To examine code files
- Grep: To search for patterns
- Glob: To find relevant files
```

### reference
```markdown
# 参考文档路径
# 内容包括：
- 知识库
- 检查清单
- 模板
- 示例代码

# 引用方式
## Reference
See `reference.md` for detailed checklists and best practices.
```

---

## 总结

### Skill 创建清单

- [ ] 确定目标和使用场景
- [ ] 创建目录 `.claude/skills/{name}/`
- [ ] 编写 `skill.md` 主文件
- [ ] 添加 `reference.md` 参考文档
- [ ] 定义触发词（中英文）
- [ ] 编写结构化的 instructions
- [ ] 测试和迭代

### 资源

- 示例 Skill: `.claude/skills/code-reviewer/`
- 触发示例: `examples.md`
- 参考文档: `reference.md`