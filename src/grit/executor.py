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
    """Returns a sanitized diff of currently staged files for AI context."""
    from grit.constants import AI_FILE_EXCLUDE
    
    try:
        # Build exclusion pathspecs: :(exclude)*.lock :(exclude)*.toml etc.
        exclude_args = [f":(exclude){pattern}" for pattern in AI_FILE_EXCLUDE]
        
        # Use --no-prefix and --unified=3 to keep it concise
        cmd = ["git", "diff", "--staged", "--no-color", "--no-prefix", "--"] + exclude_args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return _sanitize_diff(result.stdout)
    except Exception:
        return ""

def get_diff_hash(diff: str) -> str:
    """Returns a SHA-256 hash of the diff string for caching purposes."""
    import hashlib
    return hashlib.sha256(diff.encode('utf-8')).hexdigest()

def _sanitize_diff(raw_diff: str) -> str:
    """
    Cleans up git diff output to make it more readable for LLMs.
    Removes index lines, metadata, and reduces overhead.
    """
    if not raw_diff.strip():
        return ""

    clean_lines = []
    for line in raw_diff.splitlines():
        # Skip noise metadata
        if line.startswith(("index ", "diff --git ", "--- ", "+++ ")):
            # We keep the filename info if it's the 'diff --git' line but simplify it
            if line.startswith("diff --git "):
                clean_lines.append(f"\nFILE: {line.split(' ')[-1]}")
            continue
        
        # Keep hunk headers but clean them up (@@ -1,1 +1,1 @@ -> [Line 1])
        if line.startswith("@@"):
            clean_lines.append("[Hunk Header]")
            continue

        clean_lines.append(line)

    return "\n".join(clean_lines).strip()

def has_staged_files() -> bool:
    """Checks if there are any files currently added to the staging area."""
    try:
        result = subprocess.run(["git", "diff", "--name-only", "--cached"], capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except Exception:
        return False

def has_unstaged_files() -> bool:
    """Checks if there are any files currently modified but not staged."""
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
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
    
    # Inject custom editor if configured
    editor_command = state.get_config("editor_command")
    if editor_command:
        env["GIT_EDITOR"] = editor_command
    
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
    if has_unstaged_files():
        print("Your working directory has unstaged changes. Please commit or stash them before spreading.")
        return False

    original_branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
    is_detached = not original_branch
    if is_detached:
        # Detached HEAD? Let's use the current hash
        original_branch = get_head_hash()

    temp_branch = f"grit-spread-{int(datetime.now().timestamp())}"
    
    try:
        # Base is the parent of the first commit in the range
        first_commit = commit_hashes[0]
        base_res = subprocess.run(["git", "rev-parse", f"{first_commit}^1"], capture_output=True, text=True)
        
        if base_res.returncode != 0:
            # If no parent exists, it's a root commit.
            is_root = True
            base_commit = first_commit
        else:
            is_root = False
            base_commit = base_res.stdout.strip()
            
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

# ==========================================
# Remote, Branch, and Worktree Management
# ==========================================

def get_remotes() -> list[dict]:
    try:
        res = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
        remotes = {}
        for line in res.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0]
                url = parts[1]
                type_ = parts[2].strip("()")
                if name not in remotes:
                    remotes[name] = {"name": name, "fetch": "", "push": ""}
                if type_ == "fetch":
                    remotes[name]["fetch"] = url
                elif type_ == "push":
                    remotes[name]["push"] = url
        return list(remotes.values())
    except Exception:
        return []

