import sys
import shutil
import subprocess
import time
import random
from datetime import datetime, timedelta
from typing import Optional, Annotated
import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.padding import Padding
from rich.live import Live

from grit import __version__
from grit.state import StateManager
from grit.allocator import DateAllocator
from grit.executor import execute_git_commit, get_unstaged_files, get_staged_diff, has_staged_files, is_commit_pushed, get_head_author_date
from grit.ai import generate_commit_message
from grit.sync import fetch_github_contributions, get_local_git_stats, merge_sync_data, sync_historical_data
from grit.updater import is_update_available, get_upgrade_command
from grit.dashboard import start_dashboard

# Initialize the state globally for the CLI context
state = StateManager()
console = Console()
err_console = Console(stderr=True)

# Billion Dollar Design System (Official Grit Palette)
# These constants define the sacred visual identity of Grit.
BRAND_COLOR = "bright_cyan"    # Primary teal/blue brand highlight
SUCCESS_COLOR = "spring_green3" # For checkmarks and completion
WARN_COLOR = "gold1"           # For warnings and non-blocking issues
ERROR_COLOR = "deep_pink3"     # For fatal errors or destructive prompts
ACCENT_COLOR = "bright_cyan"   # Secondary highlights (standardized to brand color)

def print_banner(animated: bool = False):
    """
    Renders a premium minimalist banner to provide branding consistency.
    This banner is printed at the start of most high-level user commands.
    """
    ascii_art = r"""
    ██████╗ ██████╗ ██╗████████╗
    ██╔════╝ ██╔══██╗██║╚══██╔══╝
    ██║  ███╗██████╔╝██║   ██║   
    ██║   ██║██╔══██╗██║   ██║   
    ╚██████╔╝██║  ██║██║   ██║   
     ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝   
    """
    
    # Print ASCII art in BRAND_COLOR
    for line in ascii_art.strip("\n").split("\n"):
        console.print(Text(line, style=f"bold {BRAND_COLOR}"))
    
    tagline = Text()
    tagline.append("✦ ", style=BRAND_COLOR)
    tagline.append(f"v{__version__}", style="dim")
    tagline.append(" — Intelligently distribute your commits", style="dim")
    console.print(Padding(tagline, (0, 0, 1, 0)))

def is_config_valid() -> bool:
    """Checks if the core configuration variables are set and not placeholders."""
    required_keys = ["daily_target", "start_date", "github_username", "fill_strategy"]
    for key in required_keys:
        val = state.get_config(key)
        if not val or val == "Not configured" or val == "None" or val == "":
            return False
    return True

