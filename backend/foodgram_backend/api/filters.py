from django_filters import rest_framework as filters
from recipes.models import Recipe
from rest_framework import filters as rest_filters


class RecipeFilter(filters.FilterSet):
    """
    Фильтры для модели Recipe.
    Позволяет фильтровать по автору, статусу в избранном и списке покупок
    """

    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset


class IngredientNameSearchFilter(rest_filters.SearchFilter):
    """
    Кастомный SearchFilter, который использует GET-параметр 'name'
    вместо стандартного 'search'.
    """
    search_param = "name"
