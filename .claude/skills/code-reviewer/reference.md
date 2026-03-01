# Code Review Reference Guide

## Security Checklist

### OWASP Top 10 Quick Reference

| Vulnerability | What to Check |
|---------------|---------------|
| Injection | SQL queries, command execution, user input handling |
| Broken Auth | Session management, password storage, MFA |
| Sensitive Data | Encryption, data exposure in logs |
| XXE | XML parser configuration |
| Broken Access | Authorization checks, IDOR |
| Security Misconfig | Default credentials, unnecessary features |
| XSS | Output encoding, CSP headers |
| Insecure Deserialization | Object validation, type checking |
| Known Vulnerabilities | Dependency versions, CVE checks |
| Logging | Sensitive data in logs, monitoring |

### Common Vulnerability Patterns

```javascript
// BAD: SQL Injection vulnerable
const query = "SELECT * FROM users WHERE id = " + userId;

// GOOD: Parameterized query
const query = "SELECT * FROM users WHERE id = ?";
db.query(query, [userId]);
```

```python
# BAD: Command injection vulnerable
os.system(f"ping {user_input}")

# GOOD: Safe subprocess call
subprocess.run(["ping", user_input], shell=False)
```

## Language-Specific Best Practices

### JavaScript/TypeScript

1. **Use `const` by default, `let` when needed, avoid `var`**
2. **Handle promises properly** - always use try/catch with async/await
3. **Validate input** - use libraries like Joi, Zod, or Yup
4. **Avoid `eval()` and `Function()`** - security risk
5. **Use strict equality `===`** - avoids type coercion bugs

### Python

1. **Use context managers** - `with open()` for file handling
2. **Follow PEP 8** - consistent style
3. **Use type hints** - improves readability and IDE support
4. **Handle exceptions specifically** - don't use bare `except:`
5. **Use f-strings** - cleaner string formatting

### Go

1. **Always check errors** - Go doesn't have exceptions
2. **Defer close operations** - ensure cleanup
3. **Use interfaces for flexibility** - small interfaces
4. **Goroutine safety** - protect shared state with mutexes
5. **Context for cancellation** - propagate context

## Code Quality Indicators

### Readability
- Clear variable/function names
- Consistent formatting
- Appropriate comments (why, not what)
- Single responsibility principle

### Maintainability
- DRY (Don't Repeat Yourself)
- SOLID principles
- Dependency injection
- Test coverage

### Performance
- Avoid premature optimization
- Choose appropriate data structures
- Consider time/space complexity
- Profile before optimizing

## Review Checklist Template

```markdown
## Code Review Checklist

### Functionality
- [ ] Does the code do what it's supposed to do?
- [ ] Are edge cases handled?
- [ ] Is error handling appropriate?

### Security
- [ ] Input validation present?
- [ ] Authentication/authorization correct?
- [ ] No sensitive data exposed?

### Quality
- [ ] Code is readable?
- [ ] Naming is clear?
- [ ] No code duplication?
- [ ] Functions are focused?

### Testing
- [ ] Unit tests exist?
- [ ] Tests cover edge cases?
- [ ] Integration tests if needed?

### Documentation
- [ ] Public APIs documented?
- [ ] Complex logic explained?
- [ ] README updated if needed?
```

## Severity Classification

| Level | Description | Action |
|-------|-------------|--------|
| Critical | Security vulnerability or crash bug | Must fix before merge |
| Warning | Code quality issue or potential bug | Should fix before merge |
| Suggestion | Improvement opportunity | Consider for future PRs |
| Info | Educational note | No action required |