import httpx
import sys
import shutil
from datetime import datetime, timedelta
from typing import Optional
from grit import __version__
from grit.constants import UPDATE_CHECK_TIMEOUT
from grit.state import StateManager

# We can point this to a raw file on GitHub or a simple version endpoint
VERSION_URL = "https://raw.githubusercontent.com/hammaadworks/grit/main/pyproject.toml"

def get_upgrade_command() -> str:
    """
    Intelligently determines the best upgrade command based on the environment.
    """
    # Check if running via 'uv'
    if "uv" in sys.executable or shutil.which("uv"):
        return "uv tool upgrade grit"
    
    return "pip install -U grit"

def get_latest_version(state: StateManager) -> Optional[str]:
    """
    Checks if a version update is available, but only once per day to stay premium.
    """
    last_check_str = state.get_config("last_update_check")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if last_check_str == today:
        return state.get_config("latest_version_available")
    
    try:
        # We'll try to fetch the latest version from a remote pyproject.toml
        # For this example, we timeout quickly to not block the CLI
        with httpx.Client(timeout=UPDATE_CHECK_TIMEOUT) as client:
            response = client.get(VERSION_URL)
            if response.status_code == 200:
                # Simple parsing of version = "X.X.X" from pyproject.toml
                import re
                match = re.search(r'version = "([^"]+)"', response.text)
                if match:
                    latest_version = match.group(1)
                    state.set_config("last_update_check", today)
                    if latest_version != __version__:
                        state.set_config("latest_version_available", latest_version)
                        return latest_version
                    else:
                        state.set_config("latest_version_available", "")
    except Exception:
        # Fail silently to maintain a premium, uninterrupted experience
        pass
    
    return None

def is_update_available(state: StateManager) -> Optional[str]:
    """Returns the latest version if an update is available, otherwise None."""
    return get_latest_version(state)
