"""Local Apptainer container client (sole supported runtime)."""

from __future__ import annotations

import shutil
import sys

from utils import apptainer_compat
from utils.apptainer_compat import ApptainerClient


def require_container_runtime() -> str:
    """Return the Apptainer executable or raise for an unsupported runtime.

    Raises:
        RuntimeError: Python is not running on Linux or Apptainer is missing.
    """
    if sys.platform != "linux":
        raise RuntimeError(
            "MGM benchmark execution requires Linux + Apptainer. "
            f"Current interpreter: {sys.executable}. "
            "Run with Linux Python inside WSL2/Ubuntu or on a Linux server; "
            "Windows Conda Python cannot execute Linux containers. "
            "See docs/local-debug.md."
        )
    executable = shutil.which(apptainer_compat.APPTAINER_BIN)
    if executable is None:
        raise RuntimeError(
            f"Apptainer executable not found: {apptainer_compat.APPTAINER_BIN!r}. "
            "Install Apptainer in this Linux environment and add it to PATH, "
            "or set APPTAINER_BIN before starting Python. "
            "Verify with 'apptainer version'."
        )
    return executable


def container_from_env(timeout: int | None = None) -> ApptainerClient:
    """Return the Apptainer client used by all harness and self-improve paths."""
    require_container_runtime()
    return ApptainerClient(timeout=timeout)
