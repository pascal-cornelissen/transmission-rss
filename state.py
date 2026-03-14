import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

def load_last_date(state_file):
    path = Path(state_file)
    if not path.exists():
        log.info("No state file found, will process all items")
        return None
    try:
        raw = path.read_text().strip()
        dt = datetime.fromisoformat(raw)
        log.info(f"Last processed date: {dt}")
        return dt
    except ValueError:
        log.warning("Could not parse state file, will process all items")
        return None

def save_last_date(state_file, dt):
    path = Path(state_file)
    path.write_text(dt.isoformat())
    log.debug(f"State saved: {dt}")

