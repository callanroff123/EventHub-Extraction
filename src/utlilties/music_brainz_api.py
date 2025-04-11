import requests
import os
from dotenv import load_dotenv
from src.utlilties.log_handler import setup_logging


# MusicBrainz is freeeee! No auth and set up needed too.
load_dotenv()
logger = setup_logging(logger_name = "scraping_logger")
GMAIL_USER_EMAIL = os.environ.get("GMAIL_USER_EMAIL")
HEADERS = {
    "User-Agent": f"EventHubApp/1.0 ({GMAIL_USER_EMAIL})"
}


def search_artist_music_brainz(artist_name):
    logger.info(f"Using MusicBrainz to get ID for {artist_name}")
    try:
        url = "https://musicbrainz.org/ws/2/artist/"
        params = {
            'query': f'artist:{artist_name}',
            'fmt': 'json'
        }
        response = requests.get(
            url, 
            params = params,
            headers = HEADERS
        )
        data = response.json()
        if data['artists']:
            artist = data['artists'][0]
            if artist_name.upper().strip() == artist.upper().strip():
                return(artist['id'])
            else:
                return(None, None)
        else:
            return(None, None)
    except Exception as e:
        logger.warning(f"Error getting ID for {artist['id']} - {e}")
        return(None)


def get_artist_genre_music_brainz(artist_id):
    logger.info(f"Using MusicBrainz to get genre for {artist_id}")
    try:
        url = f"https://musicbrainz.org/ws/2/artist/{artist_id}"
        params = {
            'fmt': 'json',
            'inc': 'genres',
        }
        response = requests.get(
            url, 
            params = params,
            headers = HEADERS
        )
        data = response.json()
        genres = [genre['name'] for genre in data.get('genres', [])]
        return(genres)
    except Exception as e:
        logger.warning(f"Error getting genre for {artist_id} - {e}")
        return(None)