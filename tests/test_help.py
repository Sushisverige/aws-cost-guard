from typer.testing import CliRunner
from aws_cost_guard.cli import app

def test_help():
    r = CliRunner().invoke(app, ["--help"])
    assert r.exit_code == 0
