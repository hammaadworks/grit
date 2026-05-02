# 📖 User Guide

Build an unbreakable GitHub streak with Grit—the intelligent, high-fidelity git wrapper architected for professional consistency.

---

## 1. Initial Setup

Configure your commitment boundaries using the interactive Control Center.

```bash
$ grit config
```

**Key Parameters:**
1.  **Daily Target:** Your committed frequency of contributions per calendar day.
2.  **Start Date:** The historical boundary for timeline backfilling.
3.  **Allocation Strategy:** 
    *   `today`: Prioritize filling recent gaps.
    *   `start_date`: Fill gaps chronologically from the beginning.
4.  **GitHub Username:** Required for remote contribution grid synchronization.

!!! tip "AI Configuration"
    Grit supports Gemini, OpenAI, and Ollama. Configure your provider via:
    ```bash
    $ grit config --ai-key YOUR_API_KEY --ai-model gemini-1.5-flash
    ```

---

## 2. Web Intelligence Dashboard (`grit dash`)

Launch a modern, high-fidelity web interface to monitor your graph integrity.

```bash
$ grit dash
```

- **Visual Velocity:** Real-time metrics and activity charts for the last 30 days.
- **Pipeline Analysis:** See exactly where your next commits will be allocated.
- **Local Database Inspector:** Directly view and edit your system state (config, commits, drafts).

---

## 3. CommitScribe AI (`grit commit`)

Elevate your history with **CommitScribe**, an AI agent that generates precise, architectural commit messages.

### Background Generation
Run AI generation in a background thread to stay in your flow.
```bash
$ grit commit --ai
```
- **macOS Notifications:** CommitScribe notifies you when your draft is ready.
- **Live Logs:** Monitor background progress with `tail -f ~/.config/grit/ai_bg_<hash>.log`.

### The Interactive DevX Wizard
Run `grit commit` without arguments to launch the high-fidelity wizard.

1.  **File Picker:** Fluidly stage files with arrow keys and **Spacebar**. Supports directory folding via **Tab**.
2.  **CommitScribe Analysis:** Select `✨ Auto-generate (AI)` to trigger a deep-diff analysis.
3.  **Draft Caching:** Grit hashes your diffs. If you've generated a draft before, it loads instantly from a 50-entry FIFO cache.
4.  **Smart Distribution:** CommitScribe automatically calculates the optimal backdated timestamp to preserve your streak.

---

## 4. Professional Logging (`--logs`)

Grit features a professional, system-wide logging engine powered by **Loguru**.

- **Global Visibility:** Append `--logs` to any command for real-time internal diagnostics.
- **Persistent Records:** Detailed `DEBUG` logs are always maintained in `~/.grit/logs/` with automatic rotation.

```bash
$ grit sync --logs
```

---

## 5. History Redistribution (`grit spread`)

Redistribute a range of existing commits across historical gaps to repair your timeline.

```bash
$ grit spread HEAD~10 --push
```

- **Shadow Branch Strategy:** Executes rewrites on a temporary branch for maximum safety.
- **Atomic Synchronization:** State is updated only after a successful git operation.
- **Force-Push Protection:** Use `--push` to safely sync with your remote using `--force-with-lease`.

---

## 6. Quantum Undo (`grit undo`)

Safely regress your last commit and perfectly restore your Grit state.

```bash
$ grit undo
```
*Grit detects pushed commits and warns you before allowing a history rewrite.*

---

## 7. Self-Healing Sync Engine (`grit sync`)

Ensure your local state is perfectly aligned with both your local `git log` and your remote GitHub contribution grid.

```bash
$ grit sync
```
*Grit uses a MAX(local, remote, internal) rule to ensure your commit counts only ever move forward.*

---

## 8. Context & Branch Management (`grit branch`)

Switch between projects and branches without the "Stash Nightmares."

```bash
$ grit branch
```

- **Unified Interface**: List local branches, remote branches, and active Worktrees in one TUI.
- **Conflict-Free Switching**: If your tree is dirty, Grit will prompt you to create a **Worktree** (Best Practice) or a **WIP Commit** instead of messy stashing.
- **Smart Worktrees**: Automatically copies `.env` files when creating new Worktrees to avoid "Duplicate Setup Tax."
- **Bulk Cleanup**: Select multiple stale branches using **Spacebar** and delete them all at once with **D**.

---

## 9. Remote Management (`grit config`)

Manage your project remotes with professional precision inside the Control Center.

1. Run `grit config`.
2. Scroll to the bottom and select **Manage Git Remotes**.

- **Safe Sync**: Synchronize forks via clean `rebase` instead of polluting merges.
- **Stale Pruning**: Clean up "ghost" branches that no longer exist on the remote.
- **Quick Migration**: Easily rename remotes or update fetch/push URLs.

---

## 10. Support Grit (`grit sponsor`)
...
## Maintenance & Integrity

### Version Check
```bash
$ grit --version
```

### Decommissioning (`grit ungrit`)
Completely wipe all local Grit state and configuration.
```bash
$ grit ungrit --force
```
