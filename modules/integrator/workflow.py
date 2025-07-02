import asyncio
import json
import logging
import os
from modules.parser.tutti_session import TuttiSession
from modules.parser.tutti_scraper import parse_all_pages
from modules.email_checker.async_checker import run_async_email_check
from modules.smtp_sender.smtp_sender import send_emails_async


def run_parser(max_pages=3, cookies_path="config/tutti_cookies.json"):
    logging.info("[WORKFLOW] Парсинг объявлений")
    session = TuttiSession(cookies_path=cookies_path, headless=True)
    driver = session.driver

    try:
        results = parse_all_pages(driver, max_pages=max_pages)
        os.makedirs("data", exist_ok=True)
        with open("data/parsed_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logging.info(f"[WORKFLOW] Парсинг завершён. Сохранено: {len(results)} записей.")
    except Exception as e:
        logging.error(f"[WORKFLOW] Ошибка на этапе парсинга: {e}")
    finally:
        session.close()


async def run_workflow(dry_run=True):
    logging.info("[WORKFLOW] Запуск полного пайплайна...")

    # 1. Tutti Parser
    run_parser()

    # 2. Email Generator & Checker
    logging.info("[WORKFLOW] Генерация и валидация email-адресов...")
    try:
        await run_async_email_check()
        logging.info("[WORKFLOW] Проверка e-mail адресов завершена.")
    except Exception as e:
        logging.error(f"[WORKFLOW] Ошибка при проверке e-mail: {e}")

    # 3. SMTP Sender
    logging.info("[WORKFLOW] Отправка писем...")
    try:
        await send_emails_async(dry_run=dry_run)
        logging.info("[WORKFLOW] Рассылка завершена.")
    except Exception as e:
        logging.error(f"[WORKFLOW] Ошибка при отправке писем: {e}")
