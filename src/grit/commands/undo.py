import subprocess
import typer
from rich.padding import Padding
from rich.text import Text

from grit.executor import is_commit_pushed
from grit.state import StateManager
from grit.ui import ACCENT_COLOR, console, ERROR_COLOR, SUCCESS_COLOR

def run_undo(state: StateManager):
    """
    Quantum Undo: Safely regress the last commit and restore your streak count.
    """
    res = subprocess.run(
        ["git", "show", "-s", "--format=%h|%s|%ad", "--date=short", "HEAD"],
        capture_output=True, text=True
        )
    if res.returncode != 0 or not res.stdout.strip():
        console.print(f"[{ERROR_COLOR}]✗ No commits found to undo.[/{ERROR_COLOR}]")
        return

    head_hash, head_msg, head_date = res.stdout.strip().split('|', 2)

    console.print(
        Padding(
            Text("QUANTUM UNDO INITIATED", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)
            )
        )

    if is_commit_pushed():
        console.print(
            Padding(
                Text("STATUS: PUSHED TO REMOTE", style=f"bold {ERROR_COLOR}"),
                (1, 2, 0, 2)
                )
            )
        if not typer.confirm("Force Undo?", default=False):
            return
    else:
        if not typer.confirm(f"Undo commit {head_hash}?", default=True):
            return

    res = subprocess.run(["git", "reset", "--soft", "HEAD~1"])
    if res.returncode == 0:
        if head_date:
            state.decrement_commit_count(head_date)
        console.print(f"\n[{SUCCESS_COLOR}]✓ Quantum Undo complete.[/{SUCCESS_COLOR}]")
    else:
        console.print(f"[{ERROR_COLOR}]✗ Failed to undo commit.[/{ERROR_COLOR}]")
