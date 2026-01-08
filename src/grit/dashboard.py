import http.server
import json
import socketserver
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from grit.allocator import DateAllocator
from grit.state import StateManager
from grit.sync import sync_historical_data


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler for the Grit Dashboard.
    Provides a REST API for metrics and serves the static dashboard UI.
    """
    state = StateManager()

    def send_json(self, data: Any, status: int = 200):
        """Helper to send JSON with correct headers, preventing FD leaks via
        Content-Length."""
        response_body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response_body)))
        self.send_header(
            'Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0'
            )
        self.send_header('Pragma', 'no-cache')
        self.end_headers()
        self.wfile.write(response_body)

    def do_GET(self):
        if self.path.startswith('/api/stats'):
            stats = self._get_stats()
            self.send_json(stats)
        elif self.path == '/api/db/tables':
            cursor = self.state._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
                )
            tables = [row[0] for row in cursor.fetchall()]
            self.send_json(tables)
        elif self.path.startswith('/api/db/data'):
            from urllib.parse import urlparse, parse_qs

            query = parse_qs(urlparse(self.path).query)
            table = query.get('table', [None])[0]
            if table in ['config', 'commits']:
                cursor = self.state._conn.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                self.send_json(rows)
            else:
                self.send_error(400, "Invalid table")
        elif self.path == '/' or self.path == '/dashboard':
            # Serve the dashboard.html file
            html_path = Path(__file__).parent / "dashboard.html"
            if html_path.exists():
                with open(html_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Content-Length', str(len(content)))
                self.send_header(
                    'Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0'
                    )
                self.send_header('Pragma', 'no-cache')
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Dashboard UI not found.")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/config':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return self.send_json({"error": "Empty payload"}, 400)
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)

                # Update configuration keys
                for key in ["daily_target", "start_date", "github_username",
                            "fill_strategy", "ai_base_url", "ai_api_key", "ai_model"]:
                    if key in data:
                        self.state.set_config(key, str(data[key]))

                # Trigger sync if relevant settings changed
                if "github_username" in data or "start_date" in data:
                    username = self.state.get_config("github_username")
                    start_date = self.state.get_config("start_date")
                    if username and username != "Not configured" and start_date:
                        sync_historical_data(self.state, str(username), str(start_date))

                self.send_json({"status": "success"})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
        elif self.path == '/api/db/edit':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return self.send_json({"error": "Empty payload"}, 400)
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                table = data.get('table')
                row = data.get('row')  # This should be a list/dict of values

                if table == 'config':
                    self.state.set_config(row[0], row[1])
                elif table == 'commits':
                    self.state.set_commit_count(row[0], int(row[1]))
                else:
                    raise Exception("Invalid table")

                self.send_json({"status": "success"})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
        elif self.path == '/api/db/delete':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return self.send_json({"error": "Empty payload"}, 400)
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                table = data.get('table')
                pk = data.get('pk')  # Primary key value

                with self.state._conn as conn:
                    if table == 'config':
                        conn.execute("DELETE FROM config WHERE key = ?", (pk,))
                    elif table == 'commits':
                        conn.execute("DELETE FROM commits WHERE date = ?", (pk,))
                    else:
                        raise Exception("Invalid table")

                self.send_json({"status": "success"})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
        elif self.path == '/api/sync':
            try:
                username = self.state.get_config("github_username")
                start_date = self.state.get_config("start_date")
                if username and username != "Not configured" and start_date:
                    sync_historical_data(self.state, str(username), str(start_date))

                self.send_json({"status": "success"})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
        else:
            self.send_error(404)

    def _get_stats(self) -> dict[str, Any]:
        """Calculates all metrics required for the visual dashboard."""
        target_raw = self.state.get_config("daily_target")
        start_date = self.state.get_config("start_date")
        username = self.state.get_config("github_username")
        fill_strategy = self.state.get_config("fill_strategy") or "start_date"

        def is_placeholder(val):
            return not val or val in ["Not configured", "None", ""]

        target = int(target_raw) if not is_placeholder(target_raw) else 0
        today_dt = datetime.now()
        today = today_dt.strftime("%Y-%m-%d")

        # Core metrics
        today_count = self.state.get_commit_count(today)

        total_days = 0
        total_required = 0
        pending = 0
        progress_pct = 0.0
        effective_done = 0

        if not is_placeholder(start_date):
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            total_days = (today_dt - start_dt).days + 1
            total_required = total_days * target

            # Use Effective Commits for logic
            effective_done = self.state.get_effective_commits(start_date, target)
            pending = max(0, total_required - effective_done)
            progress_pct = min(
                100.0, (effective_done / total_required) * 100
                ) if total_required > 0 else 0.0

        # Pipeline data
        allocator = DateAllocator(self.state)
        allocations = allocator.get_status_allocations()

        # History data for the chart (last 365 days for the contribution graph) in a
        # single query
        history = self.state.get_history(365)
        for h in history:
            h["target"] = target

        # Monthly stats for sparkline
        monthly_stats = []
        for i in range(5, -1, -1):
            # Last 6 months
            month_date = today_dt - timedelta(days=i * 30)
            month_key = month_date.strftime("%Y-%m")
            monthly_stats.append(
                {
                    "month": month_date.strftime("%b"),
                    "count": self.state.get_monthly_commits(month_key)
                }
            )

        return {
            "config": {
                "username": username,
                "target": target,
                "start_date": start_date,
                "fill_strategy": fill_strategy,
                "ai_base_url": self.state.get_config("ai_base_url"),
                "ai_api_key": self.state.get_config("ai_api_key"),
                "ai_model": self.state.get_config("ai_model"),
                "db_path": str(self.state.db_path)
            },
            "metrics": {
                "total_done": self.state.get_total_commits(
                    start_date
                    ) if not is_placeholder(start_date) else 0,
                "yearly_done": self.state.get_yearly_commits(today_dt.year),
                "effective_done": effective_done,
                "total_required": total_required,
                "pending": pending,
                "progress_pct": progress_pct,
                "today_count": today_count
            },
            "monthly_stats": monthly_stats,
            "pipeline": allocations,
            "history": history
        }


def start_dashboard(port: int = 0):
    """
    Launches the Grit Dashboard server.
    If port is 0, it finds an available port automatically.
    """
    handler = DashboardHandler
    # Allow port reuse to avoid 'address already in use' errors on restart
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", port), handler) as httpd:
        actual_port = httpd.server_address[1]
        url = f"http://localhost:{actual_port}/"

        print(f"✦ Grit Dashboard active at {url}")
        print("  Press Ctrl+C to shutdown the server.")

        # Automatically open the browser
        webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Grit Dashboard...")
            httpd.shutdown()
