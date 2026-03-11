import pytest
from typer.testing import CliRunner
from grit.cli import app
from unittest.mock import MagicMock

runner = CliRunner()

def test_sponsor_command_output(mocker):
    """Test that the sponsor command displays the sponsorship panel."""
    # Mock webbrowser.open to avoid opening a real browser
    mock_browser = mocker.patch("webbrowser.open")
    # Mock Confirm.ask to return False to avoid blocking
    mocker.patch("grit.commands.sponsor.Confirm.ask", return_value=False)
    # Mock banner to avoid cluttering output
    mocker.patch("grit.commands.sponsor.get_banner_layout", return_value="")
    
    result = runner.invoke(app, ["sponsor"])
    
    assert result.exit_code == 0
    assert "Support Grit Development" in result.stdout
    assert "Sponsor on GitHub" in result.stdout
    assert "Buy Me a Coffee" in result.stdout

def test_sponsor_command_opens_browser(mocker):
    """Test that the sponsor command opens the browser when confirmed."""
    mock_browser = mocker.patch("webbrowser.open")
    mock_confirm = mocker.patch("grit.commands.sponsor.Confirm.ask", return_value=True)
    mocker.patch("grit.commands.sponsor.get_banner_layout", return_value="")
    
    result = runner.invoke(app, ["sponsor"])
    
    assert result.exit_code == 0
    mock_confirm.assert_called_once()
    # Verify default=True is passed
    assert mock_confirm.call_args[1].get('default') is True
    mock_browser.assert_called_once_with("https://github.com/sponsors/hammaadworks")

def test_help_sections(mocker):
    """Test that the help output contains the reorganized sections."""
    # We need to run with --help
    result = runner.invoke(app, ["--help"])
    
    assert result.exit_code == 0
    # Typer with rich_markup_mode="rich" should show the panel titles
    assert "Maintenance & Support" in result.stdout
    assert "sponsor" in result.stdout
    assert "info" in result.stdout
    assert "ungrit" in result.stdout
