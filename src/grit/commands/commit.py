import sys
import subprocess
import typer
from typing import Annotated, Optional
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.padding import Padding
from rich.prompt import Confirm
from grit.ui import (
    console, err_console, BRAND_COLOR, SUCCESS_COLOR, WARN_COLOR, ERROR_COLOR, ACCENT_COLOR,
    get_key
)
from grit.state import StateManager
from grit.allocator import DateAllocator
from grit.executor import (
    execute_git_commit, 
    get_unstaged_files, 
    get_staged_diff, 
    has_staged_files, 
    get_staged_files,
    get_status_files
)
from grit.ai import generate_commit_message
from grit.commands.status import run_status

def run_commit(state: StateManager, ctx: typer.Context):
    """
    The core wrapper for `git commit`. Automatically allocates dates to preserve streaks.
    Run without arguments to enter the Interactive AI DevX Wizard.
    """
    args = ctx.args
    
    # INTERACTIVE DEVX WIZARD (Zero arguments)
    if not args:
        # Step A: File Picker (Interactive `git add`)
        status_files = get_status_files()
        files = [f for f, s in status_files]
        status_map = {f: s for f, s in status_files}
        staged_files = get_staged_files()
        
        if not files:
            console.print(f"[{WARN_COLOR}]No changes to commit.[/{WARN_COLOR}]")
            raise typer.Exit(0)
            
        # 1. Build nested dict tree
        root_tree = {}
        for f in sorted(files):
            parts = f.split('/')
            curr = root_tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1: # File
                    curr[part] = f
                else: # Dir
                    if part not in curr:
                        curr[part] = {}
                    curr = curr[part]
        
        # 2. Flatten into items list with hierarchical data
        items = [{"type": "all", "label": "(Select All)", "files": files, "depth": 0}]
        
        def flatten_tree(curr_dict, depth, parent_path=""):
            res = []
            # Sort so dirs come before files, then alphabetically
            sorted_names = sorted(curr_dict.keys(), key=lambda n: (not isinstance(curr_dict[n], dict), n))
            
            for name in sorted_names:
                val = curr_dict[name]
                # Ensure parent_path ends with / for startswith matching
                path = f"{parent_path}{name}/"
                
                if isinstance(val, dict):
                    # Directory: Recursively find all nested files for bulk toggle
                    def get_all_nested_files(d):
                        fs = []
                        for k, v in d.items():
                            if isinstance(v, dict): fs.extend(get_all_nested_files(v))
                            else: fs.append(v)
                        return fs
                    
                    dir_files = get_all_nested_files(val)
                    res.append({
                        "type": "dir", 
                        "label": f"[bold]{name}/[/bold]", 
                        "path": path, 
                        "files": dir_files, 
                        "depth": depth, 
                        "collapsed": False,
                        "parent": parent_path
                    })
                    res.extend(flatten_tree(val, depth + 1, path))
                else:
                    # File
                    res.append({
                        "type": "file", 
                        "label": name, 
                        "file": val, 
                        "depth": depth, 
                        "parent": parent_path,
                        "status": status_map.get(val, "modified")
                    })
            return res

        items.extend(flatten_tree(root_tree, 1))
                
        selected = set(staged_files)
        idx = 0
        visible_count = 12
        scroll_offset = 0
        
        with Live(auto_refresh=False, console=console, screen=False) as live:
            while True:
                # Calculate visible items based on collapsed state (prefix-based inheritance)
                visible_items = []
                collapsed_prefixes = {item["path"] for item in items if item["type"] == "dir" and item.get("collapsed")}
                
                for item in items:
                    if item["type"] == "all":
                        visible_items.append(item)
                        continue
                        
                    # An item is hidden if any of its parent path prefixes are collapsed
                    is_hidden = False
                    item_parent = item.get("parent", "")
                    for prefix in collapsed_prefixes:
                        if item_parent.startswith(prefix):
                            is_hidden = True
                            break
                    
                    if not is_hidden:
                        visible_items.append(item)

                # Clamp index to visible bounds
                if idx >= len(visible_items):
                    idx = len(visible_items) - 1
                if idx < 0:
                    idx = 0

                # Sync scroll offset
                if idx < scroll_offset:
                    scroll_offset = idx
                elif idx >= scroll_offset + visible_count:
                    scroll_offset = idx - visible_count + 1

                grid = Table.grid(expand=True)
                grid.add_row(Text("Select files to stage (Space: toggle, Tab/←/→: fold, Enter: confirm, Q: abort):", style=f"bold {ACCENT_COLOR}"))
                grid.add_row("") # Spacer
                
                if scroll_offset > 0:
                    grid.add_row(Text.from_markup(f"      ↑ [dim](more files above)[/dim]", style=BRAND_COLOR))

                # File selection table
                table = Table(box=None, padding=(0, 1), show_header=False, expand=False)
                table.add_column("Cursor", width=2, justify="left")
                table.add_column("Checkbox", width=3, justify="left")
                table.add_column("Path", justify="left")

                for i in range(scroll_offset, min(scroll_offset + visible_count, len(visible_items))):
                    item = visible_items[i]
                    is_cur = i == idx
                    
                    if item["type"] == "file":
                        is_sel = item["file"] in selected
                        is_partial = False
                        icon = ""
                    elif item["type"] == "dir":
                        fs = item["files"]
                        is_sel = len(fs) > 0 and all(f in selected for f in fs)
                        is_partial = len(fs) > 0 and any(f in selected for f in fs) and not is_sel
                        icon = "📁 " if item.get("collapsed") else "📂 "
                    else: # type == "all"
                        fs = item["files"]
                        is_sel = len(fs) > 0 and all(f in selected for f in fs)
                        is_partial = len(fs) > 0 and any(f in selected for f in fs) and not is_sel
                        icon = ""
                        
                    cursor = "▶" if is_cur else ""
                    indent = "  " * item["depth"]
                    
                    # High-fidelity checkbox icons
                    if is_sel:
                        box = f"[{SUCCESS_COLOR}]✔[/]"
                        style = SUCCESS_COLOR
                    elif is_partial:
                        box = f"[{WARN_COLOR}]━[/]"
                        style = SUCCESS_COLOR # Keep text success colored
                    else:
                        box = "[dim]○[/dim]"
                        style = "dim" if not is_cur else "white"
                        
                    label = item['label']
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

                    table.add_row(
                        Text(cursor, style=f"bold {BRAND_COLOR}"),
                        Text.from_markup(box),
                        Text.from_markup(f"{indent}{label}", style=style)
                    )
                
                grid.add_row(table)
                
                if scroll_offset + visible_count < len(visible_items):
                     grid.add_row(Text.from_markup(f"      ↓ [dim](more files below)[/dim]", style=BRAND_COLOR))
                    
                live.update(Padding(grid, (1, 2)), refresh=True)
                key = get_key()
                
                if key == '\x1b[A': idx = (idx - 1) % len(visible_items)
                elif key == '\x1b[B': idx = (idx + 1) % len(visible_items)
                elif key == '\x1b[C': # Right (Expand)
                    item = visible_items[idx]
                    if item["type"] == "dir":
                        item["collapsed"] = False
                elif key == '\x1b[D': # Left (Collapse)
                    item = visible_items[idx]
                    if item["type"] == "dir":
                        item["collapsed"] = True
                elif key == '\t': # Tab (Toggle fold)
                    item = visible_items[idx]
                    if item["type"] == "dir":
                        item["collapsed"] = not item.get("collapsed", False)
                elif key == ' ': 
                    item = visible_items[idx]
                    if item["type"] == "file":
                        f = item["file"]
                        if f in selected: selected.remove(f)
                        else: selected.add(f)
                    else:
                        fs = item["files"]
                        if all(f in selected for f in fs):
                            for f in fs: selected.discard(f)
                        else:
                            for f in fs: selected.add(f)
                elif key.lower() == 'q':
                    console.print("[dim]Aborted.[/dim]")
                    raise typer.Exit(0)
                elif key in ('\r', '\n'): 
                    break
        
        if not selected:
            console.print("[dim]Aborted. No files selected.[/dim]")
            raise typer.Exit(0)
            
        # Synchronize the staging area with the user's final selection
        # First, unstage everything that was originally staged but now deselected
        to_unstage = [f for f in staged_files if f not in selected]
        if to_unstage:
            subprocess.run(["git", "reset"] + to_unstage, capture_output=True)
            
        # Then, stage everything that is currently selected
        subprocess.run(["git", "add"] + list(selected))
        console.print(f"[{SUCCESS_COLOR}]✓ Staging area synchronized ({len(selected)} files selected).[/{SUCCESS_COLOR}]")
        
        # Step B: Semantic & AI Wizard
        ai_key = state.get_config("ai_api_key")
        ai_url = state.get_config("ai_base_url")
        ai_model = state.get_config("ai_model")
        
        commit_types = ["feat", "fix", "docs", "style", "refactor", "test", "chore"]
        options = []
        if ai_key and ai_key != "Not configured" and ai_key != "":
            options.append("✨ Auto-generate (AI)")
        options.extend(commit_types)
        options.append("↩ Go Back")
        
        idx = 0
        final_msg = ""
        
        while True:
            with Live(auto_refresh=False, console=console, screen=False) as live:
                while True:
                    grid = Table.grid(expand=True)
                    grid.add_row(Text("Select commit type:", style=f"bold {ACCENT_COLOR}"))
                    for i, opt in enumerate(options):
                        is_cur = i == idx
                        prefix = "▶ " if is_cur else "  "
                        style = f"bold {BRAND_COLOR}" if i == idx else "dim"
                        grid.add_row(Text(f"{prefix}{opt}", style=style))
                    
                    live.update(Padding(grid, (1, 2)), refresh=True)
                    key = get_key()
                    
                    if key == '\x1b[A': idx = (idx - 1) % len(options)
                    elif key == '\x1b[B': idx = (idx + 1) % len(options)
                    elif key in ('\r', '\n'): break
            
            choice = options[idx]
            if choice == "↩ Go Back":
                 # Simple way to go back: call commit again?
                 subprocess.run(["git", "reset"])
                 return run_commit(state, ctx)
            
            if choice == "✨ Auto-generate (AI)":
                diff = get_staged_diff()
                with console.status(f"[bold {BRAND_COLOR}]AI analyzing diff...[/bold {BRAND_COLOR}]", spinner="dots12"):
                    msg = generate_commit_message(diff, ai_url, ai_key, ai_model)
                if msg:
                    final_msg = typer.edit(msg) or msg
                    break
                else:
                    err_console.print(f"[{ERROR_COLOR}]✗ AI generation failed. Falling back to manual.[/{ERROR_COLOR}]")
                    choice = "feat" # Default fallback
            
            if choice != "✨ Auto-generate (AI)":
                # Manual Message Entry
                type_prefix = choice
                scope = typer.prompt(f"Scope (optional)", default="", show_default=False)
                subject = typer.prompt(f"Subject")
                
                console.print(f"\n[{ACCENT_COLOR}]Body (optional): [dim](Opening editor for multi-line support...)[/dim]")
                body = typer.edit() or ""
                body = body.strip()
                
                final_msg = f"{type_prefix}"
                if scope: final_msg += f"({scope})"
                final_msg += f": {subject}"
                if body:
                    final_msg += f"\n\n{body}"
                break

        # Step C: Date Allocation & Final Execution
        allocator = DateAllocator(state)
        target_date = allocator.get_next_date()
        
        console.print(f"\n[dim]Allocating commit to: [bold white]{target_date}[/bold white][/dim]")
        
        # We pass -m as a list item to ensure Typer/Git handles spaces correctly.
        if execute_git_commit(["-m", final_msg], target_date, state):
            console.print(f"[{SUCCESS_COLOR}]✓ Commit successfully distributed.[/{SUCCESS_COLOR}]")
            
            # Post-commit actions: Push and Status Chaining
            console.print()
            push_prompt = Confirm.ask(f"[{ACCENT_COLOR}]Would you like to push these changes now?[/]", default=True, console=console)
            if push_prompt:
                console.print(f"[{BRAND_COLOR}]Pushing to remote...[/{BRAND_COLOR}]")
                subprocess.run(["git", "push"])
            
            # Chain grit status at the end
            run_status(state)
        else:
            console.print(f"[{WARN_COLOR}]⚠ Commit cancelled or failed.[/{WARN_COLOR}]")

    else:
        # Pass-through Mode: Just allocate the date and run git commit
        allocator = DateAllocator(state)
        target_date = allocator.get_next_date()
        
        # Check if we should warn about --amend
        is_amend = "--amend" in args
        if is_amend:
            console.print(f"[{WARN_COLOR}]⚠ Amend detected. Grit will not increment daily target for amends.[/{WARN_COLOR}]")
            
        if execute_git_commit(list(args), target_date, state):
            if not is_amend:
                console.print(f"[{SUCCESS_COLOR}]✓ Commit distributed to {target_date}.[/{SUCCESS_COLOR}]")
            else:
                console.print(f"[{SUCCESS_COLOR}]✓ Commit amended.[/{SUCCESS_COLOR}]")
            
            # Post-commit actions: Push and Status Chaining
            console.print()
            push_prompt = Confirm.ask(f"[{ACCENT_COLOR}]Would you like to push these changes now?[/]", default=True, console=console)
            if push_prompt:
                console.print(f"[{BRAND_COLOR}]Pushing to remote...[/{BRAND_COLOR}]")
                subprocess.run(["git", "push"])
                
            # Chain grit status at the end
            run_status(state)
        else:
            # If execute_git_commit returns False, it means the commit failed or was cancelled
            pass
