import subprocess
import typer
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.padding import Padding
from grit.ui import (
    console, err_console, BRAND_COLOR, SUCCESS_COLOR, WARN_COLOR, ERROR_COLOR, ACCENT_COLOR,
    get_key
)
from grit.state import StateManager
from grit.allocator import DateAllocator
from grit.executor import execute_grit_spread, is_commit_pushed

def get_commit_original_date(commit_hash: str) -> str:
    """Returns the YYYY-MM-DD author date of a specific commit."""
    try:
        result = subprocess.run(
            ["git", "show", "-s", "--format=%ad", "--date=short", commit_hash], 
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return ""

def run_move(state: StateManager):
    """
    Grit Move: Interactive history re-allocator.
    Select a commit from your history and move it to the next available fill slot.
    """
    # 1. Fetch recent commits
    # Format: hash|message|author|time
    format_str = "%h|%s|%an|%ar"
    res = subprocess.run(
        ["git", "log", f"--pretty=format:{format_str}", "-n", "20"], 
        capture_output=True, text=True
    )
    
    if res.returncode != 0 or not res.stdout.strip():
        err_console.print(f"[{ERROR_COLOR}]✗ Failed to fetch git log.[/{ERROR_COLOR}]")
        return

    lines = res.stdout.strip().splitlines()
    commits = []
    for line in lines:
        parts = line.split('|')
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2],
                "time": parts[3]
            })

    if not commits:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No commits found to move.")
        return

    # 2. Selection UI
    idx = 0
    selected_commit = None
    
    with Live(auto_refresh=False, console=console, screen=False) as live:
        while True:
            grid = Table.grid(expand=True)
            grid.add_row(Text("Select a commit to move to the next fill slot:", style=f"bold {ACCENT_COLOR}"))
            grid.add_row("") # Spacer
            
            table = Table(box=None, padding=(0, 1), show_header=False, expand=True)
            table.add_column("Cursor", width=2)
            table.add_column("Hash", width=8)
            table.add_column("Details")
            
            for i, commit in enumerate(commits):
                is_cur = i == idx
                cursor = "▶" if is_cur else ""
                style = f"bold {BRAND_COLOR}" if is_cur else "dim"
                
                details = Text()
                details.append(f"{commit['subject'][:50]:<50} ", style="white" if is_cur else "dim")
                details.append(f"• {commit['author']} ", style="cyan" if is_cur else "dim")
                details.append(f"({commit['time']})", style=SUCCESS_COLOR if is_cur else "dim")
                
                table.add_row(
                    Text(cursor, style=f"bold {BRAND_COLOR}"),
                    Text(commit['hash'], style=style),
                    details
                )
                
            grid.add_row(table)
            grid.add_row(Text("\n [↑↓] Navigate  [Enter] Select  [Q] Abort", style="dim"))
            
            live.update(Padding(grid, (1, 2)), refresh=True)
            key = get_key()
            
            if key == '\x1b[A': idx = (idx - 1) % len(commits)
            elif key == '\x1b[B': idx = (idx + 1) % len(commits)
            elif key.lower() == 'q':
                console.print("[dim]Aborted.[/dim]")
                return
            elif key in ('\r', '\n'):
                selected_commit = commits[idx]
                break

    if not selected_commit:
        return

    # 3. Allocation & Confirmation
    allocator = DateAllocator(state)
    next_date = allocator.get_next_date()
    old_date = get_commit_original_date(selected_commit['hash'])
    
    if old_date == next_date:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] Commit {selected_commit['hash']} is already allocated to {next_date}.")
        return

    console.print(f"\n[{BRAND_COLOR}]✦ Target Slot:[/{BRAND_COLOR}] [bold white]{next_date}[/bold white]")
    console.print(f"[{BRAND_COLOR}]✦ Moving Commit:[/{BRAND_COLOR}] {selected_commit['hash']} - {selected_commit['subject']}")
    
    # Check if pushed
    # Note: is_commit_pushed() in executor check HEAD. We need one for specific hash.
    # I'll do a quick local check.
    is_pushed = False
    try:
        p_res = subprocess.run(
            ["git", "branch", "-r", "--contains", selected_commit['hash']], 
            capture_output=True, text=True
        )
        is_pushed = len(p_res.stdout.strip()) > 0
    except: pass

    if is_pushed:
        console.print(f"[{ERROR_COLOR}]⚠ WARNING: This commit has already been pushed to remote.[/{ERROR_COLOR}]")
        if not typer.confirm("Move anyway? (Requires force push later)", default=False):
            return
    elif not typer.confirm("Confirm move?", default=True):
        return

    # 4. Execution
    # To move a commit, we need to rewrite everything from its parent to HEAD.
    commit_hash = selected_commit['hash']
    res = subprocess.run(
        ["git", "rev-list", "--reverse", f"{commit_hash}..HEAD"], 
        capture_output=True, text=True
    )
    
    if res.returncode != 0:
        err_console.print(f"[{ERROR_COLOR}]✗ Failed to calculate rewrite range.[/{ERROR_COLOR}]")
        return

    # The range to rewrite is: [selected_commit, ...remaining]
    remaining_hashes = res.stdout.strip().splitlines()
    all_hashes = [commit_hash] + remaining_hashes
    
    hash_to_date = {}
    # First commit gets the new date
    hash_to_date[commit_hash] = next_date
    
    # Rest preserve their original dates
    for h in remaining_hashes:
        hash_to_date[h] = get_commit_original_date(h)

    with console.status(f"[bold {BRAND_COLOR}]Re-allocating history...[/bold {BRAND_COLOR}]", spinner="dots12"):
        # We need to manually handle state here because execute_grit_spread 
        # increments EVERYTHING in hash_to_date.
        # But we only want to:
        # 1. Decrement old_date
        # 2. Let execute_grit_spread increment everything (which might be messy if some weren't tracked)
        # Actually, the simplest way is to decrement old_date, 
        # then let spread increment ALL dates in the range, 
        # BUT spread only increments what's in hash_to_date.
        
        # A cleaner way: execute_grit_spread is a bit too "bulk" for this.
        # But if we want it to work, we can:
        state.decrement_commit_count(old_date)
        success = execute_grit_spread(all_hashes, hash_to_date, state)
        
    if success:
        console.print(f"[{SUCCESS_COLOR}]✓ Successfully moved {commit_hash} to {next_date}.[/{SUCCESS_COLOR}]")
        # Optional: run status
        from grit.commands.status import run_status
        run_status(state)
    else:
        # Revert decrement if failed? (Spread handles git revert but not our DB)
        state.increment_commit_count(old_date)
        err_console.print(f"[{ERROR_COLOR}]✗ Failed to move commit.[/{ERROR_COLOR}]")
