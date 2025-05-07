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
import os
from uuid import uuid4
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from src.event_extraction.eventbrite import get_events_eventbrite
from src.event_extraction.humanitx import get_events_humanitix
from src.event_extraction.moshtix import get_events_moshtix
from src.event_extraction.oztix import get_events_oztix
from src.event_extraction.ticketek import get_events_ticketek
from src.event_extraction.bar_303 import get_events_bar_303
from src.event_extraction.birds_basement import get_events_birds_basement
from src.event_extraction.cherry_bar import get_events_cherry_bar
from src.event_extraction.festival_hall import get_events_festival_hall
from src.event_extraction.jazzlab import get_events_jazzlab
from src.event_extraction.mamma_chens import get_events_mamma_chens
from src.event_extraction.melbourne_recital_centre import get_events_melbourne_recital_centre
from src.event_extraction.melbourne_park import get_events_melbourne_park
from src.event_extraction.memo_music_hall import get_events_memo_music_hall
from src.event_extraction.my_aeon import get_events_my_aeon
from src.event_extraction.palais_theatre import get_events_palais_theatre
from src.event_extraction.paris_cat import get_events_paris_cat
from src.event_extraction.punters_club import get_events_punters_club
from src.event_extraction.the_penny_black import get_events_penny_black
from src.event_extraction.twentyfour_moons import get_events_24_moons
from src.event_extraction.brunswick_ballroom import get_events_brunswick_ballroom
from src.event_extraction.howler import get_events_howler
from src.event_extraction.kindred_bandroom import get_events_kindred_bandroom
from src.event_extraction.northcote_theatre import get_events_northcote_theatre
from src.event_extraction.russell_street import get_events_170_russell
from src.event_extraction.the_nightcat import get_events_nightcat
from src.event_extraction.the_toff import get_events_the_toff
from src.config import OUTPUT_PATH, MIN_SPOTIFY_RANK_FOR_YOUTUBE_API, ARTIST_CERTAINTY_THRESHOLD, BATCH_SIZE, venues, LOOKBACK_DAYS, RECENT_DAYS
from src.utlilties.log_handler import setup_logging
from src.utlilties.ai_wrappers import openai_artist_extraction
from src.utlilties.youtube_data_api import search_artist_video
from src.utlilties.spotify_web_api import get_artist_from_search, get_artist_most_played_track
from src.utlilties.azure_blob_connection import read_from_azure_blob_storage, show_azure_blobs
from dotenv import load_dotenv


#2. Specify defaults.
load_dotenv()
logger = setup_logging("scraping_logger")
EVENT_FROM_DATE = datetime.now().date().strftime(format = "%Y-%m-%d")
EVENT_TO_DATE = (datetime.now().date() + relativedelta(months = 12)).strftime(format = "%Y-%m-%d")
MS_BLOB_CONNECTION_STRING = os.environ.get("MS_BLOB_CONNECTION_STRING")
MS_BLOB_CONTAINER_NAME = os.environ.get("MS_BLOB_CONTAINER_NAME")


