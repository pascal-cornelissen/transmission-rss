import subprocess
import logging
from pathlib import Path

log = logging.getLogger(__name__)

def add_torrent(host, port, username, password, magnet, destination_path, dry_run):
    cmd = ["transmission-remote", f"{host}:{port}"]
    
    if username and password:
        cmd += ["--auth", f"{username}:{password}"]
    
    cmd += ["--download-dir", str(destination_path), "--add", magnet]
    
    if dry_run:
        log.info(f"  [DRY RUN] Would add to: {destination_path}")
        log.info(f"  [DRY RUN] Magnet: {magnet[:50]}...")
        return True

    log.debug(f"Running command: {cmd}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        log.info(f"  ✓ Added successfully")
        return True
    
    if "authentication" in result.stderr.lower() or "401" in result.stderr:
        log.error("Authentication failed — check tr_username and tr_password in config")
    else:
        log.error(f"Failed to add torrent: {result.stderr.strip()}")
    return False


def build_destination_path(destination, show_name, season):
    base = Path(destination)
    show = sanitise_dirname(show_name)
    
    if season:
        path = base / show / season
    else:
        log.warning(f"No season found for '{show_name}', using show folder")
        path = base / show

    return path


def sanitise_dirname(name):
    import re
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()