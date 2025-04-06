import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
load_dotenv()


# Don't need to directly call the environment variables
# SpotifyClientCredentials takes care of this
sp = spotipy.Spotify(client_credentials_manager = SpotifyClientCredentials())


def get_artist_from_search(artist_name):
    """
        Searches for an artist in spotify and pick the top match.

        Input: artist_name (str) -> The name of the artist we are searching Spotify for.
        Output: matched_artist (dict) -> A dictionary containing high-level data of the mathced artist and a corresponding URI. 
    """
    try:
        result = sp.search(
            q = f"artist:{artist_name}", 
            type = "artist", 
            limit = 3
        )
        artists = result.get("artists", {}).get("items", [])
        if not artists:
            return(None)
        artists = [a for a in artists if (a["name"] == artist_name) and (a["type"] == "artist")]
        artist = artists[0]
        return(
            {
                "artist_id": artist["id"],
                "artist_name": artist["name"],
                "artist_uri": artist["uri"],
                "followers": artist["followers"]["total"],
                "genres": artist["genres"]
            }
        )
    except Exception as e:
        print(f"Error implementing artist search functionality for artist: {artist_name}: {e}")
        return(None)


def get_artist_most_played_track(artist_id):
    """
        Get the most-played song for a Spotify-listed artist.

        Input: artist_id (str) -> The artist we want to extract songs for.
        Output: artist_top_track (dic) -> A dictionary containing track metadata, including the player URL.
    """
    try:
        top_tracks = sp.artist_top_tracks(
            artist_id = artist_id
        )
        if top_tracks["tracks"]:
            track = top_tracks["tracks"][0]
            return(
                {
                    "track_id": track["id"],
                    "track_name": track["name"]
                }
            )
        else:
            return(None)
    except Exception as e:
        print(f"Error finding top track for given artist_id: {artist_id}: {e}")
        return(None)




