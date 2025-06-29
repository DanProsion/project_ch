import argparse
import logging
import json
import asyncio

from modules.parser.tutti_scraper import create_driver, parse_all_pages
from modules.parser.tutti_session import TuttiSession
from modules.email_checker.async_checker import run_async_email_check
from utils.logger import setup_logging


def main():
    parser = argparse.ArgumentParser(description="Automation Project CLI")

    parser.add_argument(
        "--run-parser", action="store_true", help="Run the tutti.ch parser module"
    )
    parser.add_argument(
        "--run-checker", action="store_true", help="Run the email validation module"
    )
    parser.add_argument(
        "--run-sender", action="store_true", help="Run the SMTP sender module"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Run sender in dry-run mode (no emails sent)"
    )

    parser.add_argument(
        "--manage-accounts", action="store_true", help="Manage SMTP accounts"
    )
    parser.add_argument(
        "--run-workflow", action="store_true", help="Run the entire integrated workflow"
    )

    args = parser.parse_args()
    setup_logging()
    logging.info("Starting Automation Project...")

    if args.run_parser:
        logging.info("Running tutti.ch parser...")
        session = TuttiSession(cookies_path="config/tutti_cookies.json", headless=False)
        driver = session.driver
        results = parse_all_pages(driver, max_pages=3)

        with open("data/parsed_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        session.close()
        logging.info("Parser completed. Data saved to data/parsed_data.json")

    if args.run_checker:
        logging.info("Running email checker...")
        asyncio.run(run_async_email_check())
        logging.info("Email check completed.")

    if args.run_sender:
        logging.info("Running SMTP sender...")
        from modules.smtp_sender.smtp_sender import send_emails_async
        asyncio.run(send_emails_async(dry_run=args.dry_run))

    if args.manage_accounts:
        logging.info("Managing SMTP accounts...")
        # TODO: Implement SMTP account management

    if args.run_workflow:
        logging.info("Running integrated workflow...")
        # TODO: Implement full workflow execution


if __name__ == "__main__":
    main()
