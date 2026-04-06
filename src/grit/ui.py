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
