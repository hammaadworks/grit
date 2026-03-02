import http.server
import socketserver
import json
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

from grit.state import StateManager
from grit.allocator import DateAllocator
from grit.sync import sync_historical_data

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler for the Grit Dashboard.
    Provides a REST API for metrics and serves the static dashboard UI.
    """
    state = StateManager()

    def do_GET(self):
        if self.path.startswith('/api/stats'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()
            
            stats = self._get_stats()
            self.wfile.write(json.dumps(stats).encode())
        elif self.path == '/' or self.path == '/dashboard':
            # Serve the dashboard.html file
            html_path = Path(__file__).parent / "dashboard.html"
            if html_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
                self.send_header('Pragma', 'no-cache')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Dashboard UI not found.")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                
                # Update configuration keys
                if "daily_target" in data:
                    self.state.set_config("daily_target", str(data["daily_target"]))
                if "start_date" in data:
                    self.state.set_config("start_date", str(data["start_date"]))
                if "github_username" in data:
                    self.state.set_config("github_username", str(data["github_username"]))
                if "fill_strategy" in data:
                    self.state.set_config("fill_strategy", str(data["fill_strategy"]))
                if "ai_base_url" in data:
                    self.state.set_config("ai_base_url", str(data["ai_base_url"]))
                if "ai_api_key" in data:
                    self.state.set_config("ai_api_key", str(data["ai_api_key"]))
                if "ai_model" in data:
                    self.state.set_config("ai_model", str(data["ai_model"]))
                
                # Trigger sync if relevant settings changed
                if "github_username" in data or "start_date" in data:
                    username = self.state.get_config("github_username")
                    start_date = self.state.get_config("start_date")
                    if username and username != "Not configured" and start_date:
                        sync_historical_data(self.state, str(username), str(start_date))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif self.path == '/api/sync':
            try:
                username = self.state.get_config("github_username")
                start_date = self.state.get_config("start_date")
                if username and username != "Not configured" and start_date:
                    sync_historical_data(self.state, str(username), str(start_date))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

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
            progress_pct = min(100.0, (effective_done / total_required) * 100) if total_required > 0 else 0.0

        # Pipeline data
        allocator = DateAllocator(self.state)
        allocations = allocator.get_status_allocations()
        
        # History data for the chart (last 365 days for the contribution graph)
        history = []
        for i in range(364, -1, -1):
            d = (today_dt - timedelta(days=i)).strftime("%Y-%m-%d")
            history.append({
                "date": d,
                "count": self.state.get_commit_count(d),
                "target": target
            })

        # Monthly stats for sparkline
        monthly_stats = []
        for i in range(5, -1, -1):
            # Last 6 months
            month_date = today_dt - timedelta(days=i*30)
            month_key = month_date.strftime("%Y-%m")
            monthly_stats.append({
                "month": month_date.strftime("%b"),
                "count": self.state.get_monthly_commits(month_key)
            })

        return {
            "config": {
                "username": username,
                "target": target,
                "start_date": start_date,
                "fill_strategy": fill_strategy,
                "ai_base_url": self.state.get_config("ai_base_url"),
                "ai_api_key": self.state.get_config("ai_api_key"),
                "ai_model": self.state.get_config("ai_model")
            },
            "metrics": {
                "total_done": self.state.get_total_commits(start_date) if not is_placeholder(start_date) else 0,
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
