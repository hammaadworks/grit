import subprocess
import sys
from typing import Annotated, Optional

import typer

from grit import __version__
from grit.commands.commit import run_commit
# Command Implementations
from grit.commands.config import run_config_interactive
from grit.commands.log import run_log
from grit.commands.move import run_move
from grit.commands.status import run_status
from grit.commands.sync import run_sync
from grit.dashboard import start_dashboard
from grit.executor import execute_grit_spread, is_commit_pushed
from grit.state import StateManager
from grit.ui import (ACCENT_COLOR, BRAND_COLOR, console, err_console, ERROR_COLOR,
                     print_banner, SUCCESS_COLOR, WARN_COLOR)

from grit.logger import setup_logger

# Initialize the state globally for the CLI context
state = StateManager()

# Main Typer Application Interface
app = typer.Typer(
    help="Grit: Intelligently distribute your git commits to maintain a consistent "
         "graph.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=False
)


def version_callback(value: bool):
    if value:
        console.print(f"Grit v{__version__}")
        raise typer.Exit()


def is_config_valid() -> bool:
    """Checks if the core configuration variables are set and not placeholders."""
    required_keys = ["daily_target", "start_date", "github_username", "fill_strategy"]
    for key in required_keys:
        val = state.get_config(key)
        if not val or val == "Not configured" or val == "None" or val == "":
            return False
    return True


@app.callback(invoke_without_command=True)
def main(
        ctx: typer.Context,
        version: Annotated[
            Optional[bool],
            typer.Option("--version", "-v", callback=version_callback, is_eager=True)
        ] = None,
        logs: Annotated[
            bool,
            typer.Option("--logs", help="Enable detailed system logs for debugging")
        ] = False
):
    """
    Primary entry point for the Grit CLI.
    If invoked without a subcommand, intelligently routes to config or status.
    """
    # Initialize Loguru based on the --logs flag
    setup_logger(verbose=logs)

    # Improved interactive detection: check subcommand directly
    interactive_cmds = ["config", "dashboard", "dash", "move", "_ai-internal"]
    invoked = ctx.invoked_subcommand
    
    is_interactive = invoked in interactive_cmds
    
    # Commit without passthrough args is interactive and uses custom UI
    if invoked == "commit" and not ctx.args:
        is_interactive = True
    
    # Handle the no-args case where we might jump straight into config
    if invoked is None and not is_config_valid():
        is_interactive = True

    if "--help" not in sys.argv and "-v" not in sys.argv and "--version" not in sys.argv and not is_interactive:
        print_banner()

    if ctx.invoked_subcommand is None:
        if not is_config_valid():
            ctx.invoke(config)
        else:
            ctx.invoke(status)
        raise typer.Exit()
    elif ctx.invoked_subcommand not in ["config", "ungrit", "info",
                                        "dashboard"] and not is_config_valid():
        err_console.print(
            f"[{WARN_COLOR}]⚠ Configuration is incomplete. Launching Control "
            f"Center...[/{WARN_COLOR}]"
            )
        ctx.invoke(config)
        raise typer.Exit()


@app.command()
def config(
        target: Annotated[Optional[int], typer.Option(
            "--target", "-t", help="Daily commit target"
            )] = None,
        start: Annotated[Optional[str], typer.Option(
            "--start", "-s", help="Start date (YYYY-MM-DD)"
            )] = None,
        username: Annotated[Optional[str], typer.Option(
            "--username", "-u", help="GitHub username"
            )] = None,
        fill_from: Annotated[Optional[str], typer.Option(
            "--fill-from", "-f", help="Fill strategy (today or start_date)"
            )] = None
):
    """
    Grit Control Center: High-fidelity interactive settings management.
    Navigate with arrow keys, edit with Enter, and save with S.
    """
    # Headless Update Mode: Applied if any flags are passed.
    if any(v is not None for v in [target, start, username, fill_from]):
        if target is not None:
            state.set_config("daily_target", str(target))
        if start is not None:
            state.set_config("start_date", start)
        if username is not None:
            state.set_config("github_username", username)
        if fill_from is not None:
            if fill_from in ["today", "start_date"]:
                state.set_config("fill_strategy", fill_from)
            else:
                err_console.print(
                    f"[{ERROR_COLOR}]✗ Invalid fill strategy. Use 'today' or "
                    f"'start_date'.[/{ERROR_COLOR}]"
                    )
                raise typer.Exit(1)
        console.print(
            f"[{SUCCESS_COLOR}]✓ Headless configuration applied.[/{SUCCESS_COLOR}]"
            )
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
def status(
        yes: Annotated[
            bool, typer.Option("--yes", "-y", help="Skip the repository state prompt")
        ] = False
):
    """
    Renders the Grit Intelligence Dashboard.
    Displays metrics, the spillover pipeline, and celebrates daily goals.
    """
    run_status(state, yes=yes)


