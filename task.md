# Claude Code Skill 示例创建计划

## 任务概述
创建一个功能完整的示例 skill，用于技术分享，演示 Claude Code Skill 的各项功能和最佳实践。

## 任务分解

### 阶段 1: 规划与设计
- [x] 分析项目结构
- [x] 确定 skill 主题：创建一个"代码审查助手"skill
- [x] 定义 skill 组件结构

### 阶段 2: 创建 Skill 文件
- [x] 创建 skill 目录结构 `.claude/skills/`
- [x] 编写 skill 主文件 `skill.md`
- [x] 添加参考文档 `reference.md`
- [x] 添加触发示例 `examples.md`

### 阶段 3: 编写分享文档
- [x] 创建 SKILL_GUIDE.md 分享文档
- [x] 覆盖多种使用场景

### 阶段 4: 验收测试
- [x] 验证 skill 结构完整性
- [x] 确认文档可供分享

## Skill 组件说明

| 组件 | 说明 | 必需性 |
|------|------|--------|
| name | skill 名称，简洁描述性强 | 必需 |
| description | 功能说明，用于自动匹配用户意图 | 必需 |
| triggers | 触发关键词列表 | 推荐 |
| instructions | 核心执行指令 | 必需 |
| reference | 参考文档路径 | 可选 |
| tools | 需要使用的工具列表 | 可选 |
| context | 上下文说明 | 可选 |

## 文件结构
```
.claude/
├── settings.local.json      # 本地设置
└── skills/
    └── code-reviewer/
        ├── skill.md         # skill 主文件
        └── reference.md     # 参考文档
```

## 验收标准
- [x] skill 文件结构符合 Claude Code 规范
- [x] 包含所有核心组件
- [x] 触发示例清晰可用
- [x] 文档完整，可供分享使用

## 创建的文件

| 文件 | 说明 |
|------|------|
| `task.md` | 本计划文档 |
| `.claude/skills/code-reviewer/skill.md` | Skill 主文件 |
| `.claude/skills/code-reviewer/reference.md` | 参考知识库 |
| `.claude/skills/code-reviewer/examples.md` | 触发示例 |
| `SKILL_GUIDE.md` | 分享指南文档 |