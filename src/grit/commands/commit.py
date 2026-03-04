import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from time import time
import typer
from rich.live import Live
from rich.padding import Padding
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from grit.constants import (
    DIFF_TRUNCATION_LIMIT, UI_REFRESH_RATE, 
    STAGE_PICKER_OVERHEAD_LINES, KEY_READ_TIMEOUT, DEFAULT_COMMIT_TYPES_STR
)
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


def run_commit(state: StateManager, ctx: typer.Context, verbose: bool = False, ai: bool = False):
    """
    The core wrapper for `git commit`. Automatically allocates dates to preserve streaks.
    Run without arguments to enter the Interactive AI DevX Wizard.
    """
    args = ctx.args

    if args:
        _run_passthrough_commit(state, args)
        return

    # AI Logic: Repurposed --ai flag for prompt transparency (Dry Run)
    if ai:
        ai_key = state.get_config("ai_api_key")
        ai_url = state.get_config("ai_base_url")
        ai_model = state.get_config("ai_model")
        has_ai_config = ai_key and ai_key != "Not configured" and ai_key != ""

        if not has_ai_config:
            err_console.print(f"[{ERROR_COLOR}]✗ AI is not configured. Run [bold white]grit config[/bold white] first.[/{ERROR_COLOR}]")
            raise typer.Exit(1)
            
        from rich.panel import Panel
        from grit.constants import RAW_DIFF_PROMPT_LIMIT
        
        # 1. Fetch staged state directly (no picker)
        staged_files = get_staged_files()
        diff = get_staged_diff()
        
        # 2. Fetch Configs
        commit_types_str = state.get_config("commit_types") or DEFAULT_COMMIT_TYPES_STR
        commit_types = [t.strip() for t in commit_types_str.split(",") if t.strip()]
        rules_path = state.db_path.parent / "commit_message_rules.md"
        custom_rules = "None configured"
        if rules_path.exists():
            try:
                content = rules_path.read_text().strip()
                if content and content != "# Custom Commit Rules\n\nAdd your instructions here.":
                    custom_rules = content
            except Exception as e:
                custom_rules = f"Error reading rules: {e}"

        # 3. System Instructions
        instructions = (
            "You are a Senior Staff Engineer. Your task is to transform a raw code diff into a high-fidelity Conventional Commit message.\n"
            "Write commit messages terse and exact. No fluff. Why over what.\n\n"
            "RULES:\n"
            "1. SUBJECT LINE:\n"
            "   - <type>(<scope>): <imperative summary>\n"
            "   - Imperative mood: 'add', 'fix', 'remove' - NOT 'added', 'adds', 'adding'.\n"
            "   - ≤50 chars when possible, hard cap 72. No trailing period.\n"
            "   - Match project convention for capitalization after colon.\n"
            "2. THE BODY (ONLY IF NEEDED):\n"
            "   - Skip entirely when subject is self-explanatory.\n"
            "   - Add ONLY for: non-obvious *why*, breaking changes, migration notes, linked issues.\n"
            "   - Wrap at 72 chars. Bullets '-' not '*'.\n"
            "   - Reference issues: 'Closes #42', 'Refs #17'.\n"
            "3. SCOPE PRECISION: Primary module affected. Do not restate file names.\n"
            "4. PROHIBITED:\n"
            "   - 'This commit does X', 'I', 'we', 'now', 'currently'.\n"
            "   - 'As requested by...', AI attributions.\n"
            "   - Emojis.\n\n"
            "Respond ONLY with the requested structured output.\n\n"
            "CRITICAL: If the USER CUSTOM RULES below contradict any of the above instructions, "
            "the USER CUSTOM RULES MUST take absolute precedence."
        )
        
        # 4. User Prompt
        if staged_files:
            files_list = "\n".join(f"- {f}" for f in staged_files)
            diff_text = diff[:RAW_DIFF_PROMPT_LIMIT] if diff else "(Empty Diff)"
            user_prompt = f"""STAGED FILES:
{files_list}

RAW DIFF:
{diff_text}

Generate a Conventional Commit message.
The 'type' MUST be one of: {', '.join(COMMIT_TYPES)}.
The 'scope' should be the primary module or component affected.
The 'message' should be a high-level summary (≤50 chars).
The 'body' should be a list of strings explaining rationale and impact (ONLY if the 'why' is not obvious from the subject).
"""
        else:
            user_prompt = "[italic yellow]⚠ No files are currently staged in git. To see a full prompt, stage some files first.[/italic yellow]"

        console.print("\n[bold bright_cyan]AI INTELLIGENCE CORE: DRY RUN[/bold bright_cyan]\n")
        
        console.print(Panel(
            instructions,
            title="[bold white]SYSTEM INSTRUCTIONS[/bold white]",
            border_style=BRAND_COLOR,
            padding=(1, 2)
        ))
        
        console.print(Panel(
            custom_rules,
            title="[bold white]USER CUSTOM RULES[/bold white]",
            border_style=ACCENT_COLOR,
            padding=(1, 2)
        ))
        
        console.print(Panel(
            user_prompt,
            title="[bold white]USER PROMPT[/bold white]",
            border_style="dim",
            padding=(1, 2)
        ))
        
        console.print(f"\n[dim]Model: {ai_model} | URL: {ai_url}[/dim]\n")
        raise typer.Exit(0)

    console.clear()
    selected = _interactive_stage_picker()
    _sync_staging_area(selected)

    # Manual / AI Flow
    final_msg = _interactive_commit_message_flow(state, ctx, verbose=verbose)
    _finalize_commit(state, final_msg)


