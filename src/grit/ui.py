import os
import sys
import tty
import termios
import select
from rich.console import Console
from rich.text import Text
from rich.padding import Padding
from grit import __version__

# Billion Dollar Design System (Official Grit Palette)
# These constants define the sacred visual identity of Grit.
BRAND_COLOR = "bright_cyan"    # Primary teal/blue brand highlight
SUCCESS_COLOR = "spring_green3" # For checkmarks and completion
WARN_COLOR = "gold1"           # For warnings and non-blocking issues
ERROR_COLOR = "deep_pink3"     # For fatal errors or destructive prompts
ACCENT_COLOR = "bright_cyan"   # Secondary highlights (standardized to brand color)

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

def print_banner(animated: bool = False):
    """
    Renders a premium minimalist banner to provide branding consistency.
    This banner is printed at the start of most high-level user commands.
    """
    console.print(get_banner_layout())

def get_key() -> str:
    """
    Reads a single keypress from the terminal for navigation (blocking).
    Uses unbuffered input capture to ensure zero-latency response.
    """
    fd = sys.stdin.fileno()
    if not os.isatty(fd):
        return sys.stdin.read(1)

    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        # Read the first byte
        ch = os.read(fd, 1).decode(errors='ignore')
        
        if ch == '\x03': # Ctrl+C
            raise KeyboardInterrupt
        
        # If it's an escape sequence, read the next bytes with a short timeout
        if ch == '\x1b':
            # Check if there's more data to read (the rest of the arrow key)
            # We use select with a very short timeout to avoid blocking if it's just ESC
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                # Capture the rest (usually 2 more chars for arrows like [A)
                # We read up to 2 bytes to complete the sequence
                ch += os.read(fd, 2).decode(errors='ignore')
                
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

from rich.live import Live
from rich.panel import Panel

def run_text_input(title: str, initial_text: str = "", help_text: str = "") -> str:
    """
    Renders an interactive TUI text box for multi-line free-text input.
    """
    text = initial_text
    
    with Live(auto_refresh=False, console=console, screen=True) as live:
        while True:
            # Compose final view
            grid = Table.grid(expand=True)
            grid.add_row(get_banner_layout())
            
            # Input area
            input_grid = Table.grid(expand=True)
            input_grid.add_row(Text(f" {title}", style=f"bold {ACCENT_COLOR}"))
            
            # Text area with cursor emulation
            display_text = Text(text)
            display_text.append("█", style=f"bold {BRAND_COLOR}") # Cursor
            
            input_grid.add_row(Padding(
                Panel(display_text, border_style=BRAND_COLOR, padding=(1, 2), height=10),
                (1, 0)
            ))
            
            # Footer / Help
            if not help_text:
                help_text = "[Enter] Newline  [Ctrl+D] Save  [Ctrl+C] Abort"
            input_grid.add_row(Text(f" {help_text}", style="dim"))
            
            grid.add_row(Padding(input_grid, (0, 4)))
            live.update(grid, refresh=True)
            
            key = get_key()
            
            if key == '\x04': # Ctrl+D (EOF / Save)
                break
            elif key in ('\r', '\n'):
                text += "\n"
            elif key == '\x7f' or key == '\x08': # Backspace
                text = text[:-1]
            elif key == '\x03': # Ctrl+C
                raise KeyboardInterrupt
            elif len(key) == 1:
                text += key
                
    return text.strip()

def run_selection_menu(title: str, options: list[str], selected_idx: int = 0) -> tuple[str, int]:
    """
    Renders a consistent full-screen selection menu with the Grit banner.
    Returns (selected_option, index) or (None, -1) if aborted.
    """
    idx = selected_idx
    with Live(auto_refresh=False, console=console, screen=True) as live:
        while True:
            grid = Table.grid(expand=True)
            grid.add_row(get_banner_layout())
            
            menu_grid = Table.grid(expand=True)
            menu_grid.add_row(Text(f" {title}", style=f"bold {ACCENT_COLOR}"))
            menu_grid.add_row("")
            
            for i, opt in enumerate(options):
                is_cur = i == idx
                prefix = "▶ " if is_cur else "  "
                style = f"bold {BRAND_COLOR}" if is_cur else "dim"
                menu_grid.add_row(Text(f"{prefix}{opt}", style=style))
                
            grid.add_row(Padding(menu_grid, (0, 4)))
            grid.add_row(Text("\n [↑↓] Navigate  [Enter] Select  [Q] Abort", style="dim"))
            
            live.update(grid, refresh=True)
            key = get_key()
            
            if key == '\x1b[A': idx = (idx - 1) % len(options)
            elif key == '\x1b[B': idx = (idx + 1) % len(options)
            elif key.lower() == 'q': return None, -1
            elif key in ('\r', '\n'): return options[idx], idx

def show_victory_animation():
    """
    Renders a brief, premium confetti-like animation for achieving the daily goal.
    Uses random particles and colors to create a 'Victory Burst' effect.
    """
    import random
    import time
    import shutil
    
    particles = ["✨", "✦", "✖", "◆", "⭐", "★"]
    colors = ["yellow", "cyan", "magenta", "white", "green"]
    
    with Live(auto_refresh=False, console=console) as live:
        for _ in range(12):  # Brief 1.2s burst
            width = shutil.get_terminal_size().columns
            burst = "".join([
                f"[bold {random.choice(colors)}]{random.choice(particles)}[/] " 
                if random.random() > 0.8 else "  " 
                for _ in range(width // 2)
            ])
            live.update(Padding(Text.from_markup(burst), (0, 2)), refresh=True)
            time.sleep(0.08)
        live.update(Text("")) # Clear after burst
