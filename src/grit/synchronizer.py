import subprocess
import httpx
from datetime import datetime
from bs4 import BeautifulSoup
from collections import Counter
from typing import Dict
from grit.state import StateManager

def parse_local_git_log(log_output: str) -> Dict[str, int]:
    """
    Parses `git log --format="%ad" --date=short` output.
    Returns a dictionary of {date: count}.
    """
    counts = Counter()
    for line in log_output.strip().split('\n'):
        if line:
            counts[line] += 1
    return dict(counts)

def get_local_git_stats(author: str = None, since: str = None) -> Dict[str, int]:
    """
    Executes git log on the local repository to build a map of daily commits.
    """
    cmd = ["git", "log", "--format=%ad", "--date=short"]
    if author:
        cmd.append(f"--author={author}")
    if since:
        cmd.append(f"--since={since}")
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return parse_local_git_log(result.stdout)
    except subprocess.CalledProcessError:
        return {}

from grit.constants import GITHUB_CONTRIBUTIONS_TIMEOUT

def fetch_github_contributions(username: str, year: int = None) -> dict[str, int]:

    """
    Silently scrapes the user's public GitHub contribution graph without requiring a PAT.
    If year is provided, it fetches that specific historical year.
    Returns a dictionary of {date: count}.
    """
    url = f"https://github.com/users/{username}/contributions"
    if year:
        url += f"?from={year}-01-01&to={year}-12-31"
        
    try:
        response = httpx.get(url, timeout=GITHUB_CONTRIBUTIONS_TIMEOUT)
        response.raise_for_status()
    except (httpx.HTTPStatusError, httpx.RequestError, Exception):
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    contributions = {}
    
    days = soup.find_all('td', class_='ContributionCalendar-day')
    for day in days:
        date_str = day.get('data-date')
        if not date_str:
            continue
            
        # GitHub uses tool-tips mapped by ID to show exact contribution numbers
        day_id = day.get('id')
        tool_tip = soup.find('tool-tip', {'for': day_id})
        count = 0
        
        if tool_tip:
            text = tool_tip.text.strip().lower()
            if "no contributions" in text:
                count = 0
            else:
                # Text is typically formatted as "5 contributions on January 1, 2024"
                try:
                    count_str = text.split()[0]
                    # Handle numbers like "1,234" just in case
                    count = int(count_str.replace(',', '')) 
                except (ValueError, IndexError):
                    count = 0
                    
        if count > 0:
            contributions[date_str] = count

    return contributions

def merge_sync_data(state: StateManager, sync_data: Dict[str, int], verified_year: int = None):
    """
    Merges sync data into the local DB using a "Lower Bound Update" rule.
    Grit will NEVER overwrite a higher local count with a lower remote count.
    
    If 'verified_year' is provided, it marks that year as fully synchronized in the DB.
    """
    for date, count in sync_data.items():
        current = state.get_commit_count(date)
        if count > current:
            state.set_commit_count(date, count)
            
    # Mark the year as synchronized if explicitly verified.
    if verified_year:
        state.add_synced_year(verified_year)
    else:
        # If no explicit year, we infer from data (e.g. current year)
        # But usually we want explicit verification for historical safety.
        pass

def sync_historical_data(state: StateManager, username: str, start_date_str: str, on_progress=None):
    """
    Performs a full historical synchronization from the start date's year to today.
    Calls on_progress(year) if provided.
    """
    current_year = datetime.now().year
    
    try:
        start_year = int(start_date_str.split("-")[0])
    except (ValueError, IndexError):
        return
        
    for year in range(start_year, current_year + 1):
        if on_progress:
            on_progress(year)
        data = fetch_github_contributions(username, year)
        if data:
            merge_sync_data(state, data, verified_year=year)
        else:
            state.add_synced_year(year)