# =========================
# INTERACTIVE STAGING FLOW
# =========================

def _interactive_stage_picker():
    from grit.ui import set_terminal_title
    set_terminal_title("Grit — Staging")
    
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
    scroll_offset = 0

    # Use screen=False to allow history to persist on the terminal
    with Live(auto_refresh=False, console=console, screen=False) as live:
        last_size = console.size
        
        def render():
            nonlocal idx, scroll_offset
            # Dynamically calculate height to be as big as possible (overhead lines defined in constants)
            v_count = max(5, console.height - STAGE_PICKER_OVERHEAD_LINES)
            v_items = _get_visible_items(items)
            idx, scroll_offset = _clamp_cursor(idx, scroll_offset, v_items, v_count)
            live.update(_render_stage_picker(v_items, idx, scroll_offset, v_count, selected), refresh=True)

        render() # Initial render

        while True:
            key = get_key(timeout=KEY_READ_TIMEOUT)
            
            if console.size != last_size:
                last_size = console.size
                render()
                if key is None: continue

            if key is None:
                continue

            # Process key first
            visible_items = _get_visible_items(items)
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
            
            # Re-render immediately after state change
            render()

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
    table.add_column("Cursor", width=2, justify="left", no_wrap=True)
    table.add_column("Checkbox", width=3, justify="left", no_wrap=True)
    table.add_column("Path", justify="left", no_wrap=True)

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

def _interactive_commit_message_flow(state: StateManager, ctx: typer.Context, verbose: bool = False):
    ai_key = state.get_config("ai_api_key")
    ai_url = state.get_config("ai_base_url")
    ai_model = state.get_config("ai_model")
    
    # Custom Types
    commit_types_str = state.get_config("commit_types") or DEFAULT_COMMIT_TYPES_STR
    commit_types = [t.strip() for t in commit_types_str.split(",") if t.strip()]

    # Check if a draft is already ready for the currently staged diff
    from grit.executor import get_staged_diff, get_diff_hash
    diff = get_staged_diff()
    has_draft = False
    if diff:
        diff_hash = get_diff_hash(diff)
        draft = state.get_draft(diff_hash)
        has_draft = draft and draft["status"] == "success"

    options = _build_commit_options(ai_key, commit_types, has_draft=has_draft)
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
            return run_commit(state, ctx, verbose=verbose)

        if choice in ["✨ Auto-generate (AI)", "✨ Use AI Draft (Ready)"]:
            force = (choice == "✨ Auto-generate (AI)" and has_draft)
            msg = _generate_ai_commit_message(ai_url, ai_key, ai_model, state=state, verbose=verbose, force=force)
            if msg:
                final = _edit_ai_commit_message(msg)
                if final == "RETRY_MENU":
                    # If we just generated a new one, has_draft will be true next time
                    if msg:
                        diff = get_staged_diff()
                        if diff:
                            has_draft = True
                            options = _build_commit_options(ai_key, commit_types, has_draft=has_draft)
                    continue
                if final:
                    return final

            # If failed, refresh draft status and options
            diff = get_staged_diff()
            if diff:
                diff_hash = get_diff_hash(diff)
                draft = state.get_draft(diff_hash)
                has_draft = draft and draft["status"] == "success"
                options = _build_commit_options(ai_key, commit_types, has_draft=has_draft)

            idx = options.index("feat") if "feat" in options else 0
            continue


        if choice in commit_types:
            return _manual_commit_message(choice)

        console.print(f"[{ERROR_COLOR}]Unexpected choice: {choice}. Please try again.[/]")


