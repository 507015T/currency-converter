from django.contrib import admin
from currency.models import Currency

# Register your models here.
@admin.register(Currency)
class ChatAdmin(admin.ModelAdmin): ...
