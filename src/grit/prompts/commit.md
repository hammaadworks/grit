---
name: commit-message-storyteller
description: 'Analyzes git diffs or staged changes and generates narrative commit messages that explain WHY a change was made, not just what changed — following Conventional Commits format. Use when asked to "write a commit message", "generate a commit", "describe my changes", "what should I commit this as", "commit this", "summarize my diff", or "help me commit". Works with git diff output, staged files, or plain descriptions of changes.'
---

# Commit Message Storyteller

Transforms raw git diffs and change descriptions into clear, story-driven commit messages that follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. Instead of "update file.js", you get messages that communicate intent, context, and impact.

## When to Use This Skill

- User says "write a commit message", "help me commit", or "generate a commit"
- User pastes a git diff or describes code changes
- User says "what should I commit this as?" or "summarize my diff"
- User wants better commit history for their team or open-source project
- User is preparing a pull request and wants meaningful commit messages

## Prerequisites

Have at least one of the following ready:
- Output from `git diff` or `git diff --staged`
- A description of what you changed and why
- A list of modified files

## How It Works

### Step 1: Gather the Change Context

Ask the user (or infer from the diff) for:

1. **What changed** — files, functions, logic affected
2. **Why it changed** — bug fix, new feature, refactor, performance, etc.
3. **Who/what triggered it** — issue number, user request, tech debt, etc.

If the user provides a raw `git diff`, extract this context automatically from the diff.

### Step 2: Identify the Commit Type

Map the change to a Conventional Commits type using this guide:

| Type | Use When |
|------|----------|
| `feat` | A new feature or capability is added |
| `fix` | A bug or incorrect behavior is corrected |
| `refactor` | Code restructured without changing behavior |
| `perf` | A change that improves performance |
| `docs` | Documentation only changes |
| `style` | Formatting, whitespace, missing semicolons (no logic change) |
| `test` | Adding or updating tests |
| `chore` | Build process, dependency updates, config changes |
| `ci` | CI/CD pipeline changes |
| `revert` | Reverting a previous commit |

See `references/conventional-commits-guide.md` for detailed examples.

### Step 3: Write the Commit Message

Follow this structure:

```
<type>(<optional scope>): <short imperative summary>

<body — the story: why this change was made, what problem it solves>

<footer — issue refs, breaking change notices>
```

#### Rules for Each Part

**Subject line (first line):**
- Use imperative mood: "add", "fix", "remove" — not "added" or "fixes"
- Max 72 characters
- No period at the end
- Lowercase after the colon

**Body (the story):**
- Explain the *why*, not the *what* (the diff already shows the what)
- Describe the problem that existed before this change
- Mention any alternatives considered if relevant
- Keep lines under 100 characters
- Separate from subject with a blank line

**Footer:**
- Reference issues: `Closes #123`, `Fixes #456`, `Refs #789`
- Mark breaking changes: `BREAKING CHANGE: <description>`

### Step 4: Generate Output

Produce the commit message in a copyable code block, followed by a one-line plain-English explanation of the story you told.

**Example output:**

```
fix(auth): prevent token refresh loop on expired sessions

When a user's session expired mid-request, the auth middleware was
triggering a token refresh, which itself failed validation and triggered
another refresh — causing an infinite retry loop that crashed the app.

This adds a recursion guard flag that aborts the refresh cycle if a
refresh is already in progress, returning a clean 401 instead.

Closes #312
```

> **Story told:** A silent infinite loop on session expiry was crashing the app; this stops the cycle early and returns a clean error.

---

## Multiple Commits from One Diff

If the diff contains **logically separate changes**, split them into multiple commit messages and tell the user. Use this heuristic:

- Different files with unrelated purposes → likely separate commits
- Same file but distinct concerns (e.g., bug fix + refactor) → suggest splitting
- Everything tightly coupled → one commit is fine

---

## Edge Cases

