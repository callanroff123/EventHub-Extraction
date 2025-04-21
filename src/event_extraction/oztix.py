################################
### Gets events from: ##########
### *  Northcote Social Club ###
### * The Workers Club #########
### * Corner Hotel #############
### * Croxton Bandroom #########
### * Max Watt's Melbourne #####
### * Gasometer ################
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
venues_oztix = [
    i for i in venues if i in [
        "Northcote Social Club",
        "The Workers Club",
        "Corner Hotel",
        "Croxton Bandroom",
        "Max Watt's Melbourne",
        "Gasometer (Upstairs)",
        "Gasometer Downstairs",
        "Prince Bandroom",
        "Epsy Basement",
        "The Tote - Upstairs",
        "The Tote - Bandroom",
        "The Tote - Front Bar",
        "Bar Open",
        "The Old Bar",
        "Bergy Bandroom",
        "The Evelyn Hotel",
        "John Curtin Hotel",
        "The Last Chance"
    ]
]
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_oztix(dates):
    f'''
        * Date parser specifically for ingesting oztix event dates.
        * Unlike with ticketek, artists with multiple events on different days in Oztix are posted as separate events.
        * This removes the need for multiple date edge-case handling.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from Oztix.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string).   
    '''
    parsed_dates = []
    logger.info("Beginning date parsing for Oztix events.")
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
    logger.info("Completed date parsing for Ticketek events.")
    return(parsed_dates)



def get_events_oztix():
    '''
        Gets events from Oztix.
        OUTPUT:
            - Dataframe object containing preprocessed Oztix events.
    '''
    logger.info("OZTIX started.")
    driver = webdriver.Chrome(options = options)
    driver.get("https://www.oztix.com.au/")
    time.sleep(1)
    df_final = pd.DataFrame({
        "Title": [""],
        "Date": [""],
        "Venue": [""],
        "Venue1": [""],
        "Link": [""],
        "Image": [""]
    })
    for venue in venues_oztix:
        logger.info(f"Extracting Events from '{venue}'")
        try:
            search = venue
            time.sleep(1)
            search_box = driver.find_element(
                By.XPATH,
                '/html/body/div[1]/div/header/div[3]/div/form/label/input'
            )
            search_box.send_keys(search)
            search_box.send_keys(Keys.ENTER)
            time.sleep(1)
            soup = BeautifulSoup(
                driver.page_source, "html"
            )
            postings = soup.find_all("li", {"tabindex": "-1"})
            df = pd.DataFrame({
                "Title": [""],
                "Date": [""],
                "Venue": [""],
                "Venue1": [""],
                "Link": [""],
                "Image": [""]
            })
            for post in postings:
                title = post.find(
                    "h3", {"class": "event-details__name"}).text.strip()
                date = post.find("div", {"class": "event-when"}).text.strip()
                ven = venue.split(",", 1)[0]
                ven1 = post.find("p", {"class": "detail"}).text.strip()
                link = post.find(
                    "a", {"class": "search-event_container"}).get("href")
                image = post.find("img").get("src")
                df = pd.concat(
                    [df, pd.DataFrame({
                        "Title": title,
                        "Date": date,
                        "Venue": ven,
                        "Venue1": ven1,
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
                '//*[@id="app"]/div/header/div[1]/a'
            ).click()
            time.sleep(1)
        except:
            logger.error(f"Failure to extract events from '{venue}'.")
    df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
    df_final["correct_venue_flag"] = np.zeros(df_final.shape[0])
    for i in range(df_final.shape[0]):
        if df_final["Venue"][i] in df_final["Venue1"][i]:
            df_final["correct_venue_flag"][i] = 1
        else:
            logger.info(f"Dropping events from {df_final['Venue'][i]}.")
    driver.close()
    df_final = df_final[df_final["correct_venue_flag"] == 1][[
        "Title",
        "Date",
        "Venue",
        "Link",
        "Image"
    ]].reset_index(drop=True)
    df_final["Date"] = dateparser_oztix(df_final["Date"])
    df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
    logger.info("OZTIX Completed.")
    return(df_final)