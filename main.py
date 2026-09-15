import yaml
import logging
from pathlib import Path
import rss
import state
import transmission

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    
    config = {
        "rss_url":          raw["rss_url"],
        "quality":          (raw.get("quality") or "").strip(),
        "state_file":       Path(raw["state_file"]).expanduser(),
        "log_file":         Path(raw["log"]["file"]).expanduser(),
        "log_level":        raw["log"]["level"].upper(),
        "tr_host":          raw["transmission"]["host"],
        "tr_port":          raw["transmission"]["port"],
        "tr_username":      raw["transmission"]["username"],
        "tr_password":      raw["transmission"]["password"],
        "tr_destination":   raw["transmission"]["destination"],
        "dry_run":          raw.get("dry_run", False),
    }

    return config

def setup_logging(log_level, log_file):
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
 
def process_feed(config, url, since=None):
    items = rss.get_items(url)
    log.info(f"Found {len(items)} items in feed")

    if config["quality"]:
        quality = config["quality"].lower()
        items = [i for i in items if quality in i["raw_title"].lower()]
        log.info(f"{len(items)} items left after quality filter '{config['quality']}'")

    if since:
        items = [i for i in items if i["pub_date"] > since]
        log.info(f"{len(items)} new items since {since}")

    newest_date = None
    for item in items:
        log.info(f"  {item['show_name']} | {item['season']} | {item['pub_date']}")

        destination_path = transmission.build_destination_path(
            config["tr_destination"],
            item["show_name"],
            item["season"]
        )

        success = transmission.add_torrent(
            host=config["tr_host"],
            port=config["tr_port"],
            username=config["tr_username"],
            password=config["tr_password"],
            magnet=item["magnet"],
            destination_path=destination_path,
            dry_run=config["dry_run"]
        )

        if success and (newest_date is None or item["pub_date"] > newest_date):
            newest_date = item["pub_date"]

    return newest_date

config = load_config()

setup_logging(config["log_level"], config["log_file"])
log = logging.getLogger(__name__)

log.info("Config loaded successfully")

items = rss.get_items(config["rss_url"])
log.info(f"Found {len(items)} items in feed")

last_date = state.load_last_date(config["state_file"])
newest_date = process_feed(config, config["rss_url"], since=last_date)

if newest_date:
    state.save_last_date(config["state_file"], newest_date)