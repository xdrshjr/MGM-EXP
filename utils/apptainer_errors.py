"""Exception types used by the Apptainer Docker compatibility client."""

from __future__ import annotations

try:
    from docker.errors import APIError, BuildError, ImageNotFound, NotFound
except ImportError:
    class APIError(Exception):
        pass


    class NotFound(Exception):
        pass


    class ImageNotFound(NotFound):
        pass


    class BuildError(Exception):
        def __init__(self, message: str, build_log: str = "") -> None:
            super().__init__(message)
            self.build_log = build_log
