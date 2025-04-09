import requests
import os
from dotenv import load_dotenv
from src.utlilties.log_handler import setup_logging


# Load API key from environment variables
load_dotenv()
API_KEY = os.environ.get("YOUTUBE_DATA_API_KEY")
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
logger = setup_logging(logger_name = "scraping_logger")


def search_artist_video(artist_name):
    """
        Function which returns a URL for the top youtube video of a search for a given artist.

        Input: artist_name (str) -> The artist's name/alias.
        Ouput: video_url (str) -> The URL of the top video corresponding to the search.
    """
    try:
        params = {
            "part": "snippet",
            "q": f"{artist_name} live performance",
            "type": "video",
            "maxResults": 4,
            "videoEmbeddable": "true",
            "key": API_KEY
        }
        response = requests.get(SEARCH_URL, params = params)
        data = response.json()
        if "items" in data and data["items"]:
            video_id = data["items"][0]["id"]["videoId"]
            video_url = f"https://www.youtube.com/embed/{video_id}"
            return(video_url)
        else:
            return(None)
    except Exception as e:
        logger.warning(f"Error in fetching URL for search '{artist_name}' on Youtube: {e}")
        return(None)
