import pytest
from typer.testing import CliRunner
from grit.cli import app
from grit.state import StateManager

runner = CliRunner()

@pytest.fixture
def clean_state(tmp_path, mocker):
    db_path = tmp_path / "state.db"
    mock_state = StateManager(db_path)
    # Patch the global state object in cli.py
    mocker.patch("grit.cli.state", mock_state)
    # Set up basic config to avoid being redirected to config wizard
    mock_state.set_config("daily_target", "5")
    mock_state.set_config("start_date", "2024-01-01")
    mock_state.set_config("github_username", "testuser")
    mock_state.set_config("fill_strategy", "start_date")
    yield mock_state
    mock_state.close()

def test_status_command(clean_state, mocker):
    mocker.patch("grit.cli.run_status")
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0

def test_sync_command(clean_state, mocker):
    mocker.patch("grit.cli.run_sync")
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0

def test_move_command(clean_state, mocker):
    mocker.patch("grit.cli.run_move")
    result = runner.invoke(app, ["move"])
    assert result.exit_code == 0

def test_spread_command(clean_state, mocker):
    mocker.patch("grit.cli.run_spread")
    result = runner.invoke(app, ["spread", "HEAD~1..HEAD"])
    assert result.exit_code == 0

def test_undo_command(clean_state, mocker):
    mocker.patch("grit.cli.run_undo")
    result = runner.invoke(app, ["undo"])
    assert result.exit_code == 0

def test_dashboard_command(clean_state, mocker):
    mocker.patch("grit.cli.run_dashboard")
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 0

def test_branch_command(clean_state, mocker):
    mocker.patch("grit.cli.run_branch_manager")
    result = runner.invoke(app, ["branch"])
    assert result.exit_code == 0

def test_info_command(clean_state, mocker):
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Grit" in result.stdout
