import subprocess
import typer
from grit.ui import console, print_banner, BRAND_COLOR, ACCENT_COLOR, SUCCESS_COLOR

def run_log(ctx: typer.Context):
    """
    A beautiful, human-readable, and visually enhanced git log on jetpack rollerskates.
    Addresses community issues by providing a clear, colorful, and branched view of your repository history.
    """
    # Only show the banner and tips if no arguments were passed (discovery mode)
    if not ctx.args:
        from rich.padding import Padding
        from rich.text import Text
        console.print(Padding(Text("GRIT VISUAL LOG", style=f"bold {ACCENT_COLOR}"), (1, 0, 0, 0)))
        console.print(f"[dim]Showing full branch graph. Use [bold]j/k[/bold] or [bold]arrows[/bold] to navigate. Press [bold]q[/bold] to exit.[/dim]")
        console.print(f"[dim]Tip: Use `grit log --grep=\"fix\"` to search messages, or `grit log HEAD~10..HEAD` for a range.[/dim]\n")

    # High-fidelity format for maximum clarity
    # %C(auto)%d - Decorations (branches/tags)
    # %C(bold cyan)%an - Author name
    # %C(bold green)%ar - Relative time
    # %C(white)%s - Subject
    format_string = (
        "%C(bold blue)%h%C(reset) "          # Hash
        "%C(auto)%d "                        # Decorations (branches, tags)
        "%C(white)%s%C(reset) "              # Message
        "%C(dim white)- %C(bold cyan)%an%C(reset) " # Author
        "%C(bold green)(%ar)%C(reset)"       # Time
    )
    
    # --graph: Visual branching
    # --all: Show all branches, not just current
    # --decorate: Show branch/tag names
    args = [
        "git", "log", 
        "--graph", 
        "--all", 
        "--decorate",
        "--color=always", 
        "--abbrev-commit", 
        f"--format={format_string}"
    ] + ctx.args
    
    try:
        # Use subprocess.run without capture_output so git can use its native pager (less)
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError:
        pass
    except KeyboardInterrupt:
        pass
