# 项目分析检查清单

此检查清单用于指导全面的项目评估分析过程。

## 分析前准备

- [ ] 识别项目类型（Web应用、库、CLI工具等）
- [ ] 确定主要编程语言
- [ ] 检查版本控制（git、svn等）
- [ ] 识别构建系统（npm、pip、gradle、maven等）

## 目录结构分析

### 标准目录检查

| 目录 | 用途 |
|------|------|
| `src/` | 源代码 |
| `lib/` | 库代码 |
| `test/` 或 `tests/` | 测试文件 |
| `docs/` | 文档 |
| `config/` | 配置文件 |
| `public/` 或 `static/` | 静态资源 |
| `scripts/` | 构建/工具脚本 |
| `assets/` | 图片、字体等 |

### 结构特征识别

- **Monorepo**：子目录中存在多个 `package.json` 或 `Cargo.toml`
- **微服务**：多个独立的服务目录
- **模块化**：按功能/模块清晰分离
- **扁平结构**：最小的目录嵌套

## 技术栈识别

### JavaScript/TypeScript 项目

| 文件 | 表明 |
|------|------|
| `package.json` | Node.js 项目 |
| `tsconfig.json` | TypeScript |
| `next.config.js` | Next.js |
| `nuxt.config.js` | Nuxt.js |
| `vue.config.js` | Vue CLI |
| `angular.json` | Angular |
| `gatsby-config.js` | Gatsby |
| `vite.config.*` | Vite 打包器 |
| `webpack.config.*` | Webpack 打包器 |

### Python 项目

| 文件 | 表明 |
|------|------|
| `requirements.txt` | pip 依赖 |
| `setup.py` | 包分发 |
| `pyproject.toml` | 现代Python项目 |
| `Pipfile` | Pipenv |
| `poetry.lock` | Poetry |
| `manage.py` | Django |
| `wsgi.py` / `asgi.py` | Web应用 |

### 其他语言

| 文件模式 | 语言/框架 |
|----------|-----------|
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `pom.xml` | Java (Maven) |
| `build.gradle` | Java/Kotlin (Gradle) |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `.csproj` | C#/.NET |
| `Package.swift` | Swift |

## 代码指标

### 行数阈值

| 指标 | 小型 | 中型 | 大型 |
|------|------|------|------|
| 总行数 | < 10K | 10K-100K | > 100K |
| 文件数 | < 100 | 100-500 | > 500 |
| 目录数 | < 20 | 20-100 | > 100 |

### 质量指标

- **注释率**：注释行 / 总行数
  - 良好：> 10%
  - 可接受：5-10%
  - 需改进：< 5%

- **平均文件大小**：总行数 / 文件数
  - 良好：< 300行
  - 可接受：300-500行
  - 需审查：> 500行

- **目录深度**：最大嵌套层级
  - 良好：< 4层
  - 可接受：4-6层
  - 建议重构：> 6层

## 依赖分析

### 安全检查

- [ ] 扫描已知漏洞
- [ ] 检查过时的包
- [ ] 识别未使用的依赖
- [ ] 检查依赖许可证兼容性

### 依赖数量指南

| 项目规模 | 运行依赖 | 开发依赖 |
|----------|----------|----------|
| 小型 | < 10 | < 20 |
| 中型 | 10-30 | 20-50 |
| 大型 | 30-50 | 50-100 |

## 文档评估

### 检查文件

- [ ] README.md 存在且内容充实
- [ ] CHANGELOG.md 或 HISTORY.md
- [ ] CONTRIBUTING.md
- [ ] LICENSE 文件
- [ ] API 文档
- [ ] 内联代码注释
- [ ] 类型定义（TypeScript、Python类型提示）

## 测试覆盖

### 测试文件模式

- `*.test.js`, `*.spec.js` - JavaScript
- `*_test.go` - Go
- `test_*.py` - Python
- `*_test.cpp` - C++

### 覆盖率阈值

| 覆盖率 | 评估 |
|--------|------|
| > 80% | 优秀 |
| 60-80% | 良好 |
| 40-60% | 可接受 |
| < 40% | 需改进 |

## CI/CD 检测

### 配置文件

- `.github/workflows/` - GitHub Actions
- `.gitlab-ci.yml` - GitLab CI
- `.circleci/` - CircleCI
- `Jenkinsfile` - Jenkins
- `.travis.yml` - Travis CI
- `azure-pipelines.yml` - Azure Pipelines

## 容器化

### 查找内容

- `Dockerfile` - Docker 容器
- `docker-compose.yml` - Docker Compose
- `.dockerignore` - Docker 忽略规则
- `helm/` - Kubernetes Helm charts
- `k8s/` 或 `kubernetes/` - Kubernetes 清单

## 环境配置

### 配置文件

- `.env.example` - 环境变量模板
- `.env` - 本地环境变量（应被 gitignore）
- `config/` - 配置目录
- 不同环境的多个配置文件

## 分析输出格式

分析应产出：

1. **摘要统计**（JSON格式）
2. **技术栈报告**（人类可读）
3. **建议**（基于发现）
4. **可视化**（可选图表/图形）

## 常见反模式标记

- [ ] 大文件（> 1000行）
- [ ] 深层嵌套（> 4层）
- [ ] 循环依赖
- [ ] 同一目录混合多种语言
- [ ] 缺少测试文件
- [ ] 硬编码凭据
- [ ] 版本控制中的二进制文件
- [ ] 缺失或简陋的 README
- [ ] 无许可证文件