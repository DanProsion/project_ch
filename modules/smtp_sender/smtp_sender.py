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

    msg.set_content("This is a fallback plain-text message.")
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
            logging.info(f"[DRY RUN] Would send to {recipient['email']} using {sender_account['username']}")
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

        logging.info(f"Sent to {recipient['email']} using {sender_account['username']}")
        return True, None

    except Exception as e:
        err_msg = str(e).lower()

        # Проверка на ошибки SMTP-авторизации/блокировки
        auth_errors = ["535", "530", "authentication", "login failed", "403", "421", "454"]

        if any(code in err_msg for code in auth_errors):
            logging.error(f"Auth/Access Error with {sender_account['username']}: {e}")
            return False, sender_account

        # Ошибка получателя (оставим аккаунт активным)
        logging.error(f"Failed to send to {recipient['email']} using {sender_account['username']}: {e}")
        return False, None

# Главная асинхронная функция
async def send_emails_async(dry_run=False, delay_range=(2, 5), max_emails_per_account=10):
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

    # учёт использованных аккаунтов
    account_usage = {acc["username"]: 0 for acc in smtp_accounts}

    for recipient in recipients:
        sender = None

        for acc in smtp_accounts:
            if account_usage[acc["username"]] < max_emails_per_account:
                sender = acc
                account_usage[acc["username"]] += 1
                break

        if not sender:
            logging.warning("Все SMTP-аккаунты достигли лимита отправок.")
            break

        success, bad_account = await send_email(recipient, sender, subject, html_template, attachment, dry_run)

        if bad_account:
            logging.warning(f"SMTP account {bad_account['username']} marked as invalid and removed.")
            archive_burned_account(bad_account)  # добавляем в архив
            smtp_accounts = [acc for acc in smtp_accounts if acc["username"] != bad_account["username"]]
            if not smtp_accounts:
                logging.error("Все SMTP аккаунты сгорели. Остановка.")
                break

        await asyncio.sleep(random.uniform(*delay_range))


#Удаление сгоревших SMTP-аккаунтов
def archive_burned_account(account, path="logs/burned_accounts.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Загружаем существующий архив (если он есть)
    try:
        with open(path, "r", encoding="utf-8") as f:
            archive = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        archive = []

    # Добавляем новый аккаунт
    archive.append(account)

    # Перезаписываем файл
    with open(path, "w", encoding="utf-8") as f:
        json.dump(archive, f, indent=2, ensure_ascii=False)