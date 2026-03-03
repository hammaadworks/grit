import pytest
import re
from grit.executor import get_git_timestamp, execute_git_commit

def test_timestamp_formatting():
    """Test that the timestamp formatting strictly follows Git's required format."""
    date_str = "2024-03-22"
    timestamp = get_git_timestamp(date_str)
    
    # Starts with the injected target date
    assert timestamp.startswith("2024-03-22 ")
    
    # Matches: YYYY-MM-DD HH:MM:SS +/-HHMM
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}$", timestamp)

def test_state_not_incremented_on_git_failure(mocker):
    """If `git commit` fails (e.g. empty commit, pre-commit failure), do not increment count."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    
    mocker.patch("grit.executor.get_head_hash", side_effect=["old_hash", "old_hash"])
    
    mock_state = mocker.Mock()
    
    success = execute_git_commit(["-m", "fail test"], "2024-01-01", mock_state)
    
    assert success is False
    mock_state.increment_commit_count.assert_not_called()
    
    # Verify environment variable injection on the commit call
    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args.kwargs
    assert "GIT_AUTHOR_DATE" in call_kwargs["env"]
    assert "GIT_COMMITTER_DATE" in call_kwargs["env"]
    assert call_kwargs["env"]["GIT_AUTHOR_DATE"] == call_kwargs["env"]["GIT_COMMITTER_DATE"]

def test_state_incremented_on_git_success(mocker):
    """If `git commit` succeeds, increment the commit count in the database."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    
    mocker.patch("grit.executor.get_head_hash", side_effect=["old_hash", "new_hash"])
    
    mock_state = mocker.Mock()
    
    success = execute_git_commit(["-m", "success test"], "2024-01-01", mock_state)
    
    assert success is True
    mock_state.increment_commit_count.assert_called_once_with("2024-01-01")
    
    # Verify exact argument passthrough and date injection
    mock_run.assert_called_once()
    call_args = mock_run.call_args.args[0]
    call_kwargs = mock_run.call_args.kwargs
    assert call_args == ["git", "commit", "-m", "success test"]
    assert call_kwargs["env"]["GIT_AUTHOR_DATE"] == call_kwargs["env"]["GIT_COMMITTER_DATE"]
