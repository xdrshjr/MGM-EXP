"""Regression coverage for unsupported local benchmark runtimes."""

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from utils import apptainer_compat, container_runtime


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_require_runtime_rejects_non_linux(monkeypatch, platform):
    monkeypatch.setattr(sys, "platform", platform)
    with pytest.raises(RuntimeError, match="Linux \\+ Apptainer"):
        container_runtime.require_container_runtime()


def test_require_runtime_explains_missing_executable(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="APPTAINER_BIN"):
        container_runtime.require_container_runtime()


def test_require_runtime_resolves_configured_executable(monkeypatch):
    executable = "/opt/apptainer/bin/apptainer"
    looked_up = []
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(apptainer_compat, "APPTAINER_BIN", executable)

    def find_executable(name):
        looked_up.append(name)
        return executable

    monkeypatch.setattr(shutil, "which", find_executable)
    assert container_runtime.require_container_runtime() == executable
    assert looked_up == [executable]


def test_container_factory_checks_before_creating_workspaces(monkeypatch):
    created = []
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(
        container_runtime,
        "ApptainerClient",
        lambda **kwargs: created.append(kwargs),
    )
    with pytest.raises(RuntimeError, match="Linux \\+ Apptainer"):
        container_runtime.container_from_env()
    assert created == []


@pytest.mark.parametrize("entry", ["evaluate_agent", "hgm"])
def test_entry_rejects_runtime_before_dataset_or_output(entry, tmp_path):
    project = Path(__file__).resolve().parents[1]
    output = tmp_path / "must-not-be-created"
    arguments = (
        ["--agent_path", str(project), "--results_dir", str(output)]
        if entry == "evaluate_agent"
        else ["--config", "config.yaml", "--output_dir", str(output)]
    )
    code = textwrap.dedent("""
        import importlib
        import runpy
        import sys
        import datasets

        entry, arguments = sys.argv[1], sys.argv[2:]
        importlib.import_module(entry)

        def reject_dataset(*args, **kwargs):
            raise AssertionError('dataset requested before runtime check')

        datasets.load_dataset = reject_dataset
        sys.platform = 'win32'
        sys.argv = [entry + '.py', *arguments]
        runpy.run_path(sys.argv[0], run_name='__main__')
    """)
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-s", "-c", code, entry, *arguments],
        cwd=project,
        env={**os.environ, "HF_HUB_OFFLINE": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Linux + Apptainer" in result.stderr
    assert "dataset requested" not in result.stderr
    assert not output.exists()