def _build_commit_options(ai_key, commit_types, has_draft: bool = False):
    options = []
    if ai_key and ai_key != "Not configured" and ai_key != "":
        options.append("✨ Auto-generate (AI)")
        if has_draft:
            options.append("✨ Use AI Draft (Ready)")
    options.extend(commit_types)
    options.append("↩ Go Back")
    return options


def _generate_ai_commit_message(ai_url, ai_key, ai_model, state: StateManager, verbose: bool = False, force: bool = False):
    import time
    from rich.spinner import Spinner
    from rich.columns import Columns
    from grit.executor import get_diff_hash

    diff = get_staged_diff()
    if not diff:
        return None
        
    diff_hash = get_diff_hash(diff)
    
    # Check for cached draft first unless forced
    if not force:
        draft = state.get_draft(diff_hash)
        if draft and draft["status"] == "success":
            if verbose: console.print(f"[{SUCCESS_COLOR}]✨ Using cached draft.[/{SUCCESS_COLOR}]")
            return draft["message"]

    # Custom Configs
    commit_types_str = state.get_config("commit_types") or DEFAULT_COMMIT_TYPES_STR
    commit_types = [t.strip() for t in commit_types_str.split(",") if t.strip()]

    rules_path = state.db_path.parent / "commit_message_rules.md"
    custom_rules = None
    if rules_path.exists():
        try:
            content = rules_path.read_text().strip()
            if content and content != "# Custom Commit Rules\n\nAdd your instructions here.":
                custom_rules = content
                console.print(f"    [{BRAND_COLOR}]✨ Using custom AI rules from: {rules_path}[/{BRAND_COLOR}]")
        except Exception as e:
            if verbose: console.print(f"[red]Failed to read rules file: {e}[/red]")
    start_time = time.time()
    
    # Limit diff size for AI if it's massive to save memory/tokens
    if len(diff) > DIFF_TRUNCATION_LIMIT:
        if verbose: console.print(f"[{WARN_COLOR}]⚠ Diff too large ({len(diff)} chars), trimming context.[/{WARN_COLOR}]")
        diff = diff[:DIFF_TRUNCATION_LIMIT] + "\n... (Diff truncated for memory optimization)"

    last_error = None
    with Live(console=console, refresh_per_second=UI_REFRESH_RATE) as live:
        from concurrent.futures import ThreadPoolExecutor
        from grit.constants import AI_ANALYSIS_QUOTES, QUOTE_CHANGE_INTERVAL_SECONDS
        
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            generate_commit_message, diff, ai_url, ai_key, ai_model, commit_types, custom_rules, verbose
        )
        
        # Keep the UI alive and updating while the thread is running
        while not future.done():
            elapsed_total = time.time() - start_time
            
            # Select quote based on time rotation
            quote_index = int(elapsed_total // QUOTE_CHANGE_INTERVAL_SECONDS) % len(AI_ANALYSIS_QUOTES)
            current_quote = AI_ANALYSIS_QUOTES[quote_index]
            
            ui = Columns([
                Spinner("dots12", style=BRAND_COLOR),
                Text.from_markup(
                    f" [bold {BRAND_COLOR}]{current_quote}[/bold {BRAND_COLOR}] "
                    f"[dim]({elapsed_total:.1f}s)[/dim]"
                )
            ])
            live.update(ui)
            time.sleep(KEY_READ_TIMEOUT) # Small sleep to prevent CPU hammering
        
        try:
            msg = future.result()
            if msg:
                state.set_draft(diff_hash, msg)
        except Exception as e:
            last_error = e
            if verbose: console.print(f"[red]Error: {e}[/red]")
            msg = None
            
        # Final update with the total time
        total_elapsed = time.time() - start_time
        live.update(
            Text.from_markup(f"    [{SUCCESS_COLOR}]✓ CommitScribe analysis complete ({total_elapsed:.1f}s)[/{SUCCESS_COLOR}]")
        )

    if msg:
        return msg

    if last_error:
        err_msg = str(last_error)
        if "nodename nor servname provided" in err_msg or "connection" in err_msg.lower():
             err_console.print(f"[{ERROR_COLOR}]✗ Internet is not available or connection not established.[/{ERROR_COLOR}]")
             err_console.print(f"[dim]Detailed error: {err_msg}[/dim]")
        else:
             err_console.print(f"[{ERROR_COLOR}]✗ AI generation failed: {err_msg}[/{ERROR_COLOR}]")
    else:
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
    console.print("\n[bold bright_cyan]Enter commit body (optional): "
                  "[/bold bright_cyan]")
    console.print("[dim]Press Enter twice to finish • Ctrl+C to abort[/dim]\n")
    return _read_multiline_input()


def _edit_ai_commit_message(initial_text: str):
    from rich.panel import Panel
    
    # Show the AI suggestion as a polished draft in a prominent box
    console.print("\n\n[bold bright_cyan]AI Draft:[/bold bright_cyan]\n")
    console.print(Panel(initial_text, border_style=BRAND_COLOR, padding=(1, 2), title="Draft Review", title_align="left"))
    
    options = ["✅ Confirm & Commit", "📝 Edit in Editor", "🔄 Regenerate", "↩ Go Back"]
    choice, _ = run_selection_menu("Accept this commit message?", options, show_banner=False)

    if choice == "✅ Confirm & Commit":
        return initial_text
        
    if choice == "📝 Edit in Editor":
        temp_file_path = None # Initialize to None for finally block
        try:
            with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as temp_file:
                temp_file.write(initial_text)
                temp_file_path = temp_file.name # Get the name of the created temp file

            # Get editor command from state manager, or fallback to sensible defaults
            state_manager = StateManager()
            editor_command = state_manager.get_config("editor_command")

            if not editor_command:
                # Default logic for different OS
                if sys.platform == "darwin": # macOS
                    editor_command = "open -e" # TextEdit
                elif sys.platform.startswith("win"): # Windows
                    editor_command = "notepad.exe" # Notepad
                else: # Linux and others
                    # Prioritize VS Code if available, otherwise fall back to EDITOR env var, then nano
                    if shutil.which("code"):
                        editor_command = "code --wait"
                    else:
                        editor_command = os.environ.get("EDITOR", "nano")

            console.print(f"[dim]Opening editor: [bold]{editor_command} {temp_file_path}[/bold][/dim]")
            subprocess.run(f"{editor_command} {temp_file_path}", shell=True, check=True) # blocking call

            with open(temp_file_path, "r", encoding="utf-8") as f:
                edited_text = f.read()

            if not edited_text.strip():
                console.print("[dim]Aborted: Empty message.[/dim]")
                raise typer.Exit(0)

            return edited_text
        except Exception as e:
            err_console.print(f"[bold red]Error opening editor:[/bold red] {e}")
            return "RETRY_MENU" # Or some other appropriate error handling
        finally:
            if temp_file_path and Path(temp_file_path).exists():
                os.remove(temp_file_path)

    if choice == "✨ Fine-tune Here":
        # The granular terminal flow for small fixes without leaving the shell
        parsed = _parse_ai_commit_message(initial_text)
        console.print("\n\n[bold bright_cyan]Quick Refine:[/bold bright_cyan]\n")
        scope_value = _prompt_ai_scope(parsed["scope"], parsed["type"])
        prefix_part = f"{parsed['type']}({scope_value})" if scope_value else parsed["type"]
        subject = _prompt_ai_subject(prefix_part, parsed["subject"])
        if not subject.strip(): raise typer.Exit(0)
        body = _prompt_ai_body(prefix_part, parsed["body"])
        return _compose_commit_message(prefix_part, subject, body)
        
    if choice == "🔄 Regenerate":
        return None 
        
    if choice == "↩ Go Back":
        return "RETRY_MENU"
        
    return initial_text


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
    # Some models include chatty preamble like "Here is your commit message:".
    # We attempt to find the first line that actually looks like a Conventional Commit.
    import re
    lines = msg.splitlines()
    
    clean_lines = []
    found_start = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if found_start: # Keep internal whitespace
                clean_lines.append("")
            continue
            
        # Check for <type>(<scope>): <subject> or <type>: <subject>
        if not found_start:
            if re.match(r'^[a-z]+(\([a-z0-9_-]+\))?: .+', stripped.lower()):
                found_start = True
        
        if found_start:
            clean_lines.append(stripped)
            
    # If we couldn't find a standard start, just use everything cleaned up
    if not clean_lines:
        clean_lines = [l.strip() for l in lines if l.strip()]

    first_line = clean_lines[0] if clean_lines else ""
    body = "\n".join(clean_lines[1:]).strip() if len(clean_lines) > 1 else ""

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
        
        # Cleanup: If this was a cached draft, delete its log file
        try:
            from grit.executor import get_staged_diff, get_diff_hash
            diff = get_staged_diff()
            if diff:
                h = get_diff_hash(diff)
                log_file = state.db_path.parent / f"ai_bg_{h}.log"
                log_file.unlink(missing_ok=True)
        except: pass

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

