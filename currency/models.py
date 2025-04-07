from django.db import models


class Currency(models.Model):
    currency_name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=15, decimal_places=7)
    actual_date = models.DateField()
    is_deleted = models.BooleanField(default=False)
    is_modified = models.BooleanField(default=False)

    def __str__(self):
        return self.currency_name
