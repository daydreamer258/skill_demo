---
name: prompt-optimizer
description: Professional prompt engineering tool that optimizes vague, redundant, or poorly structured prompts into high-quality, executable, low-ambiguity prompts. Use when users ask to optimize prompts, improve prompts, refine prompts, fix prompts, or make prompts better. Trigger when user says "优化prompt", "优化提示词", "改进prompt", "完善提示词", "prompt优化", "帮我写个prompt", "optimize prompt", "improve prompt", "refine prompt", "prompt optimization" in either Chinese or English.
---

# Prompt Optimizer

Transform vague, redundant, or unstructured prompts into high-quality, executable, low-ambiguity prompts.

## Workflow

When user provides a prompt to optimize, follow these steps:

### Step 1: Problem Diagnosis

Analyze the original prompt:
- Is the objective clear?
- Identify ambiguities, redundancies, conflicts, or missing constraints
- Note structural issues (missing role definition, output format, constraints)
- Present findings as a bullet list

### Step 2: Optimization & Restructuring

Improve the prompt:
- Clarify the task objective
- Define role if needed
- Specify input/output format
- Add necessary constraints (length, style, audience, tone)
- Remove redundancies and conflicts
- Enhance executability and stability

### Step 3: Output Two Versions

**1. Concise Version** - Minimal necessary instructions

**2. Professional Version** - Structured for complex tasks

## Requirements

- Do NOT change the original task's core objective
- Do NOT add unrelated tasks
- Optimized prompts must be ready to copy and use
- Use clear structure and numbering

## Example

**User input:**
```
帮我写一个产品介绍
```

**Step 1 - Diagnosis:**
- Missing product information
- No target audience specified
- No output format or length requirements
- No style or tone guidance

**Step 2 - Optimization:**
- Added role: Product Copywriter
- Specified output format
- Added length and style constraints

**Step 3 - Output:**

**Concise Version:**
```
作为产品文案专家，为[产品名称]撰写一段200字的产品介绍。
目标受众：[用户群体]
核心卖点：[卖点1、卖点2、卖点3]
风格：专业简洁、突出价值
```

**Professional Version:**
```
# Role
你是一名资深产品文案专家，擅长撰写吸引目标用户的产品介绍。

# Task
为指定产品撰写一段产品介绍文案。

# Input Format
- 产品名称：[待填写]
- 目标受众：[待填写]
- 核心卖点：[待填写]
- 竞品差异：[待填写]

# Output Format
- 字数：150-250字
- 结构：痛点引入 → 产品方案 → 价值主张 → 行动号召
- 风格：专业但不生硬，有说服力

# Constraints
- 避免使用夸张宣传语
- 不使用第一人称
- 突出实际价值而非功能罗列
```