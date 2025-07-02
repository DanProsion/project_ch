import argparse
import logging
import json
import asyncio

from modules.parser.tutti_scraper import create_driver, parse_all_pages
from modules.parser.tutti_session import TuttiSession
from modules.email_checker.async_checker import run_async_email_check
from modules.smtp_account_manager.account_manager import SMTPAccountManager
from utils.logger import setup_logging
from modules.integrator.workflow import run_workflow

def main():
    parser = argparse.ArgumentParser(description="Automation Project CLI")

    parser.add_argument("--run-parser", action="store_true", help="Run the tutti.ch parser module")
    parser.add_argument("--run-checker", action="store_true", help="Run the email validation module")
    parser.add_argument("--run-sender", action="store_true", help="Run the SMTP sender module")
    parser.add_argument("--dry-run", action="store_true", help="Run sender in dry-run mode (no emails sent)")
    parser.add_argument("--manage-accounts", action="store_true", help="Manage SMTP accounts")
    parser.add_argument("--list", action="store_true", help="List all SMTP accounts")
    parser.add_argument("--add-json", type=str, help="Add SMTP accounts from a JSON file")
    parser.add_argument("--add-csv", type=str, help="Add SMTP accounts from a CSV file")
    parser.add_argument("--deactivate", type=str, help="Deactivate SMTP account by username")
    parser.add_argument("--update", type=str, help="Update SMTP account by username")
    parser.add_argument("--update-field", type=str, help="Field to update")
    parser.add_argument("--update-value", type=str, help="New value for the field")
    parser.add_argument("--run-workflow", action="store_true", help="Run the entire integrated workflow")
    parser.add_argument("--run-scheduler", action="store_true", help="Запуск задачи по расписанию")


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
        manager = SMTPAccountManager()

        if args.list:
            manager.list_accounts()
        elif args.add_json:
            try:
                with open(args.add_json, "r", encoding="utf-8") as f:
                    new_accounts = json.load(f)
                manager.add_accounts_from_json(new_accounts)
            except Exception as e:
                logging.error(f"Failed to add accounts from JSON: {e}")
        elif args.add_csv:
            try:
                manager.add_accounts_from_csv(args.add_csv)
            except Exception as e:
                logging.error(f"Failed to add accounts from CSV: {e}")
        elif args.deactivate:
            manager.deactivate_account(args.deactivate)
        elif args.update and args.update_field and args.update_value:
            manager.update_account(args.update, {args.update_field: args.update_value})
        else:
            logging.info("No valid subcommand provided for account management.")

    if args.run_workflow:
        logging.info("Running integrated workflow...")
        asyncio.run(run_workflow(dry_run=args.dry_run))

    if args.run_scheduler:
        from modules.integrator import scheduler


if __name__ == "__main__":
    main()