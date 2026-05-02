import os
import re
from datetime import datetime
from pathlib import Path

from rich.live import Live
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from rich import box

from grit.constants import (ACCENT_COLOR, BRAND_COLOR, ERROR_COLOR, 
                            SUCCESS_COLOR, WARN_COLOR, DEFAULT_COMMIT_TYPES_STR,
                            KEY_READ_TIMEOUT)
from grit.state import StateManager
from grit.synchronizer import sync_historical_data
from grit.ui import (console, get_key, get_banner_layout, print_banner)


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


def validate_file_path(path_str: str) -> tuple[bool, str]:
    """Validates that a file path exists if provided."""
    if not path_str or path_str.lower() == "none" or path_str == "Not configured":
        return True, ""
        
    p = Path(path_str).expanduser()
    if p.exists() and p.is_file():
        return True, ""
    return False, f"File not found: {path_str}"


def _interactive_type_picker(current_types_str: str) -> str:
    """
    Renders an interactive multi-select menu for commit types.
    Allows toggling standard types and adding custom ones.
    """
    from grit.constants import COMMIT_TYPES
    from grit.ui import set_terminal_title
    
    set_terminal_title("Grit — Commit Types")
    
    # Parse current list
    current_list = [t.strip() for t in current_types_str.split(",") if t.strip()]
    
    # We want a base list of "available" types to show
    # This includes the default COMMIT_TYPES and any custom ones the user already has
    available = list(dict.fromkeys(COMMIT_TYPES + current_list))
    selected = set(current_list)
    
    idx = 0
    error_msg = ""
    
    with Live(auto_refresh=False, console=console, screen=False) as live:
        last_size = console.size
        
        def render():
            grid = Table.grid(expand=True)
            grid.add_row(get_banner_layout())
            
            menu_grid = Table.grid(expand=True)
            menu_grid.add_row(Text(" Select active commit types (Space: toggle, Enter: confirm, Q: abort):", style=f"bold {ACCENT_COLOR}"))
            menu_grid.add_row("")
            
            # List types
            for i, t in enumerate(available):
                is_cur = i == idx
                is_sel = t in selected
                
                cursor = "▶ " if is_cur else "  "
                box = f"[{SUCCESS_COLOR}]✔[/]" if is_sel else "[dim]○[/dim]"
                style = f"bold {BRAND_COLOR}" if is_cur else "white" if is_sel else "dim"
                
                menu_grid.add_row(Text.from_markup(f"{cursor}{box} {t}", style=style))
            
            # Special options
            is_add = idx == len(available)
            is_done = idx == len(available) + 1
            
            menu_grid.add_row(Text(f"{'▶ ' if is_add else '  '}[+] Add New Type...", style=f"bold {BRAND_COLOR}" if is_add else "dim italic"))
            menu_grid.add_row(Text(f"{'▶ ' if is_done else '  '}[✔] Confirm & Done", style=f"bold {SUCCESS_COLOR}" if is_done else "dim"))
            
            if error_msg:
                menu_grid.add_row("")
                menu_grid.add_row(Text(f" ✗ {error_msg}", style=f"bold {ERROR_COLOR}"))
            
            grid.add_row(Padding(menu_grid, (0, 4)))
            live.update(grid, refresh=True)

        render()
        
        while True:
            key = get_key(timeout=KEY_READ_TIMEOUT)
            if console.size != last_size:
                last_size = console.size
                render()
                if key is None: continue
            if key is None: continue

            if key == '\x1b[A':  # Up
                idx = (idx - 1) % (len(available) + 2)
                error_msg = ""
            elif key == '\x1b[B':  # Down
                idx = (idx + 1) % (len(available) + 2)
                error_msg = ""
            elif key == ' ':  # Toggle (Space)
                if idx < len(available):
                    t = available[idx]
                    if t in selected:
                        selected.remove(t)
                    else:
                        selected.add(t)
                    error_msg = ""
            elif key in ('\r', '\n'):  # Enter
                if idx < len(available):
                    # Also toggle on Enter for convenience
                    t = available[idx]
                    if t in selected: selected.remove(t)
                    else: selected.add(t)
                elif idx == len(available):
                    # Add New Type
                    live.stop()
                    console.print(f"\n [bold {ACCENT_COLOR}]Enter new commit type name:[/] ", end="")
                    new_type = input().strip().lower()
                    if new_type:
                        import re
                        if re.match(r"^[a-z0-9-]+$", new_type):
                            if new_type not in available:
                                available.append(new_type)
                            selected.add(new_type)
                            idx = available.index(new_type)
                        else:
                            error_msg = "Invalid name (lowercase alphanumeric & dashes only)."
                    live.start()
                elif idx == len(available) + 1:
                    # Done
                    if not selected:
                        error_msg = "At least one type must be selected."
                    else:
                        break
            elif key.lower() == 'q':
                return current_types_str
            
            render()

    # Order resulting types by their order in 'available' to preserve user preference
    result = [t for t in available if t in selected]
    return ",".join(result)


