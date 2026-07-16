import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest
from typer.testing import CliRunner

from estate_intelligence.cli import app


def test_dashboard_cli_check_passes(dashboard_database: Path) -> None:
    result = CliRunner().invoke(app, ["dashboard-check", "--database", str(dashboard_database)])

    assert result.exit_code == 0
    assert "Dashboard check passed." in result.output
    assert "simulation_readiness: review_required" in result.output


def test_streamlit_app_starts_locally_and_stops_cleanly() -> None:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "dashboard/streamlit_app.py",
            "--server.headless",
            "true",
            "--server.address",
            "127.0.0.1",
            "--server.port",
            "8507",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 20
        started = False
        health_urls = (
            "http://127.0.0.1:8507/_stcore/health",
            "http://127.0.0.1:8507/healthz",
        )
        while time.time() < deadline:
            if process.poll() is not None:
                break
            for health_url in health_urls:
                try:
                    with urlopen(health_url, timeout=1) as response:
                        started = response.status == 200
                        break
                except OSError:
                    continue
            if started:
                break
            time.sleep(0.5)
        if not started and process.poll() is not None and process.stdout is not None:
            output = process.stdout.read()
            if "PermissionError" in output and "Operation not permitted" in output:
                pytest.skip("Local sandbox blocked child-process Streamlit socket binding.")
        assert started
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
