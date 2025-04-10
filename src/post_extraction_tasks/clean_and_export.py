##############################################################################################################
### This program extracts music events from some of my favourite venues across Melbourne. ####################
### The aim is to compile the events into an organised output table, which can be filtered easily by date. ###
### This should save time spent browsing across multiple event webpages. #####################################
##############################################################################################################


# 1. Load required libraries.
from pathlib import Path
import numpy as np
import pandas as pd
import re
import requests
import lxml
import html
import time
from uuid import uuid4
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from src.event_extraction.eventbrite import get_events_eventbrite
from src.event_extraction.humanitx import get_events_humanitix
from src.event_extraction.moshtix import get_events_moshtix
from src.event_extraction.oztix import get_events_oztix
from src.event_extraction.ticketek import get_events_ticketek
from src.config import LOGGING_PARAMS, venues, OUTPUT_PATH
from src.utlilties.log_handler import setup_logging
from src.utlilties.ai_wrappers import openai_artist_extraction
from src.utlilties.youtube_data_api import search_artist_video
from src.utlilties.spotify_web_api import get_artist_from_search, get_artist_most_played_track


#2. Specify defaults.
logger = setup_logging("scraping_logger")
EVENT_FROM_DATE = datetime.now().date().strftime(format = "%Y-%m-%d")
EVENT_TO_DATE = (datetime.now().date() + relativedelta(months = 4)).strftime(format = "%Y-%m-%d")


def get_all_events():
    '''
        Concatenates results across various sources, and performs some additional cleaning
    '''
    df_moshtix = get_events_moshtix()
    df_oztix = get_events_oztix()
    df_eventbrite = get_events_eventbrite()
    df_humanitix = get_events_humanitix()
    df_ticketek = get_events_ticketek()
    logger.info("Consolidating events from all ticketing websites.")
    df = pd.concat(
        [
            df for df in [
                df_moshtix, 
                df_oztix, 
                df_eventbrite, 
                df_humanitix, 
                df_ticketek
            ] 
            if df.shape[0] > 0
        ],
        axis = 0
    )
    df_out = df[[
        "Title",
        "Date",
        "Venue",
        "Link",
        "Image"
    ]].sort_values("Date", ascending=True)
    df_out = df_out.drop_duplicates(
        subset = ["Date", "Venue"], 
        keep = "first"
    ).reset_index(drop=True)
    df_out["Image"] = ["https:" + im if im[0:2] == "//" else im for im in df_out["Image"]]
    logger.info("Events successfully consolidated.")
    return(df_out)


# TO DO
# Youtube + Spotify player URL implementations.
# Get the top X youtube videos that CAN be embedded (from a total of Y > X searches)
# Getting an error in some of the spotify tasks: "list index out of range"
# Note youtube embedding is troublesome at the moment so just going with the spotify player embedding for the time being
def embed_players(artist_certainty_threshold = 10):
    df_raw = get_all_events()
    df = df_raw.copy()
    input_list = [[df["Title"][i], df["Venue"][i]] for i in range(len(df))]
    logger.info("Detecting artists from event titles...")
    extracted_artists = openai_artist_extraction(input_list)
    df_extraction = pd.DataFrame(extracted_artists)
    df_extraction.columns = ["Title", "Artist", "Artist_Certainty"]
    df = pd.merge(
        left = df,
        right = df_extraction,
        on = ["Title"],
        how = "left"
    )
    df["Artist"] = df["Artist"].fillna("")
    df["Artist_Certainty"] = df["Artist_Certainty"].fillna(0)
    spotify_artist_list = []
    for i in range(len(df)):
        print(f"Fetching Spotify data for artist: {df['Artist'][i]}")
        if (df["Artist"][i] != "") and (df["Artist_Certainty"][i] > artist_certainty_threshold):
            artist_search = get_artist_from_search(df["Artist"][i].strip())
            if not artist_search:
                get_artist_from_search(df["Artist"][i].strip().lower())
            if artist_search:
                artist_most_played_track = get_artist_most_played_track(artist_search["artist_id"])
                if artist_most_played_track:
                    out_dict = artist_search | artist_most_played_track
                    spotify_artist_list.append(out_dict)
    df_artist_list = pd.DataFrame(spotify_artist_list)
    df = pd.merge(
        left = df,
        right = df_artist_list,
        left_on = ["Artist"],
        right_on = ["artist_name"],
        how = "left"
    )
    df = df.drop_duplicates(["Title", "Venue", "Date"]).reset_index(drop = True)
    df["followers_rank"] = df["followers"].fillna(0).rank(ascending = False)
    return(df)


def export_events(from_date = EVENT_FROM_DATE, to_date = EVENT_TO_DATE):
    '''
        Export output to CSV format
    '''
    df = embed_players()
    df = df[
        (pd.to_datetime(df["Date"]) >= pd.to_datetime(from_date)) &
        (pd.to_datetime(df["Date"]) <= pd.to_datetime(to_date))
    ]
    logger.info("Overwrting music_events.csv")
    df.to_csv(str(OUTPUT_PATH) + "/music_events.csv", index = False)