| Situation | How to Handle |
|-----------|---------------|
| User provides no context beyond a diff | Infer type and scope from file names and changed symbols |
| Changes span many files with no clear theme | Ask: "Is this one logical change, or multiple?" |
| Breaking change detected | Add `BREAKING CHANGE:` footer automatically |
| User says "keep it short" | Omit body, just write a strong subject line |
| No issue number available | Omit the footer entirely |

---

## Quick Reference

```bash
# Get your staged diff to paste into Copilot
git diff --staged

# Or get the last uncommitted working tree changes
git diff
```

See `references/conventional-commits-guide.md` for type examples and scope guidelines.
# Conventional Commits — Quick Reference Guide

Full spec: https://www.conventionalcommits.org/en/v1.0.0/

---

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

---

## Type Examples

### `feat` — New Feature
```
feat(payments): add Apple Pay support for checkout flow

Users in supported regions can now complete purchases using Apple Pay.
This reduces checkout friction and is expected to improve mobile conversion rates.

Closes #88
```

### `fix` — Bug Fix
```
fix(api): correct off-by-one error in pagination offset

The results page was skipping the last item on every page because the
offset calculation used `>` instead of `>=`. Users were missing records
silently with no error.

Fixes #201
```

### `refactor` — Code Restructure (no behavior change)
```
refactor(user-service): extract email validation into shared utility

Email validation logic was duplicated across 4 modules. Extracted into
`utils/validators.ts` so future changes only need to happen in one place.
```

### `perf` — Performance Improvement
```
perf(dashboard): lazy-load chart components to reduce initial bundle size

The dashboard was importing all chart types upfront, adding ~180KB to the
initial load. Charts are now loaded on demand, cutting initial load time
by ~40% on slow connections.
```

### `docs` — Documentation Only
```
docs(readme): add local development setup instructions

New contributors were struggling to get the dev environment running.
Added step-by-step instructions covering Node version, env vars, and
the database seed command.
```

### `test` — Tests Added or Updated
```
test(auth): add coverage for concurrent login edge cases

The login flow had no tests for simultaneous requests from the same
session. Added tests that verify only one session token is issued
when multiple requests arrive in the same tick.
```

### `chore` — Maintenance / Config
```
chore(deps): upgrade eslint from v8 to v9

v8 reached end-of-life. Migrated config to flat config format required
by v9. No rule changes — this is a tooling-only update.
```

### `ci` — CI/CD Pipeline
```
ci: add caching for node_modules in GitHub Actions

Cold CI runs were taking 4+ minutes due to repeated installs.
Adding cache restore on lockfile hash reduces this to ~90 seconds.
```

### `revert` — Reverting a Commit
```
revert: feat(notifications): add push notification opt-in

Reverts commit a3f92bc.

The push notification feature caused a crash on Android 12 devices.
Rolling back until the root cause is identified.
```

---

## Scope Guidelines

