from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from currency.models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    currency_name = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    deleted_date = serializers.ReadOnlyField()
    is_modified = serializers.ReadOnlyField()

    def update(self, instance, validated_data):
        validated_data["is_modified"] = True
        return super().update(instance, validated_data)

    class Meta:
        model = Currency
        fields = "__all__"


class CurrencyConvertSerializer(serializers.Serializer):
    from_currency = serializers.ChoiceField(choices=[], required=True)
    to_currency = serializers.ChoiceField(choices=[], required=True)
    amount = serializers.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            currencies = list(
                Currency.objects.values_list("currency_name", flat=True)
            ) + ["EUR"]
            choices = [(c, c) for c in currencies]
            self.fields["from_currency"].choices = choices
            self.fields["to_currency"].choices = choices
        except:
            self.fields["from_currency"].choices = []
            self.fields["to_currency"].choices = []

    def validate(self, attrs):
        if attrs.get("from_currency") == attrs.get("to_currency"):
            raise ValidationError({"response": "Нельзя указывать одинаковые валюты"})
        if attrs["from_currency"] != "EUR":
            attrs["from_currency"] = Currency.objects.get(
                currency_name=attrs["from_currency"]
            )
        if attrs["to_currency"] != "EUR":
            attrs["to_currency"] = Currency.objects.get(
                currency_name=attrs["to_currency"]
            )
        return attrs

    def to_representation(self, instance):
        from_currency = instance.get("from_currency")
        to_currency = instance.get("to_currency")
        amount = instance.get("amount")
        if from_currency == "EUR":
            return {"result": "%.7f" % float(to_currency.rate * amount)}
        if to_currency == "EUR":
            return {"result": "%.7f" % float(amount / from_currency.rate)}
        return {
            "result": "%.7f" % float(to_currency.rate / from_currency.rate * amount)
        }

    class Meta:
        fields = "__all__"
