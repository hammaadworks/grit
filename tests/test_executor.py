import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch
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
    
def test_is_commit_pushed(mocker):
    """Test is_commit_pushed logic."""
    from grit.executor import is_commit_pushed
    mock_run = mocker.patch("subprocess.run")
    
    # Simulate not pushed (empty output from branch -r)
    mock_run.return_value.stdout = ""
    assert is_commit_pushed() is False
    
    # Simulate pushed
    mock_run.return_value.stdout = "origin/main"
    assert is_commit_pushed() is True

def test_execute_grit_spread(mocker):
    """Test execute_grit_spread success and rollback."""
    from grit.executor import execute_grit_spread
    
    mock_run = mocker.patch("subprocess.run")
    # Success return object
    success_mock = mocker.Mock(returncode=0, stdout="main")
    
    # Setup success path
    mock_run.side_effect = None
    mock_run.return_value = success_mock
    
    mocker.patch("grit.executor.has_unstaged_files", return_value=False)
    mocker.patch("grit.executor.get_head_hash", return_value="h1")
    
    mock_state = mocker.Mock()
    
    hashes = ["h1", "h2"]
    dates = {"h1": "2024-01-01", "h2": "2024-01-02"}
    
    success = execute_grit_spread(hashes, dates, mock_state)
    assert success is True
    
    # Test failure path: Next call to run should raise exception
    # 1. git branch --show-current (success)
    # 2. git rev-parse (failure)
    # 3. git checkout (cleanup)
    # 4. git branch -D (cleanup)
    mock_run.side_effect = [success_mock, Exception("git failed"), success_mock, success_mock]
    success = execute_grit_spread(hashes, dates, mock_state)
    assert success is False

def test_get_status_files(mocker):
    """Test get_status_files parsing."""
    from grit.executor import get_status_files
    mock_run = mocker.patch("subprocess.run")
    
    # Mock git status --porcelain output
    mock_run.return_value.stdout = "M  file1.txt\nA  file2.txt\n?? new.txt\n D deleted.txt"
    files = get_status_files()
    
    assert len(files) == 4
    assert ("file1.txt", "modified") in files
    assert ("file2.txt", "new") in files
    assert ("new.txt", "new") in files
    assert ("deleted.txt", "deleted") in files
