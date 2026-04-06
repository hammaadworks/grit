from typing import Optional
from datetime import datetime
from grit.ui import console, SUCCESS_COLOR, WARN_COLOR, BRAND_COLOR
from grit.state import StateManager
from grit.sync import fetch_github_contributions, merge_sync_data, get_local_git_stats

def _sync_github(state: StateManager, username: str, year: Optional[int] = None):
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

def run_sync(state: StateManager):
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
            _sync_github(state, username, current_year)
        
        start_date_str = state.get_config("start_date")
        if start_date_str:
            start_year = int(start_date_str.split("-")[0])
            next_sync_year_str = state.get_config("github_next_sync_year")
            next_sync_year = int(next_sync_year_str) if next_sync_year_str else (current_year - 1)
                
            if next_sync_year >= start_year:
                with console.status(f"[bold {BRAND_COLOR}]Backfilling GitHub history for {next_sync_year}...[/bold {BRAND_COLOR}]", spinner="dots12"):
                    _sync_github(state, username, next_sync_year)
                    state.set_config("github_next_sync_year", str(next_sync_year - 1))
            else:
                console.print(f"[{SUCCESS_COLOR}]✓[/{SUCCESS_COLOR}] GitHub historical data fully synced.")
    else:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No GitHub username configured. Remote sync skipped.")
