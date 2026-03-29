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

    def get_next_date(self) -> str:
        """
        Determines the next date to allocate a commit to based on the configured strategy:
        1. If today's count < daily_target, return today.
        2. If today is full, fill gaps based on 'fill_strategy' (today or start_date).
        3. If all past dates are full, schedule in the future (earliest available).
        
        Returns:
            str: The target date in YYYY-MM-DD format.
        """
        target_str = self.state.get_config("daily_target")
        start_date = self.state.get_config("start_date")
        fill_strategy = self.state.get_config("fill_strategy") or "today"
        
        def is_placeholder(val):
            return not val or val in ["Not configured", "None", ""]
            
        if is_placeholder(target_str) or is_placeholder(start_date):
            raise ValueError("Grit is not fully configured. Please run `grit config`.")
            
        daily_target = int(target_str)
        today = get_today()
        
        # Determine filling direction for past holes
        # 'today' means DESC (closest to today first)
        # 'start_date' means ASC (closest to start date first)
        order_dir = "DESC" if fill_strategy == "today" else "ASC"
        
        query = f"""
        WITH RECURSIVE dates(d) AS (
            SELECT ? -- Start Date
            UNION ALL
            SELECT date(d, '+1 day')
            FROM dates
            WHERE d < date(?, '+365 days') -- Bounded search space
        )
        SELECT d.d
        FROM dates d
        LEFT JOIN commits c ON d.d = c.date
        WHERE COALESCE(c.count, 0) < ?
        ORDER BY 
            CASE 
                WHEN d.d = ? THEN 0 -- Today is the highest priority
                WHEN d.d < ? THEN 1 -- Past dates are next (backfilling)
                ELSE 2              -- Future dates are the spillover
            END ASC,
            CASE 
                WHEN d.d < ? THEN d.d 
            END {order_dir},
            d.d ASC   -- Fill the EARLIEST future hole first
        LIMIT 1;
        """
        
        with sqlite3.connect(self.state.db_path) as conn:
            # We pass 'today' multiple times for the priority CASE logic
            cursor = conn.execute(query, (start_date, today, daily_target, today, today, today))
            row = cursor.fetchone()
            if row:
                target_date = row[0]
                target_year = int(target_date.split('-')[0])
                
                # Verified Boundary Rule:
                # We refuse to allocate to a year that hasn't been synced.
                # This prevents "Dark Zone" collisions where Grit assumes 0 commits
                # because it hasn't checked GitHub/Git logs for that year yet.
                if not self.state.is_year_synced(target_year):
                    # We'll allow the CLI to handle the JIT Sync, but for the allocator,
                    # we must signal that this date is 'Unverified'.
                    pass 
                
                return target_date
                
        return today

    def get_status_allocations(self) -> list[dict]:
        """
        Returns a specific 4-row timeline for the status dashboard:
        1. Yesterday: To show historical context.
        2. Today: The current primary focus.
        3. Next Available: The first date where a new commit will land (following the streak logic).
        4. Next-Next Available: The subsequent spillover target.
        
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
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        fill_strategy = self.state.get_config("fill_strategy") or "today"
        order_dir = "DESC" if fill_strategy == "today" else "ASC"
        
        # We start with the guaranteed "Context Rows" (Yesterday and Today).
        res_dates = [today, yesterday]
        
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
            
            # Fill out the remaining two slots from the query results.
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
