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
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] > %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


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
        currency_name = self.kwargs.get(self.lookup_url_kwarg).upper()
        self.get_queryset()
        try:
            obj = Currency.objects.filter(is_deleted=False).get(
                currency_name=currency_name
            )
            return obj
        except Currency.DoesNotExist:
            raise NotFound(f"Валюта {currency_name} не найдена")

    # when updating => restart cache
    def perform_update(self, serializer):
        cache.clear()
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        self.get_queryset()
        currency_name = self.kwargs.get(self.lookup_url_kwarg).upper()
        obj = Currency.objects.get(currency_name=currency_name)
        obj.is_deleted, obj.is_modified = True, True
        obj.save()
        return Response(
            {"response": f"Currency {currency_name} successful deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(("POST",), detail=False)
    def convert(self, request, *args, **kwargs):
        self.get_queryset()
        data = CurrencyConvertSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(data.data, status=status.HTTP_200_OK)


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
        objects = _check_currencies_existance()
        return _set_cache(objects)
    logging.debug("Данные получены из кеша")
    return cache_data


def _check_currencies_existance():
    queryset = Currency.objects.filter(is_deleted=False)
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
    return created_objects


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
    for i, j in zip(queryset, ecb_api_data):
        if (
            not i.is_deleted
            and not i.is_modified
            and i.id == j["id"]
            and i.currency_name == j["currency_name"]
        ):
            i.actual_date = j["actual_date"]
            i.rate = j["rate"]
    updated_objects = Currency.objects.bulk_update(queryset, ["actual_date", "rate"])
    logging.debug("Данные успешно обновлены")

    logging.debug("Получение всех валют")
    queryset = Currency.objects.filter(is_deleted=False)

    return queryset
