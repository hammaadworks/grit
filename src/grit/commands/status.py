import subprocess
import sys
import time
from datetime import datetime

import typer
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from grit import __version__
from grit.allocator import DateAllocator
from grit.commands.sync import _sync_github
from grit.state import StateManager
from grit.sync import get_local_git_stats, merge_sync_data
from grit.ui import (BRAND_COLOR, console, show_victory_animation, SUCCESS_COLOR,
                     WARN_COLOR)
from grit.updater import get_upgrade_command, is_update_available


def run_status(state: StateManager, yes: bool = False):
    """
    Renders the Grit Intelligence Dashboard.
    Displays metrics, the spillover pipeline, and celebrates daily goals.
    """
    target_str = state.get_config("daily_target")
    start_date = state.get_config("start_date")
    username = state.get_config("github_username")

    # 1. Update Check & GitHub Sync (Grouped under a single spinner if possible)
    last_sync = state.get_last_sync_time()
    last_update_check = state.get_config("last_update_check")
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    needs_sync = username and (time.time() - last_sync) > 3600
    needs_update_check = last_update_check != today_date
    
    if needs_sync or needs_update_check:
        with console.status(
                "[dim]Synchronizing intelligence (Remote)...[/dim]", spinner="dots12"
                ):
            if needs_update_check:
                is_update_available(state)
            
            if needs_sync:
                _sync_github(state, str(username), datetime.now().year)
                state.update_sync_timestamp()

    # 2. Local Intelligence Verification
    if username:
        with console.status(
                "[dim]Synchronizing intelligence (Local)...[/dim]", spinner="dots12"
                ):
            local_data = get_local_git_stats(since=start_date)
            merge_sync_data(state, local_data, verified_year=datetime.now().year)

    target = int(target_str)
    today_dt = datetime.now()
    today = today_dt.strftime("%Y-%m-%d")
    current_month = today_dt.strftime("%Y-%m")

    count = state.get_commit_count(today)
    monthly_count = state.get_monthly_commits(current_month)

    # Global Progress & ETA Calculation
    total_days = 0
    pending = 0
    progress_pct = 0.0

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        total_days = (today_dt - start_dt).days + 1
        total_required = total_days * target

        # Progress is based on "Effective Commits" (capped at target per day)
        effective_done = state.get_effective_commits(start_date, target)
        pending = max(0, total_required - effective_done)
        progress_pct = min(
            100.0, (effective_done / total_required) * 100
            ) if total_required > 0 else 0.0

    # Victory Celebration Logic
    goal_met = count >= target
    if goal_met and state.get_config("last_celebration") != today:
        show_victory_animation()
        state.set_config("last_celebration", today)

    allocator = DateAllocator(state)
    allocations = allocator.get_status_allocations()
    next_date = allocator.get_next_date()

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
        journey_text.append(
            debt_status, style=f"bold {WARN_COLOR if pending > 0 else SUCCESS_COLOR}"
            )

        journey_grid.add_row(journey_text)
        console.print(Padding(journey_grid, (0, 2, 1, 2)))

    # Pipeline View: Detailed breakdown of current and upcoming allocation slots.
    alloc_table = Table(
        box=None, padding=(0, 2), header_style=f"bold {BRAND_COLOR}", expand=True
        )
    alloc_table.add_column("Date", style="dim", width=12)
    alloc_table.add_column("Timeline", style="italic dim", width=10)
    alloc_table.add_column("Status", justify="center", width=8)
    alloc_table.add_column("Load", justify="right")

    for i, alloc in enumerate(allocations):
        date_str = alloc['date']
        is_today = date_str == today
        day_count, day_target = alloc['count'], alloc['target']

        is_full = day_count >= day_target
        is_next_fill = date_str == next_date

        if is_today:
            status_icon = "◆" if not is_full else "✔"
            status_style = SUCCESS_COLOR if is_full else BRAND_COLOR
        else:
            status_icon = "✔" if is_full else "◇"
            status_style = SUCCESS_COLOR if is_full else "dim"

        if i == 0:
            phase = "today"
        elif i == 1:
            phase = "next"
        elif i == 2:
            phase = "then"
        else:
            phase = "later"

        row_style = f"on {BRAND_COLOR} bold white" if is_next_fill else ""

        alloc_table.add_row(
            date_str,
            phase,
            Text(status_icon, style=status_style),
            f"{day_count}/{day_target}",
            style=row_style
        )

    # Use BRAND_COLOR for the border if target not met, SUCCESS_COLOR if met
    border = SUCCESS_COLOR if goal_met else BRAND_COLOR
    console.print(
        Panel(
            alloc_table,
            title=f"[bold {border}]Commit Intelligence Pipeline[/bold {border}]",
            border_style=border, padding=(1, 2)
            )
        )
    console.print(
        Padding(
            Text(
                "ℹ Use `grit config` to adjust strategy. Use `grit info` for help.",
                style="dim"
                ), (1, 2)
            )
        )

    # New Release Detection
    latest = state.get_config("latest_version_available")
    if latest:
        upgrade_cmd = get_upgrade_command()
        upgrade_banner = Text()
        upgrade_banner.append("Upgrade Available: ", style="bold")
        upgrade_banner.append(f"v{__version__} → v{latest}", style=SUCCESS_COLOR)
        upgrade_banner.append(f"\nRun {upgrade_cmd} to stay up to date.", style="dim")
        console.print(
            Padding(
                Panel(
                    upgrade_banner, border_style=SUCCESS_COLOR,
                    title=f"[{SUCCESS_COLOR}]New Release[/{SUCCESS_COLOR}]"
                    ), (0, 2)
                )
            )

    # Vanilla Git Status Integration
    if sys.stdout.isatty():
        try:
            show_status = yes
            if not show_status:
                show_status = typer.confirm("\nView local repository state?", default=False)
            
            if show_status:
                console.print()
                # Run vanilla git status directly to preserve native git colors and
                # formatting
                subprocess.run(["git", "-c", "color.status=always", "status"])
        except typer.Abort:
            pass
