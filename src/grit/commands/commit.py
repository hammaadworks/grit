import os
import subprocess
import tempfile

import typer
from rich.live import Live
from rich.padding import Padding
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from grit.ai import generate_commit_message
from grit.allocator import DateAllocator
from grit.commands.status import run_status
from grit.executor import (
    execute_git_commit,
    get_staged_diff,
    get_staged_files,
    get_status_files
)
from grit.state import StateManager
from grit.ui import (
    ACCENT_COLOR,
    BRAND_COLOR,
    console,
    err_console,
    ERROR_COLOR,
    get_banner_layout,
    get_key,
    run_selection_menu,
    SUCCESS_COLOR,
    WARN_COLOR,
)


COMMIT_TYPES = ["feat", "fix", "docs", "style", "refactor", "test", "chore"]


def run_commit(state: StateManager, ctx: typer.Context):
    """
    The core wrapper for `git commit`. Automatically allocates dates to preserve streaks.
    Run without arguments to enter the Interactive AI DevX Wizard.
    """
    args = ctx.args

    if args:
        _run_passthrough_commit(state, args)
        return

    selected = _interactive_stage_picker()
    _sync_staging_area(selected)

    final_msg = _interactive_commit_message_flow(state, ctx)
    _finalize_commit(state, final_msg)


# =========================
# INTERACTIVE STAGING FLOW
# =========================

def _interactive_stage_picker():
    status_files = get_status_files()
    files = [f for f, _ in status_files]
    status_map = {f: s for f, s in status_files}
    staged_files = get_staged_files()

    if not files:
        console.print(f"[{WARN_COLOR}]No changes to commit.[/{WARN_COLOR}]")
        raise typer.Exit(0)

    root_tree = _build_file_tree(files)
    items = _build_tree_items(root_tree, files, status_map)

    selected = set(staged_files)
    idx = 0
    visible_count = 12
    scroll_offset = 0

    with Live(auto_refresh=False, console=console, screen=False) as live:
        while True:
            visible_items = _get_visible_items(items)
            idx, scroll_offset = _clamp_cursor(idx, scroll_offset, visible_items, visible_count)

            live.update(
                _render_stage_picker(visible_items, idx, scroll_offset, visible_count, selected),
                refresh=True
            )

            key = get_key()
            action = _handle_stage_picker_key(key, visible_items, idx, selected)

            if action == "abort":
                console.print("[dim]Aborted.[/dim]")
                raise typer.Exit(0)
            elif action == "confirm":
                break
            elif action == "up":
                idx = (idx - 1) % len(visible_items)
            elif action == "down":
                idx = (idx + 1) % len(visible_items)

    if not selected:
        console.print("[dim]Aborted. No files selected.[/dim]")
        raise typer.Exit(0)

    return selected


def _build_file_tree(files):
    root_tree = {}
    for f in sorted(files):
        parts = f.split("/")
        curr = root_tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                curr[part] = f
            else:
                curr = curr.setdefault(part, {})
    return root_tree


def _build_tree_items(root_tree, files, status_map):
    items = [{"type": "all", "label": "(Select All)", "files": files, "depth": 0}]
    items.extend(_flatten_tree(root_tree, status_map, depth=1))
    return items


def _flatten_tree(curr_dict, status_map, depth, parent_path=""):
    res = []
    sorted_names = sorted(curr_dict.keys(), key=lambda n: (not isinstance(curr_dict[n], dict), n))

    for name in sorted_names:
        val = curr_dict[name]
        path = f"{parent_path}{name}/"

        if isinstance(val, dict):
            dir_files = _get_all_nested_files(val)
            res.append({
                "type": "dir",
                "label": f"[bold]{name}/[/bold]",
                "path": path,
                "files": dir_files,
                "depth": depth,
                "collapsed": False,
                "parent": parent_path,
            })
            res.extend(_flatten_tree(val, status_map, depth + 1, path))
        else:
            res.append({
                "type": "file",
                "label": name,
                "file": val,
                "depth": depth,
                "parent": parent_path,
                "status": status_map.get(val, "modified"),
            })

    return res


def _get_all_nested_files(d):
    fs = []
    for _, v in d.items():
        if isinstance(v, dict):
            fs.extend(_get_all_nested_files(v))
        else:
            fs.append(v)
    return fs


def _get_visible_items(items):
    visible_items = []
    collapsed_prefixes = {
        item["path"]
        for item in items
        if item["type"] == "dir" and item.get("collapsed")
    }

    for item in items:
        if item["type"] == "all":
            visible_items.append(item)
            continue

        item_parent = item.get("parent", "")
        is_hidden = any(item_parent.startswith(prefix) for prefix in collapsed_prefixes)

        if not is_hidden:
            visible_items.append(item)

    return visible_items


