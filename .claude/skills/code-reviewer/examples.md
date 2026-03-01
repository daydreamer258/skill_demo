# Code Reviewer Skill - 触发示例

## 示例 1: 基础代码审查

### 触发词
```
review this code
代码审查
检查这段代码
```

### 预期行为
skill 会被激活，对指定代码进行全面的代码审查，包括：
- 代码质量分析
- 安全漏洞检查
- 性能建议
- 最佳实践建议

### 示例交互
```
用户: review the login function in auth.js

Claude: [激活 code-reviewer skill]

## Code Review Summary

### Overview
Reviewed `login` function in auth.js - handles user authentication.

### Issues Found

#### Warning
- Password comparison using `===` instead of timing-safe comparison
- Missing rate limiting on login attempts

#### Suggestion
- Consider adding MFA support
- Add logging for failed attempts

### Positive Highlights
- Good use of parameterized queries
- Proper error message sanitization
```

---

## 示例 2: 安全焦点审查

### 触发词
```
security review
安全审查
check for vulnerabilities
漏洞检查
```

### 预期行为
skill 会专注于安全方面的审查，特别关注：
- OWASP Top 10 漏洞
- 输入验证
- 认证授权问题
- 敏感数据处理

### 示例交互
```
用户: security review the user input handling

Claude: [激活 code-reviewer skill，安全焦点模式]

## Security Review Report

### Critical
- SQL Injection vulnerability in search function
  ```javascript
  // VULNERABLE:
  const query = `SELECT * FROM products WHERE name LIKE '%${searchTerm}%'`;

  // FIXED:
  const query = `SELECT * FROM products WHERE name LIKE ?`;
  db.query(query, [`%${searchTerm}%`]);
  ```

### Warning
- Missing CSRF token validation on POST requests

### Recommendations
1. Implement input validation layer
2. Add Content Security Policy headers
3. Enable rate limiting
```

---

## 示例 3: PR 审查

### 触发词
```
pr review
review pull request
PR 代码审查
```

### 预期行为
skill 会分析 PR 中的所有变更，提供综合审查意见。

### 示例交互
```
用户: pr review the changes in src/api/

Claude: [激活 code-reviewer skill]

## Pull Request Review

### Files Changed: 5
- src/api/users.js (modified)
- src/api/auth.js (modified)
- src/api/products.js (new)
- src/utils/validation.js (modified)
- tests/api.test.js (new)

### Summary
The PR adds product management API endpoints and improves validation.

### Blocking Issues
None

### Required Changes
- Add input validation to POST /products
- Missing error handling in async function

### Suggestions
- Consider adding API rate limiting
- Add integration tests for new endpoints

### Verdict
✅ Approve with minor suggestions
```

---

## 示例 4: 性能审查

### 触发词
```
performance review
性能分析
check performance issues
```

### 预期行为
skill 会专注于性能问题的识别和优化建议。

### 示例交互
```
用户: check performance issues in data processing loop

Claude: [激活 code-reviewer skill，性能焦点]

## Performance Review

### Issues Found

#### Critical
- N+1 query problem in user data fetching
  ```javascript
  // CURRENT: O(n) database calls
  for (const user of users) {
    const profile = await db.getProfile(user.id);
  }

  // RECOMMENDED: Batch fetch
  const profiles = await db.getProfiles(users.map(u => u.id));
  ```

#### Warning
- Synchronous file operation in async context
- Unnecessary array re-creation in loop

### Optimization Suggestions
1. Use streaming for large file processing
2. Add caching layer for frequently accessed data
3. Consider using worker threads for CPU-intensive tasks
```

---

## 示例 5: 最佳实践审查

### 触发词
```
code quality check
best practices review
代码质量检查
```

### 预期行为
skill 会检查代码是否符合最佳实践和编码规范。

### 示例交互
```
用户: check if this code follows best practices

Claude: [激活 code-reviewer skill]

## Best Practices Review

### Code Style
✅ Consistent naming conventions
⚠️ Mixed use of var/let/const - prefer const by default
⚠️ Missing JSDoc comments for public functions

### Design Patterns
✅ Good use of dependency injection
⚠️ Consider using Repository pattern for data access
💡 Suggestion: Implement Factory pattern for object creation

### Error Handling
❌ Bare catch block - should handle specific errors
❌ Missing input validation

### Testing
⚠️ No unit tests found for this module

### Recommendations
1. Add comprehensive unit tests (aim for 80%+ coverage)
2. Implement proper error types
3. Add input validation with a library like Zod
4. Document public API with JSDoc
```

---

## 触发词完整列表

| 触发词 (英文) | 触发词 (中文) | 审查重点 |
|--------------|---------------|---------|
| `code review` | `代码审查` | 全面审查 |
| `review code` | `代码评审` | 全面审查 |
| `check code` | `检查代码` | 全面审查 |
| `security review` | `安全审查` | 安全焦点 |
| `vulnerability check` | `漏洞检查` | 安全焦点 |
| `performance review` | `性能分析` | 性能焦点 |
| `pr review` | `PR 审查` | 变更审查 |
| `code quality` | `代码质量` | 最佳实践 |
| `analyze code` | `分析代码` | 全面分析 |