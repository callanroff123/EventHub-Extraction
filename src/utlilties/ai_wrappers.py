# Import libraries
import os
from openai import OpenAI
import openai
from datetime import datetime
from dotenv import load_dotenv
import json
import ast
from src.config import EVENT_TITLE_EXCLUSIONS, EVENT_TITLE_MODIFICATIONS


# Load openai API key from environment variables
load_dotenv()
OPENAI_KEY = os.environ.get("OPENAI_KEY")
CURRENT_YEAR = str(datetime.now().year)
client = OpenAI(api_key = OPENAI_KEY)


def openai_dateparser(date):
    """
        Function which converts a list of raw dates to YYYY-mm-dd format.
        To be used when built-in date parser fails.

        * Input: date (str) -> the raw date requiring conversion
        * Output output_dates (str) cleaned dates, still in string format, but all converted to YYYY-mm-dd 
    """
    prompt = (
        f"""
            Extract the date from the following string and return in YYYY-MM-DD format.
            If no year is detected, assume the year is {CURRENT_YEAR}.
            If an element is detected to have multiple dates, or a range of dates, return each date, split by separated by ', ' (ex: '2025-01-01', '2025-01-02').
            Here is the string: {date}
            Just message me the resultant date please.
        """
    )
    try:
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            store = True,
            messages = [
                {"role": "user", "content": prompt}
            ]
        )
        output = response.choices[0].message.content
        output_dates = [i.strip() for i in output.split(",")]
        return(output_dates)
    except Exception as e:
        print(f"Error extracting dates: {e}")
        return([])


def openai_artist_extraction(title_list):
    """
        Function with identifies the main artist from a list of event headings (IF there is an artist...).
        Note not every heading will contain an artist (ex: Fundraiser, NIEUW MONDYAS, Private Event).
        In which case the reponse will include the artist + the % certainty of the response

        * Input: title_list (list[str, str]) -> list of event titles + the venue
        * Output: output_list (list[str, str]) -> list of presumed artists and the probability they're an artist
    """
    prompt = f"""
        You are given a list of event titles and their venues in Melbourne. Each item is a pair: [event title, venue].
        These titles include the performing artist/band/DJ name.
        Your task:
        - Return the most likely artist.
        - Provide a percentage certainty the above guess is actually an aritst (given the title, venue and your knowledge of existing artists/DJs).
        Rules:
        - If the event title contains any of these phrases, treat them as likely NOT featuring an artist and limit certainty to 10%: {EVENT_TITLE_EXCLUSIONS}.
        - If the title contains any of these phrases (regardless of upper/lowercase), remove these characters then continue: {EVENT_TITLE_MODIFICATIONS}.
        - If the response detects multiple artists, please return only one.
        - Titles with phrases like "Private Party", "Open Mic Night", etc. typically don't contain an artist.
        - If an artist can't be identified, return an empty string for the artist guess.
        Input (list of [title, venue]):
        {title_list}
        Return a valid JSON list of [title, artist_guess, certainty_percentage] for each input pair.
        Respond with only JSON — no explanations, no text.
    """
    try:
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            store = True,
            messages = [
                {"role": "user", "content": prompt}
            ]
        )
        output = response.choices[0].message.content
        output = ast.literal_eval(output.replace("`", "").replace("json", "").replace("\n", "").replace("]]]", "]]"))
        return(output)
    except Exception as e:
        print(f"Error in artist extraction: {e}")
        return([[]])
