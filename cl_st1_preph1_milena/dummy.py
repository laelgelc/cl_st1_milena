#!/usr/bin/env python3
import argparse
import logging
import sys
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dummy long-running job for testing EC2 + Bash orchestration."
    )
    parser.add_argument(
        "--test",
        "-t",
        action="store_true",
        help="Run in test mode (5 minutes instead of 10).",
    )
    return parser.parse_args()


def setup_logging() -> None:
    # Logs to both stdout and a file named dummy.log
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("dummy.log", mode="a", encoding="utf-8"),
        ],
    )


def main() -> None:
    args = parse_args()
    setup_logging()

    total_minutes = 5 if args.test else 10
    mode = "TEST" if args.test else "PRODUCTION"

    logging.info("Starting dummy job in %s mode for %d minutes.", mode, total_minutes)

    for minute in range(1, total_minutes + 1):
        logging.info("Dummy job progress: minute %d/%d", minute, total_minutes)
        time.sleep(60)

    logging.info("Dummy job finished successfully after %d minutes.", total_minutes)


if __name__ == "__main__":
    main()