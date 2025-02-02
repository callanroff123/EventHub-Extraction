FROM python:3.9-slim

# Set project working directory for container
WORKDIR /usr/app

# Install system dependencies required to run chromedriver for selenium automation
# apt-get update -> update the package list for the latest version of system dependencies
# apt-get install -y -> Installs the subsequent system dependencies
RUN apt-get update && apt-get install -y \
    # wget + curl -> commands used to download chrome and chromedriver from the internet
    wget \
    curl \
    # unzip -> Extracts chromedriver from a zip file
    unzip \
    # xvbf -> Runs a browser w/o a GUI (for headless mode)
    xvfb \
    # libnss3 -> Needed for chrome to work
    libnss3 \
    # libxss1 -> Needed for chrome's tab restoration feature (not sure why we need but whatevs)
    libxss1 \
    # libappindicator3-1 -> Helps with Chrome's system tray notifications (again, not quite sure what this is doing but continuing to follow the recipe)
    libappindicator3-1 \
    # libasound2 -> Provides sound support (Not really needed but still; just following the recipe)
    libasound2 \
    # fonts-liberation -> Ensures fonts are rendered in headless Chrome
    fonts-liberation \
    # libgbm1 -> Allows chrome to run in headless mode with GPU acceleration
    libgbm1 \
    gnupg2 \
    # Clean up the package list cache after installation to reduce size of docker image
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome to container
# Specifically, download and add google's package signing key
# i.e., ensure the package we download from google is a 'trusted source'
# wget -q -O - https://dl.google.com/linux/linux_signing_key.pub -> download google's signing key
# -q -0 -> Runs wget in no-output (quiet) mode, then output file content directly to terminal (w/o saving in container)
# | apt-key add - -> pipes (|) downloaded sigining key into apt-key add - (system's list of trusted keys)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    # echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" -> create entry point from Chrome's package repo
    # deb -> debian package repo
    # [arch=amd64] -> package is for 64-bit (AMD64) systems
    # http://dl.google.com/linux/chrome/deb/ -> url of google's debian package repo
    # stable main -> install the stable version of chrome
    # >> /etc/apt/sources.list.d/google-chrome.list -> append (>>) the google debian package repo to a file in the container named google-chrome.list
    # i.e., info on where to find the chrome package in the container
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    # apt-get update -> refresh package index: apt-get knows about latest chrome repository
    && apt-get update \
    # && apt-get install -y google-chrome-stable -> Installs the stable version of Chrome (-y -> automatically confirm installation)
    && apt-get install -y google-chrome-stable=132.0.6834.159-1

# Install Chrome Driver; allows selenium to interact with Chrome programatically
# CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) -> Stores fetched chromedriver version as a variable
# curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE -> fetch data from url (curl) in silent (-sS) mode (i.e., hides progress)
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    # wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -> Download the corresponding ChromeDriver (via wget command (the download command))
    # -0 chromedriver.zip -> Instructions on where to store the downloaded file in container
    wget -q "https://storage.googleapis.com/chrome-for-testing-public/132.0.6834.159/linux64/chromedriver-linux64.zip" -O chromedriver.zip && \
    # unzip chromedriver.zip -> Extract (unzip) chromedriver binary from chromedriver.zip (i.e., we now have a folder called chromedriver)
    unzip chromedriver.zip && \
    # mv chromedriver /usr/local/bin/ -> move unzipped chromedriver folder to a directory in the system: /usr/local/bin/
    mv chromedriver-linux64/chromedriver /usr/local/bin/ && \
    ls -R && \
    # chmod +x /usr/local/bin/chromedriver -> chmod +x permits chromedriver binary execution
    # i.e., ensures system recognises it as a runnable program  
    chmod +x /usr/local/bin/chromedriver && \
    # rm chromedriver.zip remove the downloaded zipped file to save space in container
    rm chromedriver.zip

# Copy requirements.txt locally inside the project working dir we set for the container
COPY requirements.txt .
# --no cache-dir -> prevents caching of installed python dependencies
# Saves space in the image
RUN pip install --no-cache-dir -r requirements.txt

# Copy project from local to image
COPY . /usr/app/

# Disable output buffering. This ensures the logs we set are visible and we can see how the program is tracking in real time.
ENV PYTHONUNBUFFERED=1

CMD ["python3", "src/main.py"]
