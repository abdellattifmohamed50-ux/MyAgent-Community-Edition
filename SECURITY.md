# Security Policy

## Supported version

Security fixes are applied to the current `3.x` Community Edition line. Older
`1.x` and `2.x` snapshots are engineering references and are not supported.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use the repository's
private security-advisory workflow and include:

- affected version and deployment mode;
- reproduction steps or a minimal proof of concept;
- expected impact and required privileges;
- logs with secrets and personal data removed;
- any proposed mitigation.

Maintainers should acknowledge a complete report within five business days.
Disclosure timing is coordinated after validation and a fix or mitigation is
available.

## Security boundaries

Community Edition provides application-level controls, not a complete hosting
security platform. Production operators remain responsible for TLS termination,
network policy, backups, secret storage, database hardening, patching, and log
retention. Never commit `.env` files, provider keys, JWT secrets, database
passwords, or exported user data.

See `docs/SECURITY.md` and `docs/audits/SECURITY_AUDIT.md` for implementation
details and the latest audit evidence.
