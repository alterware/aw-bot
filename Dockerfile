FROM python:slim-bookworm

RUN apt update && apt install -y ffmpeg

WORKDIR /aw-bot

RUN python -m venv /bot-env

# Activate the virtual environment and install dependencies
COPY requirements.txt .
RUN /bot-env/bin/pip install --no-cache-dir -r requirements.txt

COPY bot /aw-bot/bot
COPY database /aw-bot/database
COPY sounds /aw-bot/sounds
COPY aw.py .
COPY LICENSE .

ENV BOT_TOKEN=""

# Where the database will be stored
ENV BOT_DATA_DIR=""

CMD ["/bot-env/bin/python", "aw.py"]
