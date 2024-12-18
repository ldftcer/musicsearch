FROM python:3.9-slim

RUN apt-get update && apt-get install -y ffmpeg

# Копируем приложение и устанавливаем зависимости
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# Запуск приложения
CMD ["python", "searchmusic.py"]
 
