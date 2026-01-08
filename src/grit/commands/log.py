import shutil
import subprocess

import typer

from grit.ui import ACCENT_COLOR, BRAND_COLOR, console, SUCCESS_COLOR, WARN_COLOR


def run_log(ctx: typer.Context):
    """
    A beautifully enhanced, high-fidelity git log on jetpack rollerskates.
    Optimized for developer clarity, visual hierarchy, and solving the 'git log'
    readability pain.
    """
    # 1. Adaptive Sizing
    columns, _ = shutil.get_terminal_size()

    # 2. Header and Legend (Discovery Mode Only)
    if not ctx.args:
        from rich.padding import Padding
        from rich.text import Text

        # Premium Header
        header = Text()
        header.append("✦ ", style=BRAND_COLOR)
        header.append("GRIT INTELLIGENCE LOG", style=f"bold {ACCENT_COLOR}")
        header.append(" — ", style="dim")
        header.append("Full Repository Graph", style="dim italic")

        legend = Text.from_markup(
            f"[bold {BRAND_COLOR}]HASH[/] [white]MESSAGE[/] [dim white]-[/] ["
            f"cyan]AUTHOR[/] [bold {SUCCESS_COLOR}](TIME)[/]"
        )

        console.print(Padding(header, (1, 0, 0, 0)))
        console.print(Padding(legend, (0, 0, 1, 2)))

    # 3. The "Billion Dollar" Log Format
    # Logic: 
    # - Bold Cyan Hash for easy reference (Git uses standard names like 'cyan')
    # - Auto-color decorations for branch/tag visibility
    # - High-contrast White for the commit message (the "what")
    # - Cyan for the author (the "who")
    # - Success Green for relative time (the "when")
    format_string = (
        "%C(bold cyan)%h%C(reset) "  # Hash
        "%C(auto)%d "  # Decorations
        "%C(white)%s%C(reset) "  # Message
        "%C(dim white)• %C(bold cyan)%an%C(reset) "  # Author
        "%C(bold green)(%ar)%C(reset)"  # Relative Time
    )

    # 4. Command Construction
    # Solving Pain Points:
    # - --graph: Visualizes branching/merging complexity
    # - --all: Provides full context across all local branches
    # - --date-order: Keeps the timeline logical
    # - --abbrev-commit: Keeps output dense
    args = [
               "git", "log",
               "--graph",
               "--all",
               "--decorate",
               "--color=always",
               "--abbrev-commit",
               "--date-order",
               f"--format={format_string}"
           ] + ctx.args

    # 5. Execution & Pager Handling
    try:
        # We use a subshell to ensure git can find its native pager (less) 
        # and respect user-configured GIT_PAGER/PAGER environments.
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError:
        # Common for 'q' exit or broken pipe in pager
        pass
    except KeyboardInterrupt:
        # Smooth exit for Ctrl+C
        console.print("\n[dim italic]Log session terminated.[/dim]")
    except Exception as e:
        console.print(
            f"[{WARN_COLOR}]![/{WARN_COLOR}] Unexpected error rendering log: {str(e)}"
        )
