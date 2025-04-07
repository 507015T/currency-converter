#!/bin/bash

while true; do
    PS3='Вы используете docker-compose или docker compose (1/2)? '
    options=("docker-compose" "docker compose" "Выход")
    select opt in "${options[@]}"
    do
        case $opt in
            "docker-compose")
                docker_compose=("docker-compose")
                echo "Вы выбрали: $docker_compose"
                break 2
                ;;
            "docker compose")
                docker_compose=("docker" "compose")
                echo "Вы выбрали: $docker_compose"
                break 2
                ;;
            "Выход")
                echo "Выход из выбора."
                exit 0
                ;;
            *)
                echo "Некорректный выбор. Попробуйте снова."
                ;;
        esac
    done
done
"${docker_compose[@]}" build
"${docker_compose[@]}" run --rm tests
if [ $? -eq 0 ]; then
  sleep 1
  echo "Тесты пройдены. Запускаем app..."
  $docker_compose up app
else
  echo "Тесты упали. Запуск отменён."
fi
