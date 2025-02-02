# Import required libraries 
import os
from pathlib import Path
import logging


# Speicify path defaults
APP_PATH = Path(os.environ["PYTHONPATH"]) / "src"
OUTPUT_PATH = APP_PATH / "data/"
LOG_PATH = APP_PATH / "logs/"


# Email
SMTP_SERVER = "smtp.gmail.com"
PORT = 465


# Logging
LOGGING_PARAMS = {
    "file_mode": "a",
    "max_bytes": 5 * 1024 * 1024,
    "backup_count": 10
}


# Venue-address mapping
venues = [
    "Brunswick Ballroom",
    "The Night Cat",
    "Croxton Bandroom",
    "Corner Hotel",
    "Northcote Theatre",
    "Northcote Social Club",
    "The Workers Club",
    "The Retreat",
    "The Retreat Hotel",
    "Sub Club",
    "Sub Club Melbourne",
    "Miscellania",
    "Melbourne Recital Centre",
    "280 Sydney Rd",
    "Max Watt's Melbourne",
    "Sidney Myer Music Bowl",
    "Forum Melbourne",
    "Howler",
    "The Toff in Town",
    "Kindred Bandroom",
    "Gasometer (Upstairs)",
    "Gasometer Downstairs",
    "170 Russell",
    "Arts Centre",
    "Hamer Hall",
    "Sidney Myer Music Bowl"
]


PROMOTER_DICT  = [
    {
        "promoter": "CAT HOUSE MELBOURNE",
        "listings": "humanitix",
        "url": "https://events.humanitix.com/host/62984569eb9a6c0bb63f11bc",
        "venues": ["Miscellania", "Sub Club", "24 Moons", "Angel Music Bar"]
    },
    {
        "promoter": "Miscellania",
        "listings": "humanitix",
        "url": "https://events.humanitix.com/host/60e557b6a7532e000a4f0c92",
        "venues": ["Miscellania"]
    },
    {
        "promoter": "Charades x Sub Club",
        "listings": "eventbrite",
        "url": "https://www.eventbrite.com.au/o/charades-x-sub-club-48348435443",
        "venues": [
            {
                "venue_name": "Sub Club",
                "venue_address": "Flinders Ct"
            }
        ]
    },
    {
        "promoter": "The Retreat Hotel",
        "listings": "eventbrite",
        "url": "https://www.eventbrite.com.au/o/the-retreat-hotel-28439300263",
        "venues": [
            {
                "venue_name": "The Retreat Hotel",
                "venue_address": "280 Sydney Rd"
            }
        ]
    },
    {
        "promoter": "Lucid",
        "listings": "humanitix",
        "url": "https://events.humanitix.com/host/luciddanceclub",
        "venues": [
            {
                "venue_name": "Collingwood Yards",
                "venue_address": "36 Johnston St"
            },
            {
                "venue_name": "Abbotsford Convent",
                "venue_address": "1 Heliers St"
            },
            {
                "venue_name": "Sub Club",
                "venue_address": "Flinders Ct"
            },
            {
                "venue_name": "The Nightcat",
                "venue_address": "Johnston St"
            }
        ]
    },
    {
        "promoter": "Melbourne Techno Collective",
        "listings": "humanitix",
        "url": "https://events.humanitix.com/host/melbourne-techno-collective",
        "venues": [
            {
                "venue_name": "Collingwood Yards",
                "venue_address": "36 Johnston St"
            },
            {
                "venue_name": "Abbotsford Convent",
                "venue_address": "1 Heliers St"
            },
            {
                "venue_name": "Sub Club",
                "venue_address": "Flinders Ct"
            },
            {
                "venue_name": "The Night Cat",
                "venue_address": "Johnston St"
            }
        ]
    },
    {
        "promoter": "Other Worlds Other Sounds",
        "listings": "eventbrite",
        "url": "https://www.eventbrite.com/o/other-worlds-other-sounds-57795243423",
        "venues": [
            {
                "venue_name": "24 Moons",
                "venue_address": "2 Arthurton Rd"
            },
            {
                "venue_name": "The Night Cat",
                "venue_address": "Johnston St"
            },
            {
                "venue_name": "Angel Music Bar",
                "venue_address": "12 Bourke St"
            },
            {
                "venue_name": "The Night Cat",
                "venue_address": "Johnston St"
            },
            {
                "venue_name": "Howler",
                "venue_address": "Dawson St" 
            }
        ]
    },
]