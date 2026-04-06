import os
import subprocess
from datetime import datetime
from grit.state import StateManager

def get_git_timestamp(date_str: str) -> str:
    """
    Generates a valid Git ISO-8601 timestamp for injection.
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
        # -uall shows individual untracked files
        result = subprocess.run(["git", "status", "--porcelain", "-uall"], capture_output=True, text=True)
        # We must NOT strip the entire output as it removes leading spaces from the first line
        lines = result.stdout.splitlines()
        files = []
        for line in lines:
            if not line or len(line) < 4: continue
            
            status_code = line[:2]
            filename_part = line[3:]
            
            # If renamed (R) or copied (C), git shows "old -> new"
            if 'R' in status_code or 'C' in status_code:
                if " -> " in filename_part:
                    filename = filename_part.split(" -> ")[-1].strip('"')
                else:
                    filename = filename_part.strip('"')
            else:
                filename = filename_part.strip('"')
                
            files.append(filename)
        return files
    except Exception:
        return []

def get_status_files() -> list[tuple[str, str]]:
    """Returns a list of (filename, status) tuples from git status."""
    try:
        # -uall shows individual untracked files
        result = subprocess.run(["git", "status", "--porcelain", "-uall"], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        files = []
        for line in lines:
            if not line or len(line) < 4: continue
            
            status_code = line[:2]
            filename_part = line[3:]
            
            # If renamed (R) or copied (C), git shows "old -> new"
            if 'R' in status_code or 'C' in status_code:
                if " -> " in filename_part:
                    filename = filename_part.split(" -> ")[-1].strip('"')
                else:
                    filename = filename_part.strip('"')
            else:
                filename = filename_part.strip('"')

            # Simplified mapping:
            # 1. Deleted takes precedence (D or d)
            if 'D' in status_code:
                status = 'deleted'
            # 2. Untracked (??) or Added (A) is New
            elif status_code == '??' or 'A' in status_code:
                status = 'new'
            # 3. Everything else is Modified
            else:
                status = 'modified'
            
            files.append((filename, status))
        return files
    except Exception:
        return []

def get_staged_files() -> list[str]:
    """Returns a list of files currently in the staging area."""
    try:
        result = subprocess.run(["git", "diff", "--name-only", "--cached"], capture_output=True, text=True)
        return [f for f in result.stdout.strip().split('\n') if f]
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
    Executes the vanilla `git commit` command with the injected GIT_AUTHOR_DATE 
    and GIT_COMMITTER_DATE to ensure a consistent, uniform backdated history.
    If the commit succeeds AND the HEAD hash changed, increments the local state.
    """
    timestamp = get_git_timestamp(target_date)
    
    # Capture HEAD state before the operation
    old_head = get_head_hash()
    
    # Copy existing environment to ensure things like SSH agents/GPG keys still work
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = timestamp
    env["GIT_COMMITTER_DATE"] = timestamp
    
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

def execute_grit_spread(commit_hashes: list[str], hash_to_date: dict[str, str], state: StateManager) -> bool:
    """
    Redistributes a range of commits across the timeline.
    Uses a temporary branch and cherry-picking to rewrite history safely.
    """
    if not commit_hashes:
        return False
        
    # Safety Check: Is the working directory clean?
    status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if status_res.stdout.strip():
        print("Your working directory has unstaged changes. Please commit or stash them before spreading.")
        return False

    original_branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
    is_detached = not original_branch
    if is_detached:
        # Detached HEAD? Let's use the current hash
        original_branch = get_head_hash()

    # Base is the parent of the first commit in the range
    first_commit = commit_hashes[0]
    base_res = subprocess.run(["git", "rev-parse", f"{first_commit}^1"], capture_output=True, text=True)
    
    if base_res.returncode != 0:
        # If no parent exists, it's a root commit. We can't easily rebase/cherry-pick it onto 'nothing'
        # without --orphan, but for simplicity we'll assume the range starts AFTER the root commit
        # or we'll handle it by checking out the root commit and amending it.
        # Actually, if it's the root, we can use the root itself as the starting point.
        is_root = True
        base_commit = first_commit
    else:
        is_root = False
        base_commit = base_res.stdout.strip()
    
    temp_branch = f"grit-spread-{int(datetime.now().timestamp())}"
    
    try:
        if is_root:
            # If the first commit is root, we checkout it and amend it first.
            subprocess.run(["git", "checkout", "-b", temp_branch, base_commit], check=True, capture_output=True)
            target_date = hash_to_date[first_commit]
            timestamp = get_git_timestamp(target_date)
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = timestamp
            env["GIT_COMMITTER_DATE"] = timestamp
            subprocess.run(["git", "commit", "--amend", "--no-edit"], env=env, check=True, capture_output=True)
            # Remaining hashes to cherry-pick
            remaining_hashes = commit_hashes[1:]
        else:
            # 1. Create temporary branch at base
            subprocess.run(["git", "checkout", "-b", temp_branch, base_commit], check=True, capture_output=True)
            remaining_hashes = commit_hashes
        
        # 2. Cherry-pick and rewrite each remaining commit
        for commit_hash in remaining_hashes:
            target_date = hash_to_date[commit_hash]
            timestamp = get_git_timestamp(target_date)
            
            cp_res = subprocess.run(["git", "cherry-pick", commit_hash], capture_output=True)
            if cp_res.returncode != 0:
                print(f"Conflict detected while cherry-picking {commit_hash}. Aborting spread.")
                subprocess.run(["git", "cherry-pick", "--abort"])
                raise Exception("Cherry-pick conflict")
            
            # Amend the commit with the new date
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = timestamp
            env["GIT_COMMITTER_DATE"] = timestamp
            
            subprocess.run(["git", "commit", "--amend", "--no-edit"], env=env, check=True, capture_output=True)
            
        # 3. Success! Move back and reset
        subprocess.run(["git", "checkout", original_branch], check=True, capture_output=True)
        subprocess.run(["git", "reset", "--hard", temp_branch], check=True, capture_output=True)
        
        # 4. Update state only after successful rebase
        for target_date in hash_to_date.values():
            state.increment_commit_count(target_date)
            
        return True
        
    except Exception as e:
        # Attempt to return to original state
        subprocess.run(["git", "checkout", original_branch], capture_output=True)
        return False
    finally:
        # Cleanup
        subprocess.run(["git", "branch", "-D", temp_branch], capture_output=True)
