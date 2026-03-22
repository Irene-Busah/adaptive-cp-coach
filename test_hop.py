import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from cli import app as cli_app

runner = CliRunner()

@patch("commands.hop.subprocess.run")
def test_hop_no_git_repo(mock_run):
    # Mock get_current_branch returning empty string (not a git repo)
    mock_run.return_value = MagicMock(stdout="")
    result = runner.invoke(cli_app, ["hop", "main"])
    assert result.exit_code == 1
    assert "Not currently in a git repository" in result.stdout

@patch("commands.hop.subprocess.run")
def test_hop_to_same_branch(mock_run):
    # Mock current branch as 'main'
    mock_run.return_value = MagicMock(stdout="main\n")
    result = runner.invoke(cli_app, ["hop", "main"])
    assert result.exit_code == 0
    assert "Already on branch 'main'" in result.stdout

@patch("commands.hop.has_uncommitted_changes")
@patch("commands.hop.get_current_branch")
@patch("commands.hop.subprocess.run")
def test_hop_to_different_branch_no_changes(mock_run, mock_get_branch, mock_has_changes):
    mock_get_branch.return_value = "main"
    mock_has_changes.return_value = False
    
    # Mock checkout to succeed
    mock_checkout = MagicMock()
    mock_checkout.returncode = 0
    mock_run.return_value = mock_checkout
    
    result = runner.invoke(cli_app, ["hop", "feature-branch"])
    assert result.exit_code == 0
    assert "Changes detected" not in result.stdout
    assert "Checking out branch 'feature-branch'" in result.stdout
    assert "Pulling latest changes" in result.stdout
    assert "Successfully hopped to feature-branch" in result.stdout

@patch("commands.hop.has_uncommitted_changes")
@patch("commands.hop.get_current_branch")
@patch("commands.hop.subprocess.run")
def test_hop_to_different_branch_with_changes(mock_run, mock_get_branch, mock_has_changes):
    mock_get_branch.return_value = "main"
    mock_has_changes.return_value = True
    
    # Mock checkout to succeed
    mock_checkout = MagicMock()
    mock_checkout.returncode = 0
    mock_run.return_value = mock_checkout
    
    result = runner.invoke(cli_app, ["hop", "feature-branch"])
    assert result.exit_code == 0
    assert "Changes detected! Saving stash..." in result.stdout
    assert "Checking out branch 'feature-branch'" in result.stdout
    assert "Successfully hopped to feature-branch" in result.stdout

@patch("commands.hop.get_current_branch")
@patch("commands.hop.subprocess.run")
def test_hop_back(mock_run, mock_get_branch):
    mock_get_branch.return_value = "feature-branch"
    
    result = runner.invoke(cli_app, ["hop", "-"])
    assert result.exit_code == 0
    assert "Hopping back to previous branch" in result.stdout
    assert "Popping the most recent stash" in result.stdout
    assert "Successfully hopped back!" in result.stdout
