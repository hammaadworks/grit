import pytest
from unittest.mock import patch, MagicMock
from pydantic_ai.models.test import TestModel
from grit.ai import generate_commit_message
from grit.constants import COMMIT_TYPES

def test_generate_commit_message_success():
    """Verify that generate_commit_message handles successful model output correctly."""
    diff = "test diff"
    base_url = "http://localhost:11434/v1"
    api_key = "ollama"
    model_name = "ollama:llama3.2"

    # Mock get_staged_files to avoid git dependency in this test
    with patch("grit.executor.get_staged_files", return_value=["file1.py", "file2.py"]):
        # Use a real CommitMessage instance as the model output
        # With dynamic model, we can't import the class, but the mock can return an object
        # with the required attributes.
        mock_output = MagicMock()
        mock_output.type = "feat"
        mock_output.scope = "core"
        mock_output.message = "add new feature"
        mock_output.body = ["detailed point 1", "detailed point 2"]
        
        mock_result = MagicMock()
        mock_result.output = mock_output
        
        with patch("grit.ai.Agent.run_sync", return_value=mock_result):
            res = generate_commit_message(diff, base_url, api_key, model_name, COMMIT_TYPES)
            
            assert res is not None
            assert "feat(core): add new feature" in res
            assert "- detailed point 1" in res
            assert "- detailed point 2" in res

def test_generate_commit_message_failure():
    """Verify that generate_commit_message returns None on fatal errors."""
    diff = "test diff"
    
    with patch("grit.ai.Agent.run_sync", side_effect=Exception("API failure")):
        res = generate_commit_message(diff, "url", "key", "model", COMMIT_TYPES)
        assert res is None

def test_generate_commit_message_empty_diff():
    """Verify that generate_commit_message returns None for empty diff."""
    res = generate_commit_message("", "url", "key", "model", COMMIT_TYPES)
    assert res is None

def test_generate_commit_message_gemini_detection():
    """Verify that gemini models trigger the google-gla provider and set correct env vars."""
    diff = "test diff"
    base_url = "Not configured"
    api_key = "test-gemini-key"
    model_name = "gemini-1.5-flash"

    with patch("grit.executor.get_staged_files", return_value=["test.py"]):
        mock_output = MagicMock()
        mock_output.type = "fix"
        mock_output.scope = "ui"
        mock_output.message = "fix bug"
        mock_output.body = ["impact analysis"]
        
        mock_result = MagicMock()
        mock_result.output = mock_output
        
        # Patch the Agent class itself so we can check its initialization
        with patch("grit.ai.Agent") as MockAgent:
            # Setup the mock agent instance
            mock_agent_instance = MockAgent.return_value
            mock_agent_instance.run_sync.return_value = mock_result
            
            with patch("os.environ.update") as mock_env_update:
                generate_commit_message(diff, base_url, api_key, model_name, COMMIT_TYPES)
                
                # Verify provider detection logic
                MockAgent.assert_called()
                args, kwargs = MockAgent.call_args
                assert args[0] == "google-gla:gemini-1.5-flash"
                
                # Check if environment variables were updated with GEMINI_API_KEY
                called_env = mock_env_update.call_args[0][0]
                assert called_env["GEMINI_API_KEY"] == "test-gemini-key"
                assert called_env["GOOGLE_API_KEY"] == "test-gemini-key"

def test_generate_commit_message_no_body():
    """Verify that generate_commit_message handles empty body correctly (no extra newlines)."""
    diff = "test diff"
    from grit.constants import COMMIT_TYPES
    
    with patch("grit.executor.get_staged_files", return_value=["file1.py"]):
        mock_output = MagicMock()
        mock_output.type = "feat"
        mock_output.scope = "core"
        mock_output.message = "add new feature"
        mock_output.body = [] # Empty body
        
        mock_result = MagicMock()
        mock_result.output = mock_output
        
        with patch("grit.ai.Agent.run_sync", return_value=mock_result):
            res = generate_commit_message(diff, "url", "key", "model", COMMIT_TYPES)
            
            assert res == "feat(core): add new feature"

def test_generate_commit_message_instructions():
    """Verify that the instructions passed to the Agent contain the caveman-commit rules."""
    diff = "test diff"
    from grit.constants import COMMIT_TYPES
    
    with patch("grit.executor.get_staged_files", return_value=["test.py"]):
        with patch("grit.ai.Agent") as MockAgent:
            mock_agent_instance = MockAgent.return_value
            mock_agent_instance.run_sync.return_value = MagicMock()
            
            generate_commit_message(diff, "url", "key", "model", COMMIT_TYPES)
            
            MockAgent.assert_called()
            args, kwargs = MockAgent.call_args
            instructions = kwargs.get("instructions", "")
            
            assert "terse and exact" in instructions
            assert "No fluff" in instructions
            assert "Why over what" in instructions
            assert "PROHIBITED" in instructions
            assert "≤50 chars" in instructions