def show_victory_animation():
    """
    Renders a brief, premium confetti-like animation for achieving the daily goal.
    Uses random particles and colors to create a 'Victory Burst' effect.
    """
    particles = ["✨", "✦", "✖", "◆", "⭐", "★"]
    colors = ["yellow", "cyan", "magenta", "white", "green"]
    
    with Live(auto_refresh=False, console=console) as live:
        for _ in range(12):  # Brief 1.2s burst
            width = shutil.get_terminal_size().columns
            burst = "".join([
                f"[bold {random.choice(colors)}]{random.choice(particles)}[/] " 
                if random.random() > 0.8 else "  " 
                for _ in range(width // 2)
            ])
            live.update(Padding(Text.from_markup(burst), (0, 2)), refresh=True)
            time.sleep(0.08)
        live.update(Text("")) # Clear after burst

# Main Typer Application Interface
app = typer.Typer(
    help="Grit: Intelligently distribute your git commits to maintain a consistent graph.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=False
)

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

def validate_date(date_text: str) -> bool:
    """Strictly validates YYYY-MM-DD format."""
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_int(val_text: str) -> bool:
    """Validates that the input is a positive integer."""
    try:
        val = int(val_text)
        return val >= 0
    except ValueError:
        return False

def get_key() -> str:
    """Reads a single keypress from the terminal for navigation."""
    import tty
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x03': # Ctrl+C
            raise KeyboardInterrupt
        if ch == '\x1b': # Escape sequence
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

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

    # Interactive Settings Schema
    options = [
        {"id": "target", "title": "Daily Commit Target *", "desc": "Maximum commits to allocate per calendar day.", "key": "daily_target", "default": "1"},
        {"id": "start", "title": "Timeline Start Date *", "desc": "The historical boundary for backfilling (YYYY-MM-DD).", "key": "start_date", "default": datetime.now().strftime("%Y-%m-%d")},
        {"id": "fill", "title": "Allocation Strategy *", "desc": "Where to fill gaps from (today or start_date).", "key": "fill_strategy", "default": "today"},
        {"id": "user", "title": "GitHub Identity *", "desc": "Your public username for contribution graph integration.", "key": "github_username", "default": "Not configured"},
        {"id": "ai_url", "title": "AI: Base URL", "desc": "LLM API endpoint (e.g. http://localhost:11434/v1 for Ollama, or Anthropic/Groq).", "key": "ai_base_url", "default": "Not configured"},
        {"id": "ai_key", "title": "AI: API Key", "desc": "Your API token for the LLM provider (leave blank for local models).", "key": "ai_api_key", "default": ""},
        {"id": "ai_model", "title": "AI: Model Name", "desc": "The model to use (e.g. llama3 for Ollama, claude-3-haiku-20240307).", "key": "ai_model", "default": "Not configured"},
    ]
    
    selected_idx = 0
    error_msg = ""

    # Clear screen for immersive experience
    console.clear()

    with Live(auto_refresh=False, console=console, screen=False) as live:
        while True:
            # 1. Build the Menu UI
            menu_grid = Table.grid(expand=True)
            menu_grid.add_column(width=2) # Left padding
            menu_grid.add_column()
            
            # Header Section
            header = Text.from_markup(f"✦ [bold {BRAND_COLOR}]SETTINGS[/bold {BRAND_COLOR}] [dim]/ Control Center[/dim]\n")
            
            # Options List
            for i, opt in enumerate(options):
                is_selected = i == selected_idx
                current_val = state.get_config(opt["key"]) or opt["default"]
                
                # Title & Value Row
                title_text = Text()
                title_text.append("▶ " if is_selected else "  ", style=f"bold {BRAND_COLOR}" if is_selected else "dim")
                title_text.append(opt["title"], style="bold" if is_selected else "white")
                
                val_text = Text(current_val, style=f"bold {BRAND_COLOR}" if is_selected else "dim")
                
                row_grid = Table.grid(expand=True)
                row_grid.add_column()
                row_grid.add_column(justify="right")
                row_grid.add_row(title_text, val_text)
                
                menu_grid.add_row("", row_grid)
                
                # Subtitle Row
                desc_text = Text(f"    {opt['desc']}", style="dim italic")
                menu_grid.add_row("", desc_text)
                menu_grid.add_row("", "") # Spacer

            # Footer Section
            footer = Table.grid(expand=True)
            footer.add_row(Text("\n  [↑/↓] Navigate  [Enter] Edit  [S] Save & Sync  [Q] Cancel", style="dim"))
            if error_msg:
                footer.add_row(Text(f"  ⚠ {error_msg}", style=f"bold {ERROR_COLOR}"))

            # Assemble full display
            full_content = Group(
                header,
                Padding(Panel(menu_grid, border_style=BRAND_COLOR if not error_msg else ERROR_COLOR, padding=(1, 2)), (0, 2)),
                footer
            )
            
            live.update(full_content, refresh=True)
            error_msg = "" # Clear error after render

            # 2. Input Handling
            key = get_key()
            
            if key == '\x1b[A': # Up
                selected_idx = (selected_idx - 1) % len(options)
            elif key == '\x1b[B': # Down
                selected_idx = (selected_idx + 1) % len(options)
            elif key in ('\r', '\n'): # Enter (Edit)
                opt = options[selected_idx]
                
                # Special Case: Toggle for Strategy
                if opt["id"] == "fill":
                    current_val = state.get_config(opt["key"]) or opt["default"]
                    new_val = "start_date" if current_val == "today" else "today"
                    state.set_config(opt["key"], new_val)
                    continue

                live.stop()
                current_val = state.get_config(opt["key"]) or opt["default"]
                new_val = typer.prompt(f"Edit {opt['title']}", default=current_val)
                
                # Validation Logic
                valid = True
                if opt["id"] == "target" and not validate_int(new_val):
                    error_msg = "Invalid Target: Must be a positive number."
                    valid = False
                elif opt["id"] == "start" and not validate_date(new_val):
                    error_msg = "Invalid Date: Must use YYYY-MM-DD format."
                    valid = False
                elif opt["id"] == "fill" and new_val not in ["today", "start_date"]:
                    error_msg = "Invalid Strategy: Use 'today' or 'start_date'."
                    valid = False
                
                if valid:
                    state.set_config(opt["key"], str(new_val))
                
                live.start()
                console.clear()
            elif key.upper() == 'S':
                live.stop()
                # Ensure all visible options (including defaults) are persisted before sync
                for opt in options:
                    if not state.get_config(opt["key"]):
                        state.set_config(opt["key"], opt["default"])

                final_user = state.get_config("github_username")
                start_date = state.get_config("start_date")
                
                if final_user and final_user != "Not configured" and start_date:
                    with console.status(f"[bold {BRAND_COLOR}]Cold Start: Synchronizing historical data @{final_user}...[/bold {BRAND_COLOR}]", spinner="dots12"):
                        sync_historical_data(state, str(final_user), str(start_date))
                
                console.print(f"\n[bold {SUCCESS_COLOR}]✓ Environment optimized![/bold {SUCCESS_COLOR}] Global historical state synchronized.")
                break
            elif key.upper() == 'Q':
                console.print("[dim]Aborted.[/dim]")
                break

def _sync_github(username: str, year: Optional[int] = None):
    """
    Internal helper to execute a GitHub contribution sync.
    Fetches public HTML graph data and merges it into the local state.
    """
    data = fetch_github_contributions(username, year)
    if data:
        merge_sync_data(state, data, verified_year=year)
        msg = f"for {year}" if year else "for the past 365 days"
        console.print(f"[{SUCCESS_COLOR}]✓[/{SUCCESS_COLOR}] Successfully merged [bold]{len(data)}[/bold] data points from GitHub {msg}.")
    else:
        state.add_synced_year(year) if year else None
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No public contribution data found for GitHub @{username} {year or ''}.")

@app.command()
def sync():
    """
    Self-Healing Engine: Re-aligns the local state with Git and GitHub.
    Performs a three-way merge to ensure the global source of truth is accurate.
    """
    username = state.get_config("github_username")
    
    with console.status(f"[bold {BRAND_COLOR}]Scanning local git log...[/bold {BRAND_COLOR}]", spinner="dots12"):
        local_data = get_local_git_stats()
        merge_sync_data(state, local_data, verified_year=datetime.now().year)
        console.print(f"[{SUCCESS_COLOR}]✓[/{SUCCESS_COLOR}] Scanned local git log. Merged [bold]{len(local_data)}[/bold] commits.")
    
    if username:
        current_year = datetime.now().year
        with console.status(f"[bold {BRAND_COLOR}]Fetching GitHub contributions for @{username}...[/bold {BRAND_COLOR}]", spinner="dots12"):
            _sync_github(username, current_year)
        
        start_date_str = state.get_config("start_date")
        if start_date_str:
            start_year = int(start_date_str.split("-")[0])
            next_sync_year_str = state.get_config("github_next_sync_year")
            next_sync_year = int(next_sync_year_str) if next_sync_year_str else (current_year - 1)
                
            if next_sync_year >= start_year:
                with console.status(f"[bold {BRAND_COLOR}]Backfilling GitHub history for {next_sync_year}...[/bold {BRAND_COLOR}]", spinner="dots12"):
                    _sync_github(username, next_sync_year)
                    state.set_config("github_next_sync_year", str(next_sync_year - 1))
            else:
                console.print(f"[{SUCCESS_COLOR}]✓[/{SUCCESS_COLOR}] GitHub historical data fully synced.")
    else:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No GitHub username configured. Remote sync skipped.")

@app.command()
def status():
    """
    Renders the Grit Intelligence Dashboard.
    Displays metrics, the spillover pipeline, and celebrates daily goals.
    """
    if not is_config_valid():
        err_console.print(f"[{WARN_COLOR}]⚠ Configuration is incomplete. Run `grit config`.[/{WARN_COLOR}]")
        raise typer.Exit(1)
        
    target_str = state.get_config("daily_target")
        
    # Smart Caching for GitHub Sync (15-minute window)
    username = state.get_config("github_username")
    if username:
        last_sync = state.get_last_sync_time()
        if (time.time() - last_sync) > 900: 
            with console.status(f"[dim]Synchronizing intelligence...[/dim]", spinner="dots12"):
                _sync_github(str(username), datetime.now().year)
                state.update_sync_timestamp()
        
        local_data = get_local_git_stats()
        merge_sync_data(state, local_data, verified_year=datetime.now().year)

    target = int(target_str)
    start_date = state.get_config("start_date")
    today_dt = datetime.now()
    today = today_dt.strftime("%Y-%m-%d")
    current_month = today_dt.strftime("%Y-%m")
    
    count = state.get_commit_count(today)
    monthly_count = state.get_monthly_commits(current_month)
    
    # Global Progress & ETA Calculation
    total_days = 0
    total_done = 0
    pending = 0
    progress_pct = 0.0
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        total_days = (today_dt - start_dt).days + 1
        total_required = total_days * target
        
        # FIX: Progress is based on "Effective Commits" (capped at target per day)
        # to show true graph optimization progress.
        effective_done = state.get_effective_commits(start_date, target)
        pending = max(0, total_required - effective_done)
        progress_pct = min(100.0, (effective_done / total_required) * 100) if total_required > 0 else 0.0

    # Victory Celebration Logic
    goal_met = count >= target
    if goal_met and state.get_config("last_celebration") != today:
        show_victory_animation()
        state.set_config("last_celebration", today)

    allocator = DateAllocator(state)
    allocations = allocator.get_status_allocations()
    
    # Dashboard Layout: Top Metrics
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=2)
    grid.add_column(justify="right", ratio=1)
    
    today_progress = f"[{SUCCESS_COLOR if goal_met else BRAND_COLOR}]"
    filled = min(count, target)
    today_progress += "█" * filled + "░" * (target - filled)
    today_progress += f"[/] [bold]{count}/{target}[/] [dim]today[/dim]"
    
    if goal_met:
        today_progress += f" [bold {SUCCESS_COLOR}]OPTIMIZED[/]"
        
    month_text = Text(f"{datetime.now().strftime('%B')} Volume: ", style="dim")
    month_text.append(f"{monthly_count}", style="bold")
    
    grid.add_row(today_progress, month_text)
    console.print(Padding(grid, (1, 2, 0, 2)))

    # Global Journey Progress Bar (Commit Debt)
    if start_date:
        journey_grid = Table.grid(expand=True)
        journey_grid.add_column(ratio=1)
        
        # Build a high-fidelity progress bar
        bar_width = 40
        filled_width = int((progress_pct / 100) * bar_width)
        bar = Text()
        bar.append("━" * filled_width, style=SUCCESS_COLOR)
        bar.append("━" * (bar_width - filled_width), style="dim")
        
        debt_status = "ZERO DEBT" if pending == 0 else f"{pending} COMMITS BEHIND"
        
        # Build composite text object to ensure single-line rendering
        journey_text = Text()
        journey_text.append("✦ ", style=BRAND_COLOR)
        journey_text.append("Optimization Progress: ", style="bold")
        journey_text.append(f"{progress_pct:.1f}% ")
        journey_text.append(bar)
        journey_text.append(" ")
        journey_text.append(debt_status, style=f"bold {WARN_COLOR if pending > 0 else SUCCESS_COLOR}")
        
        journey_grid.add_row(journey_text)
        console.print(Padding(journey_grid, (0, 2, 1, 2)))
    
    # Pipeline View: Detailed breakdown of current and upcoming allocation slots.
    alloc_table = Table(box=None, padding=(0, 2), header_style=f"bold {BRAND_COLOR}", expand=True)
    alloc_table.add_column("Date", style="dim", width=12)
    alloc_table.add_column("Timeline", style="italic dim", width=10)
    alloc_table.add_column("Status", justify="center", width=8)
    alloc_table.add_column("Load", justify="right")
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    for i, alloc in enumerate(allocations):
        date_str = alloc['date']
        is_today = date_str == today
        is_yesterday = date_str == yesterday
        day_count, day_target = alloc['count'], alloc['target']
        
        is_full = day_count >= day_target
        if is_today:
            status_icon = "◆" if not is_full else "✔"
            status_style = SUCCESS_COLOR if is_full else BRAND_COLOR
        else:
            status_icon = "✔" if is_full else "◇"
            status_style = SUCCESS_COLOR if is_full else "dim"
        
        phase = "today" if is_today else ("yesterday" if is_yesterday else ("next fill" if i == 2 else "then fill"))
            
        alloc_table.add_row(date_str, phase, Text(status_icon, style=status_style), f"{day_count}/{day_target}")
    
    # Use BRAND_COLOR for the border if target not met, SUCCESS_COLOR if met
    border = SUCCESS_COLOR if goal_met else BRAND_COLOR
    console.print(Panel(alloc_table, title=f"[bold {border}]Commit Intelligence Pipeline[/bold {border}]", border_style=border, padding=(1, 2)))
    console.print(Padding(Text("ℹ Use `grit config` to adjust strategy. Use `grit info` for help.", style="dim"), (1, 2)))

    # New Release Detection
    latest = is_update_available(state)
    if latest:
        upgrade_cmd = get_upgrade_command()
        upgrade_banner = Text()
        upgrade_banner.append("Upgrade Available: ", style="bold")
        upgrade_banner.append(f"v{__version__} → v{latest}", style=SUCCESS_COLOR)
        upgrade_banner.append(f"\nRun {upgrade_cmd} to stay up to date.", style="dim")
        console.print(Padding(Panel(upgrade_banner, border_style=SUCCESS_COLOR, title=f"[{SUCCESS_COLOR}]New Release[/{SUCCESS_COLOR}]"), (0, 2)))

    # Vanilla Git Status Integration
    if sys.stdout.isatty():
        try:
            if typer.confirm("\nView local repository state?", default=False):
                console.print()
                # Run vanilla git status directly to preserve native git colors and formatting
                subprocess.run(["git", "-c", "color.status=always", "status"])
        except typer.Abort:
            pass

