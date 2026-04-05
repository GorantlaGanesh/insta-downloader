FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["python", "app.py"]
