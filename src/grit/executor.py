import os
import subprocess
from datetime import datetime
from grit.state import StateManager

def get_git_timestamp(date_str: str) -> str:
    """
    Generates a valid GIT_AUTHOR_DATE timestamp.
    Combines the target YYYY-MM-DD with the current system time and timezone.
    Internal calculation is done in UTC to prevent drift during travel.
    """
    now = datetime.now()
    year, month, day = map(int, date_str.split('-'))
    
    # Standardize to target date with current time
    target_dt = now.replace(year=year, month=month, day=day)
    
    # Capture the local timezone offset to maintain 'Billion Dollar' accuracy
    # while standardizing internal state.
    local_astimezone = target_dt.astimezone()
    
    # Format according to Git ISO 8601 strict format: YYYY-MM-DD HH:MM:SS +/-HHMM
    return local_astimezone.strftime("%Y-%m-%d %H:%M:%S %z")

def get_head_hash() -> str:
    """Returns the current HEAD hash, or empty string if no commits yet."""
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return ""

def get_head_author_date() -> str:
    """Returns the YYYY-MM-DD author date of the current HEAD commit."""
    try:
        result = subprocess.run(["git", "show", "-s", "--format=%ad", "--date=short", "HEAD"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return ""

def is_commit_pushed() -> bool:
    """Checks if the local HEAD has been pushed to a remote tracking branch."""
    try:
        # If this command returns output, the commit exists on a remote branch
        result = subprocess.run(["git", "branch", "-r", "--contains", "HEAD"], capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except Exception:
        return False

def get_unstaged_files() -> list[str]:
    """Returns a list of modified or untracked files from git status."""
    try:
        # --porcelain format: XY filename
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        # We must NOT strip the entire output as it removes leading spaces from the first line
        lines = result.stdout.splitlines()
        files = []
        for line in lines:
            if not line or len(line) < 4: continue
            
            # In porcelain v1, the filename starts at index 3.
            # We don't strip the line before this to preserve the fixed-width status columns.
            filename = line[3:].strip('"')
            files.append(filename)
        return files
    except Exception:
        return []

def get_staged_diff() -> str:
    """Returns the raw diff of currently staged files for AI context."""
    try:
        result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return ""

def has_staged_files() -> bool:
    """Checks if there are any files currently added to the staging area."""
    try:
        result = subprocess.run(["git", "diff", "--name-only", "--cached"], capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except Exception:
        return False

def execute_git_commit(args: list[str], target_date: str, state: StateManager) -> bool:
    """
    Executes the vanilla `git commit` command with the injected GIT_AUTHOR_DATE.
    If the commit succeeds AND the HEAD hash changed, increments the local state.
    """
    timestamp = get_git_timestamp(target_date)
    
    # Capture HEAD state before the operation
    old_head = get_head_hash()
    
    # Copy existing environment to ensure things like SSH agents/GPG keys still work
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = timestamp
    
    # We explicitly do not set GIT_COMMITTER_DATE to preserve real chronological history
    result = subprocess.run(["git", "commit"] + args, env=env)
    
    if result.returncode == 0:
        # Final Verification: Did the commit actually happen?
        # Pre-commit hooks might exit 0 but cancel the commit, or the user
        # might have used --allow-empty (which we track) or had nothing staged.
        new_head = get_head_hash()
        if new_head != old_head:
            state.increment_commit_count(target_date)
            return True
        else:
            # If the hash didn't change, no commit was created.
            # We don't increment the DB to maintain 'Billion Dollar' accuracy.
            return False
    
    return False
