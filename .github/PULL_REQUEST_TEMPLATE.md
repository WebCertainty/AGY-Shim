## Pull request checklist

- [ ] PR description explains the change and its rationale (link to blog post if relevant)
- [ ] Security implications considered and documented (update SECURITY.md if needed)
- [ ] Tests added or updated where applicable
- [ ] CI passes locally / in CI
- [ ] Ensure AGY_SHIM_ALLOW_BYPASS is not introduced in code or CI

### Reviewer(s)
- Add at least one security reviewer for changes touching subprocess, permissions, auth, or logging.

