#########################################
### Gets events from: ###################
### * Miscellania (2/401 Swanston St) ###
#########################################


# 1. Load required libraries.
from pathlib import Path
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import re
import requests
import lxml
import html
import traceback
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
from src.utlilties.ai_dateparser import openai_dateparser
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
venues_humanitix = [i for i in venues if i in ["Miscellania", "Sub Club"]]
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_humanitix(dates):
    f'''
        * Date parser specifically for ingesting Humanitix event dates.
        * While there may be some events which display multiple dates, it's typically because they go into the previous morning.
        * In this case it makes more sense to just extract the first date.
        * Otherwise, the dateparser functions in the relatively standard manner.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from Humanitix.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string). 
    '''
    parsed_dates = []
    logger.info("Beginning date parsing for Humanitix events.")
    for date in dates:
        if any(char in ["&", "+", "-", " and ", " to "] for char in date):
            date = re.split(r'[&+-]|\s+to\+s|\s+and\s+', date)[0]
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
    logger.info("Completed date parsing for Humanitix events.")
    return(parsed_dates)


def get_events_humanitix():
    '''
        Gets events from Humanitix.
        OUTPUT:
            - Dataframe object containing preprocessed Humanitix events.
    '''
    logger.info("HUMANITIX started.")
    driver = webdriver.Chrome(options = options)
    time.sleep(1)
    df_final = pd.DataFrame({
        "Title": [""],
        "Date": [""],
        "Venue": [""],
        "Link": [""],
        "Image": [""]
    })
    for venue in venues_humanitix:
        logger.info(f"Extracting Events from '{venue}'")
        try:
            if venue == "Miscellania":
                driver.get("https://events.humanitix.com/host/60e557b6a7532e000a4f0c92")
            time.sleep(2)
            soup = BeautifulSoup(
                driver.page_source, "html"
            )
            show_more = soup.find(
                "div", {"class": "loadmore"}
            )
            if show_more:
                try:
                    button = driver.find_element(By.XPATH, "/html/body/div/div[1]/div[2]/main/aside/div[2]/div[2]/aside/div[2]/button[1]")
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                except:
                    logger.warning("Failure to click 'show more' button")
            df = pd.DataFrame({
                "Title": [""],
                "Date": [""],
                "Venue": [""],
                "Link": [""],
                "Image": [""]
            })  
            postings = soup.find_all(
                "a", {"class": "EventCard"}
            )
            for post in postings:
                date = post.find(
                    "div", {"class": "date"}
                ).text.strip()
                date = post.find(
                    "div", {"class": "date"}
                ).text.strip()
                title = post.find(
                    "div", {"class": "title"}
                ).text.strip()
                link = post.get("href")
                image = post.find("img").get("src")
                df = pd.concat(
                    [
                        df, 
                        pd.DataFrame(
                            {
                                "Title": title,
                                "Date": date,
                                "Venue": venue,
                                "Link": link,
                                "Image": image
                            }, 
                            index = [0]
                        )
                    ], 
                    axis = 0
                ).reset_index(drop = True)
                df = df.reset_index(drop=True)
                if len(df[df["Title"] != ""]) == 0:
                    logger.error(f"Failure to extract events from '{venue}'.")
            df_final = pd.concat([df_final, df], axis = 0).reset_index(drop = True)
        except:
            logger.error(f"Failure to extract events from '{venue}'.")
    driver.close()
    df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
    df_final["Date"] = dateparser_humanitix(df_final["Date"])
    df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
    logger.info("MOSHTIX Completed.")
    return(df_final)