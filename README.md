# 🧱 Grit

> The intelligent `git commit` wrapper that keeps your GitHub graph perfectly consistent with a unified backdated history.

You code every day, but maybe you batch your commits or work on side projects sporadically. The result is a GitHub contribution graph that looks sparse. **Grit fixes this.**

Instead of generating fake work, Grit takes your *real* work and intelligently distributes it across a timeline to help you hit a specific daily commit target. It does this by dynamically calculating and injecting both `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` into your commits to ensure a consistent, uniform history.

## 🚀 The Features

- **No More Ghost Towns:** Set a daily commit target and let Grit mathematically distribute your commits.
- **AI-Powered Semantic Commits:** Built-in support for Gemini, OpenAI, and Ollama. Grit can analyze your diffs and generate perfect Conventional Commits in the background.
- **O(1) Allocation Engine:** Uses a blazing-fast SQL engine to find the optimal next commit date instantly.
- **Interactive Dashboard:** A beautiful, high-fidelity visualization GUI to monitor your graph integrity and pipeline.
- **Self-Healing Sync:** Scrapes your public GitHub graph to ensure Grit never overwrites days you've already filled.
- **History Redistributor:** Use `grit spread` to take a batch of existing commits and automatically distribute them across historical gaps.
- **Zero-Friction Wrapper:** Transparently passes all arguments directly to vanilla `git commit`.

## 📦 Installation

Grit is built with Python. You can install it globally using `uv` (recommended) or `pipx`:

```bash
uv tool install grit
# OR
pipx install grit
```

Alternatively, you can download the latest source code or wheels from [GitHub Releases](https://github.com/hammaadworks/grit/releases).

## 🛠️ Quick Start

1. **Configure Grit:**
   Run the interactive setup wizard or use headless flags for AI configuration.
   ```bash
   grit config --ai-key YOUR_KEY --ai-model gemini-1.5-flash
   ```

2. **Start Committing:**
   Use `grit commit` or let the AI do the work with the background flag.
   ```bash
   grit commit -m "feat: add super cool new feature"
   # Or go pragmatic with ai
   grit commit --ai
   ```

3. **Check your Status:**
   View your current daily progress and see where your next commit will land. Use `-y` to skip the repository state prompt.
   ```bash
   grit status -y
   ```

4. **Verify Version:**
   Check your current Grit version.
   ```bash
   grit --version
   ```

5. **Visualize History:**
   See a beautiful, branching, and colorful view of your repository history.
   ```bash
   grit log
   ```

6. **Launch the Dashboard:**
   Open the high-fidelity visualization GUI. It launches in the background by default!
   ```bash
   grit dash
   # To stop the background server:
   grit dash --stop
   # To run in foreground:
   grit dash --logs
   ```

## ⚠️ Important Disclaimers

* **Collaboration:** Use Grit primarily in **personal or solo projects**. Modifying author dates in heavily collaborative repositories can cause timeline confusion for other developers.
* **Squash Merges:** Squash merging via the GitHub UI will destroy individual commit dates. Use **rebase** or **merge commits** to preserve Grit's allocated dates.

## 📖 Documentation & Marketing

Looking to share this tool or understand exactly how it is built under the hood? 
Check out our comprehensive [Documentation & Landing Page](https://github.com/hammaadworks/grit) (or visit [grit.hammaadworks.com](https://grit.hammaadworks.com)).
