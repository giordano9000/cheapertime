# Usa l'immagine di base di Python
FROM python:3.9-slim-buster

# Imposta la directory di lavoro nell'immagine
WORKDIR /app

# Copia il codice dell'app Flask nella directory di lavoro
COPY app /app

RUN apt-get update && apt-get install -y ffmpeg libavcodec-extra

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta 5000 per l'app Flask
EXPOSE 5000

# Esegui l'app Flask
CMD ["python", "app.py"]
