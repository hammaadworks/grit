# git2grit

**Git on steroids. Chronic streak OCD.**
The ultimate TUI + AI wrapper for Git.

<p align="center">
  <img src="https://raw.githubusercontent.com/hammaadworks/grit/main/diagrams/graph.png" alt="Grit Streak" width="400" />
  <img src="https://raw.githubusercontent.com/hammaadworks/grit/main/diagrams/anime-typing.gif" alt="Grit Power" width="400" />
</p>

### 🎯 The "Pure UX" Mode
Just here for the beautiful TUI and AI? Set `target = 0` in `grit config`. 
No date manipulation. No history rewrites. Just an elite Git experience.

`uv tool install git2grit`

---

## 🔥 Experience the Difference

### Boring Git Status
```text
$ git status
On branch master
Your branch is up to date with 'origin/master'.
nothing to commit, working tree clean
```

### Grit Intelligence Dashboard
```text
$ grit status
    ██████╗ ██████╗ ██╗████████╗
    ██╔════╝ ██╔══██╗██║╚══██╔══╝
    ██║  ███╗██████╔╝██║   ██║
    ██║   ██║██╔══██╗██║   ██║
    ╚██████╔╝██║  ██║██║   ██║
     ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝
    ✦ v0.0.1 - Intelligently distribute your commits

  █░ 1/2 today                                           April Volume: 56
  ✦ Optimization Progress: 41.9% ━━━━━━━━━━━━━━━━━━━━━━━ 554 COMMITS BEHIND

╭────────────────────────── Commit Intelligence Pipeline ──────────────────────────╮
│                                                                                  │
│    Date               Timeline           Status                   Load           │
│    2026-04-22         today               ◆                       1/2            │
│    2026-04-21         next                ◇                       0/2            │
│    2026-02-03         then                ◇                       1/2            │
│    2026-01-27         later               ◇                       0/2            │
│                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────╯
```

---

## 🔥 Features for the Obsessed

### 🤖 CommitScribe AI (`grit commit`)
Revamp your commit experience with an elite interactive TUI.
- **Interactive File Picker:** Fluidly stage/unstage files with a high-fidelity selector.
- **Deep-Diff Analysis:** Powered by **Pydantic AI**. It understands *why* you changed that line.
- **Architectural Messages:** Automatically generates professional, context-aware commit messages.
- **Draft Caching:** Remembers your AI drafts so you never lose a masterpiece.

### 📅 Real-Time Reallocation
Obsessed with the perfect graph?
- **Automatic Allocation:** If `target > 0`, Grit intelligently shifts your commit dates *as you code* to ensure your streak never breaks.
- **Spread Intelligence:** Use `grit spread` to redistribute a range of commits across historical gaps.

### 🛠️ The Control Center (`grit config`)
A beautiful interactive TUI to manage your "Juice."
- **AI Configuration:** Effortlessly set up Gemini, OpenAI, or Ollama.
- **Boundary Setting:** Define your daily targets and historical boundaries.
- **Strategy Selection:** Choose between `today` or `start_date` allocation patterns.

---

## 🛠 Commands at a Glance

| Command | The Vibe |
| :--- | :--- |
| `grit commit` | **The Core.** Elite TUI + AI commit wizard. |
| `grit branch` | **The Switch.** Unified context & Worktree manager. |
| `grit status` | **The Hub.** Check metrics, velocity, and streak health. |
| `grit dash` | **The View.** High-fidelity web-based intelligence dashboard. |
| `grit spread` | **The Gap Filler.** Redistribute work across history. |
| `grit sponsor`| **The Love.** Support the ongoing Grit journey. 💖 |
| `grit undo` | **The Oops.** Regress commits and restore state. |
| `grit config` | **The Control.** Interactive setup and remote manager. |

---

## ⚠️ Disclaimer: History Manipulation
`git2grit` modifies `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` to protect your streaks. 
- **Use with precaution on public/shared repos.**
- **History Rewrites:** Spreading and moving commits will rewrite Git history.
- **Safe Mode:** Set `target = 0` to disable all date-shifting while keeping the TUI/AI.

---

**Built with ❤️ by [hammaadworks](https://github.com/hammaadworks)**

*Disclaimer: Reflect your real work, don't fake it. Use your powers for good.*
