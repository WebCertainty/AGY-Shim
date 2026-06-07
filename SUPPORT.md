# Support

> **TL;DR:** This is a limited-maintenance evaluation project with no
> compatibility or response-time guarantees.

AGY-Shim is maintained primarily for the author's own workflow and is shared
as-is for evaluation and reuse.

There are no guarantees of:

- compatibility with future Antigravity, ACP, or Clairvoyance versions;
- a release schedule or long-term maintenance;
- feature development;
- support response times;
- suitability for production or sensitive workloads.

Bug reports and focused pull requests are welcome and may be reviewed as time
permits. General questions can be sent to
[hello@webcertainty.com.au](mailto:hello@webcertainty.com.au).

Do not send vulnerability details through a public issue. Follow
[SECURITY.md](SECURITY.md) for private security reporting.

## Provider Controls

Do not use a host application's Sign In, Auth, Update, Reinstall, or Install
controls for the provider identity used by AGY-Shim. Those actions target the
genuine provider CLI lifecycle, not the shim. Manage Antigravity authentication
and updates separately and update AGY-Shim from this repository.
