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

def print_banner(animated: bool = False):
    """
    Renders a premium minimalist banner to provide branding consistency.
    This banner is printed at the start of most high-level user commands.
    """
    ascii_art = r"""
    ██████╗ ██████╗ ██╗████████╗
    ██╔════╝ ██╔══██╗██║╚══██╔══╝
    ██║  ███╗██████╔╝██║   ██║   
    ██║   ██║██╔══██╗██║   ██║   
    ╚██████╔╝██║  ██║██║   ██║   
     ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝   
    """
    
    # Print ASCII art in BRAND_COLOR
    for line in ascii_art.strip("\n").split("\n"):
        console.print(Text(line, style=f"bold {BRAND_COLOR}"))
    
    tagline = Text()
    tagline.append("✦ ", style=BRAND_COLOR)
    tagline.append(f"v{__version__}", style="dim")
    tagline.append(" — Intelligently distribute your commits", style="dim")
    console.print(Padding(tagline, (0, 0, 1, 0)))

def show_victory_animation():
    """
    Renders a brief, premium confetti-like animation for achieving the daily goal.
    Uses random particles and colors to create a 'Victory Burst' effect.
    """
    import random
    import time
    import shutil
    from rich.live import Live
    
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
