import os
import random
import sys
import time
from pathlib import Path
import subprocess

from grit.ai import generate_commit_message
from grit.state import StateManager, DEFAULT_DB_DIR
from grit.constants import AI_ANALYSIS_QUOTES

def run_ai_worker(diff_path: str, diff_hash: str, verbose: bool = False):
    """
    Internal background worker for AI generation. 
    Reads a diff from disk, contacts the LLM, and persists the draft.
    """
    # Ensure the directory exists
    DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
    log_file = DEFAULT_DB_DIR / f"ai_bg_{diff_hash}.log"
    
    # Redirect stdout/stderr to the log file for background visibility
    log_stream = None
    try:
        log_stream = open(log_file, "a", buffering=1)
        sys.stdout = log_stream
        sys.stderr = log_stream
    except Exception as e:
        sys.stderr.write(f"Failed to open log file {log_file}: {e}\n")
        _send_macos_notification("Grit AI Error", f"Failed to start AI background: {e}")
        return

    def log(msg):
        ts = time.strftime('%H:%M:%S')
        print(f"[{ts}] {msg}")

    log("✦ Grit Intelligence System: Background Thread Initialized")
    log(f"✦ Process ID: {os.getpid()}")
    log(f"✦ Target Diff: {diff_hash[:8]}")
    log("-" * 50)
    
    state = StateManager()
    ai_key = state.get_config("ai_api_key")
    ai_url = state.get_config("ai_base_url")
    ai_model = state.get_config("ai_model")

    try:
        log("➤ Reading staged changes...")
        diff = Path(diff_path).read_text(encoding="utf-8")
        log(f"✓ Diff ingested ({len(diff)} characters)")
        
        log(f"➤ Contacting LLM Intelligence Core ({ai_model})...")
        # Log a few random quotes to keep the log file "hilarious"
        for _ in range(3):
            log(f"✦ {random.choice(AI_ANALYSIS_QUOTES)}")
        
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
            
            _send_macos_notification("Grit AI Success", "✨ AI draft is ready! Run 'grit commit' to review.", sound="Glass")
        else:
            log("✗ LLM returned empty message or failed.")
            state.set_draft(diff_hash, "", status="failure")
            _send_macos_notification("Grit AI Failed", "AI generation failed. LLM returned empty result.", sound="Basso")

    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        state.set_draft(diff_hash, str(e), status="failure")
        _send_macos_notification("Grit AI Error", f"AI Failed: {str(e)[:40]}", sound="Basso")
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

def _send_macos_notification(title, message, sound=None):
    """Utility to send system notifications on macOS."""
    try:
        cmd = f'display notification "{message}" with title "{title}"'
        if sound:
            cmd += f' sound name "{sound}"'
        subprocess.run(["osascript", "-e", cmd], capture_output=True, check=False)
    except:
        pass
