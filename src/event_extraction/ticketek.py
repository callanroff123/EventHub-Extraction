#########################
### Gets events from: ###
### * The Forum #########
#########################


# 1. Load required libraries.
from pathlib import Path
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import lxml
import html
import time
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import re
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
# Ticketek is a tricky case in that it know's you're browsing in 'headless' mode.
# Line 44 seems to get around this issue
year = str(datetime.today().year)
options = Options()
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
venues_ticketek = [i for i in venues if i in ["Forum Melbourne", "Hamer Hall", "Sidney Myer Music Bowl"]]
searches = ["Forum Melbourne", "Arts Centre"]
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_ticketek(dates):
    f'''
        * Date parser specifically for ingesting ticketek event dates.
        * Ticketek is unique in that some artists events can occur over multiple dates.
        * Ex: 'Tues 30 Jan & Wed 31 Jan' or 'Tues 30 Jan - Wed 31 Jan'.
        * AI is prompted to handle such cases and parse them accordingly.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from ticketek.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string).  
    '''
    parsed_dates = []
    logger.info("Beginning date parsing for Ticketek events.")
    for date in dates:
        if any(char in ["&", "+", "-", " and ", " to "] for char in date):
            logger.warning(f"Multiple dates detected in '{date}'. Using AI parser...")
            try:
                parsed_date = openai_dateparser(date)
            except Exception as e:
                logger.warning(f"{e} - Failure to parse '{date}' using AI. Setting as NaT.")
                parsed_date = pd.NaT
        else:
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


def get_events_ticketek():
    '''
        Gets events from premier.ticketek.com.au (for the Forum only)
        OUTPUT:
            - Dataframe object containing preprocessed ticketek events
    '''
    logger.info("TICKETEK started.")
    driver = webdriver.Chrome(options = options)
    df_out = pd.DataFrame({
        "Title": [""],
        "Date": [""],
        "Venue": [""],
        "Link": [""],
        "Image": [""]
    })
    for venue in searches:
        logger.info(f"Extracting Events from '{venue}'")
        try:
            if venue == "Forum Melbourne":
                base_link = "https://premier.ticketek.com.au/shows/show.aspx?sh=FORUMELB"
            else:
                base_link = "https://premier.ticketek.com.au/shows/show.aspx?sh=ACM"
            driver.get(base_link)
            time.sleep(1)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "show")))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            soup = BeautifulSoup(
                driver.page_source, "html"
            )
            postings = soup.find_all(
                "div", {"class": "show"}
            )
            df = pd.DataFrame({
                "Title": [""],
                "Date": [""],
                "Venue": [""],
                "Link": [""],
                "Image": [""]
            })
            for post in postings:
                text = post.find(
                    "div", {"class": "text-content"}
                )
                title = text.find("h3").text.strip()
                if venue == "Forum Melbourne":
                    ven = venue
                else:
                    ven = text.find_all("p")[0].text.strip()
                date = text.find_all("p")[-2].text.strip()
                link = post.find(
                    "a", {"class": "btn btn-primary"}
                ).get("href")
                if link[0] == "/":
                    link = "https://premier.ticketek.com.au/" + link
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
            df_out = pd.concat([df_out, df], axis = 0)
            time.sleep(1)
        except:
            logger.error(f"Failure to extract events from '{venue}'.")
    df_out = df_out[df_out["Title"] != ""].reset_index(drop=True)
    df_out["correct_venue_flag"] = np.zeros(len(df_out))
    venues_ticketek_alt = [i.lower().replace(" ", "") for i in venues_ticketek]
    for i in range(len(df_out)):
        if df_out["Venue"][i].lower().replace(" ", "") in venues_ticketek_alt:
            df_out["correct_venue_flag"][i] = 1
        else:
            logger.info(f"Dropping events from {df_out['Venue'][i]}.")
    driver.close()
    df_out = df_out[df_out["correct_venue_flag"] == 1].drop_duplicates().reset_index(drop = True)
    df_out = df_out[[
        "Title",
        "Date",
        "Venue",
        "Link",
        "Image"
    ]]
    df_out["Date"] = dateparser_ticketek(df_out["Date"])
    rows_to_add = []
    rows_to_drop = []
    for i in range(len(df_out)):
        if isinstance(df_out["Date"][i], list):
            logger.info("Expanding events with multiple dates.")
            for j in [0, -1]:
                rows_to_add.append([
                    df_out["Title"][i],
                    df_out["Date"][i][j],
                    df_out["Venue"][i],
                    df_out["Link"][i],
                    df_out["Image"][i]
                ])
            rows_to_drop.append(i)
    for row in rows_to_add:
        df_out.loc[len(df_out)] = row
    df_out = df_out.drop(index = rows_to_drop)
    df_out = df_out.sort_values(by = "Date").reset_index(drop = True)
    df_out["Date"] = pd.to_datetime(df_out["Date"].str.strip(), errors = "coerce")
    logger.info("TICKETEK Completed.")
    return(df_out)