@app.command()
def dashboard(port: int = typer.Option(0, "--port", "-p", help="Port to run the dashboard on")):
    """
    Launches the Grit Intelligence Dashboard in your browser.
    A high-fidelity offline-first GUI for your commit pipeline.
    """
    start_dashboard(port)

@app.command()
def info():
    """
    Displays the comprehensive Grit Manual and Command Reference.
    
    This command provides detailed documentation on every available command,
    all supported flags, and essential usage disclaimers.
    """
    # 1. Introduction
    console.print(Padding(Text("SYSTEM OVERVIEW", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)))
    console.print(Padding(
        "Grit is a high-performance CLI wrapper designed to maintain a consistent "
        "GitHub contribution graph by intelligently distributing your real work across "
        "a timeline. It operates with zero latency and prioritizes repository integrity.",
        (0, 2, 1, 2)
    ))

    # 2. Command Reference (Semantic List with Table-based alignment for flags)
    console.print(Padding(Text("COMMAND REFERENCE", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)))
    
    # Ordered exactly as requested: info, config, commit, status, sync, ungrit, undo
    commands = [
        ("info", "View this comprehensive documentation and command reference.", []),
        ("config", "Enter the interactive Control Center to manage your targets and identity.", [
            ("-t, --target [int]", "Set your daily commit goal."),
            ("-s, --start [date]", "Define the timeline start boundary (YYYY-MM-DD)."),
            ("-u, --username [str]", "Link your GitHub identity for graph synchronization."),
            ("-f, --fill-from [str]", "Allocation strategy: 'today' or 'start_date'.")
        ]),
        ("dashboard", "Launch the high-fidelity web dashboard for visual intelligence.", [
            ("-p, --port [int]", "Specify a custom port for the local server.")
        ]),
        ("commit", "The core wrapper for `git commit`. Run without arguments for the Interactive AI Wizard.", [
            ("[standard git flags]", "All native git arguments are passed through transparently."),
            ("--amend", "Grit detects and warns that amends do not increment daily targets.")
        ]),
        ("status", "View your Intelligence Dashboard, commit capacity, and future pipeline.", []),
        ("sync", "Manually trigger a three-way merge between Local Git, Remote GitHub, and Grit State.", []),
        ("undo", "The 'Quantum Undo'. Safely regress the last commit and restore your streak count.", []),
        ("ungrit", "Securely decommission Grit and delete all local configuration and state.", [
            ("-f, --force", "Bypass the interactive confirmation prompt.")
        ])
    ]

    for cmd, desc, flags in commands:
        # Command Header
        console.print(Padding(Text(f"• {cmd}", style=f"bold {BRAND_COLOR}"), (0, 4)))
        console.print(Padding(desc, (0, 6)))
        
        if flags:
            # We use a Table here to ensure that if a description wraps, it stays
            # perfectly aligned in its own column rather than leaking under the flag name.
            flag_table = Table(box=None, show_header=False, padding=(0, 2), expand=False)
            flag_table.add_column(width=28) # Fixed width for the flag/option name
            flag_table.add_column()         # Description column
            
            for flag, flag_desc in flags:
                flag_table.add_row(
                    Text(f"  {flag}", style=ACCENT_COLOR),
                    Text(flag_desc, style="dim")
                )
            console.print(Padding(flag_table, (0, 6)))
        
        console.print() # Spacer

    # 3. Critical Disclaimers
    console.print(Padding(Text("USAGE CONSTRAINTS & INTEGRITY", style=f"bold {ERROR_COLOR}"), (1, 2, 0, 2)))
    disclaimers = [
        ("Collaboration", "Use Grit primarily in solo projects. Modifying author dates in shared repos can cause timeline drift for others."),
        ("Squash Merges", "Avoid UI-based squash merges on GitHub as they overwrite author dates. Use rebase or merge commits instead."),
        ("Git Amends", "Grit tracks new work only. Amending existing commits will not increment your daily contribution target."),
        ("Empty Commits", "To ensure data accuracy, Grit will only record a transaction if the Git HEAD actually changes.")
    ]

    for title, detail in disclaimers:
        d_text = Text()
        d_text.append(f"• {title}: ", style=f"bold {WARN_COLOR}")
        d_text.append(detail, style="dim")
        console.print(Padding(d_text, (0, 4, 1, 4)))

