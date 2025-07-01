import pandas as pd
import dns.resolver
import asyncio
import random
from aiosmtplib import SMTP
from aiosmtplib.errors import SMTPRecipientsRefused, SMTPException


def get_mx_records(domain):
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return [str(r.exchange).rstrip('.') for r in answers]
    except Exception:
        return None


async def check_email_smtp_async(email, mx_records, attempt=1, max_attempts=3):
    from_address = "info@example.com"

    for mx in mx_records:
        server = SMTP(hostname=mx, port=25, timeout=20)
        try:
            await asyncio.sleep(random.uniform(1.5, 3.5))
            await server.connect()

            if "starttls" in server.esmtp_extensions:
                await server.starttls()

            await server.helo()
            await server.mail(from_address)
            code, message = await server.rcpt(email)

            if code in (250, 251):
                return {"email": email, "status": "valid"}
            elif code == 550:
                return {"email": email, "status": "invalid"}
            elif code == 451 and attempt < max_attempts:
                await asyncio.sleep(30)
                return await check_email_smtp_async(email, mx_records, attempt + 1, max_attempts)
            else:
                return {"email": email, "status": "unknown"}

        except SMTPRecipientsRefused as e:
            for recipient, (code, message) in e.recipients.items():
                if code == 550:
                    return {"email": email, "status": "invalid"}
            return {"email": email, "status": "unknown"}

        except SMTPException as e:
            code = getattr(e, "code", None)
            if code == 550:
                return {"email": email, "status": "invalid"}
            return {"email": email, "status": "unknown"}

        except Exception:
            return {"email": email, "status": "unknown"}

        finally:
            try:
                await server.quit()
            except Exception:
                pass


async def run_async_email_check():
    df = pd.read_csv("data/parsed_data.csv")
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)

    logins = df["login"].unique()
    domains = df["domain"].unique()
    emails = [{"email": f"{row['login']}@{row['domain']}", "name": row["name"]} for _, row in df.iterrows()]

    tasks = []
    for entry in emails:
        domain = entry["email"].split("@")[1]
        mx_records = get_mx_records(domain)
        if mx_records:
            tasks.append(check_email_smtp_async(entry["email"], mx_records))
        else:
            tasks.append(asyncio.sleep(0, result={"email": entry["email"], "status": "unknown"}))

    results = await asyncio.gather(*tasks)
    for i in range(len(results)):
        results[i]["name"] = emails[i]["name"]

    # Полный отчёт
    df_out = pd.DataFrame(results)
    df_out.to_csv("data/email_check_report.csv", index=False)

    # Только валидные — для рассылки
    valid_df = df_out[df_out["status"] == "valid"]
    valid_df[["email", "name"]].to_csv("data/recipients.csv", index=False)

    print("Проверка завершена.")
    print("Отчёт сохранён как data/email_check_report.csv")
    print("Валидные адреса сохранены как data/recipients.csv")