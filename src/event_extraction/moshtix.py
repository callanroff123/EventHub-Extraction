############################
### Gets events from: ######
### * Brunswick Ballroom ###
### * The Toff in Town #####
### * Northcote Theatre ####
### * The Night Cat ########
### * Howler ###############
### * Kindred Bandroom #####
### * 170 Russell ##########
############################


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
venues_moshtix = [
    i for i in venues if i in [
        "Brunswick Ballroom",
        "The Toff in Town",
        "Northcote Theatre",
        "The Night Cat",
        "Howler",
        "Kindred Bandroom",
        "170 Russell",
        "Laundry Bar",
        "Revolver Upstairs"
    ]
]
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_moshtix(dates):
    f'''
        * Similar to Oztix in that it doesn;t seem we require multi-date handling.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from Moshtix.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string).   
    '''
    parsed_dates = []
    logger.info("Beginning date parsing for Moshtix events.")
    for date in dates:
        try:
            parsed_date = parse(date).strftime(format = "%Y-%m-%d")
        except Exception as e:
            logger.warning(f"{e} - Cannot parse '{date}' with dateutils. Using AI instead.")
            try:
                parsed_date = openai_dateparser(date)
            except Exception as ee:
                logger.warning(f"{ee} - Failure to parse '{date}' using AI. Setting as NaT.")
                parsed_date = pd.NaT
        parsed_dates.append(parsed_date)
    logger.info("Completed date parsing for Ticketek events.")
    return(parsed_dates)


def get_events_moshtix():
    '''
        Gets events from Moshtix.
        OUTPUT:
            - Dataframe object containing preprocessed Moshtix events.
    '''
    logger.info("MOSHTIX started.")
    driver = webdriver.Chrome(options = options)
    driver.get("https://www.moshtix.com.au/v2/")
    time.sleep(1)
    df_final = pd.DataFrame({
        "Title": [""],
        "Date": [""],
        "Venue": [""],
        "Link": [""],
        "Image": [""]
    })
    for venue in venues_moshtix:
        logger.info(f"Extracting Events from '{venue}'")
        try:
            search = venue
            search_box = driver.find_element(
                By.XPATH,
                '//*[@id="query"]'
            )
            search_box.send_keys(search)
            search_box.send_keys(Keys.ENTER)
            time.sleep(1)
            soup = BeautifulSoup(
                driver.page_source, "html"
            )
            postings = soup.find_all("div", {"class": "searchresult clearfix"})
            df = pd.DataFrame({
                "Title": [""],
                "Date": [""],
                "Venue": [""],
                "Link": [""],
                "Image": [""]
            })
            for post in postings:
                title = post.find(
                    "h2", {"class": "main-event-header"}).text.strip()
                date = post.find(
                    "h2", {"class": "main-artist-event-header"}).text.strip()
                date = date.split(",", 1)[0]
                ven = venue.split(",", 1)[0]
                link = post.find(
                    "h2", {"class": "main-event-header"}).find("a").get("href")
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
            driver.find_element(
                By.XPATH,
                '//*[@id="header"]/nav/ul/li[1]/a'
            ).click()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Failure to extract events from '{venue}' - {e}.")
    driver.close()
    df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
    if len(df_final) > 0:
        df_final["Date"] = dateparser_moshtix(df_final["Date"])
        df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
        logger.info("MOSHTIX Completed.")
    return(df_final)