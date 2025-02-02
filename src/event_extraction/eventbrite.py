#########################
### Gets events from: ###
### * The Retreat #######
### * Sub Club ##########
#########################


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
venues_eventbrite = [
    i for i in venues if i in [
        "The Retreat Hotel",
        "Sub Club"
    ]
]
DAYS_OF_WEEK = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6
}
logger = setup_logging(logger_name = "scraping_logger")


def dateparser_eventbrite(dates):
    f'''
        * Eventbrite is a tricky one!
        * If the event is within the week, it won't indicate it is such, and instead present as the date "Tomorrow at ..." or "Friday at ..." for example.
        * We make use of the DAYS_OF_WEEK dict to handle these cases.
        * Otherwise the dates are presented nicely and no pre-parsing processing is required.
        * INPUT:
            - dates (list[str]): the raw dates extracted from scraping events from Eventbrite.
        * OUTPUT:
            - parsed_dates (list[str]): parsed dates in YYYY-mm-dd format (though still remains a string). 
    '''
    parsed_dates = []
    logger.info("Beginning date parsing for Eventbrite events.")
    for date in dates:
        try:
            if "+" in date:
                date = date.split("+")[0]
            if "TOMORROW" in date.upper():
                parsed_date = datetime.now().date() + timedelta(days = 1)
            elif "TODAY" in date.upper():
                parsed_date = datetime.now().date()
            else:
                day_of_week_scan = [i for i in DAYS_OF_WEEK.keys() if i in date.upper()]
                if len(day_of_week_scan) > 0:
                    day_num = DAYS_OF_WEEK[day_of_week_scan[0]]
                    current_day_num = datetime.now().weekday()
                    delta = (day_num - current_day_num) % 7
                    parsed_date = (datetime.now().date() + timedelta(days = delta)).strftime(format = "%Y-%m-%d")
                else:
                    parsed_date = parse(date).strftime(format = "%Y-%m-%d")
        except Exception as e:
            logger.warning(f"{e} - Cannot parse '{date}' with dateutils. Using AI instead.")
            try:
                parsed_date = openai_dateparser(date)
            except Exception as ee:
                logger.warning(f"{ee} - Failure to parse '{date}' using AI. Setting as NaT.")
                parsed_date = pd.NaT
        parsed_dates.append(parsed_date)
    logger.info("Completed date parsing for Eventbrite events.")
    return(parsed_dates)


def get_events_eventbrite():
    '''
        Gets events from Eventbrite.
        OUTPUT:
            - Dataframe object containing preprocessed Eventbrite events.
    '''
    logger.info("EVENTBRITE started.")
    df_final = pd.DataFrame({
        "Title": [""],
        "Date": [""],
        "Venue": [""],
        "Venue1": [""],
        "Link": [""]
    })
    for venue in venues_eventbrite:
        try:
            logger.info(f"Extracting Events from '{venue}'")
            driver = webdriver.Chrome(options = options)
            if venue == "Sub Club":
                driver.get(f"https://www.eventbrite.com.au/o/charades-x-sub-club-48348435443")
            elif venue == "The Retreat Hotel":
                driver.get(f"https://www.eventbrite.com.au/o/the-retreat-hotel-28439300263")
            time.sleep(1)
            soup = BeautifulSoup(
                driver.page_source, "html"
            )
            show_more = soup.find(
                "div", {"class": "organizer-profile__show-more"}
            )
            if show_more:
                try:
                    show_more_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[2]/div/div/div/div[1]/div/main/section/div[2]/div[3]/section/div/div[1]/div/div[3]/button"))
                    )
                    show_more_button.click()
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                except:
                    print("Failure to click 'show more' button")
            upcoming = soup.find(
                "div", {"data-testid": "organizer-profile__future-events"}
            )
            postings = upcoming.find_all(
                "div", {"class": "event-card"})
            df = pd.DataFrame({
                "Title": [""],
                "Date": [""],
                "Venue": [""],
                "Venue1": [""],
                "Link": [""]
            })
            for post in postings:
                title = post.find(
                    "h3").text.strip()
                ven = venue.split(",", 1)[0]
                ven1 = post.find_all(
                    "p")[1].text.strip()
                date = post.find_all(
                    "p")[0].text.strip()
                link = post.find(
                    "a", {"class": "event-card-link"}).get("href")
                df = pd.concat(
                    [df, pd.DataFrame({
                        "Title": title,
                        "Date": date,
                        "Venue": ven,
                        "Venue1": ven1,
                        "Link": link
                    }, index = [0])], axis = 0
                ).reset_index(drop = True)
                df = df.reset_index(drop=True)
                if len(df[df["Title"] != ""]) == 0:
                    logger.error(f"Failure to extract events from '{venue}'.")
            df_final = pd.concat([df_final, df], axis = 0).reset_index(drop = True)
            time.sleep(1)
            driver.close()
        except:
            logger.error(f"Failure to extract events from '{venue}'.")
    df_final = df_final[df_final["Title"] != ""].drop_duplicates(
        subset = ["Title"]
    ).reset_index(drop=True)
    df_final["Date"] = dateparser_eventbrite(df_final["Date"])
    df_final["Date"] = pd.to_datetime(df_final["Date"].str.strip(), errors = "coerce")
    logger.info("HUMANITIX Completed.")
    return(df_final)