def run_config_interactive(state: StateManager):
    """
    Grit Control Center: High-fidelity interactive settings management.
    Navigate with arrow keys, edit with Enter, and save with S.
    """
    from grit.ui import set_terminal_title
    set_terminal_title("Grit — Configuration")

    # Interactive Settings Schema
    options = [
        {"id": "target", "title": "Daily Commit Target *", "category": "CORE SETTINGS",
         "desc": "Maximum commits to allocate per calendar day.", "key": "daily_target",
         "default": "1"},
        {"id": "start", "title": "Timeline Start Date *", "category": "CORE SETTINGS",
         "desc": "The historical boundary for backfilling (YYYY-MM-DD).",
         "key": "start_date", "default": datetime.now().strftime("%Y-%m-%d")},
        {"id": "fill", "title": "Allocation Strategy *", "category": "CORE SETTINGS",
         "desc": "Where to fill gaps from (today or start_date).",
         "key": "fill_strategy", "default": "start_date"},
        {"id": "user", "title": "GitHub Identity *", "category": "IDENTITY",
         "desc": "Your public username for contribution graph integration.",
         "key": "github_username", "default": "Not configured"},
        {"id": "types", "title": "Commit Types", "category": "COMMIT CONFIG",
         "desc": "Custom types. Use +type, -type to modify (e.g., '+build, -chore'), or list all.",
         "key": "commit_types", "default": DEFAULT_COMMIT_TYPES_STR},
        {"id": "ai_url", "title": "AI: Base URL", "category": "AI INTELLIGENCE",
         "desc": "LLM API endpoint (e.g. http://localhost:11434/v1 for Ollama, "
                 "or Anthropic/Groq).",
         "key": "ai_base_url", "default": "Not configured"},
        {"id": "ai_key", "title": "AI: API Key", "category": "AI INTELLIGENCE",
         "desc": "Your API token for the LLM provider (leave blank for local models).",
         "key": "ai_api_key", "default": ""},
        {"id": "ai_model", "title": "AI: Model Name", "category": "AI INTELLIGENCE",
         "desc": "The model to use (e.g. llama3 for Ollama, claude-3-haiku-20240307).",
         "key": "ai_model", "default": "Not configured"},
        {"id": "editor", "title": "Editor: Command", "category": "COMMIT MESSAGES",
         "desc": "Command to open your preferred graphical editor (e.g., 'code --wait', 'nano').",
         "key": "editor_command", "default": ""},
        {"id": "ai_rules", "title": "AI: Commit Rules", "category": "COMMIT MESSAGES",
         "desc": "Edit your custom AI commit rules in the configured editor.",
         "key": "_ai_rules_pseudo_key", "default": "▶ Enter to edit rules"},
    ]

    import subprocess
    repo_name_res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if repo_name_res.returncode == 0:
        repo_name = Path(repo_name_res.stdout.strip()).name
        options.append({
            "id": "remotes", "title": "Manage Git Remotes", "category": f"PROJECT SETTINGS ({repo_name})",
            "desc": "Interactively manage, prune, and sync remote repositories.",
            "key": "_remotes_pseudo_key", "default": "▶ Enter to open manager"
        })

    # Session State: Load everything into memory first.
    session_config = {
        opt["key"]: state.get_config(opt["key"]) or opt["default"]
        for opt in options if not opt["key"].startswith("_")
    }
    session_config["_remotes_pseudo_key"] = "▶ Enter to open manager"
    session_config["_ai_rules_pseudo_key"] = "▶ Enter to edit rules"

    selected_idx = 0
    error_msg = ""

    with Live(auto_refresh=False, console=console, screen=True) as live:
        while True:
            # 1. Build the Menu UI
            grid = Table.grid(expand=True)
            grid.add_column(justify="left")

            # Header / Banner
            grid.add_row(get_banner_layout())
            grid.add_row(Text(f"    State DB: {state.db_path}\n", style="yellow"))

            # Settings Table
            table = Table(box=box.ROUNDED, padding=(0, 1), show_header=False, expand=True, border_style="dim")
            table.add_column("Setting", width=35)
            table.add_column("Value")

            current_cat = None
            for i, opt in enumerate(options):
                # Add category header
                if opt["category"] != current_cat:
                    if current_cat is not None:
                        table.add_section()
                    current_cat = opt["category"]
                    table.add_row(Text(f"{current_cat}", style=f"bold {ACCENT_COLOR}"), "")

                val = session_config[opt["key"]]
                is_selected = (i == selected_idx)
                
                # Mask API key for security/aesthetic
                display_val = val
                if opt["key"] == "ai_api_key" and val and val != "Not configured":
                    if len(val) > 10:
                        display_val = f"{val[:6]}...{val[-4:]}"
                    else:
                        display_val = "*" * len(val)

                # Dynamic styling
                if not is_selected:
                    # Non-selected rows use subtle colors
                    table.add_row(
                        Text(f"   {opt['title']}", style="dim"),
                        Text(str(display_val), style="dim")
                    )
                else:
                    # Selected row is high-fidelity
                    cursor = " ❱ "
                    table.add_row(
                        Text(f"{cursor}{opt['title']}", style=f"bold {BRAND_COLOR}"),
                        Text(f" {display_val} ", style=f"bold black on {BRAND_COLOR}")
                    )
                    # Description sub-row
                    table.add_row(
                        Text(f"    └─ {opt['desc']}", style=f"italic {BRAND_COLOR}"),
                        ""
                    )

            grid.add_row(Padding(table, (0, 2)))

            # Footer / Status Bar
            footer = Table.grid(expand=True)
            footer.add_column(justify="left")
            
            # Help hints with "keycap" look
            help_line = Text()
            help_line.append("\n ")
            help_line.append(" ↑↓ ", style="reverse")
            help_line.append(" Navigate  ")
            help_line.append(" Enter ", style="reverse")
            help_line.append(" Edit/Toggle  ")
            help_line.append(" S ", style="reverse")
            help_line.append(" Sync & Save  ")
            help_line.append(" Q ", style="reverse")
            help_line.append(" Discard ")
            
            footer.add_row(Padding(help_line, (0, 4)))
            
            if error_msg:
                err_text = Text(f"\n   ✗ {error_msg}", style=f"bold {ERROR_COLOR}")
                footer.add_row(err_text)
                
            grid.add_row(footer)

            live.update(grid, refresh=True)

            # 2. Handle Input
            try:
                key = get_key(timeout=0.1)
                if key is None:
                    continue
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
                elif opt["id"] == "remotes":
                    live.stop()
                    from grit.commands.remote import run_remote_manager
                    run_remote_manager()
                    set_terminal_title("Grit — Configuration")
                    live.start()
                elif opt["id"] == "types":
                    # Multi-select picker for types
                    live.stop()
                    new_val = _interactive_type_picker(session_config[opt["key"]])
                    session_config[opt["key"]] = new_val
                    error_msg = ""
                    live.start()
                elif opt["id"] == "ai_rules":
                    editor = session_config.get("editor_command") or state.get_config("editor_command")
                    if not editor:
                        error_msg = "Editor not configured. Please set Editor Command first."
                    else:
                        live.stop()
                        rules_path = state.db_path.parent / "commit_message_rules.md"
                        if not rules_path.exists():
                            rules_path.write_text("# Custom Commit Rules\n\nAdd your instructions here.\n")
                        import subprocess
                        subprocess.run(editor.split() + [str(rules_path)])
                        error_msg = ""
                        live.start()
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
