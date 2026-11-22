# Security Checklist

Use this list before every release. All checks run locally.

- [ ] No secrets, tokens or keys committed to the repository
- [ ] User input validated and length-limited
- [ ] SQL built with parameters, never string concatenation
- [ ] File paths normalised and confined to an allowed root
- [ ] Deserialisation limited to trusted, local sources
- [ ] Dependencies pinned and reviewed
- [ ] Errors logged without leaking sensitive values

Run `python enhancement_system/security/templates/security_scanner.py`
to get an automated first-pass report.
