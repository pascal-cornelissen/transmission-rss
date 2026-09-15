import urllib.request
import xml.etree.ElementTree as ET
import logging
import re
from datetime import timezone
from email.utils import parsedate_to_datetime

log = logging.getLogger(__name__)

TV_NS = "https://showrss.info"

def fetch_feed(url):
    log.info("Fetching RSS feed")
    req = urllib.request.Request(url, headers={"User-Agent": "transmission-rss/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

def parse_items(xml_text):
    log.debug("Parsing RSS items")
    root = ET.fromstring(xml_text)
    items = []
    
    for item in root.findall(".//item"):
        # extracting data

        #title
        title_el = item.find("title")
        title = title_el.text.strip() if title_el is not None else "Unknown"
        
        # Publication date
        pubdate_el = item.find("pubDate")
        if pubdate_el is None or not pubdate_el.text:
            log.warning(f"Skipping item without pubDate: {title}")
            continue
        try:
            pub_date = parsedate_to_datetime(pubdate_el.text.strip()).astimezone(timezone.utc)
        except Exception as e:
            log.warning(f"Could not parse pubDate for '{title}': {e}")
            continue

        # Show name from <tv:show_name>
        show_el = item.find(f"{{{TV_NS}}}show_name")
        show_name = show_el.text.strip() if show_el is not None and show_el.text else "Unknown Show"

        # Raw title for season extraction
        raw_title_el = item.find(f"{{{TV_NS}}}raw_title")
        raw_title = raw_title_el.text.strip() if raw_title_el is not None and raw_title_el.text else title

        # Season derived from SxxExx pattern
        season = None
        match = re.search(r'\bS(\d{2})E\d{2}\b', raw_title, re.IGNORECASE)
        if match:
            season = f"Season {match.group(1)}"
        else:
            log.warning(f"No season found for: {title}")

        # Magnet link from <enclosure url="magnet:...">
        magnet = None
        for tag in item:
            if tag.get("url", "").startswith("magnet:"):
                magnet = tag.get("url").strip()
                break
            if tag.text and tag.text.startswith("magnet:"):
                magnet = tag.text.strip()
                break
        if magnet is None:
            log.warning(f"No magnet found for: {title}")
            continue

        items.append({
            "title":     title,
            "raw_title": raw_title,
            "pub_date":  pub_date,
            "show_name": show_name,
            "season":    season,
            "magnet":    magnet,
        })

        log.debug(f"Parsed: {title} | {show_name} | {season} | {pub_date}")

    return items

def get_items(url):
    xml_text = fetch_feed(url)
    return parse_items(xml_text)