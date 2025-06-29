from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json
import time
import os


class TuttiSession:
    def __init__(self, cookies_path="tutti_cookies.json", headless=False, proxy=None):
        self.cookies_path = cookies_path
        self.headless = headless
        self.proxy = proxy
        self.driver = self._init_driver()

    def _init_driver(self):
        options = Options()

        if self.headless:
            options.add_argument("--headless")

        options.add_argument("--window-size=1200,800")
        options.add_argument("--disable-blink-features=AutomationControlled")

        if self.proxy:
            options.add_argument(f'--proxy-server=http://{self.proxy}')

        driver_path = "/usr/local/bin/chromedriver"
        if os.name == "nt":  # Windows
            driver_path = r"C:\katya\chromedriver-win64\chromedriver.exe"

        service = Service(driver_path)
        return webdriver.Chrome(service=service, options=options)

    def load_site_and_set_cookies(self, url="https://www.tutti.ch"):
        self.driver.get(url)
        time.sleep(5)

        # Загружаем cookies
        try:
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            for cookie in cookies:
                if 'sameSite' in cookie:
                    del cookie['sameSite']
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Ошибка при добавлении cookie {cookie.get('name')}: {e}")
        except FileNotFoundError:
            print("❌ Cookie файл не найден.")

        # Перезагрузка страницы
        self.driver.get(url)
        time.sleep(60)

        # 💾 Сохраняем cookies после успешного входа
        try:
            with open(self.cookies_path, "w", encoding="utf-8") as f:
                json.dump(self.driver.get_cookies(), f, indent=4, ensure_ascii=False)
            print("✅ Cookies успешно сохранены!")
        except Exception as e:
            print(f"❌ Ошибка при сохранении cookies: {e}")

    def show_session_info(self):
        print("✅ Заголовок страницы:", self.driver.title)
        print("✅ Текущий URL:", self.driver.current_url)
        print("✅ Cookies:")
        for c in self.driver.get_cookies():
            print(f"{c['name']} = {c['value']}")

    def close(self):
        self.driver.quit()
