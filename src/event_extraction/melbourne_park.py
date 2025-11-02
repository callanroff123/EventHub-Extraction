##############################
### Gets events from: ########
### *  Margert Court Arena ###
### * Rod Laver Arena ########
### * John Cain Arena ########
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
venues = ["Rod Laver Arena", "Margaret Court Arena", "John Cain Arena"]
logger = setup_logging(logger_name = "scraping_logger")
MONTHS = [
    "JANUARY",
    "FEBRUARY",
    "MARCH",
    "APRIL",
    "MAY",
    "JUNE",
    "JULY",
    "AUGUST",
    "SEPTEMBER",
    "OCTOTBER",
    "NOVEMBER",
    "DECEMBER"
]


def dateparser_melbourne_park(dates):
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
    logger.info("Beginning date parsing for MELBOURNE PARK events.")
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
    logger.info("Completed date parsing for MELBOURNE PARK events.")
    return(parsed_dates)



def get_events_melbourne_park():
    '''
        Gets events from Melbourne Park Website.
        OUTPUT:
            - Dataframe object containing preprocessed Melbourne Park events.
    '''
    logger.info("MELBOURNE PARK started.")
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
        for page in range(1, 3):
            for venue in venues:
                logger.info(f"Extracting Events from '{venue}', page {page}.")
                try:
                    if venue == "Rod Laver Arena":
                        page_link = f"https://rodlaverarena.com.au/events/?sf_paged={page}"
                    elif venue == "Margaret Court Arena":
                        page_link = f"https://margaretcourtarena.com.au/events/?sf_paged={page}"
                    elif venue == "John Cain Arena":
                        page_link = f"https://johncainarena.com.au/events/?sf_paged={page}"
                    else:
                        pass #break
                    driver.get(page_link)
                    time.sleep(1)
                    soup = BeautifulSoup(
                        driver.page_source, features = "lxml"
                    )
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "footer"))
                    )
                    footer = driver.find_element(By.TAG_NAME, "footer")
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'end'});", footer)
                    time.sleep(1)
                    postings = soup.find("div", {"id": "eventListing"}).find_all("div", {"class": "card"})
                    df = pd.DataFrame({
                        "Title": [""],
                        "Date": [""],
                        "Venue": [""],
                        "Link": [""],
                        "Image": [""]
                    })
                    for post in postings:
                        try:
                            if len([p for p in post.find_all("p") if "CONCERT" in p.text.upper()]) > 0:
                                title = post.find("h4", {"class": "card-title"}).text.strip().replace("\n", "").replace("\t", "")[:-1]
                                date = [p for p in post.find_all("p") if any(word in p.text.strip().upper() for word in MONTHS) and any(str(i) in p.text.strip().upper() for i in range(1, 32))][0].text.strip()
                                ven = venue
                                link = post.find("a", {"class": "ticketek-buy-link"}).get("href")
                                if link[0] == "/":
                                    link = page_link.split("events/")[0] + link
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
                        except:
                            pass
                    df_final = pd.concat([df_final, df], axis = 0).reset_index(drop = True)
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Failure to extract events from '{venue}', page {page}. - {e}")
        df_final = df_final[df_final["Title"] != ""].reset_index(drop=True)
        driver.close()
        df_final["Date"] = dateparser_melbourne_park(df_final["Date"])
        rows_to_add = []
        rows_to_drop = []
        for i in range(len(df_final)):
            if isinstance(df_final["Date"][i], list):
                logger.info("Expanding events with multiple dates.")
                for j in [0, -1]:
                    rows_to_add.append([
                        df_final["Title"][i],
                        df_final["Date"][i][j],
                        df_final["Venue"][i],
                        df_final["Link"][i],
                        df_final["Image"][i]
                    ])
                rows_to_drop.append(i)
        for row in rows_to_add:
            df_final.loc[len(df_final)] = row
        df_final = df_final.drop(index = rows_to_drop)
        df_final = df_final.sort_values(by = "Date").reset_index(drop = True)
        df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
        df_final["Date"] = [date + relativedelta(years = 1) if pd.notnull(date) and date < pd.to_datetime(datetime.now().date()) else date for date in df_final["Date"]]
        logger.info(f"MELBOURNE PARK Completed ({len(df_final)} rows).")
    except:
        logger.error(f"MELBOURNE PARK Failed - {e}")
    return(df_final)