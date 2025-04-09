FROM python:3.9-slim

WORKDIR /app

# Build arguments (passed from GitHub Actions)
ARG GMAIL_APP_PASSWORD
ARG GMAIL_PASSWORD
ARG GMAIL_USER_EMAIL
ARG MS_BLOB_CONNECTION_STRING
ARG MS_BLOB_CONTAINER_NAME
ARG OPENAI_KEY
ARG YOUTUBE_DATA_API_KEY
ARG SPOTIPY_CLIENT_ID
ARG SPOTIPY_CLIENT_SECRET

# Set them as environment variables inside the container
ENV GMAIL_APP_PASSWORD=${GMAIL_APP_PASSWORD}
ENV GMAIL_PASSWORD=${GMAIL_PASSWORD}
ENV GMAIL_USER_EMAIL=${GMAIL_USER_EMAIL}
ENV MS_BLOB_CONNECTION_STRING=${MS_BLOB_CONNECTION_STRING}
ENV MS_BLOB_CONTAINER_NAME=${MS_BLOB_CONTAINER_NAME}
ENV OPENAI_KEY=${OPENAI_KEY}
ENV YOUTUBE_DATA_API_KEY=${YOUTUBE_DATA_API_KEY}
ENV SPOTIPY_CLIENT_ID=${SPOTIPY_CLIENT_ID}
ENV SPOTIPY_CLIENT_SECRET=${SPOTIPY_CLIENT_SECRET}

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN apt-get update && \
    apt-get install -y wget unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    apt-get clean

CMD ["python3", "src/main.py"]