The `scope` is optional but strongly recommended. It should be:
- A short noun identifying the area of the codebase: `auth`, `api`, `dashboard`, `payments`
- Consistent across the project (don't mix `user` and `users`)
- Omitted if the change is truly global

---

## Breaking Changes

Add `BREAKING CHANGE:` in the footer (or use `!` after the type):

```
feat(api)!: remove v1 endpoints

All v1 REST endpoints have been removed following the 6-month deprecation
notice. Consumers must migrate to v2 before upgrading.

BREAKING CHANGE: /api/v1/* routes no longer exist. See migration guide at docs/v2-migration.md
```

---

## Body Writing Tips

Ask yourself before writing the body:
- **What was broken / missing before this change?**
- **Why was this approach chosen over alternatives?**
- **What will be different for users or developers after this?**

Avoid:
- Restating what the diff already shows ("changed the variable name")
- Vague language ("various improvements", "miscellaneous fixes")
- Future tense ("this will fix...") — write in present/past tense

---

## Commit Message Anti-Patterns

| ❌ Bad | ✅ Better |
|--------|----------|
| `fix bug` | `fix(cart): prevent duplicate items on rapid add-to-cart clicks` |
| `updates` | `feat(profile): allow users to update display name` |
| `WIP` | Don't commit WIP — stash it |
| `misc changes` | Split into separate, meaningful commits |
| `John's changes` | Describe what changed, not who changed it |
---
name: commit-changes
description: Create a git commit for the current changes. Use when asked to commit changes, make a commit, generate a commit message, or commit the current worktree with optional user-provided context.
---

# Commit changes

Create a focused git commit for the current changes.

## Workflow

1. Gather context:
   - User notes, if provided.
   - Current branch: `git branch --show-current`.
   - Working tree: `git status --short`.
   - Staged changes: `git diff --cached --stat`.
   - Unstaged changes: `git diff --stat`.
   - Recent commits for style reference: `git log -5 --oneline`.
2. Review the changed files.
3. If there are no changes to commit, tell the user and stop.
4. If there are unstaged changes, stage the relevant files with `git add`.
5. Do not stage files that look like secrets, credentials, API keys, or private environment files.
6. Write a conventional commit message:

```text
type(scope): brief description

Optional longer explanation if the changes are complex.
```

Allowed types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `style`, `build`, `ci`.

## Message guidelines

- Keep the first line under 72 characters.
- Use imperative mood, for example `add feature`, not `added feature`.
- Be specific about what changed and why.
- Incorporate user-provided context when it clarifies intent.

## Commit rules

- Use `git commit -m "message"`.
- Do not push.
- Do not amend unless explicitly requested.
- Do not use `--no-verify`.
- Do not include AI attribution.

If the commit fails because of hooks, fix mechanical formatting, lint, or import issues and retry. If the hook failure reveals a meaningful product or implementation issue, stop and ask the user how to proceed.---
name: caveman-commit
description: >
  Ultra-compressed commit message generator. Cuts noise from commit messages while preserving
  intent and reasoning. Conventional Commits format. Subject ≤50 chars, body only when "why"
  isn't obvious.
---

Write commit messages terse and exact. Conventional Commits format. No fluff. Why over what.

## Rules

**Subject line:**
- `<type>(<scope>): <imperative summary>` — `<scope>` optional
- Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, `revert`
- Imperative mood: "add", "fix", "remove" — not "added", "adds", "adding"
- ≤50 chars when possible, hard cap 72
- No trailing period
- Match project convention for capitalization after the colon

**Body (only if needed):**
- Skip entirely when subject is self-explanatory
- Add body only for: non-obvious *why*, breaking changes, migration notes, linked issues
- Wrap at 72 chars
- Bullets `-` not `*`
- Reference issues/PRs at end: `Closes #42`, `Refs #17`

**What NEVER goes in:**
- "This commit does X", "I", "we", "now", "currently" — the diff says what
- "As requested by..." — use Co-authored-by trailer
- "Generated with Claude Code" or any AI attribution
- Emoji (unless project convention requires)
- Restating the file name when scope already says it

## Examples

Diff: new endpoint for user profile with body explaining the why
- ❌ "feat: add a new endpoint to get user profile information from the database"
- ✅
  ```
  feat(api): add GET /users/:id/profile

  Mobile client needs profile data without the full user payload
  to reduce LTE bandwidth on cold-launch screens.

  Closes #128
  ```

Diff: breaking API change
- ✅
  ```
  feat(api)!: rename /v1/orders to /v1/checkout

  BREAKING CHANGE: clients on /v1/orders must migrate to /v1/checkout
  before 2026-06-01. Old route returns 410 after that date.
  ```

## Auto-Clarity

Always include body for: breaking changes, security fixes, data migrations, anything reverting a prior commit. Never compress these into subject-only — future debuggers need the context.

## Boundaries

Only generates the commit message. Does not run `git commit`, does not stage files, does not amend. Output the message as a code block ready to paste. "stop caveman-commit" or "normal mode": revert to verbose commit style.