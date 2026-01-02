import subprocess
import typer
from grit.ui import console, print_banner

def run_log(ctx: typer.Context):
    """
    A beautiful, human-readable, and visually enhanced git log on jetpack rollerskates.
    Addresses community issues by providing a clear, colorful, and branched view of your repository history.
    """
    # The ultimate human-readable git log format
    format_string = (
        "%C(bold blue)%h%C(reset) "          # Hash
        "%C(dim white)-%C(reset) "           # Separator
        "%C(bold green)(%ar)%C(reset) "      # Time
        "%C(white)%s%C(reset) "              # Message
        "%C(dim white)- %an%C(reset) "       # Author
        "%C(auto)%d%C(reset)"                # Refs (branches, tags)
    )
    
    # We pass the args through so the user can still use -n 10, --author, etc.
    args = ["git", "log", "--graph", "--color=always", "--abbrev-commit", f"--format={format_string}"] + ctx.args
    
    try:
        # Use subprocess.run without capture_output so git can use its native pager (less)
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError:
        pass
    except KeyboardInterrupt:
        pass
