import atexit
import os
import select
import sys
import termios
import tty

from rich.console import Console
from rich.padding import Padding
from rich.text import Text

from grit import __version__

# Billion Dollar Design System (Official Grit Palette)
# These constants define the sacred visual identity of Grit.
BRAND_COLOR = "bright_cyan"  # Primary teal/blue brand highlight
SUCCESS_COLOR = "spring_green3"  # For checkmarks and completion
WARN_COLOR = "gold1"  # For warnings and non-blocking issues
ERROR_COLOR = "deep_pink3"  # For fatal errors or destructive prompts
ACCENT_COLOR = "bright_cyan"  # Secondary highlights (standardized to brand color)

console = Console()
err_console = Console(stderr=True)
from rich.table import Table


def get_banner_layout() -> Table:
    """
    Returns a rich Table layout containing the Grit banner.
    Used for consistent branding in interactive TUI screens.
    """
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")

    # ASCII Art
    grid.add_row(Text("    ██████╗ ██████╗ ██╗████████╗", style=BRAND_COLOR))
    grid.add_row(Text("    ██╔════╝ ██╔══██╗██║╚══██╔══╝", style=BRAND_COLOR))
    grid.add_row(Text("    ██║  ███╗██████╔╝██║   ██║   ", style=BRAND_COLOR))
    grid.add_row(Text("    ██║   ██║██╔══██╗██║   ██║   ", style=BRAND_COLOR))
    grid.add_row(Text("    ╚██████╔╝██║  ██║██║   ██║   ", style=BRAND_COLOR))
    grid.add_row(Text("     ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝   ", style=BRAND_COLOR))
    grid.add_row("")

    tagline = Text()
    tagline.append("    ✦ ", style=BRAND_COLOR)
    tagline.append(f"v{__version__}", style="dim")
    tagline.append(" — Intelligently distribute your commits", style="dim")
    grid.add_row(tagline)
    grid.add_row("")

    return grid

_suppress_title_reset = False
_title_pushed = False

def set_terminal_title(title: str = "Grit"):
    """
    Sets the terminal window/tab title using ANSI escape sequences.
    Uses title stacking to allow restoration on exit.
    """
    global _title_pushed
    if sys.stdout.isatty():
        if not _title_pushed:
            # Push current title to stack (xterm extension)
            sys.stdout.write("\033[22;0t")
            _title_pushed = True
        # \033]0;title\007 sets both the window title and the tab name
        sys.stdout.write(f"\033]0;{title}\007")
        sys.stdout.flush()


def suppress_title_reset():
    """
    Prevents the terminal title from being reset on exit.
    Used when spawning background processes that should not affect the current tab.
    """
    global _suppress_title_reset
    _suppress_title_reset = True


def reset_terminal_title():
    """
    Resets the terminal title by popping from the stack on exit.
    """
    if sys.stdout.isatty() and not _suppress_title_reset:
        if _title_pushed:
            # Restore title from stack
            sys.stdout.write("\033[23;0t")
            sys.stdout.flush()



atexit.register(reset_terminal_title)


def print_banner():
    """
    Renders a premium minimalist banner to provide branding consistency.
    This banner is printed at the start of most high-level user commands.
    """
    set_terminal_title("Grit")
    console.print(get_banner_layout())


def get_key(timeout: float = None) -> str:
    """
    Reads a single keypress from the terminal for navigation.
    If timeout is provided, returns None if no key is pressed within timeout seconds.
    Uses unbuffered input capture to ensure zero-latency response.
    """
    fd = sys.stdin.fileno()
    if not os.isatty(fd):
        return sys.stdin.read(1)

    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        
        # Check if there's data to read
        r, _, _ = select.select([fd], [], [], timeout)
        if not r:
            return None

        # Read the first byte
        ch = os.read(fd, 1).decode(errors='ignore')

        if ch == '\x03':  # Ctrl+C
            raise KeyboardInterrupt

        # If it's an escape sequence, read the next bytes immediately
        if ch == '\x1b':
            # Most terminals send [A, [B, etc. for arrows. 
            # We use a very short timeout to see if more bytes follow \x1b
            r, _, _ = select.select([fd], [], [], 0.02)
            if r:
                # Read the next two characters (e.g., '[A')
                ch += os.read(fd, 2).decode(errors='ignore')

        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


from rich.live import Live
from rich.panel import Panel


