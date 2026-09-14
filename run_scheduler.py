import schedule
import time
from pipeline import run_pipeline

def job():
    print("\n===== Time to run pipeline =====")
    run_pipeline()


schedule.every(1).minutes.do(job)

print("Scheduler started, waiting to run...")
print("Ctrl+C to stop")

while True:
    schedule.run_pending()
    time.sleep(1)