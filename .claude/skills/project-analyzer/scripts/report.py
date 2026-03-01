#!/usr/bin/env python3
"""
Report Generator Script

Generates formatted Markdown reports from analysis results.

Usage:
    python report.py [--input analysis.json] [--output report.md]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


def load_template(template_path=None):
    """Load the report template."""
    if template_path is None:
        template_path = Path(__file__).parent.parent / 'assets' / 'template.md'
    else:
        template_path = Path(template_path)

    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    # Default template (中文版)
    return """# 项目分析报告

**项目名称：** {{project_name}}
**分析日期：** {{analysis_date}}
**项目路径：** {{project_path}}

---

## 概览

| 指标 | 数值 |
|------|------|
| 文件总数 | {{total_files}} |
| 代码总行数 | {{total_lines}} |
| 有效代码行 | {{code_lines}} |
| 注释行数 | {{comment_lines}} |
| 空白行数 | {{blank_lines}} |

## 编程语言

{{languages_table}}

## 检测到的框架

{{frameworks_list}}

## 文件类型分布

{{file_types_table}}

## 最大的文件

{{largest_files_table}}

## 代码分布

下图展示了不同编程语言的代码分布情况：

{{code_distribution}}

---

*报告由 Project Analyzer Skill 生成*
"""


def format_number(num):
    """Format number with thousands separator."""
    return f"{num:,}"


def generate_languages_table(stats):
    """Generate Markdown table for languages."""
    lines = ["| 语言 | 文件数 | 总行数 | 代码行 | 注释行 | 空白行 |",
             "|------|--------|--------|--------|--------|--------|"]

    lang_data = []
    for lang, counts in stats.get('lines_by_language', {}).items():
        lang_data.append({
            'name': lang,
            'files': stats.get('files_by_language', {}).get(lang, 0),
            'total': counts.get('total', 0),
            'code': counts.get('code', 0),
            'comments': counts.get('comments', 0),
            'blank': counts.get('blank', 0),
        })

    # Sort by total lines
    lang_data.sort(key=lambda x: x['total'], reverse=True)

    for item in lang_data[:15]:  # Top 15 languages
        lines.append(
            f"| {item['name']} | {item['files']} | {format_number(item['total'])} | "
            f"{format_number(item['code'])} | {format_number(item['comments'])} | {format_number(item['blank'])} |"
        )

    return '\n'.join(lines)


def generate_frameworks_list(stats):
    """Generate list of detected frameworks."""
    frameworks = stats.get('frameworks', [])

    if not frameworks:
        return "未检测到任何框架。"

    lines = []
    for fw in frameworks:
        lines.append(f"- **{fw.title()}**")

    return '\n'.join(lines)


def generate_file_types_table(stats):
    """Generate Markdown table for file types."""
    lines = ["| 扩展名 | 数量 | 占比 |",
             "|--------|------|------|"]

    ext_data = stats.get('files_by_extension', {})
    total = sum(ext_data.values())

    # Sort by count
    sorted_ext = sorted(ext_data.items(), key=lambda x: x[1], reverse=True)

    for ext, count in sorted_ext[:20]:  # Top 20 extensions
        percentage = (count / total * 100) if total > 0 else 0
        lines.append(f"| {ext or '(no ext)'} | {count} | {percentage:.1f}% |")

    return '\n'.join(lines)


def generate_largest_files_table(stats):
    """Generate Markdown table for largest files."""
    lines = ["| 文件路径 | 大小 (字节) | 行数 |",
             "|----------|-------------|------|"]

    for item in stats.get('largest_files', [])[:10]:
        # Truncate long paths
        path = item['path']
        if len(path) > 50:
            path = '...' + path[-47:]
        lines.append(f"| `{path}` | {format_number(item['size'])} | {format_number(item['lines'])} |")

    return '\n'.join(lines)


def generate_code_distribution(stats):
    """Generate ASCII bar chart for code distribution."""
    lines_data = stats.get('lines_by_language', {})
    total_code = stats.get('code_lines', 1)

    lines = ["```"]

    sorted_langs = sorted(lines_data.items(), key=lambda x: x[1].get('code', 0), reverse=True)

    for lang, counts in sorted_langs[:10]:
        code = counts.get('code', 0)
        if code == 0:
            continue
        percentage = (code / total_code * 100) if total_code > 0 else 0
        bar_length = int(percentage / 2)  # Max 50 chars
        bar = '█' * bar_length
        lines.append(f"{lang:<15} |{bar:<50} {percentage:>5.1f}%")

    lines.append("```")
    return '\n'.join(lines)


def generate_report(analysis_path, output_path=None, template_path=None):
    """Generate a Markdown report from analysis results."""
    analysis_path = Path(analysis_path)

    if not analysis_path.exists():
        print(f"错误：分析文件未找到：{analysis_path}")
        sys.exit(1)

    # Load analysis data
    with open(analysis_path, 'r', encoding='utf-8') as f:
        stats = json.load(f)

    # Load template
    template = load_template(template_path)

    # Format analysis date
    try:
        analysis_date = datetime.fromisoformat(stats['analysis_date']).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        analysis_date = stats.get('analysis_date', 'Unknown')

    # Generate report content
    report = template
    report = report.replace('{{project_name}}', stats.get('project_name', 'Unknown'))
    report = report.replace('{{analysis_date}}', analysis_date)
    report = report.replace('{{project_path}}', stats.get('project_path', 'Unknown'))
    report = report.replace('{{total_files}}', format_number(stats.get('total_files', 0)))
    report = report.replace('{{total_lines}}', format_number(stats.get('total_lines', 0)))
    report = report.replace('{{code_lines}}', format_number(stats.get('code_lines', 0)))
    report = report.replace('{{comment_lines}}', format_number(stats.get('comment_lines', 0)))
    report = report.replace('{{blank_lines}}', format_number(stats.get('blank_lines', 0)))
    report = report.replace('{{languages_table}}', generate_languages_table(stats))
    report = report.replace('{{frameworks_list}}', generate_frameworks_list(stats))
    report = report.replace('{{file_types_table}}', generate_file_types_table(stats))
    report = report.replace('{{largest_files_table}}', generate_largest_files_table(stats))
    report = report.replace('{{code_distribution}}', generate_code_distribution(stats))

    # Set output path
    if output_path is None:
        script_dir = Path(__file__).parent
        output_path = script_dir.parent / 'assets' / 'project-report.md'

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"报告已生成：{output_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description='Generate project analysis report')
    parser.add_argument('--input', '-i', default=None,
                        help='Input analysis JSON file (default: assets/analysis.json)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output report file (default: assets/project-report.md)')
    parser.add_argument('--template', '-t', default=None,
                        help='Custom template file')

    args = parser.parse_args()

    # Set default input path
    if args.input is None:
        script_dir = Path(__file__).parent
        args.input = script_dir.parent / 'assets' / 'analysis.json'

    generate_report(args.input, args.output, args.template)


if __name__ == '__main__':
    main()