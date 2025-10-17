import pytest
from typer.testing import CliRunner
from grit.cli import app
from grit.state import StateManager

runner = CliRunner()

@pytest.fixture
def clean_state(tmp_path, mocker):
    # Create a fresh isolated DB for the CLI tests
    db_path = tmp_path / "state.db"
    mock_state = StateManager(db_path)
    
    # Patch the global state object in cli.py to use our isolated DB
    mocker.patch("grit.cli.state", mock_state)
    yield mock_state
    mock_state.close()

def test_cli_first_run_interception(clean_state, mocker):
    """If no DB config exists, grit commit launches config TUI."""
    # Mock TUI components to avoid infinite loop or terminal issues in CI
    mocker.patch("grit.cli.is_config_valid", side_effect=[False, True])
    mocker.patch("grit.cli.config")
    
    result = runner.invoke(app, ["commit", "-m", "test"])
    
    # It should detect incomplete config and try to run config()
    assert "Configuration is incomplete" in result.output

def test_cli_amend_warning(clean_state, mocker):
    """If DB is configured and we run --amend, issue warning but still run command."""
    # Setup baseline config
    clean_state.set_config("daily_target", "5")
    clean_state.set_config("start_date", "2024-01-01")
    clean_state.set_config("github_username", "testuser")
    clean_state.set_config("fill_strategy", "start_date")
    
    # Mock subprocess.run to not actually run git
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    
    result = runner.invoke(app, ["commit", "--amend", "-m", "fix"])
    
    # Check that the specific warning panel was output
    assert "Amend detected" in result.output
    
    # Check that git commit --amend was still actually executed
    calls = [call.args[0] for call in mock_run.mock_calls if call.args]
    assert ["git", "commit", "--amend", "-m", "fix"] in calls

def test_interactive_setup_flow(clean_state, mocker):
    """Simulate Typer prompt inputs for config and ensure state is saved."""
    # Mock network call so tests run fast without internet
    mocker.patch("grit.commands.config.sync_historical_data")

    # The new TUI sequence with 'Allocation Strategy' toggle:
    # 0: target. Press Enter. Mock returns "5".
    # 1: start. Press Down, Enter. Mock returns "2024-01-01".
    # 2: fill. Press Down, Enter. (Toggles instantly, no input required)
    # 3: user. Press Down, Enter. Mock returns "testuser".
    # Press 'S' to save and exit.
    keys = ['\r', '\x1b[B', '\r', '\x1b[B', '\r', '\x1b[B', '\r', 's']
    mocker.patch("grit.commands.config.get_key", side_effect=keys)

    # Mock input for the edits (only 3 calls now because 'fill' is a toggle)
    mocker.patch("builtins.input", side_effect=["5", "2024-01-01", "testuser"])

    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0

    # Verify DB was updated
    assert clean_state.get_config("daily_target") == "5"
    assert clean_state.get_config("start_date") == "2024-01-01"
    # Fill strategy toggles from 'start_date' to 'today'
    assert clean_state.get_config("fill_strategy") == "today"
    assert clean_state.get_config("github_username") == "testuser"

def test_non_interactive_setup_flow(clean_state, mocker):
    """Simulate headless setup using CLI flags."""
    # Pass all config via flags
    result = runner.invoke(app, ["config", "--target", "10", "--start", "2024-02-02", "--username", "headlessuser"])
    
    assert result.exit_code == 0
    assert "Headless configuration applied" in result.stdout
    
    # Verify DB was updated correctly without prompt blocks
    assert clean_state.get_config("daily_target") == "10"
    assert clean_state.get_config("start_date") == "2024-02-02"
    assert clean_state.get_config("github_username") == "headlessuser"

def test_wizard_staged_files_interception(clean_state, mocker):
    """If files are already staged, grit commit wizard still allows adjusting selection."""
    # Setup baseline config
    clean_state.set_config("daily_target", "5")
    clean_state.set_config("start_date", "2024-01-01")
    clean_state.set_config("github_username", "testuser")
    clean_state.set_config("fill_strategy", "start_date")

    # Mock git state: one staged file, one unstaged file
    mocker.patch("grit.commands.commit.get_unstaged_files", return_value=["staged.txt", "unstaged.txt"])
    mocker.patch("grit.commands.commit.get_staged_files", return_value=["staged.txt"])

    # Mock Live and get_key to abort immediately with 'q'
    mock_live = mocker.patch("grit.commands.commit.Live")
    mocker.patch("grit.commands.commit.get_key", return_value='q')
    
    # Run the command
    result = runner.invoke(app, ["commit"])

    # Check that Live was used for file picking
    assert mock_live.called
    assert "Aborted." in result.stdout

def test_cli_ungrit_interactive(clean_state):
    """Test securely deleting the config directory with prompt."""
    clean_state.db_path.parent.mkdir(parents=True, exist_ok=True)
    clean_state.db_path.touch()
    
    # Confirm deletion interactively
    result = runner.invoke(app, ["ungrit"], input="y\n")
    
    assert result.exit_code == 0
    assert "Grit has been decommissioned" in result.stdout
    assert not clean_state.db_path.parent.exists()

def test_cli_ungrit_force_flag(clean_state):
    """Test securely deleting the config directory with the force flag."""
    clean_state.db_path.parent.mkdir(parents=True, exist_ok=True)
    clean_state.db_path.touch()
    
    # No input provided, use flag
    result = runner.invoke(app, ["ungrit", "--force"])
    
    assert result.exit_code == 0
    assert "Grit has been decommissioned" in result.stdout
    assert not clean_state.db_path.parent.exists()

def test_cli_log_invocation(clean_state, mocker):
    """Test that grit log calls git log with the correct visual graph arguments."""
    # Pre-configure state so it doesn't trigger the config wizard
    clean_state.set_config("daily_target", "5")
    clean_state.set_config("start_date", "2024-01-01")
    clean_state.set_config("github_username", "testuser")
    clean_state.set_config("fill_strategy", "start_date")

    # We use mocker.Mock() to avoid UnsupportedOperation('fileno') 
    # when CliRunner executes the command and tries to connect to the terminal.
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    
    # We need to use catch_exceptions=False or handle the specific way 
    # git log interacts with the terminal during tests.
    result = runner.invoke(app, ["log", "-n", "5"], catch_exceptions=False)
    
    # In some test environments, invoke might fail due to TTY issues with 
    # direct subprocess calls. We'll check if it was at least attempted.
    assert mock_run.called
    
    # Check that subprocess.run was called with git log and the specific format
    calls = [call.args[0] for call in mock_run.mock_calls if call.args]
    git_log_call = next(c for c in calls if c[0] == "git" and c[1] == "log")
    
    assert "--graph" in git_log_call
    assert "--all" in git_log_call
    assert "--decorate" in git_log_call
    assert "--color=always" in git_log_call
    assert "-n" in git_log_call
    assert "5" in git_log_call
