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
ENV GOOGLE_API_KEY=""
ENV DISCOURSE_API_KEY=""
ENV DISCOURSE_BASE_URL=""
ENV DISCOURSE_USERNAME=""

# Where the database will be stored
ENV BOT_DATA_DIR=""

ENV MONGO_URI=""

# Accept build arguments for metadata
ARG BUILD_DATE=""
ARG GIT_TAG=""

# Set them as environment variables
ENV BUILD_DATE=${BUILD_DATE}
ENV GIT_TAG=${GIT_TAG}

CMD ["/bot-env/bin/python", "aw.py"]
