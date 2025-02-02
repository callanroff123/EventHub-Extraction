# Import libraries
import os
from openai import OpenAI
import openai
from datetime import datetime
from dotenv import load_dotenv


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
