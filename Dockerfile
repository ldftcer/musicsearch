FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
apt-get install ffmpeg


COPY . /app

ENTRYPOINT ["python", "searchmusic.py"]
