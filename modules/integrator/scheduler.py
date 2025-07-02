import schedule
import time
from modules.integrator.workflow import run_workflow

def job():
    print("Запуск по расписанию...")
    run_workflow(dry_run=False)

# Пример расписания:
schedule.every().day.at("05:00").do(job)
# или каждый 12 часов:
# schedule.every(12).hours.do(job)

print("Планировщик запущен...")

while True:
    schedule.run_pending()
    time.sleep(60)
