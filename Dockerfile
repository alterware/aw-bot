FROM python:alpine

WORKDIR /aw-bot

COPY . /aw-bot

RUN pip install --no-cache-dir -r requirements.txt

COPY patterns.json /aw-bot

ENV BOT_TOKEN=""

CMD ["python", "aw.py"]
