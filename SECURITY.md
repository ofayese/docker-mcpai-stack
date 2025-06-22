# Security Policy

## Reporting a Vulnerability

We take the security of docker-mcpai-stack seriously. If you believe you've found a security vulnerability, please follow these steps:

1. **Do not disclose the vulnerability publicly**
2. **Email us at <security@example.com>** with details about the vulnerability
3. **Include the following information**:
   - Type of issue
   - Location of the affected source code (URL or file)
   - Any special configuration required to reproduce the issue
   - Step-by-step instructions to reproduce the issue
   - Impact of the issue, including how an attacker might exploit it

We will acknowledge receipt of your vulnerability report within 48 hours and send a more detailed response within 72 hours indicating the next steps in handling your report.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Updates

Security updates will be released as part of our regular release cycle or as emergency patches depending on severity.

## Security Measures

- All containers run as non-root users
- Vulnerability scanning with Trivy in CI/CD pipeline
- Software Bill of Materials (SBOM) generated for all releases
- Regular dependency updates with Renovate
- Docker Scout policy checks
