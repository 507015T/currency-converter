#!/bin/sh

docker-compose build
docker-compose run --rm tests
if [ $? -eq 0 ]; then
  sleep 1
  echo "Тесты пройдены. Запускаем app..."
  docker-compose up app
else
  echo "Тесты упали. Запуск отменён."
fi
