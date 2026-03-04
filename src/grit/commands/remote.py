import typer
from rich.live import Live
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from rich import box
from rich.prompt import Confirm

from grit.constants import (ACCENT_COLOR, BRAND_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARN_COLOR, KEY_READ_TIMEOUT)
from grit.executor import (get_remotes, prune_remote, set_remote_url, rename_remote, delete_remote, sync_fork, is_working_tree_dirty)
from grit.ui import (console, get_key, get_banner_layout, set_terminal_title)

def run_remote_manager():
    """
    Interactive TUI for managing Git remotes.
    """
    set_terminal_title("Grit — Remote Manager")
    
    error_msg = ""
    success_msg = ""
    selected_idx = 0

    # Action descriptions for better UX
    DESCRIPTIONS = {
        "A": "Add a new remote repository tracking URL.",
        "D": "Remove the selected remote from your local configuration.",
        "P": "Clean up local tracking branches that no longer exist on the remote.",
        "E": "Change the fetch/push URL for the selected remote.",
        "R": "Give the selected remote a new name (e.g., rename 'origin' to 'upstream').",
        "S": "Fetch from the remote and rebase your current branch onto it.",
    }
    
    with Live(auto_refresh=False, console=console, screen=True) as live:
        while True:
            remotes = get_remotes()
            if not remotes:
                remotes = [{"name": "No remotes found", "fetch": "", "push": ""}]
                
            selected_idx = max(0, min(selected_idx, len(remotes) - 1))
            
            grid = Table.grid(expand=True)
            grid.add_column(justify="left")
            grid.add_row(get_banner_layout())
            
            menu_grid = Table.grid(expand=True)
            menu_grid.add_row(Text(" 📡 Project Remotes", style=f"bold {ACCENT_COLOR}"))
            menu_grid.add_row("")
            
            table = Table(box=box.ROUNDED, padding=(0, 1), show_header=True, expand=True, border_style="dim")
            table.add_column("Remote Name", width=15)
            table.add_column("Fetch URL")
            table.add_column("Push URL")
            
            for i, r in enumerate(remotes):
                is_sel = i == selected_idx
                style = f"bold {BRAND_COLOR}" if is_sel else "dim"
                prefix = " ❱ " if is_sel else "   "
                table.add_row(
                    Text(f"{prefix}{r['name']}", style=style),
                    Text(r['fetch'], style=style),
                    Text(r['push'], style=style)
                )
                
            grid.add_row(Padding(table, (0, 2)))
            
            footer = Table.grid(expand=True)
            footer.add_column(justify="left")
            
            help_line = Text("\n ")
            help_line.append(" ↑↓ ", style="reverse"); help_line.append(" Navigate  ")
            help_line.append(" A ", style="reverse"); help_line.append(" Add  ")
            help_line.append(" D ", style="reverse"); help_line.append(" Delete  ")
            help_line.append(" P ", style="reverse"); help_line.append(" Prune  ")
            help_line.append(" E ", style="reverse"); help_line.append(" Edit  ")
            help_line.append(" R ", style="reverse"); help_line.append(" Rename  ")
            help_line.append(" S ", style="reverse"); help_line.append(" Sync Fork  ")
            help_line.append(" Q ", style="reverse"); help_line.append(" Back ")
            
            grid.add_row(Padding(help_line, (0, 4)))

            # Dynamic description row
            desc_table = Table.grid(expand=True)
            desc_table.add_row(Text("   " + "—" * 20, style="dim"))
            
            active_remote = remotes[selected_idx]['name'] if remotes[0]["name"] != "No remotes found" else None
            if active_remote:
                desc_table.add_row(Text(f"    Selected Remote: {active_remote}", style=f"bold {BRAND_COLOR}"))
                desc_table.add_row(Text(f"    └─ P (Prune): {DESCRIPTIONS['P']}", style="dim"))
                desc_table.add_row(Text(f"    └─ S (Sync):  {DESCRIPTIONS['S']}", style="dim"))
            else:
                desc_table.add_row(Text("    No remotes available to manage. Press 'A' to add one.", style="italic dim"))
            
            grid.add_row(Padding(desc_table, (0, 2)))
            
            if error_msg:
                grid.add_row(Padding(Text(f"\n   ✗ {error_msg}", style=f"bold {ERROR_COLOR}"), (0, 2)))
            elif success_msg:
                grid.add_row(Padding(Text(f"\n   ✓ {success_msg}", style=f"bold {SUCCESS_COLOR}"), (0, 2)))
                
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
                selected_idx = (selected_idx - 1) % len(remotes)
            elif key == '\x1b[B':
                selected_idx = (selected_idx + 1) % len(remotes)
            elif key in ('a', 'A'):
                live.stop()
                console.print(f"\n [bold {ACCENT_COLOR}]Add new remote[/]")
                new_name = input(f" Name: ").strip()
                new_url = input(f" URL: ").strip()
                if new_name and new_url:
                    if add_remote(new_name, new_url):
                        success_msg = f"Added remote {new_name}."
                    else:
                        error_msg = "Failed to add remote."
                live.start()
            elif key in ('d', 'D'):
                if remotes and remotes[0]["name"] != "No remotes found":
                    remote_name = remotes[selected_idx]["name"]
                    live.stop()
                    if Confirm.ask(f"[{WARN_COLOR}]Delete remote '{remote_name}'?[/{WARN_COLOR}]"):
                        if delete_remote(remote_name):
                            success_msg = f"Deleted remote {remote_name}."
                        else:
                            error_msg = f"Failed to delete remote {remote_name}."
                    live.start()
            elif key in ('p', 'P'):
                if remotes and remotes[0]["name"] != "No remotes found":
                    remote_name = remotes[selected_idx]["name"]
                    live.stop()
                    if Confirm.ask(f"Prune stale tracking branches for '{remote_name}'?"):
                        if prune_remote(remote_name):
                            success_msg = f"Pruned {remote_name} successfully."
                        else:
                            error_msg = f"Failed to prune {remote_name}."
                    live.start()
            elif key in ('e', 'E'):
                if remotes and remotes[0]["name"] != "No remotes found":
                    remote_name = remotes[selected_idx]["name"]
                    live.stop()
                    console.print(f"\n [bold {ACCENT_COLOR}]Editing URL for remote '{remote_name}'[/]")
                    new_url = input(f" New URL: ").strip()
                    if new_url:
                        if set_remote_url(remote_name, new_url):
                            success_msg = f"Updated URL for {remote_name}."
                        else:
                            error_msg = "Failed to update remote URL."
                    live.start()
            elif key in ('r', 'R'):
                if remotes and remotes[0]["name"] != "No remotes found":
                    old_name = remotes[selected_idx]["name"]
                    live.stop()
                    console.print(f"\n [bold {ACCENT_COLOR}]Rename remote '{old_name}'[/]")
                    new_name = input(f" New Name: ").strip()
                    if new_name and new_name != old_name:
                        if rename_remote(old_name, new_name):
                            success_msg = f"Renamed remote to {new_name}."
                        else:
                            error_msg = "Failed to rename remote."
                    live.start()
            elif key in ('s', 'S'):
                if remotes and remotes[0]["name"] != "No remotes found":
                    remote_name = remotes[selected_idx]["name"]
                    live.stop()
                    if is_working_tree_dirty():
                        console.print(f"[{ERROR_COLOR}]✗ Working tree is dirty. Please stash or commit changes before syncing to prevent conflicts.[/{ERROR_COLOR}]")
                        input("Press Enter to continue...")
                    else:
                        if Confirm.ask(f"Sync (Fetch & Rebase) current branch from '{remote_name}'?\n[dim]This will update your local branch with the latest changes from {remote_name}.[/dim]"):
                            with console.status(f"[{BRAND_COLOR}]Syncing with {remote_name}...[/{BRAND_COLOR}]"):
                                ok, msg = sync_fork(remote_name)
                            if ok:
                                success_msg = "Successfully synced via rebase."
                            else:
                                error_msg = msg
                    live.start()
