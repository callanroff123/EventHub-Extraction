###################################
### Gets events from: #############
### *  Melbourne Recital Centre ###
###################################


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
venues = ["Melbourne Recital Centre"]
logger = setup_logging(logger_name = "scraping_logger")
TITLE_EXCLUSION_KEYWORDS = ["MELBOURNE POLYTECHNIC", "GRADUATION"]
STAGES = ["Elisabeth Murdoch Hall"]


def dateparser_melbourne_recital_centre(dates):
    f'''
        * Date parser specifically for ingesting Melbourne Recital Centre event dates.
        * Unlike with ticketek, artists with multiple events on different days in Melbourne Recital Centre are posted as separate events.
        * This removes the need for multiple date edge-case handling.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from Melbourne Recital Centre.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string).   
    '''
    parsed_dates = []
    logger.info(f"Beginning date parsing for {(', '.join(venues)).upper()} events.")
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
    logger.info(f"Completed date parsing for {(', '.join(venues)).upper()} events.")
    return(parsed_dates)



def get_events_melbourne_recital_centre():
    '''
        Gets events from Melbourne Recital Centre Website.
        OUTPUT:
            - Dataframe object containing preprocessed Melbourne Recital Centre events.
    '''
    logger.info(f"{(', '.join(venues)).upper()} started.")
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
                driver.get("https://www.melbournerecital.com.au/whats-on")
                time.sleep(1)
                soup = BeautifulSoup(
                    driver.page_source, features = "lxml"
                )
                acknowledgement = soup.find("div", {"class": "modal-text"})
                if acknowledgement:
                    try:
                        continue_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//div[@class='button-wrapper']//button[span[text()='Continue']]"))
                        )
                        continue_button.click()
                        time.sleep(2)
                        soup = BeautifulSoup(driver.page_source, "html.parser")
                    except:
                        print("Failure to click 'continue' button")
                show_more = [i for i in soup.find_all("button", {"type": "button"}) if "SHOW MORE" in i.text.strip().upper()]
                while show_more and len(show_more) > 0:
                    if show_more[0].text.strip().upper() == "SHOW MORE":
                        try:
                            show_more_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(text())='Show more']"))
                            )
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                            time.sleep(0.5)
                            show_more_button.click()
                            time.sleep(2)
                            soup = BeautifulSoup(driver.page_source, "html.parser")
                            show_more = [i for i in soup.find_all("button", {"type": "button"}) if "SHOW MORE" in i.text.strip().upper()]
                        except Exception as e:
                            print(f"Failure to click 'show more' button - {e}")
                            break
                posting_groups = soup.find("div", {"class": "items-wrapper"}).find_all("div")
                posting_groups = [group for group in posting_groups if group.find("article")]
                for group in posting_groups:
                    date = group.find("h3").text.strip()
                    postings = group.find_all("article")
                    df = pd.DataFrame({
                        "Title": [""],
                        "Date": [""],
                        "Venue": [""],
                        "Link": [""],
                        "Image": [""]
                    })
                    for post in postings:
                        has_book_now = any(
                            "book now" in btn.text.strip().lower()
                            for btn in post.find_all("a", class_ = "btn")
                        )
                        if has_book_now:
                            title = post.find("h3").text.strip()
                            ven = venue
                            link = [b.get("href") for b in post.find_all("a", class_ = "btn") if "book now" in b.text.strip().lower()][0]
                            if link[0] == "/":
                                link = "https://www.melbournerecital.com.au" + link
                            image = post.find("img").get("src")
                            if (post.find_all("span")[-1].text.strip().upper() in [stage.upper() for stage in STAGES]) and (not any(word in title.upper() for word in TITLE_EXCLUSION_KEYWORDS)):
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
                    df_final = pd.concat([df_final, df], axis = 0)
                    time.sleep(0.1)
            except:
                logger.error(f"Failure to extract events from '{venue}'.")
        df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
        driver.close()
        df_final["Date"] = dateparser_melbourne_recital_centre(df_final["Date"])
        df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
        df_final["Date"] = [date + relativedelta(years = 1) if pd.notnull(date) and date < pd.to_datetime(datetime.now().date()) else date for date in df_final["Date"]]
        logger.info(f"{(', '.join(venues)).upper()} completed ({len(df_final)} rows).")
    except Exception as e:
        logger.error(f"{(', '.join(venues)).upper()} failed - {e}")
    return(df_final)