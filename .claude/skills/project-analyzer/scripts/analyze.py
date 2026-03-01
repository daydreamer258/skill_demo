#!/usr/bin/env python3
"""
Project Analyzer Script

Analyzes project structure, counts code lines, and identifies technology stack.
Outputs results as JSON for further processing.

Usage:
    python analyze.py [project_path] [--output output.json]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime


# File extensions to language mapping
LANGUAGE_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript (React)',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript (React)',
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.go': 'Go',
    '.rs': 'Rust',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.cs': 'C#',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.m': 'Objective-C',
    '.scala': 'Scala',
    '.r': 'R',
    '.lua': 'Lua',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.zsh': 'Shell',
    '.ps1': 'PowerShell',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.less': 'Less',
    '.sass': 'Sass',
    '.vue': 'Vue',
    '.svelte': 'Svelte',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.xml': 'XML',
    '.sql': 'SQL',
    '.md': 'Markdown',
    '.rst': 'reStructuredText',
    '.tex': 'LaTeX',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.cfg': 'Config',
    '.env': 'Environment',
    '.gitignore': 'Git Ignore',
    '.dockerignore': 'Docker Ignore',
    'Dockerfile': 'Dockerfile',
    'Makefile': 'Makefile',
}

# Framework indicators
FRAMEWORK_INDICATORS = {
    'react': ['package.json', 'react', 'react-dom'],
    'vue': ['package.json', 'vue'],
    'angular': ['package.json', '@angular'],
    'svelte': ['package.json', 'svelte'],
    'next.js': ['package.json', 'next'],
    'nuxt.js': ['package.json', 'nuxt'],
    'express': ['package.json', 'express'],
    'fastapi': ['requirements.txt', 'fastapi'],
    'django': ['requirements.txt', 'django', 'settings.py'],
    'flask': ['requirements.txt', 'flask'],
    'spring': ['pom.xml', 'build.gradle'],
    'rails': ['Gemfile', 'rails'],
    'laravel': ['composer.json', 'laravel'],
    'dotnet': ['.csproj', '.sln'],
}


def count_lines(file_path):
    """Count lines in a file, categorizing code, comments, and blank lines."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return {'total': 0, 'code': 0, 'comments': 0, 'blank': 0}

    lines = content.split('\n')
    total = len(lines)
    blank = 0
    comments = 0
    code = 0

    ext = file_path.suffix.lower()
    in_multiline_comment = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            blank += 1
            continue

        # Python comments
        if ext == '.py':
            if stripped.startswith('#'):
                comments += 1
                continue
            if '"""' in stripped or "'''" in stripped:
                in_multiline_comment = not in_multiline_comment
                comments += 1
                continue

        # JavaScript/TypeScript/C/C++ comments
        elif ext in ['.js', '.jsx', '.ts', '.tsx', '.c', '.cpp', '.h', '.hpp', '.java', '.kt']:
            if stripped.startswith('//'):
                comments += 1
                continue
            if stripped.startswith('/*') or stripped.endswith('*/'):
                comments += 1
                continue

        # Shell comments
        elif ext in ['.sh', '.bash', '.zsh']:
            if stripped.startswith('#'):
                comments += 1
                continue

        code += 1

    return {'total': total, 'code': code, 'comments': comments, 'blank': blank}


def get_language(file_path):
    """Determine the language of a file based on its extension."""
    name = file_path.name
    ext = file_path.suffix.lower()

    if name in LANGUAGE_MAP:
        return LANGUAGE_MAP[name]
    if ext in LANGUAGE_MAP:
        return LANGUAGE_MAP[ext]
    return 'Unknown'


def should_analyze(file_path, exclude_dirs=None):
    """Determine if a file should be analyzed."""
    exclude_dirs = exclude_dirs or ['node_modules', 'venv', '__pycache__', '.git', 'dist', 'build', 'target']

    # Check if any excluded directory is in the path
    for part in file_path.parts:
        if part in exclude_dirs:
            return False

    # Skip binary files and common non-code files
    binary_extensions = {
        '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe', '.bin',
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp',
        '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
    }

    if file_path.suffix.lower() in binary_extensions:
        return False

    return True


