import typer
from rich.panel import Panel
from rich.live import Live
from rich.columns import Columns
from rich.spinner import Spinner
from rich.text import Text
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor

from grit.state import StateManager
from grit.ui import console, err_console, ERROR_COLOR, WARN_COLOR, BRAND_COLOR, SUCCESS_COLOR
from grit.executor import get_staged_diff
from grit.ai import generate_review
from grit.constants import UI_REFRESH_RATE, KEY_READ_TIMEOUT, AI_ANALYSIS_QUOTES, QUOTE_CHANGE_INTERVAL_SECONDS, DIFF_TRUNCATION_LIMIT

from grit.commands.commit import _interactive_stage_picker
import subprocess

def run_review(state: StateManager, files: list[str], verbose: bool = False):
    """
    Review staged diffs, or review full files if specified.
    """
    ai_key = state.get_config("ai_api_key")
    ai_url = state.get_config("ai_base_url")
    ai_model = state.get_config("ai_model")
    has_ai_config = ai_key and ai_key != "Not configured" and ai_key != ""

    if not has_ai_config:
        err_console.print(f"[{ERROR_COLOR}]✗ AI is not configured. Run [bold white]grit config[/bold white] first.[/{ERROR_COLOR}]")
        raise typer.Exit(1)

    diff_content = ""
    
    if files:
        # Review full files
        contents = []
        for file_path in files:
            path = Path(file_path)
            if path.exists() and path.is_file():
                try:
                    text = path.read_text(encoding='utf-8')
                    contents.append(f"--- {file_path} ---\n{text}")
                except Exception as e:
                    err_console.print(f"[{WARN_COLOR}]⚠ Could not read {file_path}: {e}[/{WARN_COLOR}]")
            else:
                err_console.print(f"[{WARN_COLOR}]⚠ File not found or is a directory: {file_path}[/{WARN_COLOR}]")
                
        if not contents:
            raise typer.Exit(1)
            
        diff_content = "\n\n".join(contents)
    else:
        # Interactive Picker
        console.clear()
        selected = _interactive_stage_picker()
        
        if not selected:
            err_console.print(f"[{WARN_COLOR}]⚠ No files selected for review.[/{WARN_COLOR}]")
            raise typer.Exit(0)
            
        # Get diff for selected files against HEAD (includes both staged and unstaged changes)
        cmd = ["git", "diff", "HEAD", "--"] + list(selected)
        res = subprocess.run(cmd, capture_output=True, text=True)
        diff_content = res.stdout

        if not diff_content:
            err_console.print(f"[{WARN_COLOR}]⚠ No differences found in selected files.[/{WARN_COLOR}]")
            raise typer.Exit(1)

    if len(diff_content) > DIFF_TRUNCATION_LIMIT:
        if verbose: console.print(f"[{WARN_COLOR}]⚠ Content too large ({len(diff_content)} chars), trimming context.[/{WARN_COLOR}]")
        diff_content = diff_content[:DIFF_TRUNCATION_LIMIT] + "\n... (Content truncated for memory optimization)"

    start_time = time.time()
    last_error = None
    review_text = None

    with Live(console=console, refresh_per_second=UI_REFRESH_RATE) as live:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            generate_review, diff_content, ai_url, ai_key, ai_model, verbose
        )
        
        while not future.done():
            elapsed_total = time.time() - start_time
            quote_index = int(elapsed_total // QUOTE_CHANGE_INTERVAL_SECONDS) % len(AI_ANALYSIS_QUOTES)
            current_quote = AI_ANALYSIS_QUOTES[quote_index]
            
            ui = Columns([
                Spinner("dots12", style=BRAND_COLOR),
                Text.from_markup(
                    f" [bold {BRAND_COLOR}]{current_quote}[/bold {BRAND_COLOR}] "
                    f"[dim]({elapsed_total:.1f}s)[/dim]"
                )
            ])
            live.update(ui)
            time.sleep(KEY_READ_TIMEOUT)
        
        try:
            review_text = future.result()
        except Exception as e:
            last_error = e
            if verbose: console.print(f"[red]Error: {e}[/red]")
            
        total_elapsed = time.time() - start_time
        live.update(
            Text.from_markup(f"    [{SUCCESS_COLOR}]✓ Code review complete ({total_elapsed:.1f}s)[/{SUCCESS_COLOR}]")
        )

    if review_text:
        console.print("\n")
        console.print(Panel(review_text, border_style=BRAND_COLOR, padding=(1, 2), title="Code Review (Caveman Mode)", title_align="left"))
    else:
        if last_error:
            err_msg = str(last_error)
            err_console.print(f"[{ERROR_COLOR}]✗ AI review failed: {err_msg}[/{ERROR_COLOR}]")
        else:
            err_console.print(f"[{ERROR_COLOR}]✗ AI review failed to generate output.[/{ERROR_COLOR}]")
