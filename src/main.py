# 1. Import modules
import os
import sys
ROOT_PATH = "/".join([i for i in os.path.dirname(os.path.abspath(__file__)).split("/")[:-1]])
sys.path.append(ROOT_PATH)
os.environ["PYTHONPATH"] = ROOT_PATH
from src.post_extraction_tasks.clean_and_export import export_events
from src.post_extraction_tasks.send_email import run_send_email
from src.utlilties.azure_blob_connection import upload_to_azure_blob_storage
from src.config import OUTPUT_PATH
from src.utlilties.log_handler import setup_logging
from dotenv import load_dotenv
from datetime import datetime


# 2. Extract enviormment variables for Azure connection
load_dotenv()
CONNECTION_STRING = os.environ.get("MS_BLOB_CONNECTION_STRING")
CONTAINER_NAME = os.environ.get("MS_BLOB_CONTAINER_NAME")
FILE_NAME = "music_events_" + str(datetime.now().date()).replace("-", "") + ".csv"
LOCAL_FILE_LOCATION = str(OUTPUT_PATH) + "/music_events.csv"
logger = setup_logging(logger_name = "scraping_logger")


# 3. Execute end-to-end app pipeline
if __name__ == "__main__":
    try:
        export_events()
        logger.info(f"Uploading '{FILE_NAME}' to Azure container '{CONTAINER_NAME}' ({os.path.getsize(LOCAL_FILE_LOCATION)} bytes).")
        upload_to_azure_blob_storage(
            connection_string = CONNECTION_STRING,
            container_name = CONTAINER_NAME,
            file_name = FILE_NAME,
            local_file_path = LOCAL_FILE_LOCATION
        )
        logger.info(f"Upload to Azure container '{CONTAINER_NAME}' successful. Sending confirmation email.")
        for file in ["music_events.csv", "missing_venues.csv"]:
            run_send_email(file_name = file)
        logger.info("Successfully sent confirmation")
        logger.info("Program successfully run!")
    except Exception as e:
        logger.critical(f"Error in scraping pipeline: {e}") 