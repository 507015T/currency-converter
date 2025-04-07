from django.test.client import Client
from django.test.testcases import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from django.db import connection
from django.conf import settings
from rest_framework.exceptions import ErrorDetail
from currency.serializers import CurrencySerializer
from currency.models import Currency
from datetime import date
from django.core.cache import cache
from rest_framework.test import APIClient
from django.test import TestCase
settings.DEBUG = True


# Create your tests here.
class CurrencyAPITestCase(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()

    def test_ok(self):
        response = self.client.get(reverse("currency-list"), format="json")
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)
        self.assertEqual(2, len(connection.queries))
        serializer_data = CurrencySerializer(Currency.objects.all(), many=True).data
        self.assertEqual(serializer_data, response.data)

    def test_get_from_cache(self):
        response = self.client.get(reverse("currency-list"), format="json")
        self.assertEqual(2, len(connection.queries))
        response = self.client.get(reverse("currency-list"), format="json")
        self.assertEqual(0, len(connection.queries))

    def test_get_currency(self):
        response = self.client.get(
            reverse("currency-detail", kwargs={"currency": "usd"}), format="json"
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)
        self.assertEqual(3, len(connection.queries))
        serializer_data = CurrencySerializer(
            Currency.objects.get(currency_name="USD")
        ).data
        self.assertEqual(serializer_data, response.data)

    def test_update_currency(self):
        response = self.client.patch(
            reverse("currency-detail", kwargs={"currency": "zar"}),
            data={"actual_date": "2025-03-15"},
            format="json",
        )
        self.assertEqual(4, len(connection.queries))
        serializer_data = CurrencySerializer(
            Currency.objects.get(currency_name="ZAR")
        ).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("2025-03-15", response.data["actual_date"])
        self.assertEqual(serializer_data["actual_date"], response.data["actual_date"])
        self.assertTrue(response.data["is_modified"])
        response = self.client.put(
            reverse("currency-detail", kwargs={"currency": "zar"}),
            data={
                "actual_date": "2025-03-11",
                "id": 30,
                "rate": "13.0000",
                "currency_name": "ZAR",
                "is_deleted": False,
                "is_modified": True,
            },
            format="json",
        )
        self.assertEqual(4, len(connection.queries))
        serializer_data = CurrencySerializer(
            Currency.objects.get(currency_name="ZAR")
        ).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("2025-03-11", response.data["actual_date"])
        self.assertEqual("ZAR", response.data["currency_name"])
        self.assertEqual(serializer_data["actual_date"], response.data["actual_date"])

    def test_get_actual_currencies_from_ecb_api(self):
        actual_date = self.client.get(
            reverse("currency-detail", kwargs={"currency": "usd"}), format="json"
        ).data["actual_date"]
        cache.clear()
        obj1 = Currency.objects.get(currency_name="USD")
        obj1.actual_date = date(2025, 3, 15)
        obj1.save()
        response = self.client.get(
            reverse("currency-detail", kwargs={"currency": "usd"}), format="json"
        )
        serializer_data = CurrencySerializer(
            Currency.objects.get(currency_name="USD")
        ).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(actual_date, response.data["actual_date"])
        obj2 = Currency.objects.get(currency_name="ZAR")
        obj2.actual_date = date(2025, 1, 1)
        obj2.is_modified = True
        obj2.save()
        cache.clear()
        response = self.client.get(reverse("currency-list"), format="json")
        serializer_data = CurrencySerializer(Currency.objects.all(), many=True).data
        self.assertEqual("2025-01-01", response.data[-1]["actual_date"])
        self.assertEqual(serializer_data, response.data)

    def test_get_updated_currencies(self):
        actual_date = self.client.patch(
            reverse("currency-detail", kwargs={"currency": "usd"}),
            data={"actual_date": "2025-02-02"},
            format="json",
        ).data["actual_date"]
        cache.clear()
        obj1 = Currency.objects.get(currency_name="JPY")
        obj1.actual_date = date(2025, 3, 15)
        obj1.save()
        response = self.client.get(reverse("currency-list"), format="json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("2025-02-02", response.data[0]["actual_date"])

    def test_delete_currency(self):
        response = self.client.delete(
            reverse("currency-detail", kwargs={"currency": "usd"}), format="json"
        )
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        expected_data = {"response": "Currency USD successful deleted."}
        self.assertEqual(expected_data, response.data)
        response = self.client.get(
            reverse("currency-detail", kwargs={"currency": "usd"}), format="json"
        )
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    # convert ----------------------
    def test_convert_ok_cross_course(self):
        usd = float(
            self.client.get(
                reverse("currency-detail", kwargs={"currency": "usd"}), format="json"
            ).data["rate"]
        )
        tryy = float(
            self.client.get(
                reverse("currency-detail", kwargs={"currency": "try"}), format="json"
            ).data["rate"]
        )
        response = self.client.post(
            reverse("currency-convert"),
            data={"from_currency": "USD", "to_currency": "TRY", "amount": 20},
            format="json",
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)
        result = "%.7f" % float(tryy / usd * 20)
        self.assertEqual(result, response.data.get("result"))

    def test_convert_ok_also_with_some_kind_of_values(self):
        usd = float(
            self.client.get(
                reverse("currency-detail", kwargs={"currency": "usd"}), format="json"
            ).data["rate"]
        )
        tryy = float(
            self.client.get(
                reverse("currency-detail", kwargs={"currency": "try"}), format="json"
            ).data["rate"]
        )
        response = self.client.post(
            reverse("currency-convert"),
            data={
                "test": 123,
                "kdsa": 1232,
                "12e": "das",
                "from_currency": "USD",
                "to_currency": "TRY",
                "amount": 20,
            },
            format="json",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        result = "%.7f" % float(tryy / usd * 20)
        self.assertEqual(result, response.data.get("result"))

    def test_convert_identical_currencies(self):
        response = self.client.post(
            reverse("currency-convert"),
            data={"from_currency": "USD", "to_currency": "USD", "amount": 100},
            format="json",
        )
        self.assertEqual(
            status.HTTP_400_BAD_REQUEST, response.status_code, response.content
        )
        expected_data = {
            "response": [
                ErrorDetail(string="Нельзя указывать одинаковые валюты", code="invalid")
            ]
        }
        self.assertEqual(expected_data, response.data)

    def test_convert_from_eur(self):
        usd = float(
            self.client.get(
                reverse("currency-detail", kwargs={"currency": "usd"}), format="json"
            ).data["rate"]
        )
        response = self.client.post(
            reverse("currency-convert"),
            data={"from_currency": "EUR", "to_currency": "USD", "amount": 100},
            format="json",
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)
        result = "%.7f" % float(usd * 100)
        self.assertEqual(result, response.data.get("result"))

    def test_convert_to_eur(self):
        php = float(
            self.client.get(
                reverse("currency-detail", kwargs={"currency": "php"}), format="json"
            ).data["rate"]
        )
        response = self.client.post(
            reverse("currency-convert"),
            data={"from_currency": "PHP", "to_currency": "EUR", "amount": 2},
            format="json",
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        result = "%.7f" % (2 / php)
        self.assertEqual(result, response.data.get("result"))

    def test_check_required_values(self):
        response = self.client.post(
            reverse("currency-convert"),
            data={"test": 123, "kdsa": 1232, "12e": "das"},
            format="json",
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        expected_data = {
            "from_currency": [
                ErrorDetail(string="This field is required.", code="required")
            ],
            "to_currency": [
                ErrorDetail(string="This field is required.", code="required")
            ],
            "amount": [ErrorDetail(string="This field is required.", code="required")],
        }
        self.assertEqual(expected_data, response.data, response.content)





class CurrencyCalcTestCase(TestCase):
    def test_html_calc_ok(self):
        response = self.client.get("/calc/")
        self.assertTemplateUsed(response, "calc.html")
        self.assertContains(response, "Calc Currencies")

