from modules.parser import tutti_scraper

if __name__ == "__main__":
    driver = tutti_scraper.create_driver()
    data = tutti_scraper.parse_all_pages(driver, max_pages=3)
    
    with open("data/tutti_ads.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Собрано объявлений: {len(data)}")
    driver.quit()
