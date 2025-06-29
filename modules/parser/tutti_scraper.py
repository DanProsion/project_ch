import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_driver():
    options = uc.ChromeOptions()
    options.add_argument("--user-data-dir=/tmp/tutti_profile")
    driver = uc.Chrome(options=options, headless=False)
    return driver

def load_cookies(driver, cookies_path):
    driver.get("https://www.tutti.ch/de")
    time.sleep(3)
    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for cookie in cookies:
        cookie.pop("sameSite", None)
        driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(5)

def wait_for_ads(driver):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/vi/"]'))
        )
        print("Объявления появились")
    except:
        print("Не дождались объявлений")
        return False
    return True

def extract_ads_links(driver):
    ads = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/de/vi/"]')
    links = list({ad.get_attribute("href") for ad in ads})
    return links

def extract_info(driver, url):
    driver.get(url)
    time.sleep(2)
    try:
        nickname = driver.find_element(By.CSS_SELECTOR, "div[data-testid='ad-detail-user-info']").text.strip().split('\n')[0]
        title = driver.find_element(By.CSS_SELECTOR, "h1").text
        print(f"{nickname} | {title}")
        return {"url": url, "nickname": nickname, "title": title}
    except Exception as e:
        print(f"Ошибка на {url}: {e}")
        return None

def go_to_next_page(driver):
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Weiter']")
        next_btn.click()
        time.sleep(5)
        return True
    except:
        return False

def parse_all_pages(driver, max_pages=3):
    load_cookies(driver, "config/tutti_cookies.json")
    if not wait_for_ads(driver):
        return []

    all_data = []
    page = 1

    while page <= max_pages:
        print(f"📄 Обрабатываем страницу {page}")
        links = extract_ads_links(driver)
        for url in links:
            data = extract_info(driver, url)
            if data:
                all_data.append(data)
        if not go_to_next_page(driver):
            print("Нет кнопки 'следующая страница'")
            break
        page += 1

    return all_data

