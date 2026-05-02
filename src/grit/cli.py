import sys
from typing import Annotated, Optional

import typer

from grit import __version__
from grit.commands.commit import run_commit
from grit.commands.config import run_config_interactive
from grit.commands.log import run_log
from grit.commands.move import run_move
from grit.commands.status import run_status
from grit.commands.sync import run_sync
from grit.commands.sponsor import run_sponsor
from grit.commands.dashboard import run_dashboard
from grit.commands.spread import run_spread
from grit.commands.undo import run_undo
from grit.commands.ungrit import run_ungrit
from grit.commands.branch import run_branch_manager

from grit.state import StateManager
from grit.ui import (BRAND_COLOR, console, err_console, ERROR_COLOR,
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
        if not val or val in ("Not configured", "None", ""):
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
    setup_logger(verbose=logs)

    interactive_cmds = ["config", "dashboard", "dash", "move"]
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
    elif ctx.invoked_subcommand not in ["config", "ungrit", "info", "dashboard"] and not is_config_valid():
        err_console.print(
            f"[{WARN_COLOR}]⚠ Configuration is incomplete. Launching Control "
            f"Center...[/{WARN_COLOR}]"
            )
        ctx.invoke(config)
        raise typer.Exit()


@app.command()
def config(
        target: Annotated[Optional[int], typer.Option("--target", "-t", help="Daily commit target")] = None,
        start: Annotated[Optional[str], typer.Option("--start", "-s", help="Start date (YYYY-MM-DD)")] = None,
        username: Annotated[Optional[str], typer.Option("--username", "-u", help="GitHub username")] = None,
        fill_from: Annotated[Optional[str], typer.Option("--fill-from", "-f", help="Strategy: 'today' or 'start_date'")] = None,
        ai_url: Annotated[Optional[str], typer.Option("--ai-url", help="LLM API base URL")] = None,
        ai_key: Annotated[Optional[str], typer.Option("--ai-key", help="LLM API key")] = None,
        ai_model: Annotated[Optional[str], typer.Option("--ai-model", help="LLM model name")] = None
):
    """Enter the interactive Control Center or apply headless configuration."""
    if any(v is not None for v in [target, start, username, fill_from, ai_url, ai_key, ai_model]):
        if target is not None: state.set_config("daily_target", str(target))
        if start is not None: state.set_config("start_date", start)
        if username is not None: state.set_config("github_username", username)
        if fill_from is not None:
            if fill_from in ["today", "start_date"]:
                state.set_config("fill_strategy", fill_from)
            else:
                err_console.print(f"[{ERROR_COLOR}]✗ Invalid fill strategy.[/{ERROR_COLOR}]")
                raise typer.Exit(1)
        if ai_url is not None: state.set_config("ai_base_url", ai_url)
        if ai_key is not None: state.set_config("ai_api_key", ai_key)
        if ai_model is not None: state.set_config("ai_model", ai_model)
        console.print(f"[{SUCCESS_COLOR}]✓ Headless configuration applied.[/{SUCCESS_COLOR}]")
        return

    run_config_interactive(state)


@app.command()
def sync():
    """Re-aligns the local state with Git and GitHub (Three-way merge)."""
    run_sync(state)


@app.command()
def status(
        yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False
):
    """Renders the Intelligence Dashboard and metrics."""
    run_status(state, yes=yes)


@app.command(name="dash", hidden=True)
def dash(
        port: int = typer.Option(0, "--port", "-p", help="Port to run on"),
        logs: bool = typer.Option(False, "--logs", "-l", help="Show server logs"),
        stop: bool = typer.Option(False, "--stop", "-s", help="Stop background dashboard")
):
    """Alias for dashboard."""
    run_dashboard(state, port, logs, stop)


@app.command()
def dashboard(
        port: int = typer.Option(0, "--port", "-p", help="Port to run on"),
        logs: bool = typer.Option(False, "--logs", "-l", help="Show server logs"),
        stop: bool = typer.Option(False, "--stop", "-s", help="Stop background dashboard")
):
    """Launches the high-fidelity web dashboard."""
    run_dashboard(state, port, logs, stop)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )
def commit(
        ctx: typer.Context,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Detailed AI logs")] = False,
        ai: Annotated[bool, typer.Option("--ai", "-a", help="Display the AI system prompt and user rules instead of committing")] = False,
        logs: Annotated[bool, typer.Option("--logs", help="System-level logging")] = False
):
    """Intelligently allocates dates and preserved streaks via git commit."""
    if logs: setup_logger(verbose=True)
    run_commit(state, ctx, verbose=verbose, ai=ai)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )
def log(ctx: typer.Context):
    """A human-readable git log on jetpack rollerskates."""
    run_log(ctx)


@app.command()
def move(push: Annotated[bool, typer.Option("--push", "-p", help="Force push changes")] = False):
    """Interactive history re-allocator."""
    run_move(state, push=push)


@app.command(rich_help_panel="Maintenance & Support")
def sponsor():
    """Support the ongoing development of Grit. 💖"""
    run_sponsor()


@app.command(rich_help_panel="Maintenance & Support")
def info(ctx: typer.Context):
    """Displays high-level system information and command overview."""
    ctx.parent.info_name = "grit"
    print_banner()
    console.print(ctx.parent.get_help())


@app.command()
def branch():
    """Unified Context & Worktree Manager."""
    run_branch_manager(state)


@app.command()
def spread(
        commit_range: Annotated[str, typer.Argument(help="Commit range (e.g. HEAD~5..HEAD)")],
        push: Annotated[bool, typer.Option("--push", "-p", help="Force push after spreading")] = False
):
    """Redistribute a range of commits across the timeline."""
    run_spread(state, commit_range, push)


@app.command()
def undo():
    """Safely regress the last commit and restore your streak count."""
    run_undo(state)


@app.command(rich_help_panel="Maintenance & Support")
def ungrit(force: Annotated[bool, typer.Option("--force", "-f", help="Bypass confirmation")] = False):
    """Decommission Grit and delete all local configuration and state."""
    run_ungrit(state, force)


if __name__ == "__main__":
    app()
