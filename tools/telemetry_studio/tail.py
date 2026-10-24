"""Live log tail: parse ZDB1 events as a log grows (read-only, no game launch)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterator

from .ingest import read_zdbi_lines


def tail_events(path: Path, *, follow: bool = False, from_start: bool = True,
                poll_seconds: float = 1.0, max_events: int | None = None) -> Iterator[dict]:
    """Yield parsed ZDB1 events from a log file.

    ``follow=False`` reads currently available lines; ``follow=True`` keeps
    polling for appended lines (intended for a live recorder session). The
    generator never writes to the log and never fabricates events.
    """
    path = Path(path).expanduser()
    emitted = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        if follow and not from_start:
            handle.seek(0, 2)
        while True:
            line = handle.readline()
            if not line:
                if not follow:
                    break
                time.sleep(max(0.2, poll_seconds))
                continue
            if not line.startswith("ZDB1|"):
                continue
            for event in read_zdbi_lines(line):
                emitted += 1
                yield event
                if max_events is not None and emitted >= max_events:
                    return
