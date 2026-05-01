# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in WasteWisely, please follow responsible disclosure:

1. **DO NOT** open a public GitHub issue for security vulnerabilities.
2. Report via [GitHub Security Advisory](https://github.com/Caliquende/WasteWisely/security/advisories/new).
3. Include a detailed description, steps to reproduce, and any potential impact.
4. We will acknowledge your report within 48 hours and aim to provide a fix within 7 days.

## Security Best Practices

- **Environment Variables:** Never commit `.env` files or credentials to the repository.
- **Dependencies:** All dependencies are monitored via Dependabot for known vulnerabilities.
- **Static Analysis:** Bandit SAST scans run on every push and pull request.
- **Dependency Auditing:** pip-audit checks installed packages against the CVE database.