def get_all_events():
    '''
        Concatenates results across various sources, and performs some additional cleaning
    '''

    # Ticketing websites #
    # df_moshtix = get_events_moshtix() I've been IP blacklisted from these guys
    df_oztix = get_events_oztix()
    df_eventbrite = get_events_eventbrite()
    df_humanitix = get_events_humanitix()
    df_ticketek = get_events_ticketek()

    # Venue-specific websites
    df_brunswick_ballroom = get_events_brunswick_ballroom()
    df_howler = get_events_howler()
    df_kindred_bandroom = get_events_kindred_bandroom()
    df_northcote_theatre = get_events_northcote_theatre()
    df_russell_street = get_events_170_russell()
    df_the_night_cat = get_events_nightcat()
    df_the_toff = get_events_the_toff()
    df_24_moons = get_events_24_moons()
    df_bar_303 = get_events_bar_303()
    df_birds_basement = get_events_birds_basement()
    df_cherry_bar = get_events_cherry_bar()
    df_festival_hall = get_events_festival_hall()
    df_jazzlab = get_events_jazzlab()
    df_mamma_chens = get_events_mamma_chens()
    df_melbourne_park = get_events_melbourne_park()
    df_melbourne_recital = get_events_melbourne_recital_centre()
    df_memo_music_hall = get_events_memo_music_hall()
    df_my_aeon = get_events_my_aeon()
    df_palais_theatre = get_events_palais_theatre()
    df_paris_cat = get_events_paris_cat()
    df_punters_club = get_events_punters_club()
    df_the_penny_black = get_events_penny_black()

    logger.info("Consolidating events from all ticketing websites.")
    df = pd.concat(
        [
            df for df in [
                df_oztix, 
                df_eventbrite, 
                df_humanitix, 
                df_ticketek,
                df_brunswick_ballroom,
                df_howler,
                df_kindred_bandroom,
                df_northcote_theatre,
                df_russell_street,
                df_the_night_cat,
                df_the_toff,
                df_24_moons,
                df_bar_303,
                df_birds_basement,
                df_cherry_bar,
                df_festival_hall,
                df_jazzlab,
                df_mamma_chens,
                df_melbourne_park,
                df_melbourne_recital,
                df_memo_music_hall,
                df_my_aeon,
                df_palais_theatre,
                df_paris_cat,
                df_punters_club,
                df_the_penny_black
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
        subset = ["Title", "Date", "Venue"], 
        keep = "first"
    ).reset_index(drop=True)
    df_out["Image"] = ["https:" + im if im[0:2] == "//" else im for im in df_out["Image"]]
    logger.info("Events successfully consolidated.")
    return(df_out)


def embed_players(
    batch_size = BATCH_SIZE, 
    artist_certainty_threshold = ARTIST_CERTAINTY_THRESHOLD, 
    min_spotify_rank_for_youtube_api = MIN_SPOTIFY_RANK_FOR_YOUTUBE_API
):
    df_raw = get_all_events()
    df = df_raw.copy()
    df["batch"] = [int(np.floor(i / batch_size)) for i in range(len(df))]
    df_extraction_all = pd.DataFrame()
    for i in df["batch"].unique():
        df_batch = df[df["batch"] == i].reset_index(drop = True)
        input_list = [[df_batch["Title"][j], df_batch["Venue"][j]] for j in range(len(df_batch))]
        logger.info(f"Detecting artists from event titles (batch {i})...")
        extracted_artists = openai_artist_extraction(input_list)
        logger.info(f"Artists successfully extracted (batch {i})!")
        df_extraction = pd.DataFrame(extracted_artists)
        df_extraction.columns = ["Title", "Artist", "Artist_Certainty"]
        df_extraction_all = pd.concat([df_extraction_all, df_extraction], axis = 0)
        time.sleep(0.5)
    df_extraction_all = df_extraction_all.reset_index(drop = True)
    df = pd.merge(
        left = df,
        right = df_extraction_all,
        on = ["Title"],
        how = "left"
    )
    df["Artist"] = df["Artist"].fillna("")
    df["Artist_Upper"] = df["Artist"].str.strip().str.upper()
    df["Artist_Certainty"] = df["Artist_Certainty"].fillna(0)
    spotify_artist_list = []
    for i in range(len(df)):
        print(f"Fetching Spotify data for artist: {df['Artist'][i]}")
        if (df["Artist"][i] not in ["", "N/A"]) and (df["Artist_Certainty"][i] > artist_certainty_threshold):
            artist_search = get_artist_from_search(df["Artist"][i].strip())
            if not artist_search:
                artist_search = get_artist_from_search(df["Artist"][i].strip().lower())
            if artist_search:
                artist_most_played_track = get_artist_most_played_track(artist_search["artist_id"])
                if artist_most_played_track:
                    out_dict = artist_search | artist_most_played_track
                    spotify_artist_list.append(out_dict)
    df_artist_list = pd.DataFrame(spotify_artist_list)
    df_artist_list["artist_name_upper"] = df_artist_list["artist_name"].str.strip().str.upper()
    df = pd.merge(
        left = df,
        right = df_artist_list,
        left_on = ["Artist_Upper"],
        right_on = ["artist_name_upper"],
        how = "left"
    )
    df = df.drop_duplicates(["Title", "Venue", "Date"]).reset_index(drop = True)
    df["followers_rank"] = df["followers"].fillna(0).rank(ascending = False)
    df["youtube_url"] = None
    df["music_brainz_genres"] = None
    for i in range(len(df)):
        if not pd.isna(df["artist_id"][i]):
            if df["followers_rank"][i] <= min_spotify_rank_for_youtube_api:
                df["youtube_url"][i] = search_artist_video(df["Artist"][i]) 
    return(df)


# Get "Just In" gigs
def recent_gigs_just_in():
    recent_events_df_full = pd.DataFrame()
    files = sorted(show_azure_blobs(MS_BLOB_CONNECTION_STRING, MS_BLOB_CONTAINER_NAME))
    for i in range(1, LOOKBACK_DAYS + 1):
        json_data = read_from_azure_blob_storage(
            connection_string = MS_BLOB_CONNECTION_STRING,
            container_name = MS_BLOB_CONTAINER_NAME,
            file_name = files[-i]
        )
        index = [f for f in files[-(LOOKBACK_DAYS + 1):]].index(files[-i])
        json_data_refined = [
            {
                k: d[k] for k in ["Artist", "Venue"]
            } for d in json_data
        ]
        recent_events_df = pd.DataFrame(json_data_refined)
        recent_events_df["day_num"] = index
        recent_events_df_full = pd.concat(
            [
                recent_events_df_full,
                recent_events_df
            ],
            axis = 0
        )
    recent_events_df_full = recent_events_df_full.reset_index(drop = True).drop_duplicates(
        ["Artist", "Venue"],
        keep = "last"
    )
    recent_events_df_full = recent_events_df_full[recent_events_df_full["Artist"].str.strip() != ""].reset_index(drop = True)
    recent_events_df_full["just_in"] = [1 if x > LOOKBACK_DAYS - RECENT_DAYS else 0 for x in recent_events_df_full["day_num"]]
    return(
        recent_events_df_full[[
            "Artist",
            "Venue",
            "just_in"
        ]]
    )


def export_events(from_date = EVENT_FROM_DATE, to_date = EVENT_TO_DATE):
    '''
        Export output to CSV format
    '''
    df = embed_players()
    df_recents = recent_gigs_just_in()
    df = pd.merge(
        left = df,
        right = df_recents,
        on = ["Artist", "Venue"],
        how = "left"
    )
    df["just_in"] = [0 if df["followers_rank"][i] == np.max(df["followers_rank"]) else df["just_in"][i] for i in range(len(df))]
    df["just_in"] = df["just_in"].fillna(1)
    df = df[
        (pd.to_datetime(df["Date"]) >= pd.to_datetime(from_date)) &
        (pd.to_datetime(df["Date"]) <= pd.to_datetime(to_date))
    ]
    logger.info("Overwrting music_events.csv")
    df.to_csv(str(OUTPUT_PATH) + "/music_events.csv", index = False)
    missing_venues = [i for i in venues if i not in df["Venue"].unique()]
    df_missing_venues = pd.DataFrame({
        "Venue": missing_venues
    })
    df_missing_venues.to_csv(str(OUTPUT_PATH) + "/missing_venues.csv", index = False)
