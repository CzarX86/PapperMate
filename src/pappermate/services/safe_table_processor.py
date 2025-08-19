"""
SafeTableProcessor: wraps Marker's TableProcessor with guards to prevent hard crashes
when tables have empty inputs or the recognizer raises.
"""

from typing import Any

try:
    from marker.processors.table import TableProcessor
    from marker.logger import get_logger
    MARKER_AVAILABLE = True
except Exception:  # pragma: no cover
    MARKER_AVAILABLE = False
    TableProcessor = object  # type: ignore


class SafeTableProcessor(TableProcessor):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        if not MARKER_AVAILABLE:
            raise ImportError("Marker is not available")
        super().__init__(*args, **kwargs)
        self._logger = get_logger()

    def __call__(self, document):  # type: ignore[override]
        try:
            return super().__call__(document)
        except Exception as exc:  # pragma: no cover
            # Soft-fail: log and skip table processing so the rest of the pipeline proceeds
            self._logger.error(f"SafeTableProcessor: skipping table processing due to error: {exc}")
            return


