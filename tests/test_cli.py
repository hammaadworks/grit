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
    return mock_state

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
    assert "Warning: Amends are not tracked" in result.stdout
    
    # Check that git commit --amend was still actually executed
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0] == ["git", "commit", "--amend", "-m", "fix"]

def test_interactive_setup_flow(clean_state, mocker):
    """Simulate Typer prompt inputs for config and ensure state is saved."""
    # Mock network call so tests run fast without internet
    mocker.patch("grit.cli._sync_github")

    # The new TUI sequence with 'Allocation Strategy' toggle:
    # 0: target. Press Enter. Mock returns "5".
    # 1: start. Press Down, Enter. Mock returns "2024-01-01".
    # 2: fill. Press Down, Enter. TOGGLES (no prompt).
    # 3: user. Press Down, Enter. Mock returns "testuser".
    # Press 'S' to save and exit.
    keys = ['\n', '\x1b[B', '\n', '\x1b[B', '\n', '\x1b[B', '\n', 'S']
    mocker.patch("grit.cli.get_key", side_effect=keys)

    # Mock typer.prompt for the 3 edits (target, start, user)
    # Fill is a toggle, so it doesn't use prompt.
    mocker.patch("typer.prompt", side_effect=["5", "2024-01-01", "testuser"])

    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0

    # Verify DB was updated
    assert clean_state.get_config("daily_target") == "5"
    assert clean_state.get_config("start_date") == "2024-01-01"
    # Default was start_date (which I set as default), toggle changed it to today
    # Wait, default in cli.py is now "start_date"
    # "start_date" toggle -> "today"
    assert clean_state.get_config("fill_strategy") == "today"
    assert clean_state.get_config("github_username") == "testuser"

def test_non_interactive_setup_flow(clean_state, mocker):
    """Simulate headless setup using CLI flags."""
    mocker.patch("grit.cli._sync_github")
    
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
    mocker.patch("grit.cli.get_unstaged_files", return_value=["staged.txt", "unstaged.txt"])
    mocker.patch("grit.cli.get_staged_files", return_value=["staged.txt"])

    # Just mock get_key to abort immediately with 'q'
    mocker.patch("grit.cli.get_key", return_value='q')
    
    # Run the command
    result = runner.invoke(app, ["commit"])

    # Check that file picker was shown
    assert "Select files to stage" in result.stdout
    assert "Aborted." in result.stdout

def test_cli_ungrit_interactive(clean_state):
    """Test securely deleting the config directory with prompt."""
    clean_state.db_path.parent.mkdir(parents=True, exist_ok=True)
    clean_state.db_path.touch()
    
    # Confirm deletion interactively
    result = runner.invoke(app, ["ungrit"], input="y\n")
    
    assert result.exit_code == 0
    assert "Grit decommissioned" in result.stdout
    assert not clean_state.db_path.parent.exists()

def test_cli_ungrit_force_flag(clean_state):
    """Test securely deleting the config directory with the force flag."""
    clean_state.db_path.parent.mkdir(parents=True, exist_ok=True)
    clean_state.db_path.touch()
    
    # No input provided, use flag
    result = runner.invoke(app, ["ungrit", "--force"])
    
    assert result.exit_code == 0
    assert "Grit decommissioned" in result.stdout
    assert not clean_state.db_path.parent.exists()
