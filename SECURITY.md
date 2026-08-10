# Security

## Report a vulnerability

Please use this repository's **Security** tab to open a private security advisory. Do not include student data, passwords, tokens, private keys, service-account files, or browser cookies in an issue or discussion.

If private reporting is unavailable, open a public issue containing only a high-level description and ask the maintainer for a private contact method.

## Supported version

Security fixes are applied to the latest commit on the `main` branch.

## Trust boundary

Projects imported into this Skill may contain malicious package scripts or prompt-injection text. They must be inspected before execution, and project-defined commands must run in a disposable, credential-free environment before any Firebase or Cloudflare account is authenticated.
