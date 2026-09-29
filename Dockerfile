# Fáze 1: Zkompilování TypeScriptu
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY tsconfig.json ./
COPY *.ts ./
RUN npm run build:ts

# Fáze 2: Spuštění Python (FastAPI) serveru
FROM python:3.11-slim
WORKDIR /app

# Instalace závislostí a klienta pro zálohování databáze
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Zkopírování zbytku projektu
COPY . .

# Přepsání zkompilovaných JS souborů z builder fáze
COPY --from=builder /app/*.js ./

# Otevření portu 8000 (uvicorn default)
EXPOSE 8000

# Příkaz pro spuštění aplikace
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
