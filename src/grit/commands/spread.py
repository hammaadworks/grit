import subprocess
from typing import Annotated
import typer
from rich.padding import Padding
from rich.text import Text

from grit.allocator import DateAllocator
from grit.executor import execute_grit_spread, is_commit_pushed
from grit.state import StateManager
from grit.ui import ACCENT_COLOR, BRAND_COLOR, console, err_console, ERROR_COLOR, SUCCESS_COLOR, WARN_COLOR

def run_spread(state: StateManager, commit_range: str, push: bool = False):
    """
    Redistribute a range of commits across the timeline to fill historical gaps.
    """
    # Normalize range: if user just says HEAD~3, we mean HEAD~3..HEAD
    actual_range = commit_range
    if ".." not in commit_range:
        actual_range = f"{commit_range}..HEAD"

    res = subprocess.run(
        ["git", "rev-list", "--reverse", actual_range], capture_output=True, text=True
        )
    if res.returncode != 0:
        err_console.print(
            f"[{ERROR_COLOR}]✗ Invalid commit range: {commit_range}[/{ERROR_COLOR}]"
            )
        raise typer.Exit(1)

    commit_hashes = res.stdout.strip().splitlines()
    if not commit_hashes:
        console.print(
            f"[{WARN_COLOR}]![/{WARN_COLOR}] No commits found in range {actual_range}."
            )
        return

    console.print(
        Padding(
            Text("GRIT SPREAD INITIATED", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)
            )
        )

    allocator = DateAllocator(state)
    hash_to_date = {}
    mock_counts = {}

    with console.status("[dim]Calculating optimal timeline...[/dim]", spinner="dots12"):
        for h in commit_hashes:
            target_date = allocator.get_next_date(current_counts=mock_counts)
            hash_to_date[h] = target_date
            mock_counts[target_date] = mock_counts.get(
                target_date, state.get_commit_count(
                    target_date
                    )
                ) + 1

    if is_commit_pushed():
        console.print(
            Padding(
                Text(
                    "WARNING: SOME COMMITS ARE ALREADY PUSHED",
                    style=f"bold {ERROR_COLOR}"
                    ), (0, 2)
                )
            )

    if not typer.confirm("Apply redistribution?", default=True):
        return

    with console.status(
            f"[bold {BRAND_COLOR}]Rewriting history...[/bold {BRAND_COLOR}]",
            spinner="dots12"
            ):
        success = execute_grit_spread(commit_hashes, hash_to_date, state)

    if success:
        console.print(
            f"[{SUCCESS_COLOR}]✓ Successfully redistributed {len(commit_hashes)} "
            f"commits.[/{SUCCESS_COLOR}]"
            )
        
        if push:
            with console.status(
                f"[bold {ACCENT_COLOR}]Synchronizing remote...[/bold {ACCENT_COLOR}]",
                spinner="dots12"
            ):
                # We use force-with-lease for safety
                res = subprocess.run(["git", "push", "--force-with-lease"], capture_output=True)
                if res.returncode == 0:
                    console.print(f"[{SUCCESS_COLOR}]✓ Remote synchronized.[/{SUCCESS_COLOR}]")
                else:
                    err_console.print(f"[{ERROR_COLOR}]✗ Failed to push to remote. You may need to manual push.[/{ERROR_COLOR}]")
    else:
        err_console.print(
            f"[{ERROR_COLOR}]✗ Failed to redistribute commits.[/{ERROR_COLOR}]"
            )