@app.command()
def undo():
    """
    Quantum Undo: Safely regress the last commit and restore your streak count.
    Warns if the commit has already been pushed to a remote repository.
    """
    # Get HEAD information
    res = subprocess.run(["git", "show", "-s", "--format=%h|%s|%ad", "--date=short", "HEAD"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        console.print(f"[{ERROR_COLOR}]✗ No commits found to undo.[/{ERROR_COLOR}]")
        return
        
    try:
        head_hash, head_msg, head_date = res.stdout.strip().split('|', 2)
    except ValueError:
        head_hash, head_msg, head_date = "HEAD", "Unknown", ""
    
    console.print(Padding(Text("QUANTUM UNDO INITIATED", style=f"bold {ACCENT_COLOR}"), (1, 2, 0, 2)))
    console.print(Padding(f"Target: [bold]{head_hash}[/bold] - {head_msg} ({head_date})", (0, 2)))
    
    if is_commit_pushed():
        console.print(Padding(Text("STATUS: PUSHED TO REMOTE", style=f"bold {ERROR_COLOR}"), (1, 2, 0, 2)))
        console.print(Padding(
            "Consequences:\n"
            "- Undoing this will rewrite public history.\n"
            "- You will need to `git push -f` which can disrupt collaborators.", 
            (0, 2, 1, 2), style="dim"
        ))
        
        choice = typer.prompt("Options: [1] Revert instead (Safe)  [2] Force Undo (Danger)  [3] Cancel", default="3")
        if choice == "1":
            subprocess.run(["git", "revert", "--no-edit", "HEAD"])
            console.print(f"[{SUCCESS_COLOR}]✓ Safe revert completed. A new commit was created to reverse changes.[/{SUCCESS_COLOR}]")
            return
        elif choice == "2":
            console.print(f"[{WARN_COLOR}]Proceeding with force undo...[/{WARN_COLOR}]")
        else:
            console.print("[dim]Aborted.[/dim]")
            return
    else:
        console.print(Padding(Text("STATUS: LOCAL ONLY (SAFE TO UNDO)", style=f"bold {SUCCESS_COLOR}"), (1, 2, 0, 2)))
        console.print(Padding(
            "Consequences:\n"
            "- Commit will be destroyed entirely.\n"
            "- Changes will remain perfectly preserved in your staging area.\n"
            f"- Grit database will decrement the count for {head_date}.", 
            (0, 2, 1, 2), style="dim"
        ))
        if not typer.confirm("Proceed with undo?", default=True):
            console.print("[dim]Aborted.[/dim]")
            return
            
    res = subprocess.run(["git", "reset", "--soft", "HEAD~1"])
    if res.returncode == 0:
        if head_date:
            state.decrement_commit_count(head_date)
            
        # Discover what got restored
        diff_res = subprocess.run(["git", "diff", "--name-only", "--cached"], capture_output=True, text=True)
        files = [f for f in diff_res.stdout.strip().split('\n') if f]
        
        console.print(f"\n[{SUCCESS_COLOR}]✓ Quantum Undo complete.[/{SUCCESS_COLOR}]")
        console.print(f"[dim]Decremented database count for {head_date}.[/dim]")
        if files:
            console.print(f"[dim]Restored {len(files)} file(s) to staging area.[/dim]")
    else:
        console.print(f"[{ERROR_COLOR}]✗ Failed to undo commit.[/{ERROR_COLOR}]")

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def commit(ctx: typer.Context):
    """
    The core wrapper for `git commit`. Automatically allocates dates to preserve streaks.
    Run without arguments to enter the Interactive AI DevX Wizard.
    """
    if not state.get_config("daily_target"):
        err_console.print(f"[{ERROR_COLOR}]✗ Grit is not configured. Run `grit config`.[/{ERROR_COLOR}]")
        raise typer.Exit(1)
        
    args = ctx.args
    
    # INTERACTIVE DEVX WIZARD (Zero arguments)
    if not args:
        # Step A: File Picker (Interactive `git add`)
        if not has_staged_files():
            files = get_unstaged_files()
            if not files:
                console.print(f"[{WARN_COLOR}]No changes to commit.[/{WARN_COLOR}]")
                raise typer.Exit(0)
                
            # Build an intelligent tree structure for the file picker
            dir_groups = {}
            for f in sorted(files):
                parts = f.rsplit('/', 1)
                d = parts[0] + '/' if len(parts) == 2 else ''
                if d not in dir_groups: dir_groups[d] = []
                dir_groups[d].append(f)
                
            items = [{"type": "all", "label": "(Select All)", "files": files, "depth": 0}]
            for d in sorted(dir_groups.keys()):
                if d != '':
                    items.append({"type": "dir", "label": f"[bold]{d}[/bold]", "files": dir_groups[d], "depth": 1})
                    for f in sorted(dir_groups[d]):
                        items.append({"type": "file", "label": f.split('/')[-1], "file": f, "depth": 2})
            if '' in dir_groups:
                for f in sorted(dir_groups['']):
                    items.append({"type": "file", "label": f, "file": f, "depth": 1})
                    
            selected = set()
            idx = 0
            visible_count = 12
            scroll_offset = 0
            
            with Live(auto_refresh=False, console=console, screen=False) as live:
                while True:
                    # Sync scroll offset
                    if idx < scroll_offset:
                        scroll_offset = idx
                    elif idx >= scroll_offset + visible_count:
                        scroll_offset = idx - visible_count + 1

                    grid = Table.grid(expand=True)
                    grid.add_row(Text("Select files to stage (Space to toggle, Enter to confirm, Q to abort):", style=f"bold {ACCENT_COLOR}"))
                    grid.add_row("") # Spacer
                    
                    if scroll_offset > 0:
                        grid.add_row(Text.from_markup(f"      ↑ [dim](more files above)[/dim]", style=BRAND_COLOR))

                    # File selection table
                    table = Table(box=None, padding=(0, 1), show_header=False, expand=True)
                    table.add_column("Cursor", width=3, justify="center")
                    table.add_column("Checkbox", width=5, justify="center")
                    table.add_column("Path")

                    for i in range(scroll_offset, min(scroll_offset + visible_count, len(items))):
                        item = items[i]
                        is_cur = i == idx
                        
                        if item["type"] == "file":
                            is_sel = item["file"] in selected
                            is_partial = False
                        else:
                            fs = item["files"]
                            is_sel = len(fs) > 0 and all(f in selected for f in fs)
                            is_partial = len(fs) > 0 and any(f in selected for f in fs) and not is_sel
                            
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
                            
                        table.add_row(
                            Text(cursor, style=f"bold {BRAND_COLOR}"),
                            Text.from_markup(box),
                            Text.from_markup(f"{indent}{item['label']}", style=style)
                        )
                    
                    grid.add_row(table)
                    
                    if scroll_offset + visible_count < len(items):
                         grid.add_row(Text.from_markup(f"      ↓ [dim](more files below)[/dim]", style=BRAND_COLOR))
                        
                    live.update(Padding(grid, (1, 2)), refresh=True)
                    key = get_key()
                    
                    if key == '\x1b[A': idx = (idx - 1) % len(items)
                    elif key == '\x1b[B': idx = (idx + 1) % len(items)
                    elif key == ' ': 
                        item = items[idx]
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
                
            subprocess.run(["git", "add"] + list(selected))
            console.print(f"[{SUCCESS_COLOR}]✓ Staged {len(selected)} files.[/{SUCCESS_COLOR}]")
        
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
                        style = f"bold {BRAND_COLOR}" if is_cur else "dim"
                        grid.add_row(Text(f"{prefix}{opt}", style=style))
                    
                    live.update(Padding(grid, (1, 2)), refresh=True)
                    key = get_key()
                    
                    if key == '\x1b[A': idx = (idx - 1) % len(options)
                    elif key == '\x1b[B': idx = (idx + 1) % len(options)
                    elif key in ('\r', '\n'): break
            
            choice = options[idx]
            if choice == "↩ Go Back":
                 # Simple way to go back: restart the script or just call commit again?
                 # Actually, we can just reset staged files and loop back to the start.
                 subprocess.run(["git", "reset"])
                 return commit(ctx)
            
            if choice == "✨ Auto-generate (AI)":
                diff = get_staged_diff()
                with console.status(f"[bold {BRAND_COLOR}]AI analyzing diff...[/bold {BRAND_COLOR}]", spinner="dots12"):
                    msg = generate_commit_message(diff, ai_url, ai_key, ai_model)
                if msg:
                    console.print(f"[{SUCCESS_COLOR}]✓ Generated:[/{SUCCESS_COLOR}] {msg}")
                    final_msg = msg
                else:
                    console.print(f"[{ERROR_COLOR}]✗ AI generation failed. Falling back to manual.[/{ERROR_COLOR}]")
                    choice = "feat" # Fallback
                
            if not final_msg:
                scope = typer.prompt("Scope (optional, press Enter to skip)", default="", show_default=False)
                desc = typer.prompt("Description")
                scope_str = f"({scope})" if scope else ""
                final_msg = f"{choice}{scope_str}: {desc}"
                
            args = ["-m", final_msg]
            console.print()
            break

    # -- STANDARD EXECUTION FLOW --
    if "--amend" in args:
        console.print(Padding(Text("! Warning: Amends are not tracked by Grit.", style=WARN_COLOR), (1, 0)))
        raise typer.Exit(subprocess.run(["git", "commit"] + args).returncode)
        
    allocator = DateAllocator(state)
    target_date = allocator.get_next_date()
    target_year = int(target_date.split('-')[0])
    
    if not state.is_year_synced(target_year):
        user = state.get_config("github_username")
        with console.status(f"[bold {BRAND_COLOR}]Verifying {target_year} integrity...[/bold {BRAND_COLOR}]", spinner="dots12"):
            if user: _sync_github(str(user), target_year)
            merge_sync_data(state, get_local_git_stats(), verified_year=target_year)
        target_date = allocator.get_next_date()
    
    if execute_git_commit(args, target_date, state):
        console.print(f"[{SUCCESS_COLOR}]✓[/{SUCCESS_COLOR}] Transaction successful. Allocated to [bold]{target_date}[/bold].")
        
        # Step D: Smart Push (Only if zero-arg wizard was used)
        if not ctx.args:
            if typer.confirm(f"🚀 Push commit for {target_date} to remote?", default=True):
                res = subprocess.run(["git", "push"])
                if res.returncode != 0:
                    console.print(Padding(Text("⚠️ Remote is ahead or rejected push.", style=WARN_COLOR), (1, 0, 0, 0)))
                    if typer.confirm("Pull and rebase automatically?", default=True):
                        subprocess.run(["git", "pull", "--rebase"])
                        subprocess.run(["git", "push"])
            
        # Trigger Status implicitly after EVERY commit to show pipeline and git status
        ctx.invoke(status)
    else:
        raise typer.Exit(1)

@app.command()
def ungrit(force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")):
    """Securely decommission Grit and delete local state."""
    if not force:
        console.print(f"\n[{ERROR_COLOR}]Destroy local state?[/{ERROR_COLOR}]")
        if not typer.confirm("This will permanently remove all configuration."):
            console.print("[dim]Aborted.[/dim]")
            return
    db_dir = state.db_path.parent
    if db_dir.exists():
        shutil.rmtree(db_dir)
        console.print(f"[{SUCCESS_COLOR}]✓[/{SUCCESS_COLOR}] Grit decommissioned.")
    else:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No Grit configuration found.")

if __name__ == "__main__":
    app()
