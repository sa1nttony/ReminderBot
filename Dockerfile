FROM python:3.10-slim

# Установим системные пакеты, если нужны (gcc для любых компиляций)
RUN apt-get update \
  && apt-get install -y gcc \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только список зависимостей, чтобы слоить кэш
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Не буферизовать вывод Python
ENV PYTHONUNBUFFERED=1

# Точка входа — будем переопределять в docker-compose
CMD ["bash", "-c", "echo 'Specify a service to run...'"]