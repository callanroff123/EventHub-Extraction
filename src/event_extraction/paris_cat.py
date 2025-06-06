##############################
### Gets events from: ########
### *  Paris Cat Jazz Club ###
##############################


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
venues = ["Paris Cat Jazz Club"]
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_paris_cat(dates):
    f'''
        * Date parser specifically for ingesting Paris Cat Jazz Club event dates.
        * Unlike with ticketek, artists with multiple events on different days in Paris Cat Jazz Club are posted as separate events.
        * This removes the need for multiple date edge-case handling.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from Paris Cat Jazz Club.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string).   
    '''
    parsed_dates = []
    logger.info("Beginning date parsing for Paris Cat Jazz Club events.")
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
    logger.info("Completed date parsing for Paris Cat Jazz Club events.")
    return(parsed_dates)



def get_events_paris_cat():
    '''
        Gets events from Paris Cat Jazz Club Website.
        OUTPUT:
            - Dataframe object containing preprocessed Paris Cat Jazz Club events.
    '''
    logger.info("PARIS CAT started.")
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
                driver.get("https://www.pariscat.com.au/")
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "section"))
                )
                time.sleep(1)
                soup = BeautifulSoup(
                    driver.page_source, "html"
                )
                sections = [section for section in soup.find_all("div") if section.has_attr("id")]
                sections = [section for section in sections if "MONTH" in section.get("id").strip().upper()]
                for section in sections:
                    try:
                        postings = section.find_all("div", recursive = False)
                        df = pd.DataFrame({
                            "Title": [""],
                            "Date": [""],
                            "Venue": [""],
                            "Link": [""],
                            "Image": [""]
                        })
                        date = datetime.now().date().strftime("%Y-%m-%d")
                        for post in postings:
                            if post.find("a"):
                                title = post.find("p").text.split("//")[1].strip()
                                date = date
                                ven = venue
                                link = post.find_all("a")[-1].get("href")
                                if link[0] == "/":
                                    link = "https://www.pariscat.com.au" + link
                                image = [i for i in post.find_all("div") if i.has_attr("style")]
                                if len(image) > 0:
                                    image = image[0].get("style").split('("')[1].split('")')[0]
                                else:
                                    image = None
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
                            else:
                                date = post.find("p").text.strip()
                        df_final = pd.concat([df_final, df], axis = 0).reset_index(drop = True)
                        time.sleep(1)
                    except:
                        logger.warning("Could not process section of posts")
                        pass
            except:
                logger.error(f"Failure to extract events from '{venue}'.")
        df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
        driver.close()
        logger.info(f"{len(df_final)} rows for PARIS CAT scrape job.")
        df_final["Date"] = dateparser_paris_cat(df_final["Date"])
        df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
        df_final["Date"] = [date + relativedelta(years = 1) if pd.notnull(date) and date < pd.to_datetime(datetime.now().date()) else date for date in df_final["Date"]]
        try:
            df_final = df_final[df_final["Date"] <= df_final["Date"].shift(-1)].reset_index(drop = True)
        except:
            pass
        logger.info("PARIS CAT Completed.")
    except Exception as e:
        logger.error(f"Failed to scrape PARIS CAT - {e}")
    return(df_final)