FROM python:alpine

WORKDIR /aw-bot

COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt  

COPY bot /aw-bot/bot  
COPY aw.py .  
COPY patterns.json .  

ENV BOT_TOKEN=""

CMD ["python", "aw.py"]
