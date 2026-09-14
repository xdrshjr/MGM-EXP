"""Check the local Python environment without API calls or containers."""

import argparse
import importlib
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    """Run offline checks; return nonzero if a requested check fails."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also require Linux and a working Apptainer executable.",
    )
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".secrets" / "local.env", override=False)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Interpreter: {sys.executable}")
    print(f"Project: {PROJECT_ROOT}")
    for package in (
        "datasets", "swebench", "openai", "anthropic", "pytest", "debugpy",
    ):
        print(f"Package {package}: {version(package)}")
    for module in (
        "config", "llm", "llm_withtools", "coding_agent",
        "coding_agent_polyglot", "utils.apptainer_compat",
        "utils.swebench_compat", "hgm", "evaluate_agent",
    ):
        importlib.import_module(module)
        print(f"Import {module}: OK")

    from config import load_config

    config = load_config(str(PROJECT_ROOT / "config.local.yaml"))
    print(f"Model: {config.llm.downstream_llm}")
    print(f"Workers: {config.execution.max_workers}")
    print(f"API key present: {bool(os.getenv('DEEPSEEK_API_KEY'))}")
    if args.full:
        return check_container_runtime()
    print("Python checks passed. No API request or benchmark was run.")
    print("Full benchmark execution requires Linux + Apptainer (--full).")
    return 0


def check_container_runtime() -> int:
    """Check Linux entry points and Apptainer; return the CLI exit status."""
    from utils.container_runtime import require_container_runtime

    try:
        executable = require_container_runtime()
    except RuntimeError as error:
        print(f"Full runtime unavailable: {error}")
        return 1
    for module in ("hgm", "evaluate_agent", "utils.swebench_compat"):
        importlib.import_module(module)
        print(f"Import {module}: OK")
    return subprocess.run([executable, "version"], timeout=15).returncode


if __name__ == "__main__":
    raise SystemExit(main())
