# Import libraries needed to automate emails
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from src import config


# Get environment variables
EMAIL = os.environ.get("GMAIL_USER_EMAIL")
PWD = os.environ.get("GMAIL_PASSWORD")
APP_PWD = os.environ.get("GMAIL_APP_PASSWORD")


# Function to send emails
def send_music_event_email(sender, sender_password, receiver, from_date, to_date):
    msg = MIMEMultipart()
    msg["Subject"] = f"Music Events From {from_date} to {to_date}"
    msg["From"] = sender
    msg["To"] = ",".join(receiver)
    part = MIMEBase("application", "octet-stream")
    part.set_payload(
        open(str(config.OUTPUT_PATH) + "/music_events.csv", "rb").read()
    )
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        "attachment; filename = music_events.csv"
    )
    msg.attach(part)
    s = smtplib.SMTP_SSL(
        host = "smtp.gmail.com",
        port = 465
    )
    s.login(user = sender, password = sender_password)
    s.sendmail(sender, receiver, msg.as_string())
    s.quit


# Run the above function with the specified inputs
def run_send_email():
    credentials = {
        "account": EMAIL,
        "password": PWD,
        "app_password": APP_PWD
    }
    sender = credentials["account"]
    sender_app_password = credentials["app_password"]
    email_list = ["callanroff@gmail.com"]
    from_date = str(datetime.today().year) + "-" + str(datetime.today().month) + "-" + str(datetime.today().day)
    to_date = str(datetime.today().year + 1) + "-" + str(datetime.today().month) + "-" + str(datetime.today().day)
    send_music_event_email(
        sender = sender,
        sender_password = sender_app_password,
        receiver = email_list,
        from_date = from_date,
        to_date = to_date
    )
    print("Email sent!")
