import json
import csv
import os
from typing import List, Dict


class SMTPAccountManager:
    def __init__(self, path="config/smtp_accounts.json"):
        self.path = path
        self.accounts = self.load_accounts()

    def load_accounts(self) -> List[Dict]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_accounts(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.accounts, f, indent=2, ensure_ascii=False)

    def list_accounts(self, active_only=False):
        for acc in self.accounts:
            if not active_only or acc.get("active", True):
                status = "ACTIVE" if acc.get("active", True) else "INACTIVE"
                print(f"{acc['username']} ({acc['host']}:{acc['port']}) — {status}")

    def add_accounts_from_json(self, new_accounts: List[Dict]):
        for new_acc in new_accounts:
            new_acc.setdefault("active", True)
            if not any(acc["username"] == new_acc["username"] for acc in self.accounts):
                self.accounts.append(new_acc)
        self.save_accounts()

    def add_accounts_from_csv(self, csv_path: str):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            new_accounts = []
            for row in reader:
                account = {
                    "username": row["username"],
                    "password": row["password"],
                    "host": row["host"],
                    "port": int(row["port"]),
                    "from_name": row.get("from_name", ""),
                    "active": row.get("active", "true").lower() == "true"
                }
                new_accounts.append(account)
            self.add_accounts_from_json(new_accounts)

    def deactivate_account(self, username: str):
        for acc in self.accounts:
            if acc["username"] == username:
                acc["active"] = False
                self.save_accounts()
                print(f"Аккаунт {username} деактивирован.")
                return
        print(f"Аккаунт {username} не найден.")

    def update_account(self, username: str, updates: Dict):
        for acc in self.accounts:
            if acc["username"] == username:
                acc.update(updates)
                self.save_accounts()
                print(f"Аккаунт {username} обновлён.")
                return
        print(f"Аккаунт {username} не найден.")