def detect_frameworks(project_path):
    """Detect frameworks used in the project."""
    frameworks = []
    project_path = Path(project_path)

    for framework, indicators in FRAMEWORK_INDICATORS.items():
        detected = False

        for indicator in indicators:
            # Check for file existence
            if not indicator.startswith('.'):
                if (project_path / indicator).exists() or (project_path / 'src' / indicator).exists():
                    detected = True
                    break

            # Check for dependency in package.json
            if indicator == 'package.json':
                pkg_path = project_path / 'package.json'
                if pkg_path.exists():
                    try:
                        with open(pkg_path, 'r', encoding='utf-8') as f:
                            pkg = json.load(f)
                            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                            for dep in indicators[1:]:
                                if any(dep.lower() in d.lower() for d in deps.keys()):
                                    detected = True
                                    break
                    except Exception:
                        pass

            # Check for dependency in requirements.txt
            if indicator == 'requirements.txt':
                req_path = project_path / 'requirements.txt'
                if req_path.exists():
                    try:
                        with open(req_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            for req in indicators[1:]:
                                if req in content:
                                    detected = True
                                    break
                    except Exception:
                        pass

        if detected:
            frameworks.append(framework)

    return frameworks


def analyze_project(project_path, output_path=None):
    """Analyze a project and return statistics."""
    project_path = Path(project_path).resolve()

    if not project_path.exists():
        print(f"错误：路径 '{project_path}' 不存在")
        sys.exit(1)

    print(f"正在分析项目：{project_path}")

    stats = {
        'project_name': project_path.name,
        'project_path': str(project_path),
        'analysis_date': datetime.now().isoformat(),
        'total_files': 0,
        'total_directories': 0,
        'total_lines': 0,
        'code_lines': 0,
        'comment_lines': 0,
        'blank_lines': 0,
        'files_by_extension': defaultdict(int),
        'files_by_language': defaultdict(int),
        'lines_by_language': defaultdict(lambda: {'total': 0, 'code': 0, 'comments': 0, 'blank': 0}),
        'directory_structure': [],
        'largest_files': [],
        'frameworks': [],
        'languages': [],
    }

    # Collect all files
    all_files = []
    for root, dirs, files in os.walk(project_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', 'venv', '__pycache__', '.git', 'dist', 'build', 'target']]

        stats['total_directories'] += len(dirs)

        for file in files:
            file_path = Path(root) / file
            if should_analyze(file_path):
                all_files.append(file_path)

    stats['total_files'] = len(all_files)

    # Analyze each file
    file_sizes = []

    for file_path in all_files:
        try:
            ext = file_path.suffix.lower() or '.no_extension'
            language = get_language(file_path)

            stats['files_by_extension'][ext] += 1
            stats['files_by_language'][language] += 1

            lines = count_lines(file_path)
            stats['total_lines'] += lines['total']
            stats['code_lines'] += lines['code']
            stats['comment_lines'] += lines['comments']
            stats['blank_lines'] += lines['blank']

            stats['lines_by_language'][language]['total'] += lines['total']
            stats['lines_by_language'][language]['code'] += lines['code']
            stats['lines_by_language'][language]['comments'] += lines['comments']
            stats['lines_by_language'][language]['blank'] += lines['blank']

            # Track file sizes
            file_size = file_path.stat().st_size
            file_sizes.append({
                'path': str(file_path.relative_to(project_path)),
                'lines': lines['total'],
                'size': file_size,
            })

        except Exception as e:
            print(f"警告：无法分析 {file_path}：{e}")

    # Sort largest files
    file_sizes.sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = file_sizes[:10]

    # Detect frameworks
    stats['frameworks'] = detect_frameworks(project_path)

    # Get top languages
    lang_counts = sorted(stats['files_by_language'].items(), key=lambda x: x[1], reverse=True)
    stats['languages'] = [{'name': name, 'files': count} for name, count in lang_counts[:10]]

    # Convert defaultdicts to regular dicts for JSON serialization
    stats['files_by_extension'] = dict(stats['files_by_extension'])
    stats['files_by_language'] = dict(stats['files_by_language'])
    stats['lines_by_language'] = dict(stats['lines_by_language'])

    # Set output path
    if output_path is None:
        script_dir = Path(__file__).parent
        output_path = script_dir.parent / 'assets' / 'analysis.json'

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\n分析完成！")
    print(f"  文件总数：{stats['total_files']}")
    print(f"  代码总行数：{stats['total_lines']:,}")
    print(f"  有效代码行：{stats['code_lines']:,}")
    print(f"  检测到的语言数：{len(stats['languages'])}")
    print(f"  检测到的框架：{', '.join(stats['frameworks']) or '无'}")
    print(f"\n结果已保存至：{output_path}")

    return stats


def main():
    parser = argparse.ArgumentParser(description='Analyze project structure and code statistics')
    parser.add_argument('project_path', nargs='?', default='.', help='Path to the project to analyze')
    parser.add_argument('--output', '-o', help='Output JSON file path')

    args = parser.parse_args()

    analyze_project(args.project_path, args.output)


if __name__ == '__main__':
    main()