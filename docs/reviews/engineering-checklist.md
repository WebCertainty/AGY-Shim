---
name: review
description: >-
  Performs a rigorous code review of the active diff or branch. Checks for completeness
  gaps, resource leaks, race conditions, and overcomplexity, suggesting auto-fixes.
---

# Staff Engineer Code Review Skill

Use this skill to review code changes before committing, pushing, or packaging a release. The goal is to catch bugs that pass automated CI/compilation checks but fail under production conditions.

## Review Checklists

Audit the changed lines and surrounding context against the following software engineering criteria:

### 1. Completeness Gaps
*   Are there unhandled exceptions or swallowed errors?
*   Are edge cases (e.g. empty lists, null bounds, negative values, EOF) covered?
*   Are all interface methods fully implemented?

### 2. Resource & Lifetime Management
*   Are file descriptors, sockets, database handles, and subprocesses closed/released under all conditions (especially inside exception catch blocks)?
*   Are context managers (`with` statements) or `try...finally` blocks used to guarantee cleanup?

### 3. Concurrency & Race Conditions
*   Are shared state structures, stdio buffers, or files accessed concurrently from multiple threads without locks?
*   Is there potential for lock contention or deadlock?

### 4. Code Quality & Orthogonality
*   Does the diff contain "slop" (unnecessary drive-by edits, reverted modifications, commented-out dead code)?
*   Is the logic declarative and readable rather than overly complex?

## Output Format

Generate a code review report containing:
1.  **Findings:** List issues found categorised by type (Safety, Architecture, Style).
2.  **Auto-Fix Proposals:** Provide exact code modifications that resolve the issues automatically.
3.  **Open Questions:** List any architectural decisions requiring human validation.
