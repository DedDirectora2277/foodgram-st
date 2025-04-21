from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart
)


class BaseAdminSettings(admin.ModelAdmin):
    """Общие настройки для админ-панели"""

    empty_value_display = '-пусто-'
    list_per_page = 20


@admin.register(Ingredient)
class IngredientAdmin(BaseAdminSettings):
    """Админ-панель для модели Ingredient"""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    """
    Инлайн для редактирования ингредиентов внутри рецепта.
    Позволяет добавлять/изменять/удалять ингредиенты и их количество.
    """

    model = RecipeIngredient

    fields = ('ingredient', 'amount')
    autocomplete_fields = ('ingredient',)
    extra = 1
    min_num = 1

    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты рецепта'


@admin.register(Recipe)
class RecipeAdmin(BaseAdminSettings):
    """Админ-панель для модели Recipe"""

    list_display = (
        'id', 'name', 'author', 'get_image_preview', 'favorited_count'
    )

    readonly_fields = ('get_image_preview', 'favorited_count')
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name')
    inlines = [RecipeIngredientInline]

    ordering = ('-pub_date',)

    def get_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" with="80" height="50" />', obj.image.url
            )
        return "Нет изображения"

    get_image_preview.short_description = 'Первью изображения'

    def favorited_count(self, obj):
        return obj.favorited_by.count()

    favorited_count.short_description = 'В избранном (раз)'
    favorited_count.admin_order_field = 'favorited_by__count'


@admin.register(Favorite)
class FavoriteAdmin(BaseAdminSettings):
    """Админ-панель для модели Favorite"""

    list_display = ('id', 'user', 'recipe', 'added_date')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
    ordering = ('-added_date',)
    autocomplete_fields = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseAdminSettings):
    """Админ-панель для модели ShoppingCart"""

    list_display = ('id', 'user', 'recipe', 'added_date')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
    ordering = ('-added_date',)
    autocomplete_fields = ('user', 'recipe')
