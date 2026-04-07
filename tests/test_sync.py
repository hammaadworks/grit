import pytest
from unittest.mock import patch, MagicMock
from grit.sync import parse_local_git_log, merge_sync_data, fetch_github_contributions

def test_sync_parser_local():
    """Ensure raw git log output is correctly grouped and summed."""
    mock_log = "2024-01-01\n2024-01-01\n2024-01-02\n2024-01-03\n2024-01-03\n2024-01-03"
    counts = parse_local_git_log(mock_log)
    assert counts == {"2024-01-01": 2, "2024-01-02": 1, "2024-01-03": 3}

def test_sync_max_merge_logic(mocker):
    """Ensure merge operations use a MAX() lower bound update rule."""
    mock_db = mocker.Mock()
    
    # Mock DB state: 2024-01-01 has 3 commits locally. Others have 0.
    def get_count_mock(date):
        if date == "2024-01-01": return 3
        return 0
    mock_db.get_commit_count.side_effect = get_count_mock

    # New sync data: 2024-01-01 has more (5), 2024-01-02 has new (2), 2024-01-03 has new (1)
    sync_data = {"2024-01-01": 5, "2024-01-02": 2, "2024-01-03": 1}

    merge_sync_data(mock_db, sync_data)

    # Assert that set_commit_count was called with the MAX values
    calls = mock_db.set_commit_count.call_args_list
    assert mocker.call("2024-01-01", 5) in calls
    assert mocker.call("2024-01-02", 2) in calls
    assert mocker.call("2024-01-03", 1) in calls

def test_sync_max_merge_logic_ignores_lower(mocker):
    """Ensure merge operations do not overwrite high local counts with low remote counts."""
    mock_db = mocker.Mock()
    
    def get_count_mock(date):
        if date == "2024-01-01": return 10 # High local count
        return 0
    mock_db.get_commit_count.side_effect = get_count_mock

    # Remote says only 2 commits
    sync_data = {"2024-01-01": 2}

    merge_sync_data(mock_db, sync_data)

    # Assert that set_commit_count was NOT called with the lower value
    mock_db.set_commit_count.assert_not_called()

def test_get_local_git_stats(mocker):
    """Test get_local_git_stats calls git log and parses correctly."""
    from grit.sync import get_local_git_stats
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.stdout = "2024-01-01\n2024-01-01\n2024-01-02"
    mock_run.return_value.returncode = 0
    
    stats = get_local_git_stats()
    assert stats == {"2024-01-01": 2, "2024-01-02": 1}

def test_fetch_github_contributions_fail(mocker):
    """Test fetch_github_contributions when request fails."""
    # We must patch httpx inside grit.sync
    mocker.patch("grit.sync.httpx.get", side_effect=Exception("Network error"))
    stats = fetch_github_contributions("testuser")
    assert stats == {}

def test_sync_historical_data(mocker):
    """Test sync_historical_data loop."""
    from grit.sync import sync_historical_data
    mock_state = mocker.Mock()
    mock_state.get_commit_count.return_value = 0
    mocker.patch("grit.sync.fetch_github_contributions", return_value={"2024-01-01": 5})
    
    # Mock datetime in grit.sync
    mock_dt = mocker.patch("grit.sync.datetime")
    mock_now = MagicMock()
    mock_now.year = 2024
    mock_dt.now.return_value = mock_now
    
    sync_historical_data(mock_state, "testuser", "2024-01-01")
        
    assert mock_state.add_synced_year.called
