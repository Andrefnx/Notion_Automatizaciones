import json
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)


def run_demo(path="demo/data.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    records = data.get("records", [])
    LOG.info("Demo loaded: %d fictitious records", len(records))
    print("NOTION AUTOMATION - DEMO MODE")
    print("No credentials or network connection are used.\n")
    for automation in data.get("automations", []):
        print(f"[OK] {automation['name']}: {automation['summary']}")
    print(f"\nProcessed records: {len(records)}")
    print(f"Simulated errors: {len(data.get('errors', []))}")
    return data
