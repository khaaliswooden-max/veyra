# Security Policy

## Reporting a Vulnerability

We take the security of Veyra seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please email: **security@zuup.org**

Include the following in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

| Timeline | Action |
|----------|--------|
| 24 hours | Acknowledgment of report |
| 72 hours | Initial assessment |
| 7 days | Detailed response with remediation plan |
| 90 days | Public disclosure (coordinated) |

### Scope

The following are in scope:
- Veyra core library (`src/veyra/`)
- Model backend integrations
- Audit trail integrity
- Safety boundary bypasses
- Authentication/authorization flaws
- Data exposure vulnerabilities

The following are **out of scope**:
- Third-party dependencies (report to upstream)
- Social engineering attacks
- Physical attacks
- Denial of service

### Safe Harbor

We will not pursue legal action against security researchers who:
- Act in good faith
- Avoid privacy violations
- Avoid data destruction
- Report vulnerabilities responsibly
- Give us reasonable time to respond

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Security Best Practices

When deploying Veyra:

1. **API Keys**: Never commit API keys. Use environment variables or secret managers.
2. **Audit Logs**: Enable audit logging in production (`governance.audit_enabled: true`).
3. **Safety Boundaries**: Keep safety boundaries enabled unless you have specific reason to disable.
4. **Network**: Run behind a reverse proxy with TLS in production.
5. **Dependencies**: Regularly update dependencies (`pip-audit`, `safety check`).

## Security Features

Veyra includes several security features:

| Feature | Description | Config |
|---------|-------------|--------|
| Audit Trail | Hash-chained, tamper-evident logging | `governance.audit_enabled` |
| Safety Boundaries | Pattern-based operation filtering | `governance.safety_boundaries` |
| Reversible-Only Mode | Restrict to reversible operations | `governance.reversible_only` |
| Input Hashing | Privacy-preserving audit logs | Automatic |

## Acknowledgments

We thank the following individuals for responsibly disclosing vulnerabilities:

- (No reports yet)

---

*Last updated: December 2024*