def _clamp_cursor(idx, scroll_offset, visible_items, visible_count):
    if idx >= len(visible_items):
        idx = len(visible_items) - 1
    if idx < 0:
        idx = 0

    if idx < scroll_offset:
        scroll_offset = idx
    elif idx >= scroll_offset + visible_count:
        scroll_offset = idx - visible_count + 1

    return idx, scroll_offset


def _render_stage_picker(visible_items, idx, scroll_offset, visible_count, selected):
    grid = Table.grid(expand=True)
    grid.add_row(get_banner_layout())

    selection_grid = Table.grid(expand=True)
    selection_grid.add_row(
        Text(
            "Select files to stage (Space: toggle, Tab/←/→: fold, Enter: confirm, Q: abort):",
            style=f"bold {ACCENT_COLOR}",
        )
    )
    selection_grid.add_row("")

    if scroll_offset > 0:
        selection_grid.add_row(
            Text.from_markup("      ↑ [dim](more files above)[/dim]", style=BRAND_COLOR)
        )

    table = Table(box=None, padding=(0, 1), show_header=False, expand=False)
    table.add_column("Cursor", width=2, justify="left")
    table.add_column("Checkbox", width=3, justify="left")
    table.add_column("Path", justify="left")

    upper = min(scroll_offset + visible_count, len(visible_items))
    for i in range(scroll_offset, upper):
        item = visible_items[i]
        is_cur = i == idx
        row = _build_stage_row(item, is_cur, selected)
        table.add_row(*row)

    selection_grid.add_row(table)

    if scroll_offset + visible_count < len(visible_items):
        selection_grid.add_row(
            Text.from_markup("      ↓ [dim](more files below)[/dim]", style=BRAND_COLOR)
        )

    grid.add_row(Padding(selection_grid, (0, 4)))
    return grid


def _build_stage_row(item, is_cur, selected):
    is_sel, is_partial, icon = _selection_state(item, selected)
    cursor = "▶" if is_cur else ""
    indent = "  " * item["depth"]

    if is_sel:
        box = f"[{SUCCESS_COLOR}]✔[/]"
        style = SUCCESS_COLOR
    elif is_partial:
        box = f"[{WARN_COLOR}]━[/]"
        style = SUCCESS_COLOR
    else:
        box = "[dim]○[/dim]"
        style = "dim" if not is_cur else "white"

    label = _format_item_label(item, icon)

    return (
        Text(cursor, style=f"bold {BRAND_COLOR}"),
        Text.from_markup(box),
        Text.from_markup(f"{indent}{label}", style=style),
    )


def _selection_state(item, selected):
    if item["type"] == "file":
        is_sel = item["file"] in selected
        return is_sel, False, ""

    fs = item["files"]
    is_sel = len(fs) > 0 and all(f in selected for f in fs)
    is_partial = len(fs) > 0 and any(f in selected for f in fs) and not is_sel
    icon = "📁 " if item["type"] == "dir" and item.get("collapsed") else "📂 " if item["type"] == "dir" else ""
    return is_sel, is_partial, icon


def _format_item_label(item, icon):
    label = item["label"]

    if item["type"] == "dir":
        label = f"{icon}{label}"
        if item.get("collapsed"):
            label += f" [dim]({len(item['files'])} hidden)[/dim]"

    elif item["type"] == "file":
        status = item.get("status", "modified")
        if status == "new":
            label = f"[white]{label}[/white]"
        elif status == "modified":
            label = f"[yellow]{label}[/yellow]"
        elif status == "deleted":
            label = f"[red]{label}[/red]"

    return label


def _handle_stage_picker_key(key, visible_items, idx, selected):
    item = visible_items[idx]

    if key == "\x1b[A":
        return "up"
    if key == "\x1b[B":
        return "down"
    if key == "\x1b[C" and item["type"] == "dir":
        item["collapsed"] = False
        return None
    if key == "\x1b[D" and item["type"] == "dir":
        item["collapsed"] = True
        return None
    if key == "\t" and item["type"] == "dir":
        item["collapsed"] = not item.get("collapsed", False)
        return None
    if key == " ":
        _toggle_selection(item, selected)
        return None
    if key.lower() == "q":
        return "abort"
    if key in ("\r", "\n"):
        return "confirm"

    return None


def _toggle_selection(item, selected):
    if item["type"] == "file":
        f = item["file"]
        if f in selected:
            selected.remove(f)
        else:
            selected.add(f)
        return

    fs = item["files"]
    if all(f in selected for f in fs):
        for f in fs:
            selected.discard(f)
    else:
        for f in fs:
            selected.add(f)