@app.command(name="dash", hidden=True)
def dash(
        port: int = typer.Option(
            0, "--port", "-p", help="Port to run the dashboard on"
            ),
        logs: bool = typer.Option(
            False, "--logs", "-l", help="Run in foreground and show server logs"
            ),
        stop: bool = typer.Option(
            False, "--stop", "-s", help="Stop a running background dashboard"
            )
):
    """Alias for dashboard."""
    dashboard(port, logs, stop)


@app.command()
def dashboard(
        port: int = typer.Option(
            0, "--port", "-p", help="Port to run the dashboard on"
            ),
        logs: bool = typer.Option(
            False, "--logs", "-l", help="Run in foreground and show server logs"
            ),
        stop: bool = typer.Option(
            False, "--stop", "-s", help="Stop a running background dashboard"
            )
):
    """
    Launches the Grit Intelligence Dashboard in your browser.
    A high-fidelity offline-first GUI for your commit pipeline.
    """
    pid_file = state.db_path.parent / "dashboard.pid"

    if stop:
        if pid_file.exists():
            try:
                import os
                import signal
                pid = int(pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                pid_file.unlink()
                console.print(f"[{SUCCESS_COLOR}]✓ Dashboard (PID {pid}) stopped.[/{SUCCESS_COLOR}]")
            except (ProcessLookupError, ValueError):
                console.print(f"[{WARN_COLOR}]! No active dashboard found with that PID. Cleaning up.[/{WARN_COLOR}]")
                if pid_file.exists(): pid_file.unlink()
            except Exception as e:
                err_console.print(f"[{ERROR_COLOR}]✗ Failed to stop dashboard: {e}[/{ERROR_COLOR}]")
        else:
            console.print(f"[{WARN_COLOR}]! No background dashboard is currently running.[/{WARN_COLOR}]")
        return

    if logs:
        # Write PID of foreground process too so it can be stopped
        import os
        pid_file.write_text(str(os.getpid()))
        try:
            start_dashboard(port)
        finally:
            if pid_file.exists(): pid_file.unlink()
    else:
        # If no port provided, find one so we can tell the user where to go
        if port == 0:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                port = s.getsockname()[1]

        console.print(
            f"[{BRAND_COLOR}]✦ Launching Grit Dashboard at [bold]http://localhost:{port}[/bold]...[/"
            f"{BRAND_COLOR}]"
            )

        # Launch in background process
        import subprocess
        import sys
        import os

        cmd = [sys.executable, "-m", "grit.cli", "dashboard", "--port", str(port),
               "--logs"]
        if "grit" in sys.argv[0] or "pytest" not in sys.argv[0]:
            cmd = [sys.argv[0], "dashboard", "--port", str(port), "--logs"]

        from grit.ui import suppress_title_reset
        suppress_title_reset()

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Save PID for future 'stop' commands
        pid_file.write_text(str(proc.pid))
        
        console.print(
            f"[dim]Background process started with PID: [bold white]{proc.pid}[/bold white][/dim]"
            )
        console.print(
            f"[dim]Run `grit dash --stop` to terminate the server.[/dim]"
            )


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )
def commit(
        ctx: typer.Context,
        verbose: Annotated[
            bool, typer.Option("--verbose", "-v", help="Show AI interaction logs")
        ] = False,
        ai: Annotated[
            bool, typer.Option("--ai", "-a", help="Run AI generation in the background and notify when ready")
        ] = False,
        logs: Annotated[
            bool, typer.Option("--logs", help="Enable detailed system logs for debugging")
        ] = False
):
    """
    The core wrapper for `git commit`. Automatically allocates dates to preserve
    streaks.
    Run without arguments to enter the Interactive AI DevX Wizard.
    """
    if logs:
        setup_logger(verbose=True)
    run_commit(state, ctx, verbose=verbose, ai=ai)


