# 🔒 Security Quick Reference Card

## For Developers Working on This Project

### ⚡ Quick Commands

```bash
# Run security tests
pytest test_security.py -v

# Check for vulnerabilities
pip install pip-audit
pip-audit

# Generate encryption key
python -c "import secrets; print(secrets.token_hex(32))"

# Run app locally (development)
streamlit run app.py

# Run with production settings
export ENCRYPTION_KEY=your-key-here
streamlit run app.py --server.port 8501
```

### 🚫 What NOT To Do

❌ **NEVER** commit:
- `.env` files with real keys
- Test data with real PII
- User uploads or generated files
- Logs containing personal information
- API keys or secrets

❌ **NEVER** log:
- Resume content
- Names, emails, phone numbers
- LinkedIn profile data
- Job descriptions with company info
- Raw user input

❌ **NEVER** store:
- User data in files
- PII in databases without encryption
- Session data persistently

### ✅ What TO Do

✅ **ALWAYS**:
- Use `sanitize_filename()` for file names
- Use `sanitize_url()` for URLs
- Use `validate_content_safety()` for user input
- Use `anonymize_for_logging()` for logs
- Use `secure_session_cleanup()` when done
- Test with `pytest test_security.py`

✅ **Before deploying**:
- Set `ENCRYPTION_KEY` env var
- Enable HTTPS/TLS
- Run all security tests
- Update privacy notice
- Review SECURITY_DEPLOYMENT.md

### 🔍 Common Security Patterns

#### File Upload
```python
# ✅ CORRECT
filename = sanitize_filename(uploaded_file.name)
if not validate_file_extension(filename):
    return "Invalid file type"

file_bytes = uploaded_file.read()
if not validate_file_size(file_bytes, MAX_SIZE):
    return "File too large"

is_safe, error = validate_content_safety(extracted_text)
if not is_safe:
    return error
```

#### URL Handling
```python
# ✅ CORRECT
safe_url = sanitize_url(user_provided_url)
if not safe_url:
    return "Invalid URL"

try:
    response = requests.get(safe_url, timeout=10)
except Exception as e:
    log_security_event('URL_FETCH_FAILED', {...})
```

#### Logging
```python
# ❌ WRONG
logger.info(f"Processing resume: {resume_text}")

# ✅ CORRECT
logger.info(f"Processing resume: {anonymize_for_logging(resume_text)}")
# Output: Processing resume: [TEXT_LENGTH:1234_HASH:a1b2c3d4]
```

#### Session Cleanup
```python
# ✅ CORRECT - At app shutdown or timeout
secure_session_cleanup(st.session_state)
GDPRCompliance.log_data_deletion(session_id, 'timeout')
```

### 📋 Pre-Commit Checklist

Before committing code:
- [ ] No PII in code or comments
- [ ] No hardcoded secrets or keys
- [ ] Security functions used correctly
- [ ] Tests pass: `pytest test_security.py`
- [ ] No `.env` or sensitive files staged
- [ ] Logs don't contain PII
- [ ] Code reviewed for security issues

### 🧪 Testing Guidelines

```python
# Test with malicious input
def test_xss_prevention():
    malicious = "<script>alert('xss')</script>"
    is_safe, _ = validate_content_safety(malicious)
    assert is_safe == False

# Test file validation
def test_file_security():
    assert validate_file_extension("evil.exe") == False
    assert validate_file_extension("resume.pdf") == True

# Test URL security
def test_ssrf_prevention():
    assert sanitize_url("http://localhost") is None
    assert sanitize_url("https://example.com") == "https://example.com"
```

### 🔐 Environment Variables

Required for production:
```bash
ENCRYPTION_KEY=<32-byte-hex>        # REQUIRED
DPO_EMAIL=privacy@domain.com        # REQUIRED
SECURITY_EMAIL=security@domain.com  # REQUIRED
DEBUG_MODE=false                    # REQUIRED in prod
LOG_LEVEL=INFO                      # Recommended
```

### 📞 Who To Contact

| Issue | Contact |
|-------|---------|
| Security vulnerability | security@yourdomain.com |
| GDPR/Privacy question | privacy@yourdomain.com |
| Code review needed | Lead developer |
| Production deployment | DevOps team |

### 🚨 Security Incident Response

1. **Detect**: Monitor logs, user reports
2. **Assess**: Scope of breach/issue
3. **Contain**: Isolate affected systems
4. **Notify**: Users within 72 hours (GDPR)
5. **Fix**: Patch vulnerability
6. **Document**: Record all actions

### 📚 Key Files

| File | Purpose |
|------|---------|
| `security_utils.py` | Input validation, sanitization |
| `gdpr_compliance.py` | Privacy notices, consent, audit |
| `test_security.py` | Security test suite |
| `SECURITY_DEPLOYMENT.md` | Full deployment guide |
| `SECURITY_README.md` | Complete overview |
| `.env.example` | Environment template |

### 💡 Tips

- **Paranoid is good**: When handling PII, err on the side of caution
- **Test everything**: Use `test_security.py` religiously
- **Document changes**: Update security docs when changing security code
- **Keep updated**: Run `pip-audit` regularly
- **Ask questions**: Better to ask than to introduce vulnerabilities

---

**Remember**: Security and privacy are not optional. They're fundamental to user trust and legal compliance.

Print this card and keep it visible while developing! 🔒
