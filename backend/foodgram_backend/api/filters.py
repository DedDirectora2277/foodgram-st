import django_filters
from recipes.models import Recipe
from rest_framework import filters as rest_filters

from users.models import User


class RecipeFilter(django_filters.rest_framework.FilterSet):
    """
    Фильтры для модели Recipe.
    Позволяет фильтровать по автору, статусу в избранном и списке покупок
    """

    author = django_filters.rest_framework.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='author'
    )
    is_favorited = django_filters.rest_framework.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.rest_framework.BooleanFilter(
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
