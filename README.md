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

2. Запускаем через Docker(Только первый запуск(Build + run tests))

```bash
chmod +x ./first_start.sh && ./first_start.sh
```
3. Далее запускать:

```bash
docker-compose up app
```
4. Консольная команда для получения всех валют из API ECB:
```bash
docker-compose -f docker-compose.command.yml up
```
*Команда импорта валют(Если не через докер)*
```bash
python3 -m venv venv && source venv/bin/activate && python3 manage.py import_exchange_rates
```
Парсит XML-файл с сайта ЕЦБ и обновляет список курсов валют.

### Тесты (Если нужно отдельно прогнать)
```bash
docker-compose run --rm tests
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


📂 Структура проекта

currency-converter/
├── backend
│   ├── __init__.py
│   ├── __pycache__
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── currency
│   ├── __init__.py
│   ├── __pycache__
│   ├── admin.py
│   ├── apps.py
│   ├── management
│   ├── migrations
│   ├── models.py
│   ├── serializers.py
│   ├── templates
│   ├── tests.py
│   ├── urls.py
│   ├── utils.py
│   └── views.py
├── docker-compose.command.yml
├── docker-compose.override.yml
├── docker-compose.yml
├── Dockerfile
├── first_start.sh
├── manage.py
├── README.md
├── requirements.txt
└── tests.sh


**by 507015✝**
