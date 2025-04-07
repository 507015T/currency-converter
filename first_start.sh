#!/bin/bash

sudo docker-compose build || sudo docker compose build
sudo docker-compose run --rm tests || sudo docker compose run tests
if [ $? -eq 0 ]; then
    sleep 1
    echo "Тесты пройдены. Запускаем app..."
    sudo docker-compose up app || sudo docker compose up app
else
    echo "Тесты упали. Запуск отменён."
fi
