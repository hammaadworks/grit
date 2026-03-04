import os
import shutil
import subprocess
import typer
from rich.live import Live
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from rich import box
from rich.prompt import Confirm
from pathlib import Path

from grit.constants import (ACCENT_COLOR, BRAND_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARN_COLOR, KEY_READ_TIMEOUT)
from grit.executor import (get_branches, get_worktrees, delete_branch, delete_worktree, create_worktree, is_working_tree_dirty, get_head_hash)
from grit.ui import (console, get_key, get_banner_layout, set_terminal_title)

def run_branch_manager(state):
    """
    Unified Context & Worktree Manager.
    """
    set_terminal_title("Grit — Context Manager")
    
    error_msg = ""
    success_msg = ""
    selected_idx = 0
    multi_selected = set()
    
    with Live(auto_refresh=False, console=console, screen=True) as live:
        while True:
            # Refresh data
            branches = get_branches()
            worktrees = get_worktrees()
            
            # Combine into a unified list of items
            items = []
            
            # Section: Worktrees
            if worktrees:
                items.append({"type": "header", "label": "Active Worktrees"})
                for wt in worktrees:
                    items.append({"type": "worktree", "data": wt, "id": wt['path']})
                    
            # Section: Local Branches
            local_branches = [b for b in branches if not b['is_remote']]
            if local_branches:
                items.append({"type": "header", "label": "Local Branches"})
                for b in local_branches:
                    items.append({"type": "branch", "data": b, "id": b['name']})
                    
            # Section: Remote Branches
            remote_branches = [b for b in branches if b['is_remote']]
            if remote_branches:
                items.append({"type": "header", "label": "Remote Branches"})
                for b in remote_branches:
                    items.append({"type": "branch", "data": b, "id": b['name']})

            if not items:
                items.append({"type": "header", "label": "No branches found"})
                
            # Filter out headers for navigation
            navigable_items = [i for i in items if i['type'] != 'header']
            if not navigable_items:
                selected_idx = 0
            else:
                selected_idx = max(0, min(selected_idx, len(navigable_items) - 1))
                
            grid = Table.grid(expand=True)
            grid.add_column(justify="left", no_wrap=True)
            grid.add_row(get_banner_layout())
            
            menu_grid = Table.grid(expand=True)
            menu_grid.add_column(no_wrap=True)
            menu_grid.add_row(Text(" 🔀 Context & Branch Manager", style=f"bold {ACCENT_COLOR}"))
            menu_grid.add_row("")
            
            table = Table(box=box.ROUNDED, padding=(0, 1), show_header=False, expand=True, border_style="dim")
            table.add_column("Select", width=3, no_wrap=True)
            table.add_column("Type/Name", no_wrap=True)
            table.add_column("Status", no_wrap=True)
            table.add_column("Tracking", no_wrap=True)
            
            nav_idx = 0
            for item in items:
                if item['type'] == 'header':
                    table.add_row("", Text(f"\n{item['label']}", style=f"bold {ACCENT_COLOR}"), "", "")
                    continue
                    
                is_cur = nav_idx == selected_idx
                is_sel = item['id'] in multi_selected
                
                cursor = "▶" if is_cur else " "
                checkbox = f"[{SUCCESS_COLOR}]✔[/]" if is_sel else "[dim]○[/dim]"
                
                # Cannot multi-select current branch or current worktree
                can_select = True
                
                if item['type'] == 'branch':
                    b = item['data']
                    if b['is_current']: can_select = False
                    
                    style = f"bold {BRAND_COLOR}" if is_cur else ("white" if b['is_current'] else "dim")
                    icon = "★ " if b['is_current'] else "  "
                    name_text = f"{icon}{b['name']}"
                    
                    status_text = ""
                    if b['status'] == '=': status_text = "[green]Up to date[/green]"
                    elif b['status'] == '>': status_text = "[yellow]Ahead[/yellow]"
                    elif b['status'] == '<': status_text = "[red]Behind[/red]"
                    elif b['status'] == '<>': status_text = "[yellow]Diverged[/yellow]"
                    
                    tracking_text = b['upstream'] if b['upstream'] else ""
                    
                elif item['type'] == 'worktree':
                    wt = item['data']
                    if '(detached)' in wt.get('branch', ''): can_select = False
                    style = f"bold {BRAND_COLOR}" if is_cur else "dim"
                    name_text = f"📁 {os.path.basename(wt['path'])}"
                    status_text = f"[cyan]{wt.get('branch', 'detached')}[/cyan]"
                    tracking_text = wt['path']
                
                if not can_select and is_sel:
                    multi_selected.remove(item['id'])
                    checkbox = "[dim]○[/dim]"
                elif not can_select:
                    checkbox = " "
                    
                table.add_row(
                    Text.from_markup(f"{cursor} {checkbox}"),
                    Text.from_markup(name_text, style=style),
                    Text.from_markup(status_text),
                    Text(tracking_text, style="dim")
                )
                nav_idx += 1
                
            grid.add_row(Padding(table, (0, 2)))
            
            footer = Table.grid(expand=True)
            footer.add_column(justify="left", no_wrap=True)
            
            help_line = Text("\n ")
            help_line.append(" ↑↓ ", style="reverse"); help_line.append(" Navigate  ")
            help_line.append(" Enter ", style="reverse"); help_line.append(" Switch/Open  ")
            help_line.append(" W ", style="reverse"); help_line.append(" New Worktree  ")
            help_line.append(" Space ", style="reverse"); help_line.append(" Select  ")
            help_line.append(" D ", style="reverse"); help_line.append(" Delete  ")
            help_line.append(" Q ", style="reverse"); help_line.append(" Back ")
            
            footer.add_row(Padding(help_line, (0, 4)))
            
            if error_msg:
                footer.add_row(Text(f"\n   ✗ {error_msg}", style=f"bold {ERROR_COLOR}"))
            elif success_msg:
                footer.add_row(Text(f"\n   ✓ {success_msg}", style=f"bold {SUCCESS_COLOR}"))
                
            grid.add_row(footer)
            live.update(grid, refresh=True)
            
            try:
                key = get_key(timeout=0.1)
                if key is None: continue
            except KeyboardInterrupt:
                break
                
            error_msg = ""
            success_msg = ""
            
            if key in ('q', 'Q', '\x1b'):
                break
            elif key == '\x1b[A':
                selected_idx = (selected_idx - 1) % len(navigable_items)
            elif key == '\x1b[B':
                selected_idx = (selected_idx + 1) % len(navigable_items)
            elif key == ' ':
                if navigable_items:
                    item = navigable_items[selected_idx]
                    # Prevent selecting current branch
                    if item['type'] == 'branch' and item['data']['is_current']:
                        error_msg = "Cannot select the currently active branch."
                    elif item['type'] == 'worktree' and '(detached)' in item['data'].get('branch', ''):
                        error_msg = "Cannot select detached worktrees for deletion this way."
                    else:
                        if item['id'] in multi_selected:
                            multi_selected.remove(item['id'])
                        else:
                            multi_selected.add(item['id'])
            elif key in ('d', 'D'):
                if multi_selected:
                    live.stop()
                    if Confirm.ask(f"[{WARN_COLOR}]Delete {len(multi_selected)} selected items? Warning: Unmerged changes may be lost![/{WARN_COLOR}]"):
                        success_count = 0
                        for item_id in list(multi_selected):
                            # Find item type
                            item_type = next((i['type'] for i in navigable_items if i['id'] == item_id), None)
                            if item_type == 'branch':
                                ok, msg = delete_branch(item_id, force=True) # Forced delete for bulk
                                if ok: success_count += 1
                                else: error_msg += f"Failed {item_id}: {msg}\n"
                            elif item_type == 'worktree':
                                ok, msg = delete_worktree(item_id, force=True)
                                if ok: success_count += 1
                                else: error_msg += f"Failed {item_id}: {msg}\n"
                        multi_selected.clear()
                        success_msg = f"Deleted {success_count} items."
                    live.start()
                else:
                    error_msg = "Select items with Spacebar first to delete."
            elif key in ('w', 'W'):
                if navigable_items:
                    item = navigable_items[selected_idx]
                    if item['type'] == 'branch':
                        b = item['data']
                        branch_name = b['name']
                        live.stop()
                        console.print(f"\n [{BRAND_COLOR}]Creating Worktree for '{branch_name}'[/{BRAND_COLOR}]")
                        
                        # Strip remote prefix for local branch name if it's a remote branch
                        local_branch_name = branch_name
                        if b['is_remote'] and branch_name.startswith('origin/'):
                            local_branch_name = branch_name[7:]

                        parent_dir = Path(os.getcwd()).parent
                        suggested_path = parent_dir / f"{Path(os.getcwd()).name}-{local_branch_name.replace('/', '-')}"
                        
                        target_path = input(f" Directory Path [{suggested_path}]: ").strip()
                        if not target_path: target_path = str(suggested_path)
                        
                        # Check if branch exists locally and is checked out
                        # Worktree add will fail if branch is already checked out elsewhere
                        # We handle this safely:
                        create_cmd = ["git", "worktree", "add"]
                        
                        if b['is_remote']:
                            create_cmd.extend([target_path, "-b", local_branch_name, branch_name])
                        else:
                            # If it's a local branch, try adding it
                            create_cmd.extend([target_path, branch_name])
                            
                        res = subprocess.run(create_cmd, capture_output=True, text=True)
                        if res.returncode == 0:
                            success_msg = f"Worktree created at {target_path}"
                            # Copy .env if exists
                            env_path = Path(".env")
                            if env_path.exists():
                                dest_env = Path(target_path) / ".env"
                                try:
                                    shutil.copy(env_path, dest_env)
                                    success_msg += " (Copied .env)"
                                except Exception as e:
                                    error_msg = f"Worktree created, but failed to copy .env: {e}"
                        else:
                            # Handle "already checked out" error
                            if "already checked out" in res.stderr:
                                console.print(f"[{WARN_COLOR}]Branch '{branch_name}' is already checked out.[/{WARN_COLOR}]")
                                if Confirm.ask("Create a new copy branch instead?"):
                                    new_b_name = f"{local_branch_name}-copy"
                                    subprocess.run(["git", "worktree", "add", "-b", new_b_name, target_path, branch_name])
                                    success_msg = f"Created worktree with new branch '{new_b_name}'"
                            else:
                                error_msg = f"Failed to create worktree: {res.stderr}"
                                
                        live.start()
            elif key in ('\r', '\n'):
                if navigable_items:
                    item = navigable_items[selected_idx]
                    if item['type'] == 'branch':
                        b = item['data']
                        if b['is_current']: continue
                        
                        branch_name = b['name']
                        live.stop()
                        
                        if is_working_tree_dirty():
                            console.print(f"\n [{WARN_COLOR}]Working tree is dirty![/{WARN_COLOR}]")
                            console.print(" Switching branches now may cause conflicts or data loss.")
                            console.print("\n Options:")
                            console.print(f"  [{ACCENT_COLOR}]1.[/{ACCENT_COLOR}] Create a Worktree (Recommended)")
                            console.print(f"  [{ACCENT_COLOR}]2.[/{ACCENT_COLOR}] Create WIP Commit & Switch")
                            console.print(f"  [{ACCENT_COLOR}]3.[/{ACCENT_COLOR}] Abort")
                            
                            choice = input("\n Select an option [1-3]: ").strip()
                            if choice == '1':
                                # Defer to 'W' logic essentially
                                console.print("Press 'W' to create a worktree.")
                                input("Press Enter to return...")
                            elif choice == '2':
                                subprocess.run(["git", "add", "."], capture_output=True)
                                subprocess.run(["git", "commit", "-m", "WIP"], capture_output=True)
                                res = subprocess.run(["git", "checkout", branch_name], capture_output=True, text=True)
                                if res.returncode == 0:
                                    success_msg = f"Saved WIP and switched to {branch_name}"
                                else:
                                    error_msg = f"Failed to switch: {res.stderr}"
                        else:
                            # Clean tree, simple checkout
                            res = subprocess.run(["git", "checkout", branch_name], capture_output=True, text=True)
                            if res.returncode == 0:
                                success_msg = f"Switched to {branch_name}"
                            else:
                                error_msg = f"Failed to switch: {res.stderr}"
                                
                        live.start()
                    elif item['type'] == 'worktree':
                        wt = item['data']
                        editor = state.get_config("editor_command")
                        if editor:
                            live.stop()
                            console.print(f"Opening {wt['path']} in {editor}...")
                            # Basic split for simple commands like 'code --wait'
                            subprocess.Popen(editor.split() + [wt['path']])
                            live.start()
                        else:
                            error_msg = "Editor not configured. Set 'editor_command' in config."
