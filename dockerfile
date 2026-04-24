FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /api

# Instalar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Cloud Run escucha en 8080
EXPOSE 8080

# Arranque Streamlit
CMD ["streamlit", "run", "app_pro.py", "--server.port=8080", "--server.address=0.0.0.0"]