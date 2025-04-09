from decimal import Decimal
from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.renderers import TemplateHTMLRenderer
from django.core.cache import cache
from currency import utils
from currency.serializers import CurrencySerializer, CurrencyConvertSerializer
from currency.models import Currency
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema_view,
)
from datetime import date, timedelta
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] > %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="Список курсов валют",
        tags=["Валюты"],
        responses={200: CurrencySerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Курс определенной валюты",
        tags=["Валюты"],
        responses={200: CurrencySerializer},
        examples=[
            OpenApiExample(
                name="Пример информации о валюте usd",
                value={
                    "id": 1,
                    "currency_name": "USD",
                    "rate": "1.1057000",
                    "actual_date": "2025-04-04",
                    "deleted_date": None,
                    "is_modified": False,
                },
            ),
        ],
    ),
    update=extend_schema(
        summary="Обновление курса валюты",
        tags=["Валюты"],
        responses={200: CurrencySerializer},
        examples=[
            OpenApiExample(
                name="Пример запроса на обновление JPY",
                value={
                    "id": 2,
                    "currency_name": "JPY",
                    "rate": "2.9328321",
                    "actual_date": "2020-04-04",
                },
            ),
        ],
    ),
    partial_update=extend_schema(
        summary="Частичное обновление курса валюты",
        tags=["Валюты"],
        responses={200: CurrencySerializer},
    ),
    destroy=extend_schema(
        summary="Удаление курса валюты (soft delete)",
        tags=["Валюты"],
        responses={204: OpenApiResponse(description="Успешное удаление")},
    ),
)
class CurrencyViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = CurrencySerializer
    lookup_field = "currency_name"
    lookup_url_kwarg = "currency"

    def get_queryset(self):
        queryset = _check_cached_currencies()
        return queryset

    def get_object(self):
        currency_name = self._get_currency_name()
        try:
            obj = self.get_queryset().get(currency_name=currency_name)
            return obj
        except Currency.DoesNotExist:
            raise NotFound(f"Валюта {currency_name} не найдена")

    # when updating => restart cache
    def perform_update(self, serializer):
        cache.clear()
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        currency_name = self._get_currency_name()
        obj = self.get_queryset().get(currency_name=currency_name)
        obj.deleted_date, obj.is_modified = date.today(), True
        obj.save()
        cache.clear()
        return Response(
            {"response": f"Currency {currency_name} successful deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Конвертация валют",
        description="Конвертирует одну валюту в другую по последнему курсу.",
        tags=["Валюты"],
        request=CurrencyConvertSerializer,
        examples=[
            OpenApiExample(
                name="Пример конвертации",
                value={"from_currency": "USD", "to_currency": "TRY", "amount": 20},
            ),
            OpenApiExample(
                name="Пример ответа",
                value={"result": 666.7777777},
                response_only=True,
            ),
        ],
    )
    @action(("POST",), detail=False)
    def convert(self, request, *args, **kwargs):
        self.get_queryset()
        data = CurrencyConvertSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(data.data, status=status.HTTP_200_OK)

    def _get_currency_name(self):
        currency_name = self.kwargs.get(self.lookup_url_kwarg).upper()
        return currency_name


@extend_schema(
    summary="HTML-калькулятор валют",
    tags=["Калькулятор"],
)
class CalcCurrencies(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "calc.html"

    def get(self, request):
        _check_cached_currencies()
        serializer = CurrencyConvertSerializer()
        return Response({"serializer": serializer})

    def post(self, request):
        serializer = CurrencyConvertSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.data.get("result")
            return Response({"serializer": serializer, "result": result})
        return Response(
            {"serializer": serializer, "result": "Нельзя указывать одинаковые валюты"}
        )


def _check_cached_currencies():
    cache_data = cache.get("currencies")
    if not cache_data:
        logging.debug("Кэш пуст")
        objects = _sync_currencies_with_api_ecb()
        return _set_cache(objects)
    logging.debug("Данные получены из кеша")
    return cache_data


def _sync_currencies_with_api_ecb():
    Currency.objects.filter(
        deleted_date__lte=timezone.now() - timedelta(days=30)
    ).delete()
    queryset = Currency.objects.filter(deleted_date=None)
    db_actual_date = _db_actual_date(queryset)
    ecb_data = utils.fetch_exchange_rates_for_db()
    ecb_actual_date = ecb_data[0]["actual_date"]

    if db_actual_date and (ecb_actual_date == str(db_actual_date)):
        logging.debug("Данные актуальны")
        return queryset

    elif db_actual_date and (ecb_actual_date != str(db_actual_date)):
        logging.debug("Не совпадают даты актуальности данных")
        return _update_currencies(queryset, ecb_data)

    logging.debug("БД пуста, создание объектов на основе API ECB...")
    return _create(ecb_data)


def _set_cache(objects):
    logging.debug("Установка кеша продолжительностью 1 день")
    cache.set("currencies", objects, timeout=86400)
    return objects


def _create(ecb_data):
    objects_to_create = [Currency(**i) for i in ecb_data]
    created_objects = Currency.objects.bulk_create(objects_to_create)
    logging.debug("Объекты успешно созданы и внесены в БД")
    queryset = Currency.objects.filter(deleted_date=None)
    return queryset


def _db_actual_date(queryset):
    if queryset:
        logging.debug("Объекты в БД были найдены")
        logging.debug("Получение актуальной даты валют из БД")
        db_actual_date = (
            queryset.filter(is_modified=False)[:1]
            .values("actual_date")
            .get()["actual_date"]
        )
        return db_actual_date


def _update_currencies(
    queryset,
    ecb_api_data,
):
    cache.clear()
    logging.debug("Обновление данных в БД")
    api_data_map = {item["currency_name"]: item for item in ecb_api_data}
    to_update = []
    for obj in queryset:
        data = api_data_map.get(obj.currency_name)
        if (
            not obj.deleted_date
            and not obj.is_modified
            and obj.currency_name == data["currency_name"]
        ):
            logging.debug(
                f"Обработка валюты {obj.currency_name} | rate: {data['rate']}"
            )
            obj.actual_date = data["actual_date"]
            obj.rate = data["rate"]
            to_update.append(obj)
    if to_update:
        Currency.objects.bulk_update(
            to_update, ["actual_date", "rate"]
        )
        logging.debug(f"Обновлено валют: {len(to_update)}")
    logging.debug("Данные успешно обновлены")
    logging.debug("Получение всех валют")
    queryset = Currency.objects.filter(deleted_date=None)

    return queryset
