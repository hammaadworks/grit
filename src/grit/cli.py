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
    help=f"\n [bold {BRAND_COLOR}]Grit v{__version__}[/bold {BRAND_COLOR}] — High-fidelity commit distribution system.\n",
    epilog=f"\n [dim]Hint: Use [bold white]grit <command> --help[/bold white] for full flag documentation.[/dim]\n",
    context_settings={"help_option_names": ["-h", "--help"]},
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

    if "--help" not in sys.argv and "-v" not in sys.argv and "--version" not in sys.argv and not is_interactive and invoked != "info":
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
            "--target", "-t", help="Daily commit target (e.g., 1)"
            )] = None,
        start: Annotated[Optional[str], typer.Option(
            "--start", "-s", help="Start date boundary (YYYY-MM-DD)"
            )] = None,
        username: Annotated[Optional[str], typer.Option(
            "--username", "-u", help="GitHub username for sync"
            )] = None,
        fill_from: Annotated[Optional[str], typer.Option(
            "--fill-from", "-f", help="Strategy: 'today' or 'start_date'"
            )] = None,
        ai_url: Annotated[Optional[str], typer.Option(
            "--ai-url", help="LLM API base URL (e.g. http://localhost:11434/v1)"
            )] = None,
        ai_key: Annotated[Optional[str], typer.Option(
            "--ai-key", help="LLM API key (Gemini, OpenAI, etc.)"
            )] = None,
        ai_model: Annotated[Optional[str], typer.Option(
            "--ai-model", help="LLM model name (e.g. 'gemini-1.5-flash')"
            )] = None
):
    """
    Enter the interactive Control Center or apply headless configuration.
    """
    # Headless Update Mode: Applied if any flags are passed.
    if any(v is not None for v in [target, start, username, fill_from, ai_url, ai_key, ai_model]):
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
        if ai_url is not None:
            state.set_config("ai_base_url", ai_url)
        if ai_key is not None:
            state.set_config("ai_api_key", ai_key)
        if ai_model is not None:
            state.set_config("ai_model", ai_model)

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
            bool, typer.Option("--yes", "-y", help="Skip the repository state confirmation prompt")
        ] = False
):
    """
    Renders the Intelligence Dashboard. Displays metrics and the spillover pipeline.
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
            0, "--port", "-p", help="Port to run the dashboard on (0 for auto-assign)"
            ),
        logs: bool = typer.Option(
            False, "--logs", "-l", help="Run in foreground and show server logs"
            ),
        stop: bool = typer.Option(
            False, "--stop", "-s", help="Stop a running background dashboard"
            )
):
    """
    Launches the high-fidelity web dashboard. 
    A modern offline-first GUI for your commit distribution metrics.
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
            bool, typer.Option("--verbose", "-v", help="Show detailed AI interaction logs")
        ] = False,
        ai: Annotated[
            bool, typer.Option("--ai", "-a", help="Trigger background AI generation and notify when draft is ready")
        ] = False,
        logs: Annotated[
            bool, typer.Option("--logs", help="Enable system-level logging for debugging")
        ] = False
):
    """
    The core wrapper for `git commit`. Intelligently allocates dates to preserve streaks.
    Pass standard git flags or run without arguments for the AI Wizard.
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
    import random
    import os
    from pathlib import Path
    from grit.state import DEFAULT_DB_DIR
    
    # Ensure the directory exists
    DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
    log_file = DEFAULT_DB_DIR / f"ai_bg_{diff_hash}.log"
    
    # Open log file immediately
    log_stream = None
    try:
        log_stream = open(log_file, "a", buffering=1)
        sys.stdout = log_stream
        sys.stderr = log_stream
    except Exception as e:
        # Fallback to stderr if log file fails
        sys.stderr.write(f"Failed to open log file {log_file}: {e}\n")
        try:
            import subprocess
            subprocess.run(["osascript", "-e", f'display notification "Failed to start AI background: {e}" with title "Grit AI Error"'], check=False)
        except: pass
        if not log_stream and not sys.stderr.isatty():
             return # Exit if we can't log anywhere useful and not in terminal

    def log(msg, color=None):
        ts = time.strftime('%H:%M:%S')
        # Use simple markers for engagement without complex rich formatting in log files
        print(f"[{ts}] {msg}")

    quotes = [
        "Analyzing architectural nuances...",
        "Evaluating semantic impact of changes...",
        "Calculating optimal conventional commit structure...",
        "Distilling technical wisdom from your diff...",
        "Synthesizing high-fidelity documentation...",
        "Aligning with industry-standard commit protocols..."
    ]

    log("✦ Grit Intelligence System: Background Thread Initialized")
    log(f"✦ Process ID: {os.getpid()}")
    log(f"✦ Target Diff: {diff_hash[:8]}")
    log("-" * 50)
    
    from grit.ai import generate_commit_message
    from grit.state import StateManager
    import subprocess

    state = StateManager()
    ai_key = state.get_config("ai_api_key")
    ai_url = state.get_config("ai_base_url")
    ai_model = state.get_config("ai_model")

    try:
        log("➤ Reading staged changes...")
        diff = Path(diff_path).read_text(encoding="utf-8")
        log(f"✓ Diff ingested ({len(diff)} characters)")
        
        log(f"➤ Contacting LLM Intelligence Core ({ai_model})...")
        log(f"✦ {random.choice(quotes)}")
        
        start_time = time.time()
        msg = generate_commit_message(diff, ai_url, ai_key, ai_model, verbose)
        elapsed = time.time() - start_time
        
        if msg:
            state.set_draft(diff_hash, msg, status="success")
            log(f"✓ Semantic synthesis complete in {elapsed:.1f}s")
            log("-" * 50)
            log("FINAL DRAFT:")
            print(msg)
            log("-" * 50)
            log("✦ Intelligence safely persisted to local database.")
            log("✦ Task complete. You may now run `grit commit` to review.")
            
            # Notify on macOS (Success)
            try:
                log("➤ Sending macOS notification...")
                msg_text = "✨ AI draft is ready! Run 'grit commit' to review."
                title_text = "Grit AI Success"
                cmd = f'display notification "{msg_text}" with title "{title_text}" sound name "Glass"'
                
                res = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
                if res.returncode != 0:
                    log(f"✗ Notification command failed with code {res.returncode}")
                    log(f"  Error: {res.stderr.strip()}")
                else:
                    log("✓ Notification sent successfully")
            except Exception as ne:
                log(f"✗ Unexpected error during notification: {ne}")
        else:
            log("✗ LLM returned empty message or failed.")
            state.set_draft(diff_hash, "", status="failure")
            try:
                log("➤ Sending failure notification...")
                msg_text = "AI generation failed. LLM returned empty result."
                title_text = "Grit AI Failed"
                cmd = f'display notification "{msg_text}" with title "{title_text}" sound name "Basso"'
                subprocess.run(["osascript", "-e", cmd], capture_output=True)
            except Exception as ne:
                log(f"✗ Failure notification failed: {ne}")

    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        state.set_draft(diff_hash, str(e), status="failure")
        try:
            # Include error reason in the notification
            error_reason = str(e)[:40]
            msg_text = f"AI Failed: {error_reason}"
            title_text = "Grit AI Error"
            cmd = f'display notification "{msg_text}" with title "{title_text}" sound name "Basso"'
            subprocess.run(["osascript", "-e", cmd], capture_output=True)
        except Exception as ne:
            log(f"✗ Error notification failed: {ne}")
    finally:
        # Cleanup temp diff file
        try:
            if Path(diff_path).exists():
                Path(diff_path).unlink()
                log("➤ Cleaned up temporary diff file.")
        except:
            pass
        if log_stream:
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
def info(ctx: typer.Context):
    """
    Displays high-level system information and command overview.
    """
    # Set the program name for the help output to ensure correct usage string
    ctx.parent.info_name = "grit"
    # Print the banner manually since we want it for info
    print_banner()
    # Print the auto-generated help content (which now includes epilog for the hint)
    console.print(ctx.parent.get_help())


@app.command()
def spread(
        commit_range: Annotated[
            str, typer.Argument(help="Commit range to redistribute (e.g. HEAD~5..HEAD)")],
        push: Annotated[
            bool, typer.Option("--push", "-p", help="Force push changes to remote after spreading")
        ] = False
):
    """
    Redistribute a range of commits across the timeline to fill historical gaps.
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
