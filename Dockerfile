FROM python:alpine

WORKDIR /aw-bot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot /aw-bot/bot
COPY database /aw-bot/database
COPY aw.py .

ENV BOT_TOKEN=""

# Where the database will be stored
ENV BOT_DATA_DIR = ""

CMD ["python", "aw.py"]
