import asyncio
import json
import os

from modules.parser.tutti_session import TuttiSession
from modules.parser.tutti_scraper import parse_all_pages
from modules.email_checker.async_checker import run_async_email_check
from modules.smtp_sender.smtp_sender import send_emails_async

from utils.logger import log_step  # Импорт функции логирования


def run_parser(max_pages=3, cookies_path="config/tutti_cookies.json"):
    log_step("[WORKFLOW] Парсинг объявлений")
    session = TuttiSession(cookies_path=cookies_path, headless=True)
    driver = session.driver

    try:
        results = parse_all_pages(driver, max_pages=max_pages)
        os.makedirs("data", exist_ok=True)
        with open("data/parsed_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        log_step(f"[WORKFLOW] Парсинг завершён. Сохранено: {len(results)} записей.")
    except Exception as e:
        log_step(f"[WORKFLOW] Ошибка на этапе парсинга: {e}")
    finally:
        session.close()


async def run_workflow(dry_run=True):
    log_step("[WORKFLOW] Запуск полного пайплайна...")

    # 1. Tutti Parser
    run_parser()

    # 2. Email Checker
    log_step("[WORKFLOW] Генерация и валидация email-адресов...")
    try:
        await run_async_email_check()
        log_step("[WORKFLOW] Проверка e-mail адресов завершена.")
    except Exception as e:
        log_step(f"[WORKFLOW] Ошибка при проверке e-mail: {e}")

    # 3. SMTP Sender
    log_step("[WORKFLOW] Отправка писем...")
    try:
        await send_emails_async(dry_run=dry_run)
        log_step("[WORKFLOW] Рассылка завершена.")
    except Exception as e:
        log_step(f"[WORKFLOW] Ошибка при отправке писем: {e}")
