
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion.logger import get_logger
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from processing.data_processor import DataProcessor

logger = get_logger("scheduler")
load_dotenv()

def job():
    try:
        logger.info("Uruchamianie aktualizacji...")
        processor = DataProcessor()
        processor.run()
        logger.info("Aktualizacja zakonczona pomyslnie.")
    except Exception as e:
        logger.error(f"Blad podczas aktualizacji: {e}")

if __name__ == "__main__":
    job()

    # potem co 24h
    interval = int(os.environ.get("INGESTION_INTERVAL_HOURS", 24))
    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", hours=interval)
    scheduler.start()
