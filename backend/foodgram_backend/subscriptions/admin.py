from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для модели Subscription"""

    list_display = ('id', 'user', 'author', 'created_date')
    search_fields = ('user__username', 'author__username')
    list_filter = ('created_date',)
    ordering = ('-created_date',)

    autocomplete_fields = ('user', 'author')
