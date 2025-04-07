# **Currency Converter API**

## Конвертер валют на основе котировок от ЕЦБ, реализованный на Django REST Framework.
### Возможности

 - Импорт котировок из официального XML источника ЕЦБ

 - API для просмотра, редактирования и удаления курсов валют

 - Конвертация валют (включая кросс-курс через EUR)

 - HTML-калькулятор (форма с выбором валют и суммы)

 - Полное покрытие тестами (100% coverage)

 - Проект в Docker-контейнерах

 - Автоматизация сборки и тестов

# Быстрый старт
1. Клонируем проект

```bash
git clone https://github.com/507015T/currency-converter.git 
cd currency-converter
```

2. Запускаем через Docker(Только первый запуск(Build + run tests + start project))

```bash
chmod +x ./first_start.sh && ./first_start.sh
```
3. Далее запускать(start project):

```bash
sudo docker-compose up app || sudo docker compose up app
```
4. Консольная команда для получения всех валют из API ECB:
```bash
sudo docker-compose -f docker-compose.command.yml up || sudo docker compose -f docker-compose.command.yml up
```
*Команда импорта валют(Если не через докер)(**Первый запуск**)*
```bash
(python3 -m venv venv || python -m venv venv || python3.13 -m venv venv) && source venv/bin/activate && pip install -r requirements.txt && (python3.13 manage.py import_exchange_rates || python manage.py import_exchange_rates || python 3.13 manage.py import_exchange_rates)
```
Далее для повторного запуска тестов(Зависит от OS каким образом писать python):
```bash
python3.13 manage.py import_exchange_rates || python manage.py import_exchange_rates || python 3.13 manage.py import_exchange_rates
```

Парсит XML-файл с сайта ЕЦБ и обновляет список курсов валют.

### Тесты (Если нужно отдельно прогнать)
```bash
sudo docker-compose run --rm tests || sudo docker compose run tests
```


Покрытие кода: 100%
📡 API эндпоинты
Метод	URL	Описание
- GET	    | /api/currencies/	Список курсов валют
- GET	    | /api/currencies/<currency>/	Курс определенной валюты
- PUT/PATCH | /api/currencies/<currency>/	Обновить курс валюты
- DELETE	| /api/currencies/<currency>/	Удалить курс валюты
- POST	    | /api/currencies/convert/  Конвертация валют
- GET/POST	| /calc/    HTML-калькулятор




## Калькулятор
Простой HTML-интерфейс на /calc/ — выбираем валюты, вводим сумму и получаем результат.
⚙️ Автоматизация

    Docker: веб-приложение, redis и зависимости изолированы

    unittests + coverage: тесты с полным покрытием


**by 507015✝**
