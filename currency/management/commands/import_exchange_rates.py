from django.core.management.base import BaseCommand
from currency.utils import fetch_exchange_rates_cmd


class Command(BaseCommand):
    help = (
        "Загружает курсы валют от Европейского Центрального Банка и выводит в консоль."
    )

    def handle(self, *args, **options):
        try:
            rates = fetch_exchange_rates_cmd()
            self.stdout.write(self.style.SUCCESS(f"Курс валют актуальный на {rates[-1]}: {rates[:-1]}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка: {e}"))
