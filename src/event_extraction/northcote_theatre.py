################################
### Gets events from: ##########
### *  Northcote Theatre #######
################################


# 1. Load required libraries.
from pathlib import Path
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import re
import requests
import lxml
import html
import time
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from src.config import venues
from src.utlilties.ai_wrappers import openai_dateparser
from src.utlilties.log_handler import setup_logging


# 2. Specify defaults
year = str(datetime.today().year)
options = Options()
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
venues = ["Northcote Theatre"]
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_northcote_theatre(dates):
    f'''
        * Date parser specifically for ingesting Northcote Theatre event dates.
        * Unlike with ticketek, artists with multiple events on different days in Northcote Theatre are posted as separate events.
        * This removes the need for multiple date edge-case handling.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from Northcote Theatre.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string).   
    '''
    parsed_dates = []
    logger.info("Beginning date parsing for Northcote Theatre events.")
    for date in dates:
        try:
            parsed_date = parse(date).strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning(f"{e} - Cannot parse '{date}' with dateutils. Using AI instead.")
            try:
                parsed_date = openai_dateparser(date)
            except Exception as ee:
                logger.warning(f"{ee} - Failure to parse '{date}' using AI. Setting as NaT.")
                parsed_date = pd.NaT
        parsed_dates.append(parsed_date)
    logger.info("Completed date parsing for Northcote Theatre events.")
    return(parsed_dates)



def get_events_northcote_theatre():
    '''
        Gets events from The Night Cat's Website.
        OUTPUT:
            - Dataframe object containing preprocessed The Night Cat's events.
    '''
    logger.info("NORTHCOTE THEATRE started.")
    driver = webdriver.Chrome(options = options)
    time.sleep(1)
    df_final = pd.DataFrame({
        "Title": [""],
        "Date": [""],
        "Venue": [""],
        "Link": [""],
        "Image": [""]
    })
    try:
        for venue in venues:
            logger.info(f"Extracting Events from '{venue}'")
            try:
                driver.get("https://northcotetheatre.com/new-homepage/")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "event-individual"))
                )
                time.sleep(1)
                soup = BeautifulSoup(
                    driver.page_source, "html"
                )
                postings = soup.find_all("div", {"class": "event-individual"})
                df = pd.DataFrame({
                    "Title": [""],
                    "Date": [""],
                    "Venue": [""],
                    "Link": [""],
                    "Image": [""]
                })
                for post in postings:
                    title = post.find("a", {"class": "event-title"}).text.strip()
                    date = post.find("p", {"class": "event-date"}).text.strip()
                    ven = venue
                    link = post.find("a", {"class": "event-title"}).get("href")
                    if link[0] == "/":
                        link = "https://northcotetheatre.com/new-homepage/" + link
                    image = post.find("img").get("src")
                    df = pd.concat(
                        [df, pd.DataFrame({
                            "Title": title,
                            "Date": date,
                            "Venue": ven,
                            "Link": link,
                            "Image": image
                        }, index = [0])], axis = 0
                    ).reset_index(drop = True)
                    df = df.reset_index(drop=True)
                    if len(df[df["Title"] != ""]) == 0:
                        logger.error(f"Failure to extract events from '{venue}'.")
                df_final = pd.concat([df_final, df], axis = 0).reset_index(drop = True)
                time.sleep(1)
            except:
                logger.error(f"Failure to extract events from '{venue}'.")
        df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
        driver.close()
        df_final["Date"] = dateparser_northcote_theatre(df_final["Date"])
        df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
        df_final["Date"] = [date + relativedelta(years = 1) if pd.notnull(date) and date < pd.to_datetime(datetime.now().date()) else date for date in df_final["Date"]]
        try:
            df_final = df_final[df_final["Date"] <= df_final["Date"].shift(-1)].reset_index(drop = True)
        except:
            pass
        logger.info("NORTHCOTE THEATRE Completed.")
    except Exception as e:
        logger.error(f"NORTHCOTE THEATRE Failed - {e}")
    return(df_final)