from datetime import datetime

from rich.live import Live
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from grit.state import StateManager
from grit.sync import sync_historical_data
from grit.ui import (ACCENT_COLOR, BRAND_COLOR, console, ERROR_COLOR, get_key,
                     get_banner_layout, print_banner, SUCCESS_COLOR, WARN_COLOR)


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
        {"id": "target", "title": "Daily Commit Target *",
         "desc": "Maximum commits to allocate per calendar day.", "key": "daily_target",
         "default": "1"},
        {"id": "start", "title": "Timeline Start Date *",
         "desc": "The historical boundary for backfilling (YYYY-MM-DD).",
         "key": "start_date", "default": datetime.now().strftime("%Y-%m-%d")},
        {"id": "fill", "title": "Allocation Strategy *",
         "desc": "Where to fill gaps from (today or start_date).",
         "key": "fill_strategy", "default": "start_date"},
        {"id": "user", "title": "GitHub Identity *",
         "desc": "Your public username for contribution graph integration.",
         "key": "github_username", "default": "Not configured"},
        {"id": "ai_url", "title": "AI: Base URL",
         "desc": "LLM API endpoint (e.g. http://localhost:11434/v1 for Ollama, "
                 "or Anthropic/Groq).",
         "key": "ai_base_url", "default": "Not configured"},
        {"id": "ai_key", "title": "AI: API Key",
         "desc": "Your API token for the LLM provider (leave blank for local models).",
         "key": "ai_api_key", "default": ""},
        {"id": "ai_model", "title": "AI: Model Name",
         "desc": "The model to use (e.g. llama3 for Ollama, claude-3-haiku-20240307).",
         "key": "ai_model", "default": "Not configured"},
    ]

    # Session State: Load everything into memory first.
    # We only write to disk when the user explicitly saves with 'S'.
    session_config = {
        opt["key"]: state.get_config(opt["key"]) or opt["default"]
        for opt in options
    }

    selected_idx = 0
    error_msg = ""

    with Live(auto_refresh=False, console=console, screen=True) as live:
        while True:
            # 1. Build the Menu UI
            grid = Table.grid(expand=True)
            grid.add_column(justify="left")

            # Header / Banner (Included in Live grid to ensure persistence in alternate screen)
            grid.add_row(get_banner_layout())

            # Settings Table
            table = Table(box=None, padding=(0, 2), show_header=False, expand=True)
            table.add_column("Cursor", width=3)
            table.add_column("Setting", width=25)
            table.add_column("Value")

            for i, opt in enumerate(options):
                val = session_config[opt["key"]]
                is_selected = (i == selected_idx)

                cursor = " ▶ " if is_selected else "   "
                style = f"bold {BRAND_COLOR}" if is_selected else "dim"
                val_style = "bold white" if is_selected else "dim"

                table.add_row(
                    Text(cursor, style=style),
                    Text(opt["title"], style=style),
                    Text(str(val), style=val_style)
                )
                
                if is_selected:
                    table.add_row(
                        "",
                        Text(f"└─ {opt['desc']}", style="dim italic"),
                        ""
                    )

            grid.add_row(Padding(table, (0, 2)))

            # Footer / Help
            footer = Table.grid(expand=True)
            help_text = Text("\n [↑↓] Navigate  [Enter] Edit/Toggle  [S] Sync & Save  [Q] Discard & Exit", style="dim")
            footer.add_row(Padding(help_text, (0, 4)))
            
            if error_msg:
                err_text = Text(f"✗ {error_msg}", style=f"bold {ERROR_COLOR}")
                footer.add_row(Padding(err_text, (1, 4)))
                
            grid.add_row(footer)

            live.update(grid, refresh=True)

            # 2. Handle Input
            try:
                key = get_key()
            except KeyboardInterrupt:
                break

            if key == 'q' or key == 'Q':
                # Explicitly do NOT save anything to state here.
                break
            elif key == '\x1b[A':  # Up
                selected_idx = (selected_idx - 1) % len(options)
                error_msg = ""
            elif key == '\x1b[B':  # Down
                selected_idx = (selected_idx + 1) % len(options)
                error_msg = ""
            elif key == '\r':  # Enter (Edit/Toggle)
                opt = options[selected_idx]
                
                if opt["id"] == "fill":
                    # Instant toggle for strategy (Session only)
                    current = session_config[opt["key"]]
                    new_val = "today" if current == "start_date" else "start_date"
                    session_config[opt["key"]] = new_val
                    error_msg = ""
                else:
                    live.stop()
                    current_val = session_config[opt["key"]]
                    console.print(f"\n [bold {ACCENT_COLOR}]Editing {opt['title']}[/]")
                    console.print(f" [dim]Current: {current_val}[/]")
                    new_val = input(f" New value: ").strip()

                    # Validation
                    if opt["id"] == "target" and not validate_int(new_val):
                        error_msg = "Target must be a positive integer."
                    elif opt["id"] == "start" and not validate_date(new_val):
                        error_msg = "Date must be YYYY-MM-DD."
                    elif new_val:
                        session_config[opt["key"]] = new_val
                        error_msg = ""

                    live.start()
            elif key == 's' or key == 'S':
                # Persist Session to Database
                for k, v in session_config.items():
                    state.set_config(k, v)

                live.stop()
                print_banner()
                username = session_config["github_username"]
                start_date = session_config["start_date"]

                if username and username != "Not configured" and start_date:
                    with console.status(
                            f"[{BRAND_COLOR}]✦ Synchronizing contribution graph for "
                            f"@{username}...[/{BRAND_COLOR}]"
                            ):
                        sync_historical_data(state, str(username), str(start_date))
                    console.print(
                        f"[{SUCCESS_COLOR}]✓ Sync complete. Grit is now "
                        f"hyper-optimized.[/{SUCCESS_COLOR}]"
                        )
                else:
                    console.print(
                        f"[{WARN_COLOR}]⚠ Username/Start date not set. Skipping "
                        f"sync.[/{WARN_COLOR}]"
                        )

                import time
                time.sleep(1)
                break

