# ❓ Frequently Asked Questions & Troubleshooting

This document addresses common questions, edge cases, and troubleshooting tips for Grit.

---

## 🛠️ Troubleshooting

### Why does my `git diff` show `c/` and `w/` instead of `a/` and `b/`?

If you notice prefixes like `c/docs/architecture.md` instead of the standard `a/docs/architecture.md` in your terminal, don't worry—Grit hasn't modified your files or your Git installation.

This is caused by a Git feature called **Mnemonic Prefixes**. It replaces generic `a/b` labels with semantic ones:
*   **`c/`**: **C**ommit (the source version)
*   **`w/`**: **W**ork tree (your current changes)
*   **`i/`**: **I**ndex (staged changes)

**How to fix it:**
If you prefer the standard `a/b` prefixes, run this command in your terminal:
```bash
git config --global diff.mnemonicprefix false
```

---

## 🏗️ Technical FAQs

### Does Grit rewrite my Git history?
**No.** Grit only modifies the `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` environment variables during the commit process. It does **not** perform `rebase`, `filter-branch`, or any other history-altering operations. This ensures that both the author and committer dates are aligned for a consistent contribution graph.

### Is Grit safe to use on professional repositories?
Yes. Because Grit is a transparent wrapper, it is compatible with all Git features (hooks, GPG signing, LFS). However, we recommend checking with your team's lead before using it on shared corporate repositories, as some teams use contribution graphs to track velocity.

### What happens if I'm offline?
Grit works perfectly offline. It uses a local SQLite database stored in `~/.config/grit/state.db`. The only feature that requires an internet connection is `grit sync` (when fetching your public GitHub graph) and the initial "Cold Start" synchronization during `grit config`.

### Can I use Grit with multiple GitHub accounts?
Grit currently stores one global `github_username` in its configuration. If you switch accounts frequently, you can quickly update your identity using:
```bash
grit config --username new_account_name
```

---

## 🗺️ Where to go next?

<div class="grid cards" markdown>

-   :material-book-open-page-variant: **[Back to User Guide ➔](user-guide.md)**
-   :material-palette: **[View Design System ➔](design_doc.md)**

</div>