@app.command(hidden=True)
def _ai_internal(
    diff_path: str,
    diff_hash: str,
    verbose: bool = False
):
    """Internal command for background AI generation. Do not call manually."""
    import sys
    import time
    from pathlib import Path
    from grit.state import DEFAULT_DB_DIR
    
    # Ensure the directory exists
    DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
    log_file = DEFAULT_DB_DIR / "ai_background.log"
    
    # Open log file immediately in 'w' mode to prevent accumulation across runs
    try:
        log_stream = open(log_file, "w", buffering=1)
    except Exception as e:
        # If we can't open the log file, we're in trouble, but let's try to notify
        try:
            import subprocess
            subprocess.run(["osascript", "-e", f'display notification "Failed to start AI background: {e}" with title "Grit AI Error"'], check=False)
        except: pass
        return

    sys.stdout = log_stream
    sys.stderr = log_stream

    def log(msg):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

    log(f"Starting background generation for diff {diff_hash[:8]}...")
    
    from grit.ai import generate_commit_message
    from grit.state import StateManager
    import subprocess

    state = StateManager()
    ai_key = state.get_config("ai_api_key")
    ai_url = state.get_config("ai_base_url")
    ai_model = state.get_config("ai_model")

    try:
        diff = Path(diff_path).read_text(encoding="utf-8")
        log(f"Read diff ({len(diff)} chars). Calling LLM ({ai_model})...")
        
        msg = generate_commit_message(diff, ai_url, ai_key, ai_model, verbose)
        
        if msg:
            state.set_draft(diff_hash, msg)
            log("Success! Draft saved to database.")
            # Notify on macOS
            try:
                subprocess.run([
                    "osascript", 
                    "-e", 
                    'display notification "✨ AI draft is ready! Run `grit commit` to review." with title "Grit AI Success" sound name "Glass"'
                ], check=False)
            except Exception as ne:
                log(f"Notification failed: {ne}")
        else:
            log("LLM returned empty message or failed.")
            try:
                subprocess.run([
                    "osascript", 
                    "-e", 
                    'display notification "AI generation failed. Please try manual commit." with title "Grit AI Failed" sound name "Basso"'
                ], check=False)
            except: pass
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        try:
            subprocess.run([
                "osascript", 
                "-e", 
                f'display notification "Error: {e}" with title "Grit AI Error" sound name "Basso"'
            ], check=False)
        except: pass
    finally:
        # Cleanup temp diff file
        try:
            Path(diff_path).unlink(missing_ok=True)
            log("Cleaned up temporary diff file.")
        except:
            pass
        log_stream.close()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )
def log(ctx: typer.Context):
    """
    A beautifully enhanced, human-readable git log on jetpack rollerskates.
    """
    run_log(ctx)


@app.command()
def move(
        push: Annotated[
            bool, typer.Option("--push", "-p", help="Force push changes to remote")
        ] = False
):
    """
    Grit Move: Interactive history re-allocator.
    Select a commit from your history and move it to the next available fill slot.
    """
    from grit.commands.move import run_move
    run_move(state, push=push)


