---
name: cso
description: >-
  Runs a comprehensive security audit of active code changes or the active workspace.
  Applies OWASP Top 10 and STRIDE threat modeling, outputting concrete exploit scenarios
  rather than generic warnings.
---

# Chief Security Officer (CSO) Security Audit Skill

Use this skill when the user asks for a security review, before committing major architectural changes, or when handling sensitive operations (file access, network writes, subprocesses, database operations, user credentials).

## Audit Methodology

You must systematically audit the target code or active changes against the STRIDE threat model and OWASP Top 10. Do not list generic security checklists; instead, identify actual "unlocked doors" and write concrete, step-by-step exploit scenarios.

### 1. STRIDE Threat Model
*   **Spoofing:** Can an attacker masquerade as a legitimate user, command wrapper, or subprocess?
*   **Tampering:** Can an attacker modify database files (e.g., WAL SQLite databases), state configuration files, or memory parameters?
*   **Repudiation:** Can actions occur without logging or auditing trail?
*   **Information Disclosure:** Are sensitive details (session IDs, conversation logs, user profiles) exposed in logs, global paths, or shared memory?
*   **Denial of Service:** Can concurrent standard input/output writes, lock contentions, or unhandled errors block the application or cause a crash?
*   **Elevation of Privilege:** Can the child process run arbitrary code or bypass sandbox permissions?

### 2. OWASP Top 10 Web & Application Vulnerabilities
*   Check for command/query injection, broken authentication, data exposure, insecure resource loading, security misconfigurations, and vulnerable dependencies.

## Output Format

Generate a security report containing:
1.  **Vulnerability Summary:** A high-level list of identified risks categorized by severity (Critical, Medium, Low).
2.  **Exploit Scenarios:** For each vulnerability, write a brief, concrete scenario demonstrating how it could be triggered and the potential impact.
3.  **Remediation Plan:** Precise code modifications or configuration changes required to resolve the threats.
