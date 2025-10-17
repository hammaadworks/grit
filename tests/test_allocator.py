import pytest
import sqlite3
from datetime import datetime
from grit.state import StateManager
from grit.allocator import DateAllocator

@pytest.fixture
def db(tmp_path):
    state_db = StateManager(tmp_path / "state.db")
    # Setup standard config
    state_db.set_config("daily_target", "5")
    state_db.set_config("start_date", "2024-01-01")
    yield state_db
    state_db.close()

def test_allocator_first_commit(db):
    """If today is empty, it should return today."""
    allocator = DateAllocator(db)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Empty DB, target=5, start=2024-01-01
    next_date = allocator.get_next_date()
    assert next_date == today

def test_allocator_forward_scan_memoization(db, mocker):
    """If today and all past dates are full, return tomorrow."""
    # Mock 'today' to be 2024-01-03
    mocker.patch('grit.allocator.get_today', return_value="2024-01-03")
    
    # Fill today and past dates
    db.set_commit_count("2024-01-01", 5)
    db.set_commit_count("2024-01-02", 5)
    db.set_commit_count("2024-01-03", 5) # today is full
    
    allocator = DateAllocator(db)
    next_date = allocator.get_next_date()
    
    # Expected tomorrow
    assert next_date == "2024-01-04"

def test_allocator_config_change_invalidates_memo(db, mocker):
    """If target changes, previously full days are now available."""
    mocker.patch('grit.allocator.get_today', return_value="2024-01-03")
    
    # Fill up to 5
    db.set_commit_count("2024-01-01", 5)
    db.set_commit_count("2024-01-02", 5)
    db.set_commit_count("2024-01-03", 5)
    
    # Change target to 10
    db.set_config("daily_target", "10")
    
    allocator = DateAllocator(db)
    next_date = allocator.get_next_date()
    
    # Today is now available again because it only has 5/10
    assert next_date == "2024-01-03"

def test_allocator_fill_strategy_today(db, mocker):
    """If fill_strategy is 'today', it should prioritize today, then future, then past."""
    mocker.patch('grit.allocator.get_today', return_value="2024-01-04")
    
    db.set_config("start_date", "2024-01-01")
    db.set_config("fill_strategy", "today")
    
    # 2024-01-02 is deficient but strategy is 'today'
    db.set_commit_count("2024-01-01", 5)
    db.set_commit_count("2024-01-02", 2) 
    db.set_commit_count("2024-01-03", 5)
    db.set_commit_count("2024-01-04", 5) # today is full
    
    allocator = DateAllocator(db)
    next_date = allocator.get_next_date()
    
    # Priority: 2024-01-04 (full) -> 2024-01-05 (empty, priority 2) -> 2024-01-02 (empty, priority 3)
    assert next_date == "2024-01-05"

def test_get_status_allocations(db, mocker):
    """Test get_status_allocations returns correct structure."""
    mocker.patch('grit.allocator.get_today', return_value="2024-01-04")
    db.set_commit_count("2024-01-04", 3)
    
    allocator = DateAllocator(db)
    allocs = allocator.get_status_allocations()
    
    assert len(allocs) > 0
    assert allocs[0]['date'] == "2024-01-04"
    assert allocs[0]['count'] == 3
    assert allocs[0]['target'] == 5

def test_allocator_unconfigured(db):
    """If config is missing, it should raise ValueError or return empty."""
    db.set_config("daily_target", "None")
    allocator = DateAllocator(db)
    
    with pytest.raises(ValueError, match="Grit is not fully configured"):
        allocator.get_next_date()
        
    allocs = allocator.get_status_allocations()
    assert allocs == []

def test_get_status_allocations_fallback(db, mocker):
    """If the search space is exhausted, it should fallback to incrementing days."""
    mocker.patch('grit.allocator.get_today', return_value="2024-01-04")
    
    # Set daily target to 0 so every day is 'full'
    db.set_config("daily_target", "0")
    
    allocator = DateAllocator(db)
    allocs = allocator.get_status_allocations()
    
    # Should still return 4 rows starting with today, then tomorrow, etc.
    assert len(allocs) == 4
    assert allocs[0]['date'] == "2024-01-04"
    assert allocs[1]['date'] == "2024-01-05"
    assert allocs[2]['date'] == "2024-01-06"
    assert allocs[3]['date'] == "2024-01-07"

def test_get_next_date_no_candidates(db, mocker):
    """If no candidates found (extremely rare), it should return today."""
    mocker.patch('grit.allocator.get_today', return_value="2024-01-04")
    
    # Set daily target to 0 so no date matches 'count < target'
    db.set_config("daily_target", "0")
    
    allocator = DateAllocator(db)
    assert allocator.get_next_date() == "2024-01-04"

def test_get_next_date_with_mock_counts(db, mocker):
    """Test get_next_date when passing temporary count overrides."""
    # Start date is 2024-01-01
    mocker.patch('grit.allocator.get_today', return_value="2024-01-04")
    
    # Fill past dates to force today or future
    db.set_commit_count("2024-01-01", 5)
    db.set_commit_count("2024-01-02", 5)
    db.set_commit_count("2024-01-03", 5)
    db.set_commit_count("2024-01-04", 4)
    
    allocator = DateAllocator(db)
    
    # If mock says today has 5, it should go to tomorrow (2024-01-05)
    next_date = allocator.get_next_date(current_counts={"2024-01-04": 5})
    assert next_date == "2024-01-05"
    
    # If mock says today has 4, it should stay today
    next_date = allocator.get_next_date(current_counts={"2024-01-04": 4})
    assert next_date == "2024-01-04"
