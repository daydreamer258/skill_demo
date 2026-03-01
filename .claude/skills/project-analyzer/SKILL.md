---
name: project-analyzer
description: 项目分析工具，用于分析代码库结构、依赖项和质量指标。在分析项目结构、生成项目报告、检查代码统计或了解代码库架构时使用。触发词：analyze project, project stats, codebase analysis, 项目分析, 代码统计。
---

# 项目分析器技能

一个用于分析项目结构、代码统计和生成报告的综合工具。在进行项目代码分析时，严格执行以下的流程。

## 概述

此技能提供以下功能：
- 分析项目目录结构
- 按语言统计代码行数和文件数
- 识别技术栈
- 生成格式化的分析报告

## 使用方法

### 分析项目

运行分析脚本扫描项目并收集统计数据：

```bash
python .claude/skills/project-analyzer/scripts/analyze.py [project_path]
```

**参数说明：**

- `project_path` - 可选，要分析的路径（默认为当前目录）

**输出：** 项目统计 JSON 文件保存至 `.claude/skills/project-analyzer/assets/analysis.json`

### 生成报告

根据分析结果生成格式化的 Markdown 报告：

```bash
python .claude/skills/project-analyzer/scripts/report.py [--input analysis.json] [--output report.md]
```

**参数说明：**
- `--input` - 分析 JSON 文件的路径（默认：`assets/analysis.json`）
- `--output` - 输出报告的路径（默认：`assets/report.md`）

## 参考文件

- **分析检查清单：** 参见 `references/checklist.md` 获取全面的分析指南
- **报告模板：** 参见 `assets/template.md` 获取报告结构

## 分析指标

分析器收集以下指标：

| 类别 | 指标 |
|------|------|
| 文件 | 总数、按扩展名统计、按目录统计 |
| 代码行数 | 总行数、代码行、注释行、空白行 |
| 技术栈 | 检测到的框架、语言、依赖项 |
| 结构 | 目录深度、文件大小分布 |

## 示例

### 快速分析

```
运行项目分析
```

### 完整报告生成

```
分析此项目并生成详细报告
```

### 中文触发

```
项目分析
```

## 注意事项

- 大型项目可能需要更长的分析时间
- 二进制文件会自动排除
- 默认包含隐藏目录（以 `.` 开头）
- 结果会缓存以提高性能