import os
import signal
import subprocess
import sys
from typing import Optional

from grit.state import StateManager
from grit.ui import BRAND_COLOR, console, err_console, ERROR_COLOR, SUCCESS_COLOR, WARN_COLOR, suppress_title_reset
from grit.dashboard import start_dashboard

def run_dashboard(state: StateManager, port: int = 0, logs: bool = False, stop: bool = False):
    """
    Launches or stops the high-fidelity web dashboard.
    A modern offline-first GUI for your commit distribution metrics.
    """
    pid_file = state.db_path.parent / "dashboard.pid"

    if stop:
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                pid_file.unlink()
                console.print(f"[{SUCCESS_COLOR}]✓ Dashboard (PID {pid}) stopped.[/{SUCCESS_COLOR}]")
            except (ProcessLookupError, ValueError):
                console.print(f"[{WARN_COLOR}]! No active dashboard found with that PID. Cleaning up.[/{WARN_COLOR}]")
                if pid_file.exists(): pid_file.unlink()
            except Exception as e:
                err_console.print(f"[{ERROR_COLOR}]✗ Failed to stop dashboard: {e}[/{ERROR_COLOR}]")
        else:
            console.print(f"[{WARN_COLOR}]! No background dashboard is currently running.[/{WARN_COLOR}]")
        return

    if logs:
        # Write PID of foreground process too so it can be stopped
        pid_file.write_text(str(os.getpid()))
        try:
            start_dashboard(port)
        finally:
            if pid_file.exists(): pid_file.unlink()
    else:
        # If no port provided, find one so we can tell the user where to go
        if port == 0:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                port = s.getsockname()[1]

        console.print(
            f"[{BRAND_COLOR}]✦ Launching Grit Dashboard at [bold]http://localhost:{port}[/bold]...[/"
            f"{BRAND_COLOR}]"
            )

        # Launch in background process using the grit dash command
        # We prefer using the current executable if possible
        cmd = [sys.executable, "-m", "grit.cli", "dashboard", "--port", str(port), "--logs"]
        if "grit" in sys.argv[0] or "pytest" not in sys.argv[0]:
            cmd = [sys.argv[0], "dashboard", "--port", str(port), "--logs"]

        suppress_title_reset()

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Save PID for future 'stop' commands
        pid_file.write_text(str(proc.pid))
        
        console.print(
            f"[dim]Background process started with PID: [bold white]{proc.pid}[/bold white][/dim]"
            )
        console.print(
            f"[dim]Run `grit dash --stop` to terminate the server.[/dim]"
            )
