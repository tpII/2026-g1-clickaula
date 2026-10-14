FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El orden va de lo que menos cambia a lo que más, para aprovechar la caché.
COPY dominio/ ./dominio/
COPY servicios/ ./servicios/
COPY app/ ./app/
COPY sim/ ./sim/
COPY run.py .

RUN mkdir -p /srv/data
EXPOSE 5000

CMD ["python", "run.py"]
