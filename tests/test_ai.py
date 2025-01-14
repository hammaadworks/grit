import pytest
from unittest.mock import patch
from pydantic_ai.models.test import TestModel
from grit.ai import generate_commit_message, CommitMessage

def test_generate_commit_message_success():
    """Verify that generate_commit_message handles successful model output correctly."""
    diff = "test diff"
    base_url = "http://localhost:11434/v1"
    api_key = "ollama"
    model_name = "ollama:llama3.2"

    # Mock get_staged_files to avoid git dependency in this test
    with patch("grit.executor.get_staged_files", return_value=["file1.py", "file2.py"]):
        # Use a real CommitMessage instance as the model output
        expected_msg = CommitMessage(
            type="feat",
            scope="core",
            message="add new feature",
            body=["detailed point 1", "detailed point 2"]
        )

        # We need to mock the agent.run_sync result.output
        # Since pydantic-ai's TestModel might not support returning custom objects easily 
        # for complex result_types in older versions without more setup, 
        # we can just patch the Agent.run_sync directly or use TestModel carefully.
        
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.output = expected_msg
        
        with patch("pydantic_ai.Agent.run_sync", return_value=mock_result):
            res = generate_commit_message(diff, base_url, api_key, model_name)
            
            assert res is not None
            assert "feat(core): add new feature" in res
            assert "- detailed point 1" in res
            assert "- detailed point 2" in res

def test_generate_commit_message_failure():
    """Verify that generate_commit_message returns None on fatal errors."""
    diff = "test diff"
    
    with patch("pydantic_ai.Agent.run_sync", side_effect=Exception("API failure")):
        res = generate_commit_message(diff, "url", "key", "model")
        assert res is None

def test_generate_commit_message_empty_diff():
    """Verify that generate_commit_message returns None for empty diff."""
    res = generate_commit_message("", "url", "key", "model")
    assert res is None