def _sync_staging_area(selected):
    staged_files = get_staged_files()
    to_unstage = [f for f in staged_files if f not in selected]

    if to_unstage:
        subprocess.run(["git", "reset"] + to_unstage, capture_output=True)

    subprocess.run(["git", "add"] + list(selected))
    console.print(
        f"    [{SUCCESS_COLOR}]✓ Staging area synchronized ({len(selected)} files selected).[/{SUCCESS_COLOR}]"
    )


# =========================
# COMMIT MESSAGE FLOW
# =========================

def _interactive_commit_message_flow(state: StateManager, ctx: typer.Context):
    ai_key = state.get_config("ai_api_key")
    ai_url = state.get_config("ai_base_url")
    ai_model = state.get_config("ai_model")

    options = _build_commit_options(ai_key)
    idx = 0

    while True:
        console.print()
        choice, idx = run_selection_menu(
            "Select commit type:",
            options,
            selected_idx=idx,
            show_banner=False,
        )

        if choice is None:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(0)

        if choice == "↩ Go Back":
            subprocess.run(["git", "reset"])
            return run_commit(state, ctx)

        if choice == "✨ Auto-generate (AI)":
            msg = _generate_ai_commit_message(ai_url, ai_key, ai_model)
            if msg:
                return _edit_ai_commit_message(msg)
            idx = options.index("feat")
            continue

        if choice in COMMIT_TYPES:
            return _manual_commit_message(choice)

        console.print(f"[{ERROR_COLOR}]Unexpected choice: {choice}. Please try again.[/]")


def _build_commit_options(ai_key):
    options = []
    if ai_key and ai_key != "Not configured" and ai_key != "":
        options.append("✨ Auto-generate (AI)")
    options.extend(COMMIT_TYPES)
    options.append("↩ Go Back")
    return options


def _generate_ai_commit_message(ai_url, ai_key, ai_model):
    diff = get_staged_diff()
    with console.status(
        f"[bold {BRAND_COLOR}]AI analyzing diff...[/bold {BRAND_COLOR}]",
        spinner="dots12",
    ):
        msg = generate_commit_message(diff, ai_url, ai_key, ai_model)

    if msg:
        return msg

    err_console.print(
        f"[{ERROR_COLOR}]✗ AI generation failed. Falling back to manual.[/{ERROR_COLOR}]"
    )
    return None


def _manual_commit_message(type_prefix):
    scope_value = _prompt_commit_scope()

    if scope_value:
        prefix_part = f"{type_prefix}({scope_value})"
    else:
        prefix_part = type_prefix

    subject = _prompt_commit_subject(prefix_part)
    if not subject.strip():
        console.print("[dim]Aborted.[/dim]")
        raise typer.Exit(0)

    body = _prompt_commit_body()

    return _compose_commit_message(prefix_part, subject, body)


def _prompt_commit_scope():
    console.print("\n    [bold bright_cyan]Enter commit scope (optional):"
                  " [/bold bright_cyan]", end="")
    return _read_single_line().replace("\n", " ").strip()


def _prompt_commit_subject(prefix_part):
    console.print("\n    [bold bright_cyan]Enter commit subject:"
                  " [/bold bright_cyan]", end="")
    console.print(f"[dim]{prefix_part}: [/dim]", end="")
    return _read_single_line().strip()


def _prompt_commit_body():
    console.print("\n[bold bright_cyan]    Enter commit body (optional): "
                  "[/bold bright_cyan]")
    console.print("[dim]    Press Enter twice to finish • Ctrl+C to abort[/dim]")
    return _read_multiline_input()


def _edit_ai_commit_message(initial_text):
    parsed = _parse_ai_commit_message(initial_text)

    console.print("\n\n[bold bright_cyan]AI suggestion loaded..[/bold bright_cyan]\n\n")

    scope_value = _prompt_ai_scope(parsed["scope"], parsed["type"])
    prefix_part = f"{parsed['type']}({scope_value})" if scope_value else parsed["type"]

    subject = _prompt_ai_subject(prefix_part, parsed["subject"])
    if not subject.strip():
        console.print("[dim]Aborted.[/dim]")
        raise typer.Exit(0)

    body = _prompt_ai_body(prefix_part, parsed["body"])

    return _compose_commit_message(prefix_part, subject, body)


def _prompt_ai_scope(default_scope, commit_type):
    console.print("\n\n[bold bright_cyan]Enter commit scope..[/bold bright_cyan]\n\n")
    console.print(f"[dim]Type: {commit_type}[/dim]\n")
    return _read_single_line(default_scope).replace("\n", " ").strip()


