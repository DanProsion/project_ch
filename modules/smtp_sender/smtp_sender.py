import asyncio
import logging
import os
import json
import csv
import pandas as pd
from email.message import EmailMessage
from aiosmtplib import SMTP
from jinja2 import Template
import random
from modules.smtp_sender.account_rotator import choose_account
from modules.smtp_sender.delivery_logger import log_delivery

# Загрузка SMTP аккаунтов из JSON
def load_smtp_accounts(filepath="config/smtp_accounts.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки SMTP аккаунтов: {e}")
        return []

# Загрузка получателей из CSV
def load_recipients(path="data/recipients.csv"):
    recipients = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            recipients.append(row)
    return recipients

# Генерация письма
def render_email_body(template_str, context):
    template = Template(template_str)
    return template.render(context)

def create_email(recipient, sender_account, subject, html_body, attachment_path=None):
    msg = EmailMessage()
    msg["From"] = f"{sender_account['from_name']} <{sender_account['username']}>"
    msg["To"] = recipient["email"]
    msg["Subject"] = subject

    msg.set_content("Это резервная версия письма в текстовом формате.")
    msg.add_alternative(html_body, subtype="html")

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    return msg

# Отправка одного письма
async def send_email(recipient, sender_account, subject, html_template, attachment_path=None, dry_run=False):
    try:
        html_body = render_email_body(html_template, recipient)
        message = create_email(recipient, sender_account, subject, html_body, attachment_path)

        if dry_run:
            logging.info(f"[ТЕСТ] Письмо бы отправилось на {recipient['email']} через {sender_account['username']}")
            log_delivery(recipient["email"], sender_account["username"], "dry_run")
            return True, None

        smtp = SMTP(
            hostname=sender_account["host"],
            port=sender_account["port"],
            timeout=20,
            start_tls=True
        )

        await smtp.connect()
        await smtp.login(sender_account["username"], sender_account["password"])
        await smtp.send_message(message)
        await smtp.quit()

        logging.info(f"Письмо отправлено на {recipient['email']} через {sender_account['username']}")
        log_delivery(recipient["email"], sender_account["username"], "success")
        return True, None

    except Exception as e:
        err_msg = str(e).lower()
        log_delivery(recipient["email"], sender_account["username"], "error", error_message=err_msg)

        auth_errors = ["535", "530", "authentication", "login failed", "403", "421", "454"]

        if any(code in err_msg for code in auth_errors):
            logging.error(f"Ошибка авторизации для {sender_account['username']}: {e}")
            return False, sender_account

        logging.error(f"Не удалось отправить письмо на {recipient['email']} через {sender_account['username']}: {e}")
        return False, None

# Главная асинхронная функция
async def send_emails_async(dry_run=False):
    recipients = load_recipients()
    smtp_accounts = load_smtp_accounts()

    if not recipients or not smtp_accounts:
        logging.error("Нет получателей или SMTP аккаунтов. Остановка.")
        return

    html_template = """
    <html>
        <body>
            <p>Привет, {{ name }}!</p>
            <p>Это тестовое письмо от нашего почтового робота.</p>
        </body>
    </html>
    """
    subject = "Тестовая рассылка"
    attachment = None

    # Счётчик писем по каждому аккаунту
    account_usage = {acc["username"]: 0 for acc in smtp_accounts}

    for recipient in recipients:
        sender = choose_account(smtp_accounts, usage_limits=account_usage)

        if not sender:
            logging.warning("Нет доступных SMTP аккаунтов для отправки.")
            break

        username = sender["username"]
        limit = sender.get("limit_per_session", 10)
        delay = sender.get("delay_seconds", 5)

        if account_usage[username] >= limit:
            logging.info(f"Аккаунт {username} достиг лимита {limit}. Пропускаем.")
            continue

        account_usage[username] += 1
        success, bad_account = await send_email(recipient, sender, subject, html_template, attachment, dry_run)

        if bad_account:
            logging.warning(f"SMTP-аккаунт {bad_account['username']} помечен как невалидный и удалён.")
            archive_burned_account(bad_account)
            smtp_accounts = [acc for acc in smtp_accounts if acc["username"] != bad_account["username"]]
            if not smtp_accounts:
                logging.error("Все SMTP-аккаунты сгорели. Остановка.")
                break
            account_usage.pop(bad_account["username"], None)
            continue

        await asyncio.sleep(delay)


# Удаление сгоревших SMTP-аккаунтов
def archive_burned_account(account, path="logs/burned_accounts.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, "r", encoding="utf-8") as f:
            archive = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        archive = []

    archive.append(account)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(archive, f, indent=2, ensure_ascii=False)