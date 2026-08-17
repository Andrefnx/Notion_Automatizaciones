import argparse
import logging

from notion_automation.config import Config
from notion_automation.demo import run_demo


def main():
    parser = argparse.ArgumentParser(description="Notion finance automation")
    parser.add_argument("--demo", action="store_true", help="Run with fictitious local data")
    parser.add_argument("--real", action="store_true", help="Validate real Notion configuration")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.demo or not args.real:
        run_demo()
        return

    config = Config.from_env()
    if config.dry_run:
        print("Real configuration validated. DRY_RUN=true: no Notion modifications executed.")
        return
    raise SystemExit("Live writes are intentionally disabled in main.py. Use a reviewed automation module explicitly.")


if __name__ == "__main__":
    main()
