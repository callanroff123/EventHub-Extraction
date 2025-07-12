###########################
### Gets events from: #####
### *  Corner Hotel #######
###########################


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
venues = ["Espy Basement"]
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_espy(dates):
    f'''
        * Date parser specifically for ingesting {venues} event dates.
        * Unlike with ticketek, artists with multiple events on different days in {venues} are posted as separate events.
        * This removes the need for multiple date edge-case handling.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from {venues}.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string).   
    '''
    parsed_dates = []
    logger.info(f"Beginning date parsing for {venues} events.")
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
    logger.info(f"Completed date parsing for {venues} events.")
    return(parsed_dates)



def get_events_espy():
    f'''
        Gets events from {venues} Website.
        OUTPUT:
            - Dataframe object containing preprocessed Corner Hotel events.
    '''
    logger.info(f"{venues} started.")
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
            i = 1
            driver.get(f"https://hotelesplanade.com.au/gig-guide/")
            while i < 3:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "hit"))
                    )
                    time.sleep(1)
                    soup = BeautifulSoup(
                        driver.page_source, "html"
                    )
                    postings = soup.find_all("article", {"class": "hit"})
                    postings = [p for p in postings if "BASEMENT" in p.find("div", {"class": "c-gig-card-tag"}).text.strip().upper()]
                    df = pd.DataFrame({
                        "Title": [""],
                        "Date": [""],
                        "Venue": [""],
                        "Link": [""],
                        "Image": [""]
                    })
                    for post in postings:
                        title = post.find("div", {"class": "c-gig-card-title"}).text.strip()
                        date = post.find("div", {"class": "c-gig-card-date"}).text.strip()
                        ven = venue
                        link = post.find("a").get("href")
                        if link[0] == "/":
                            link = "https://theprince.com.au/prince-bandroom/gig-guide" + link
                        image = post.find("div", {"class": "c-gig-card-image"}).get("style").split("'")[1]
                        df = pd.concat(
                            [df, pd.DataFrame({
                                "Title": title,
                                "Date": date,
                                "Venue": ven,
                                "Link": link,
                                "Image": image
                            }, index = [0])], axis = 0
                        ).reset_index(drop = True)
                        if len(df[df["Title"] != ""]) == 0:
                            logger.error(f"Failure to extract events from '{venue}'.")
                    df_final = pd.concat([df_final, df], axis = 0).reset_index(drop = True)
                    next_button = driver.find_element(
                        By.CSS_SELECTOR,
                        'a[aria-label="Next"]'
                    )
                    next_button.click()
                    i = i + 1
                except:
                    logger.error(f"Failure to extract events from '{venue}', page {i}.")
                    break
        df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
        driver.close()
        df_final["Date"] = dateparser_espy(df_final["Date"])
        df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
        df_final["Date"] = [date + relativedelta(years = 1) if pd.notnull(date) and date < pd.to_datetime(datetime.now().date()) else date for date in df_final["Date"]]
        logger.info(f"{venues} Completed.")
    except Exception as e:
        logger.error(f"{venues} Failed - {e}")
    return(df_final)