@app.command()
def info():
    """
    Displays the comprehensive Grit Manual and Command Reference.
    """
    # Keeping info command logic here for now as it's mostly static text
    from rich.table import Table
    from rich.padding import Padding
    from rich.text import Text

    console.print(
        Padding(Text("SYSTEM OVERVIEW", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2))
        )
    console.print(
        Padding(
            "Grit is a high-performance CLI wrapper designed to maintain a consistent "
            "GitHub contribution graph by intelligently distributing your real work "
            "across "
            "a timeline. It operates with zero latency and prioritizes repository "
            "integrity.",
            (0, 2, 1, 2)
        )
    )

    console.print(
        Padding(Text("COMMAND REFERENCE", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2))
        )

    commands = [
        ("info", "View this comprehensive documentation and command reference.", []),
        ("config",
         "Enter the interactive Control Center to manage your targets and identity.", [
             ("-t, --target [int]", "Set your daily commit goal."),
             ("-s, --start [date]", "Define the timeline start boundary (YYYY-MM-DD)."),
             ("-u, --username [str]",
              "Link your GitHub identity for graph synchronization."),
             ("-f, --fill-from [str]", "Allocation strategy: 'today' or 'start_date'."),
             ("Editor: Command", "Set your preferred editor (e.g., 'code --wait').")
         ]),
        ("commit",
         "The core wrapper for `git commit`. Run without arguments for the "
         "Interactive AI Wizard.",
         [
             ("--ai, -a", "Background AI generation and notify when draft is ready."),
             ("[standard git flags]",
              "All native git arguments are passed through transparently."),
             ("--amend",
              "Grit detects and warns that amends do not increment daily targets.")
         ]),
        ("status",
         "View your Intelligence Dashboard, commit capacity, and future pipeline.",
         [
             ("-y, --yes", "Skip the repository state prompt.")
         ]),

        ("sync",
         "Manually trigger a three-way merge between Local Git, Remote GitHub, "
         "and Grit State.",
         []),
        ("log",
         "A beautifully enhanced, human-readable git log on jetpack rollerskates.", []),

        ("move",
         "Interactive history re-allocator. Select a commit to move to the next fill slot.",
         [
             ("-p, --push", "Force push changes to remote after move.")
         ]),

        ("dashboard",
         "Launch the high-fidelity web dashboard for visual intelligence. Alias: "
         "'dash'",
         [
             ("-p, --port [int]", "Specify a custom port for the local server."),
             ("-l, --logs", "Run in foreground and show server logs."),
             ("-s, --stop", "Safely terminate any running background dashboard.")
         ]),

        ("spread",
         "Redistribute a range of commits across the timeline to fill history gaps.", [
             ("[commit-range]",
              "The range of commits to redistribute (e.g. HEAD~5..HEAD)."),
             ("-p, --push", "Force push changes to remote after spread.")
         ]),
        ("undo",
         "The 'Quantum Undo'. Safely regress the last commit and restore your streak "
         "count.",
         []),
        ("ungrit",
         "Securely decommission Grit and delete all local configuration and state.", [
             ("-f, --force", "Bypass the interactive confirmation prompt.")
         ])
    ]

    for cmd, desc, flags in commands:
        console.print(Padding(Text(f"• {cmd}", style=f"bold {BRAND_COLOR}"), (0, 4)))
        console.print(Padding(desc, (0, 6)))

        if flags:
            flag_table = Table(
                box=None, show_header=False, padding=(0, 2), expand=False
                )
            flag_table.add_column(width=28)
            flag_table.add_column()

            for flag, flag_desc in flags:
                flag_table.add_row(
                    Text(f"  {flag}", style=ACCENT_COLOR),
                    Text(flag_desc, style="dim")
                )
            console.print(Padding(flag_table, (0, 6)))
        console.print()

    # Add Tips & Tricks section
    console.print(
        Padding(Text("TIPS & TRICKS", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2))
    )
    tips = [
        ("Background AI", "Use `grit commit --ai` to background the LLM. Monitor it with: `tail -f ~/.config/grit/ai_background.log`"),
        ("Draft Caching", "Grit hashes your diff. If you've generated a message before, it loads instantly from the 50-entry FIFO cache."),
        ("Custom Editor", "Set 'Editor: Command' in config to skip Vim. Use 'code --wait' for VS Code or 'open -e' for TextEdit."),
    ]
    for tip_title, tip_desc in tips:
        console.print(Padding(f"✦ [bold white]{tip_title}[/bold white]: {tip_desc}", (0, 4, 1, 4)))


@app.command()
def spread(
        commit_range: Annotated[
            str, typer.Argument(help="Commit range to spread (e.g. HEAD~5..HEAD)")],
        push: Annotated[
            bool, typer.Option("--push", "-p", help="Force push changes to remote")
        ] = False
):
    """
    Grit Spread: Redistributes a range of commits across the timeline.
    """
    from grit.allocator import DateAllocator
    from rich.padding import Padding
    from rich.text import Text

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

    is_pushed = is_commit_pushed()
    if is_pushed:
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


@app.command()
def undo():
    """
    Quantum Undo: Safely regress the last commit and restore your streak count.
    """
    from rich.padding import Padding
    from rich.text import Text

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


@app.command()
def ungrit(
        force: Annotated[
            bool, typer.Option("--force", "-f", help="Bypass confirmation")] = False
):
    """
    Securely decommission Grit and delete all local configuration and state.
    """
    if not force:
        if not typer.confirm(
                f"[{ERROR_COLOR}]⚠ Are you sure you want to delete all Grit state?[/"
                f"{ERROR_COLOR}]",
                default=False
                ):
            return

    import shutil

    db_dir = state.db_path.parent
    if db_dir.exists() and db_dir.name != "":
        shutil.rmtree(db_dir)
        console.print(
            f"[{SUCCESS_COLOR}]✓ Grit has been decommissioned.[/{SUCCESS_COLOR}]"
            )
    else:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No Grit state found.")


if __name__ == "__main__":
    app()
