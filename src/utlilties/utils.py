# Import required modules
import os
import numpy as np
import pandas as pd
from src import config


# Heuristic logic to detect tribute shows
def flag_tribute_shows(title, tribute_keywords, artist):
    tribute = 0
    if any(word in title.upper() for word in tribute_keywords):
        tribute = 1
    elif artist.upper() + " EXPERIENCE" in title.upper():
        tribute = 1
    elif artist.upper() + " STORY" in title.upper():
        tribute = 1
    elif artist.upper() + " SONGBOOK" in title.upper():
        tribute = 1
    elif artist.upper() + " PLAYED BY" in title.upper():
        tribute = 1
    elif artist.upper() + " CELEBRATION" in title.upper():
        tribute = 1
    elif "CELEBRATING " + artist.upper() in title.upper():
        tribute = 1
    elif "YEARS OF " + artist.upper() in title.upper():
        tribute = 1
    elif "MUSIC OF " + artist.upper() in title.upper():
        tribute = 1
    elif artist.upper() + " RESURRECTED" in title.upper():
        tribute = 1
    elif "SOUNDS OF " + artist.upper() in title.upper():
        tribute = 1
    elif "SOUND OF " + artist.upper() in title.upper():
        tribute = 1
    elif "MUSICAL LIFE OF" + artist.upper() in title.upper():
        tribute = 1
    return(tribute)


# Remove non-music events
def flag_non_events(title, exclusion_phrases):
    non_event = 0
    if any(word in title.upper() for word in exclusion_phrases):
        non_event = 1
    return(non_event)


# Safe integer conversion
def safe_int(s):
    try:
        return(int(s))
    except (ValueError, TypeError):
        return(90)
