import webbrowser
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm

from grit.ui import console, BRAND_COLOR, SUCCESS_COLOR, ACCENT_COLOR, get_banner_layout

def run_sponsor():
    """
    Displays sponsorship options and opens the link.
    """
    text = Text()
    text.append("Building open-source tools takes time, coffee, and late nights. 🌙\n\n", style="dim")
    text.append("If Grit has saved your streaks, fixed your history, or made Git fun again,\n", style="dim")
    text.append("consider supporting the ongoing development of the ultimate Git TUI!\n\n", style="dim")
    
    text.append("💖 Sponsor on GitHub: ", style="bold white")
    text.append("https://github.com/sponsors/hammaadworks\n", style=f"underline {BRAND_COLOR}")
    
    text.append("☕ Buy Me a Coffee:   ", style="bold white")
    text.append("https://buymeacoffee.com/hammaadworks", style=f"underline {BRAND_COLOR}")

    panel = Panel(
        text,
        title=f"[bold {ACCENT_COLOR}]Support Grit Development[/]",
        border_style=SUCCESS_COLOR,
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print()
    
    try:
        if Confirm.ask(f"[{BRAND_COLOR}]Open sponsor page in your browser?[/{BRAND_COLOR}]", default=True):
            webbrowser.open("https://github.com/sponsors/hammaadworks")
            console.print(f"[{SUCCESS_COLOR}]✓ Thank you for your support![/{SUCCESS_COLOR}]")
    except KeyboardInterrupt:
        pass
