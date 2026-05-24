
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from processing.data_processor import DataProcessor

load_dotenv()

def job():
    try:
        processor = DataProcessor()
        processor.run()
    except Exception as e:
        print(f"Blad podczas aktualizacji: {e}")

if __name__ == "__main__":
    job()

    # potem co 24h
    interval = int(os.environ.get("INGESTION_INTERVAL_HOURS", 24))
    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", hours=interval)
    scheduler.start()
