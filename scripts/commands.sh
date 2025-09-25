#!/bin/sh

# O shell irá encerrar a execução do script quando um comando falhar
set -e

echo "Aguardando o Redis subir..."
# Espera o Redis responder na porta 6379
until nc -z redis 6379; do
  echo "Redis ainda não disponível - aguardando..."
  sleep 1
done

echo "Redis está no ar 🚀"

python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py runserver_plus 0.0.0.0:8000