def _prompt_ai_subject(prefix_part, default_subject):
    console.print("\n\n[bold bright_cyan]Enter commit subject..[/bold bright_cyan]\n\n")
    console.print(f"[dim]Prefix: {prefix_part}[/dim]\n")
    return _read_single_line(default_subject).strip()


def _prompt_ai_body(prefix_part, default_body):
    console.print("\n\n[bold bright_cyan]Enter commit body (optional, markdown supported)..[/bold bright_cyan]\n\n")
    console.print(f"[dim]Prefix: {prefix_part}[/dim]")
    console.print("[dim]Edit below • Press Enter twice to finish • Ctrl+C to abort[/dim]\n\n")

    if default_body.strip():
        console.print("[dim]--- AI Body Suggestion ---[/dim]")
        console.print(default_body)
        console.print("[dim]--------------------------[/dim]\n")

    result = _read_multiline_input()
    return result if result.strip() else default_body.strip()


def _read_single_line(default=""):
    try:
        line = input()
        return line if line.strip() else default
    except KeyboardInterrupt:
        console.print("\n[dim]Aborted.[/dim]")
        raise typer.Exit(0)


def _read_multiline_input():
    lines = []
    empty_streak = 0

    while True:
        try:
            line = input()

            if line == "":
                empty_streak += 1
                if empty_streak >= 2:
                    break
            else:
                empty_streak = 0

            lines.append(line)

        except KeyboardInterrupt:
            console.print("\n[dim]Aborted.[/dim]")
            raise typer.Exit(0)

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def _compose_commit_message(prefix_part, subject, body):
    final_lines = [f"{prefix_part}: {subject.strip()}"]

    if body.strip():
        final_lines.append("")
        final_lines.extend(body.splitlines())

    return "\n".join(final_lines)


def _parse_ai_commit_message(msg):
    lines = msg.splitlines()
    first_line = lines[0].strip() if lines else ""
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    commit_type = "feat"
    scope = ""
    subject = first_line

    if ": " in first_line:
        prefix, subject_part = first_line.split(": ", 1)
        subject = subject_part.strip()

        if "(" in prefix and prefix.endswith(")"):
            commit_type = prefix.split("(", 1)[0].strip()
            scope = prefix.split("(", 1)[1].rsplit(")", 1)[0].strip()
        else:
            commit_type = prefix.strip()

    return {
        "type": commit_type,
        "scope": scope,
        "subject": subject,
        "body": body,
    }


# =========================
# FINAL COMMIT EXECUTION
# =========================

def _finalize_commit(state: StateManager, final_msg):
    allocator = DateAllocator(state)
    target_date = allocator.get_next_date()

    console.print(f"\n[bold bright cyan]Allocating commit to:"
                  f" [bold white]{target_date}[/bold white][/bold bright cyan]")

    if _execute_multiline_git_commit(final_msg, target_date, state):
        console.print(f"[{SUCCESS_COLOR}]✓ Commit successfully distributed.[/{SUCCESS_COLOR}]")
        _post_commit_actions(state)
    else:
        console.print(f"[{WARN_COLOR}]⚠ Commit cancelled or failed.[/{WARN_COLOR}]")


def _execute_multiline_git_commit(final_msg, target_date, state):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".gitmsg", delete=False, encoding="utf-8") as tf:
        tf.write(final_msg)
        tf.flush()
        temp_path = tf.name

    try:
        return execute_git_commit(["-F", temp_path], target_date, state)
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def _run_passthrough_commit(state: StateManager, args):
    allocator = DateAllocator(state)
    target_date = allocator.get_next_date()

    is_amend = "--amend" in args
    if is_amend:
        console.print(
            f"[{WARN_COLOR}]⚠ Amend detected. Grit will not increment daily target for amends.[/{WARN_COLOR}]"
        )

    if execute_git_commit(list(args), target_date, state):
        if not is_amend:
            console.print(f"[{SUCCESS_COLOR}]✓ Commit distributed to {target_date}.[/{SUCCESS_COLOR}]")
        else:
            console.print(f"[{SUCCESS_COLOR}]✓ Commit amended.[/{SUCCESS_COLOR}]")

        _post_commit_actions(state)


def _post_commit_actions(state: StateManager):
    console.print()
    push_prompt = Confirm.ask(
        f"[{ACCENT_COLOR}]Would you like to push these changes now?[/]",
        default=True,
        console=console,
    )

    if push_prompt:
        console.print(f"[{BRAND_COLOR}]Pushing to remote...[/{BRAND_COLOR}]")
        subprocess.run(["git", "push"])

    run_status(state=state, yes=True)