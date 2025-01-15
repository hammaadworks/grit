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

!!! tip "Headless Configuration"
    For automated environments, use standard flags:
    ```bash
    $ grit config --target 3 --start 2024-01-01 --username user --fill-from today
    ```

---

## 2. Intelligence Dashboard (`grit status`)

Monitor your commit velocity and pipeline with the built-in, high-fidelity terminal dashboard.

```bash
$ grit status
```

- **Visual Velocity:** Real-time metrics of your current daily target.
- **Journey Progress:** Comprehensive tracking of pending commits toward your "Green Wall" goal.
- **Commit Intelligence Pipeline:** Forecast of where your next sequence of commits will be allocated.

---

## 3. CommitScribe AI (`grit commit`)

Elevate your history with **CommitScribe**, a Distinguished System Architect AI (powered by Pydantic AI) that generates precise, architectural commit messages.

### The Interactive DevX Wizard
Run `grit commit` without arguments to launch the high-fidelity wizard.

1.  **File Picker:** Fluidly stage files with arrow keys and **Spacebar**. Supports directory folding via **Tab**.
2.  **CommitScribe Analysis:** Select `✨ Auto-generate (AI)` to trigger a deep-diff analysis.
    *   **Architectural Wisdom:** Every message includes RATIONALE, IMPACT, and FUTURE implications.
    *   **Real-Time Feedback:** Monitor analysis time with the built-in, non-blocking timer.
3.  **Smart Distribution:** CommitScribe automatically calculates the optimal backdated timestamp to preserve your streak.

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