def prune_remote(name: str) -> bool:
    try:
        res = subprocess.run(["git", "fetch", "--prune", name], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def set_remote_url(name: str, url: str) -> bool:
    try:
        res = subprocess.run(["git", "remote", "set-url", name, url], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def rename_remote(old_name: str, new_name: str) -> bool:
    try:
        res = subprocess.run(["git", "remote", "rename", old_name, new_name], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def delete_remote(name: str) -> bool:
    try:
        res = subprocess.run(["git", "remote", "remove", name], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def sync_fork(upstream_remote: str = "upstream") -> tuple[bool, str]:
    try:
        # Fetch
        f_res = subprocess.run(["git", "fetch", upstream_remote], capture_output=True, text=True)
        if f_res.returncode != 0:
            return False, f"Fetch failed: {f_res.stderr}"
        # Rebase
        r_res = subprocess.run(["git", "rebase", f"{upstream_remote}/main"], capture_output=True, text=True)
        if r_res.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"], capture_output=True)
            # Try master if main fails
            r2_res = subprocess.run(["git", "rebase", f"{upstream_remote}/master"], capture_output=True, text=True)
            if r2_res.returncode != 0:
                subprocess.run(["git", "rebase", "--abort"], capture_output=True)
                return False, "Rebase failed (conflicts or no main/master branch found)."
        return True, "Successfully synced via rebase."
    except Exception as e:
        return False, str(e)

def is_working_tree_dirty() -> bool:
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        return len(res.stdout.strip()) > 0
    except Exception:
        return True # Assume dirty on error for safety

def get_branches() -> list[dict]:
    try:
        # Format: %(HEAD)|%(refname:short)|%(upstream:short)|%(upstream:trackshort)|%(objectname:short)
        res = subprocess.run(
            ["git", "for-each-ref", "--format=%(HEAD)|%(refname:short)|%(upstream:short)|%(upstream:trackshort)", "refs/heads/", "refs/remotes/"],
            capture_output=True, text=True
        )
        branches = []
        for line in res.stdout.strip().splitlines():
            if not line: continue
            parts = line.split('|')
            is_head = parts[0].strip() == '*'
            name = parts[1].strip()
            upstream = parts[2].strip() if len(parts) > 2 else ""
            track_status = parts[3].strip() if len(parts) > 3 else ""
            
            is_remote = name.startswith('origin/') or '/' in name and not upstream # Heuristic
            
            branches.append({
                "name": name,
                "is_current": is_head,
                "is_remote": is_remote,
                "upstream": upstream,
                "status": track_status, # e.g., '=', '>', '<', '<>'
            })
        return branches
    except Exception:
        return []

def delete_branch(name: str, force: bool = False) -> tuple[bool, str]:
    try:
        flag = "-D" if force else "-d"
        is_remote = name.startswith('origin/') or '/' in name # Basic check
        if is_remote:
            remote, bname = name.split('/', 1)
            res = subprocess.run(["git", "push", remote, "--delete", bname], capture_output=True, text=True)
        else:
            res = subprocess.run(["git", "branch", flag, name], capture_output=True, text=True)
        return res.returncode == 0, res.stderr or res.stdout
    except Exception as e:
        return False, str(e)

def get_worktrees() -> list[dict]:
    try:
        res = subprocess.run(["git", "worktree", "list", "--porcelain"], capture_output=True, text=True)
        worktrees = []
        current = {}
        for line in res.stdout.splitlines():
            if line.startswith("worktree "):
                if current: worktrees.append(current)
                current = {"path": line.replace("worktree ", "").strip()}
            elif line.startswith("branch "):
                current["branch"] = line.replace("branch ", "").replace("refs/heads/", "").strip()
            elif line == "detached":
                current["branch"] = "(detached)"
        if current: worktrees.append(current)
        return worktrees
    except Exception:
        return []

def create_worktree(path: str, branch: str) -> tuple[bool, str]:
    try:
        res = subprocess.run(["git", "worktree", "add", path, branch], capture_output=True, text=True)
        return res.returncode == 0, res.stderr or res.stdout
    except Exception as e:
        return False, str(e)

def delete_worktree(path: str, force: bool = False) -> tuple[bool, str]:
    try:
        flag = "--force" if force else ""
        cmd = ["git", "worktree", "remove", path]
        if flag: cmd.insert(3, flag)
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0, res.stderr or res.stdout
    except Exception as e:
        return False, str(e)
def add_remote(name: str, url: str) -> bool:
    try:
        res = subprocess.run(["git", "remote", "add", name, url], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False
