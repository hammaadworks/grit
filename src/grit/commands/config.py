import sys
from datetime import datetime
from typing import Optional
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.padding import Padding
from grit.ui import console, err_console, BRAND_COLOR, SUCCESS_COLOR, WARN_COLOR, ERROR_COLOR, ACCENT_COLOR
from grit.state import StateManager
from grit.sync import sync_historical_data

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

def run_config_interactive(state: StateManager):
    """
    Grit Control Center: High-fidelity interactive settings management.
    Navigate with arrow keys, edit with Enter, and save with S.
    """
    # Interactive Settings Schema
    options = [
        {"id": "target", "title": "Daily Commit Target *", "desc": "Maximum commits to allocate per calendar day.", "key": "daily_target", "default": "1"},
        {"id": "start", "title": "Timeline Start Date *", "desc": "The historical boundary for backfilling (YYYY-MM-DD).", "key": "start_date", "default": datetime.now().strftime("%Y-%m-%d")},
        {"id": "fill", "title": "Allocation Strategy *", "desc": "Where to fill gaps from (today or start_date).", "key": "fill_strategy", "default": "start_date"},
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
            menu_grid.add_column(justify="left")
            
            # Header
            header = Text()
            header.append("✦ ", style=BRAND_COLOR)
            header.append("GRIT CONTROL CENTER", style="bold white")
            menu_grid.add_row(Padding(header, (1, 0, 1, 0)))
            
            for i, opt in enumerate(options):
                val = state.get_config(opt["key"]) or opt["default"]
                is_selected = (i == selected_idx)
                
                # Render item
                item_text = Text()
                prefix = " > " if is_selected else "   "
                style = f"bold {BRAND_COLOR}" if is_selected else "dim"
                
                item_text.append(prefix, style=style)
                item_text.append(f"{opt['title']:<25}", style=style)
                item_text.append(f"{val}", style="white" if is_selected else "dim")
                
                menu_grid.add_row(item_text)
                if is_selected:
                    menu_grid.add_row(Padding(f"   [dim]{opt['desc']}[/]", (0, 0, 1, 0)))

            # Footer / Help
            footer = Text()
            footer.append("\n [↑↓] Navigate  [Enter] Edit  [S] Sync & Save  [Q] Exit", style="dim")
            if error_msg:
                footer.append(f"\n\n [bold {ERROR_COLOR}]✗ {error_msg}[/]")
            menu_grid.add_row(footer)

            live.update(menu_grid, refresh=True)

            # 2. Handle Input
            try:
                key = get_key()
            except KeyboardInterrupt:
                break

            if key == 'q' or key == 'Q':
                break
            elif key == '\x1b[A': # Up
                selected_idx = (selected_idx - 1) % len(options)
                error_msg = ""
            elif key == '\x1b[B': # Down
                selected_idx = (selected_idx + 1) % len(options)
                error_msg = ""
            elif key == '\r': # Enter (Edit)
                opt = options[selected_idx]
                live.stop()
                new_val = input(f" Edit {opt['title']} (current: {state.get_config(opt['key']) or opt['default']}): ").strip()
                
                # Validation
                if opt["id"] == "target" and not validate_int(new_val):
                    error_msg = "Target must be a positive integer."
                elif opt["id"] == "start" and not validate_date(new_val):
                    error_msg = "Date must be YYYY-MM-DD."
                elif opt["id"] == "fill" and new_val not in ["today", "start_date"]:
                    error_msg = "Fill strategy must be 'today' or 'start_date'."
                elif new_val:
                    state.set_config(opt["key"], new_val)
                    error_msg = ""
                
                live.start()
            elif key == 's' or key == 'S':
                # Save & Sync
                live.stop()
                username = state.get_config("github_username")
                start_date = state.get_config("start_date")
                
                if username and username != "Not configured" and start_date:
                    with console.status(f"[{BRAND_COLOR}]✦ Synchronizing contribution graph for @{username}...[/{BRAND_COLOR}]"):
                        sync_historical_data(state, str(username), str(start_date))
                    console.print(f"[{SUCCESS_COLOR}]✓ Sync complete. Grit is now hyper-optimized.[/{SUCCESS_COLOR}]")
                else:
                    console.print(f"[{WARN_COLOR}]⚠ Username/Start date not set. Skipping sync.[/{WARN_COLOR}]")
                
                import time
                time.sleep(1)
                break
