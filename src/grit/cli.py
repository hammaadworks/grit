import sys
import subprocess
import shutil
from datetime import datetime
from typing import Optional, Annotated
import typer

from grit import __version__
from grit.state import StateManager
from grit.executor import is_commit_pushed, execute_grit_spread
from grit.updater import is_update_available, get_upgrade_command
from grit.dashboard import start_dashboard
from grit.ui import (
    console, err_console, BRAND_COLOR, SUCCESS_COLOR, WARN_COLOR, ERROR_COLOR, ACCENT_COLOR, 
    print_banner
)

# Command Implementations
from grit.commands.config import run_config_interactive
from grit.commands.status import run_status
from grit.commands.sync import run_sync
from grit.commands.commit import run_commit

# Initialize the state globally for the CLI context
state = StateManager()

# Main Typer Application Interface
app = typer.Typer(
    help="Grit: Intelligently distribute your git commits to maintain a consistent graph.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=False
)

def is_config_valid() -> bool:
    """Checks if the core configuration variables are set and not placeholders."""
    required_keys = ["daily_target", "start_date", "github_username", "fill_strategy"]
    for key in required_keys:
        val = state.get_config(key)
        if not val or val == "Not configured" or val == "None" or val == "":
            return False
    return True

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Primary entry point for the Grit CLI.
    If invoked without a subcommand, intelligently routes to config or status.
    """
    # Always print banner except for help
    if "--help" not in sys.argv:
        print_banner()

    if ctx.invoked_subcommand is None:
        if not is_config_valid():
            ctx.invoke(config)
        else:
            ctx.invoke(status)
        raise typer.Exit()
    elif ctx.invoked_subcommand not in ["config", "ungrit", "info", "dashboard"] and not is_config_valid():
        err_console.print(f"[{WARN_COLOR}]⚠ Configuration is incomplete. Launching Control Center...[/{WARN_COLOR}]")
        ctx.invoke(config)
        raise typer.Exit()

@app.command()
def config(
    target: Annotated[Optional[int], typer.Option("--target", "-t", help="Daily commit target")] = None,
    start: Annotated[Optional[str], typer.Option("--start", "-s", help="Start date (YYYY-MM-DD)")] = None,
    username: Annotated[Optional[str], typer.Option("--username", "-u", help="GitHub username")] = None,
    fill_from: Annotated[Optional[str], typer.Option("--fill-from", "-f", help="Fill strategy (today or start_date)")] = None
):
    """
    Grit Control Center: High-fidelity interactive settings management.
    Navigate with arrow keys, edit with Enter, and save with S.
    """
    # Headless Update Mode: Applied if any flags are passed.
    if any(v is not None for v in [target, start, username, fill_from]):
        if target is not None: state.set_config("daily_target", str(target))
        if start is not None: state.set_config("start_date", start)
        if username is not None: state.set_config("github_username", username)
        if fill_from is not None: 
            if fill_from in ["today", "start_date"]:
                state.set_config("fill_strategy", fill_from)
            else:
                err_console.print(f"[{ERROR_COLOR}]✗ Invalid fill strategy. Use 'today' or 'start_date'.[/{ERROR_COLOR}]")
                raise typer.Exit(1)
        console.print(f"[{SUCCESS_COLOR}]✓ Headless configuration applied.[/{SUCCESS_COLOR}]")
        return

    run_config_interactive(state)

@app.command()
def sync():
    """
    Self-Healing Engine: Re-aligns the local state with Git and GitHub.
    Performs a three-way merge to ensure the global source of truth is accurate.
    """
    run_sync(state)

@app.command()
def status():
    """
    Renders the Grit Intelligence Dashboard.
    Displays metrics, the spillover pipeline, and celebrates daily goals.
    """
    run_status(state)

@app.command(name="dash", hidden=True)
def dash(
    port: int = typer.Option(0, "--port", "-p", help="Port to run the dashboard on"),
    logs: bool = typer.Option(False, "--logs", "-l", help="Run in foreground and show server logs")
):
    """Alias for dashboard."""
    dashboard(port, logs)

@app.command()
def dashboard(
    port: int = typer.Option(0, "--port", "-p", help="Port to run the dashboard on"),
    logs: bool = typer.Option(False, "--logs", "-l", help="Run in foreground and show server logs")
):
    """
    Launches the Grit Intelligence Dashboard in your browser.
    A high-fidelity offline-first GUI for your commit pipeline.
    """
    if logs:
        start_dashboard(port)
    else:
        console.print(f"[{BRAND_COLOR}]✦ Launching Grit Dashboard in background...[/{BRAND_COLOR}]")
        console.print(f"[dim]Run `grit dash --logs` to view server logs in the foreground.[/dim]")
        
        # Launch in background process
        import os
        import subprocess
        import sys
        
        cmd = [sys.executable, "-m", "grit.cli", "dashboard", "--port", str(port), "--logs"]
        if "grit" in sys.argv[0] or "pytest" not in sys.argv[0]:
            cmd = [sys.argv[0], "dashboard", "--port", str(port), "--logs"]
            
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def commit(ctx: typer.Context):
    """
    The core wrapper for `git commit`. Automatically allocates dates to preserve streaks.
    Run without arguments to enter the Interactive AI DevX Wizard.
    """
    run_commit(state, ctx)

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def log(ctx: typer.Context):
    """
    A beautifully enhanced, human-readable git log on jetpack rollerskates.
    """
    run_log(ctx)

@app.command()
def info():
    """
    Displays the comprehensive Grit Manual and Command Reference.
    """
    # Keeping info command logic here for now as it's mostly static text
    from rich.table import Table
    from rich.padding import Padding
    from rich.text import Text
    
    console.print(Padding(Text("SYSTEM OVERVIEW", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)))
    console.print(Padding(
        "Grit is a high-performance CLI wrapper designed to maintain a consistent "
        "GitHub contribution graph by intelligently distributing your real work across "
        "a timeline. It operates with zero latency and prioritizes repository integrity.",
        (0, 2, 1, 2)
    ))

    console.print(Padding(Text("COMMAND REFERENCE", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)))
    
    commands = [
        ("info", "View this comprehensive documentation and command reference.", []),
        ("config", "Enter the interactive Control Center to manage your targets and identity.", [
            ("-t, --target [int]", "Set your daily commit goal."),
            ("-s, --start [date]", "Define the timeline start boundary (YYYY-MM-DD)."),
            ("-u, --username [str]", "Link your GitHub identity for graph synchronization."),
            ("-f, --fill-from [str]", "Allocation strategy: 'today' or 'start_date'.")
        ]),
        ("dashboard", "Launch the high-fidelity web dashboard for visual intelligence. Alias: 'dash'", [
            ("-p, --port [int]", "Specify a custom port for the local server."),
            ("-l, --logs", "Run in foreground and show server logs.")
        ]),
        ("commit", "The core wrapper for `git commit`. Run without arguments for the Interactive AI Wizard.", [
            ("[standard git flags]", "All native git arguments are passed through transparently."),
            ("--amend", "Grit detects and warns that amends do not increment daily targets.")
        ]),
        ("log", "A beautifully enhanced, human-readable git log on jetpack rollerskates.", []),
        ("status", "View your Intelligence Dashboard, commit capacity, and future pipeline.", []),
        ("sync", "Manually trigger a three-way merge between Local Git, Remote GitHub, and Grit State.", []),
        ("spread", "Redistribute a range of commits across the timeline to fill history gaps.", [
            ("[commit-range]", "The range of commits to redistribute (e.g. HEAD~5..HEAD).")
        ]),
        ("undo", "The 'Quantum Undo'. Safely regress the last commit and restore your streak count.", []),
        ("ungrit", "Securely decommission Grit and delete all local configuration and state.", [
            ("-f, --force", "Bypass the interactive confirmation prompt.")
        ])
    ]

    for cmd, desc, flags in commands:
        console.print(Padding(Text(f"• {cmd}", style=f"bold {BRAND_COLOR}"), (0, 4)))
        console.print(Padding(desc, (0, 6)))
        
        if flags:
            flag_table = Table(box=None, show_header=False, padding=(0, 2), expand=False)
            flag_table.add_column(width=28)
            flag_table.add_column()
            
            for flag, flag_desc in flags:
                flag_table.add_row(
                    Text(f"  {flag}", style=ACCENT_COLOR),
                    Text(flag_desc, style="dim")
                )
            console.print(Padding(flag_table, (0, 6)))
        console.print()

@app.command()
def spread(
    commit_range: Annotated[str, typer.Argument(help="Commit range to spread (e.g. HEAD~5..HEAD)")]
):
    """
    Grit Spread: Redistributes a range of commits across the timeline.
    """
    from grit.allocator import DateAllocator
    from rich.table import Table
    from rich.padding import Padding
    from rich.text import Text

    # Normalize range: if user just says HEAD~3, we mean HEAD~3..HEAD
    actual_range = commit_range
    if ".." not in commit_range:
        actual_range = f"{commit_range}..HEAD"

    res = subprocess.run(["git", "rev-list", "--reverse", actual_range], capture_output=True, text=True)
    if res.returncode != 0:
        err_console.print(f"[{ERROR_COLOR}]✗ Invalid commit range: {commit_range}[/{ERROR_COLOR}]")
        raise typer.Exit(1)
        
    commit_hashes = res.stdout.strip().splitlines()
    if not commit_hashes:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No commits found in range {actual_range}.")
        return

    console.print(Padding(Text("GRIT SPREAD INITIATED", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)))
    
    allocator = DateAllocator(state)
    hash_to_date = {}
    mock_counts = {}
    
    with console.status("[dim]Calculating optimal timeline...[/dim]", spinner="dots12"):
        for h in commit_hashes:
            target_date = allocator.get_next_date(current_counts=mock_counts)
            hash_to_date[h] = target_date
            mock_counts[target_date] = mock_counts.get(target_date, state.get_commit_count(target_date)) + 1

    if is_commit_pushed():
        console.print(Padding(Text("WARNING: SOME COMMITS ARE ALREADY PUSHED", style=f"bold {ERROR_COLOR}"), (0, 2)))

    if not typer.confirm("Apply redistribution?", default=True):
        return

    with console.status(f"[bold {BRAND_COLOR}]Rewriting history...[/bold {BRAND_COLOR}]", spinner="dots12"):
        success = execute_grit_spread(commit_hashes, hash_to_date, state)
        
    if success:
        console.print(f"[{SUCCESS_COLOR}]✓ Successfully redistributed {len(commit_hashes)} commits.[/{SUCCESS_COLOR}]")
    else:
        err_console.print(f"[{ERROR_COLOR}]✗ Failed to redistribute commits.[/{ERROR_COLOR}]")

@app.command()
def undo():
    """
    Quantum Undo: Safely regress the last commit and restore your streak count.
    """
    from rich.padding import Padding
    from rich.text import Text

    res = subprocess.run(["git", "show", "-s", "--format=%h|%s|%ad", "--date=short", "HEAD"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        console.print(f"[{ERROR_COLOR}]✗ No commits found to undo.[/{ERROR_COLOR}]")
        return
        
    head_hash, head_msg, head_date = res.stdout.strip().split('|', 2)
    
    console.print(Padding(Text("QUANTUM UNDO INITIATED", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)))
    
    if is_commit_pushed():
        console.print(Padding(Text("STATUS: PUSHED TO REMOTE", style=f"bold {ERROR_COLOR}"), (1, 2, 0, 2)))
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

@app.command()
def ungrit(
    force: Annotated[bool, typer.Option("--force", "-f", help="Bypass confirmation")] = False
):
    """
    Securely decommission Grit and delete all local configuration and state.
    """
    if not force:
        if not typer.confirm(f"[{ERROR_COLOR}]⚠ Are you sure you want to delete all Grit state?[/{ERROR_COLOR}]", default=False):
            return
            
    import shutil
    db_dir = state.db_path.parent
    if db_dir.exists() and db_dir.name != "":
        shutil.rmtree(db_dir)
        console.print(f"[{SUCCESS_COLOR}]✓ Grit has been decommissioned.[/{SUCCESS_COLOR}]")
    else:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No Grit state found.")

if __name__ == "__main__":
    app()
