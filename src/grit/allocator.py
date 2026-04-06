import sqlite3
from datetime import datetime, timedelta
from grit.state import StateManager

def get_today() -> str:
    """Returns today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

class DateAllocator:
    """
    The core date discovery engine for Grit.
    
    This class handles the logic of finding the next available date for a commit
    based on the user's daily target and start date, as well as providing
    the timeline view for the status dashboard.
    """
    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    def get_next_date(self, current_counts: dict[str, int] = None) -> str:
        """
        Determines the next date to allocate a commit to based on the configured strategy.
        If current_counts is provided, it uses those values instead of querying the DB
        for those specific dates (useful for batch simulations like 'grit spread').
        """
        target_str = self.state.get_config("daily_target")
        start_date = self.state.get_config("start_date")
        fill_strategy = self.state.get_config("fill_strategy") or "start_date"
        
        def is_placeholder(val):
            return not val or val in ["Not configured", "None", ""]
            
        if is_placeholder(target_str) or is_placeholder(start_date):
            raise ValueError("Grit is not fully configured. Please run `grit config`.")
            
        daily_target = int(target_str)
        today = get_today()
        
        order_dir = "DESC" if fill_strategy == "today" else "ASC"
        
        # If we have current_counts, we can't easily do it in a single SQL query 
        # without complex temp tables. For small batches, we'll just fetch the top 
        # candidates and filter in Python.
        
        query = f"""
        WITH RECURSIVE dates(d) AS (
            SELECT ? -- Start Date
            UNION ALL
            SELECT date(d, '+1 day')
            FROM dates
            WHERE d < date(?, '+365 days')
        )
        SELECT d.d, COALESCE(c.count, 0)
        FROM dates d
        LEFT JOIN commits c ON d.d = c.date
        ORDER BY 
            CASE 
                WHEN d.d = ? THEN 0 
                WHEN d.d < ? THEN 1 
                ELSE 2 
            END ASC,
            CASE 
                WHEN d.d < ? THEN d.d 
            END {order_dir},
            d.d ASC
        LIMIT 100; -- Fetch enough to find a gap
        """
        
        with sqlite3.connect(self.state.db_path) as conn:
            cursor = conn.execute(query, (start_date, today, today, today, today))
            rows = cursor.fetchall()
            
            for date_str, db_count in rows:
                # Use current_counts override if available
                count = current_counts.get(date_str, db_count) if current_counts else db_count
                if count < daily_target:
                    return date_str
                    
        return today

    def get_status_allocations(self) -> list[dict]:
        """
        Returns a specific 3-row timeline for the status dashboard:
        1. Today: The current primary focus.
        2. Next Available: The first date where a new commit will land (following the streak logic).
        3. Next-Next Available: The subsequent spillover target.
        
        Returns:
            list[dict]: A list of objects containing 'date', 'count', and 'target'.
        """
        target_str = self.state.get_config("daily_target")
        start_date = self.state.get_config("start_date")
        
        def is_placeholder(val):
            return not val or val in ["Not configured", "None", ""]
            
        if is_placeholder(target_str) or is_placeholder(start_date):
            return []
            
        daily_target = int(target_str)
        today = get_today()
        fill_strategy = self.state.get_config("fill_strategy") or "start_date"
        order_dir = "DESC" if fill_strategy == "today" else "ASC"
        
        # We start with the guaranteed "Context Rows" (Today).
        res_dates = [today]
        
        # Use the same priority logic as get_next_date to find the next few available slots.
        query = f"""
        WITH RECURSIVE dates(d) AS (
            SELECT ? 
            UNION ALL
            SELECT date(d, '+1 day')
            FROM dates
            WHERE d < date(?, '+365 days')
        )
        SELECT d.d
        FROM dates d
        LEFT JOIN commits c ON d.d = c.date
        WHERE COALESCE(c.count, 0) < ?
        ORDER BY 
            CASE 
                WHEN d.d = ? THEN 0 
                WHEN d.d < ? THEN 1 
                ELSE 2 
            END ASC,
            CASE 
                WHEN d.d < ? THEN d.d 
            END {order_dir},
            d.d ASC
        LIMIT 10;
        """
        
        with sqlite3.connect(self.state.db_path) as conn:
            cursor = conn.execute(query, (start_date, today, daily_target, today, today, today))
            rows = cursor.fetchall()
            next_dates = [row[0] for row in rows]
            
            # Fill out the remaining slots from the query results.
            for nd in next_dates:
                if nd not in res_dates:
                    res_dates.append(nd)
                if len(res_dates) >= 4:
                    break
            
            # Emergency fallback: If search space is exhausted, simply increment days.
            if len(res_dates) < 4:
                last_date_str = res_dates[-1] if res_dates else today
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                while len(res_dates) < 4:
                    last_date += timedelta(days=1)
                    res_dates.append(last_date.strftime("%Y-%m-%d"))
        
        # Final data assembly with current commit counts from the database.
        final_allocations = []
        for d in res_dates:
            final_allocations.append({
                "date": d,
                "count": self.state.get_commit_count(d),
                "target": daily_target
            })
            
        return final_allocations
