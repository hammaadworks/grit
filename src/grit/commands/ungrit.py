import shutil
import typer
from grit.state import StateManager
from grit.ui import console, ERROR_COLOR, SUCCESS_COLOR, WARN_COLOR

def run_ungrit(state: StateManager, force: bool = False):
    """
    Securely decommission Grit and delete all local configuration and state.
    """
    if not force:
        if not typer.confirm(
                f"[{ERROR_COLOR}]⚠ Are you sure you want to delete all Grit state?[/"
                f"{ERROR_COLOR}]",
                default=False
                ):
            return

    db_dir = state.db_path.parent
    if db_dir.exists() and db_dir.name != "":
        shutil.rmtree(db_dir)
        console.print(
            f"[{SUCCESS_COLOR}]✓ Grit has been decommissioned.[/{SUCCESS_COLOR}]"
            )
    else:
        console.print(f"[{WARN_COLOR}]![/{WARN_COLOR}] No Grit state found.")