def run_text_input(title: str, initial_text: str = "", help_text: str = "",
                   show_banner: bool = True) -> str:
    """
    Renders an interactive TUI text box for multi-line free-text input.
    """
    set_terminal_title("Grit — Editing")
    text = initial_text
    min_lines = 1  # Minimum lines for collapsed view

    # Use screen=False to keep history on screen after finishing
    with Live(auto_refresh=False, console=console, screen=False) as live:
        last_size = console.size
        
        def render():
            grid = Table.grid(expand=True)
            if show_banner: grid.add_row(get_banner_layout())
            input_grid = Table.grid(expand=True)
            input_grid.add_row(Text(f" {title}", style=f"bold {ACCENT_COLOR}"))
            current_lines = text.count('\n') + 1
            target_height = max(min_lines, current_lines)
            display_text = Text(text); display_text.append("_", style="bold white")
            input_grid.add_row(Padding(Panel(display_text, border_style=BRAND_COLOR, padding=(1, 2), height=target_height), (1, 0)))
            if not help_text:
                h = "[Enter] Newline  [Ctrl+D] Save  [Ctrl+C] Abort"
            else: h = help_text
            input_grid.add_row(Text(f" {h}", style="dim"))
            grid.add_row(Padding(input_grid, (0, 4)))
            live.update(grid, refresh=True)

        render() # Initial render

        while True:
            key = get_key(timeout=0.1)
            
            # Re-render on resize regardless of key
            if console.size != last_size:
                last_size = console.size
                render()
                if key is None: continue

            if key is None:
                continue

            # Process key
            if key == '\x04':  # Ctrl+D (EOF / Save)
                break
            elif key == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            elif key in ('\r', '\n'):  # Enter key
                text += "\n"
            elif key in ('\x7f', '\x08'):  # Backspace
                text = text[:-1]
            elif len(key) == 1 and ord(key) >= 32:  # Normal character input
                text += key
            
            # Re-render after state change
            render()

    return text.strip()


def run_selection_menu(title: str, options: list[str], selected_idx: int = 0,
                       show_banner: bool = True) -> tuple[str, int]:
    """
    Renders a consistent selection menu with the Grit banner.
    Returns (selected_option, index) or (None, -1) if aborted.
    """
    set_terminal_title("Grit — Select")
    idx = selected_idx
    # Use screen=False to keep history on screen after finishing
    with Live(auto_refresh=False, console=console, screen=False) as live:
        last_size = console.size
        
        def render():
            grid = Table.grid(expand=True)
            if show_banner: grid.add_row(get_banner_layout())
            menu_grid = Table.grid(expand=True)
            menu_grid.add_row(Text(f" {title}", style=f"bold {ACCENT_COLOR}"))
            menu_grid.add_row("")
            for i, opt in enumerate(options):
                is_cur = i == idx; prefix = "▶ " if is_cur else "  "; style = f"bold {BRAND_COLOR}" if is_cur else "dim"
                menu_grid.add_row(Text(f"{prefix}{opt}", style=style))
            grid.add_row(Padding(menu_grid, (0, 4)))
            grid.add_row(Text("\n [↑↓] Navigate  [Enter] Select  [Q] Abort", style="dim"))
            live.update(grid, refresh=True)

        render() # Initial render

        while True:
            key = get_key(timeout=0.1)
            
            if console.size != last_size:
                last_size = console.size
                render()
                if key is None: continue
            
            if key is None:
                continue

            if key == '\x1b[A':
                idx = (idx - 1) % len(options)
            elif key == '\x1b[B':
                idx = (idx + 1) % len(options)
            elif key.lower() == 'q':
                return None, -1
            elif key in ('\r', '\n'):
                return options[idx], idx
            
            render()


def show_victory_animation():
    """
    Renders a brief, premium confetti-like animation for achieving the daily goal.
    Uses random particles and colors to create a 'Victory Burst' effect.
    """
    import random
    import time
    import shutil

    particles = ["✧", "✦", "⋆", "◆", "●", "◈", "✨", "⟡"]
    colors = ["yellow", "cyan", "magenta", "white", "green"]

    with Live(auto_refresh=False, console=console) as live:
        for _ in range(12):  # Brief 1.2s burst
            width = shutil.get_terminal_size().columns
            burst = "".join(
                [
                    f"[bold {random.choice(colors)}]{random.choice(particles)}[/] "
                    if random.random() > 0.8 else "  "
                    for _ in range(width // 2)
                ]
            )
            live.update(Padding(Text.from_markup(burst), (0, 2)), refresh=True)
            time.sleep(0.08)
        live.update(Text(""))  # Clear after burst
