################################
### Gets events from: ##########
### *  The Night Cat Fitzroy ###
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
venues = ["Hamer Hall", "Sidney Myer Music Bowl"]
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_art_centre(dates):
    f'''
        * Date parser specifically for ingesting Forum Melbourne's event dates.
        * Unlike with ticketek, artists with multiple events on different days in The Forum's are posted as separate events.
        * This removes the need for multiple date edge-case handling.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from The Forum.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string).   
    '''
    parsed_dates = []
    logger.info("Beginning date parsing for The Forum's events.")
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
    logger.info("Completed date parsing for The Forum's events.")
    return(parsed_dates)



def get_events_arts_center():
    '''
        Gets events from Art Centre's Website.
        OUTPUT:
            - Dataframe object containing preprocessed Art Centre's events.
    '''
    logger.info("ART CENTRE started.")
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
        logger.info(f"Extracting Events from Arts Centre Melbourne.")
        try:
            driver.get("https://www.artscentremelbourne.com.au/whats-on/contemporary-music")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "event-tile"))
            )
            time.sleep(1)
            soup = BeautifulSoup(
                driver.page_source, "html"
            )
            show_more = [i for i in soup.find_all("button") if "LOAD MORE EVENTS" in i.text.strip().upper()]
            while show_more and len(show_more) > 0:
                if show_more[0].text.strip().upper() == "LOAD MORE EVENTS":
                    try:
                        show_more_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, "load-more-events"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                        time.sleep(0.5)
                        show_more_button.click()
                        time.sleep(3)
                        soup = BeautifulSoup(driver.page_source, "html.parser")
                        show_more = [i for i in soup.find_all("button") if "LOAD MORE EVENTS" in i.text.strip().upper()]
                        logger.info("More events produced by clicking 'Load More Events'!")
                    except Exception as e:
                        print(f"Failure to click 'show more' button - {e}")
                        break
            postings = soup.find_all("a", {"class": "show-item"})
            df = pd.DataFrame({
                "Title": [""],
                "Date": [""],
                "Venue": [""],
                "Link": [""],
                "Image": [""]
            })
            for post in postings:
                title = post.find("span", {"class": "title"}).text.strip()
                date = post.find("div", {"class": "calendar"}).text.strip().replace("\n", " ")
                ven = 'N/A'
                link = post.get("href")
                if link[0] == "/":
                    link = "https://forummelbourne.com.au/shows" + link
                image = post.find("div", {"class": "image"}).get("style").split("'")[1]
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
                    logger.error(f"Failure to extract events from Arts Centre Mebourne.")
            df_final = pd.concat([df_final, df], axis = 0).reset_index(drop = True)
            time.sleep(1)
        except:
            logger.error(f"Failure to extract events from Arts Centre Melbourne.")
        df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
        driver.close()
        df_final["Date"] = dateparser_art_centre(df_final["Date"])
        df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
        df_final["Date"] = [date + relativedelta(years = 1) if pd.notnull(date) and date < pd.to_datetime(datetime.now().date()) else date for date in df_final["Date"]]
        try:
            df_final = df_final[df_final["Date"] <= df_final["Date"].shift(-1)].reset_index(drop = True)
        except:
            pass
        logger.info("FORUM MELBOURNE Completed.")
    except Exception as e:
        logger.error(f"FORUM MEBLOURNE Failed - {e}")
    return(df_final)