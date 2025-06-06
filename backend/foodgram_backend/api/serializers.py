from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from drf_extra_fields.fields import Base64ImageField

from constants import (
    RECIPES_LIMIT_IN_SUBSCRIPTION_DEFAULT,
    MIN_COOKING_TIME_VALUE,
    MIN_AMOUNT_VALUE
)

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)

from subscriptions.models import Subscription


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения данных пользователей.
    Включает поле is_subscribed для проверки
    подписки текущего пользователя.
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta():
        model = User

        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь (из запроса)
        на пользователя `obj` (профиль которого просматривается)
        """

        request = self.context.get('request')

        if request is None or not request.user.is_authenticated:
            return False

        if request.user == obj:
            return False

        return obj.follower.filter(user=request.user).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления аватара пользователя через Base64 JSON.
    """

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User

        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализацтор модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения ингредиентов в рецепте.
    Показывает id, name, measurement_unit из связанной модели
    Ingredient и amount из модели RecipeIngredient
    """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов"""

    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, read_only=True, source='recipe_ingredients'
    )

    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(
        read_only=True
    )
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def _get_user_recipe_relation(self, obj, related_model):
        """Вспомогательный метод для проверки связи User-Recipe"""

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return related_model.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_favorited(self, obj):
        """
        Проверяет, добавлен ли рецепт в избранное для текущего
        пользователя
        """

        return self._get_user_recipe_relation(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяет, добавлен ли рецепт в список покупок текущего
        пользователя
        """

        return self._get_user_recipe_relation(obj, ShoppingCart)


class IngredientAmountWriteSerializer(serializers.Serializer):
    """
    Сериализатор для приёма id ингредиента и его количества
    при создании/обновлении рецепта.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT_VALUE,
        error_messages={'min_value': 'Количество должно быть не меньше 1'}
    )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов"""

    ingredients = IngredientAmountWriteSerializer(many=True,
                                                  required=True)
    image = Base64ImageField(required=True, allow_null=False)
    author = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, ingredients):
        """Проверяем, что ингредиенты указаны и не дублируются"""

        if not ingredients:
            raise serializers.ValidationError(
                'Нужно указать хотя бы один ингредиент.'
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты в рецепте не должны повторяться.'
            )

        for item in ingredients:
            if item['amount'] < MIN_AMOUNT_VALUE:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть не меньше 1.'
                )

        return ingredients

    def validate_cooking_time(self, value):
        """Проверяем, что время приготовления положительное"""

        if value < MIN_COOKING_TIME_VALUE:
            raise serializers.ValidationError(
                'Время приготовления должно быть не меньше 1 минуты.'
            )
        return value

    def _create_ingredients(self, recipe, ingredients_data):
        """
        Вспомогательный метод для создания связей Recipe-Ingredient
        """

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_item['id'],
                amount=ingredient_item['amount']
            ) for ingredient_item in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        """Создает новый рецепт и его ингредиенты"""

        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет существующий рецепт и его ингредиенты"""

        ingredients_data = validated_data.pop('ingredients', None)
        recipe = super().update(instance, validated_data)

        if ingredients_data is not None:
            recipe.recipe_ingredients.all().delete()
            self._create_ingredients(recipe, ingredients_data)

        return recipe

    def validate(self, data):
        instance = getattr(self, 'instance', None)

        if instance and 'ingredients' not in data:
            raise serializers.ValidationError(
                "Поле 'ingredients' обязательно при обновлении рецепта."
            )

        return data

    def to_representation(self, instance):
        """При ответе используем сериализатор для чтения"""
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для рецепта (для списка подписок)"""

    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionSerializer(UserSerializer):
    """
    Сериализатор для отображения авторов, на которых подписан пользователь.
    Наследуется от UserSerializer, добавляет кол-во рецептов и их
    сокращенный список
    """

    is_subscribed = serializers.BooleanField(default=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')
        read_only_fields = fields

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов автора."""

        return obj.recipes.count()

    def get_recipes(self, obj):
        """Возвращает краткий список рецептов"""

        request = self.context.get('request')

        default_limit = RECIPES_LIMIT_IN_SUBSCRIPTION_DEFAULT
        limit_str = request.query_params.get('recipes_limit',
                                             default_limit)
        try:
            limit = int(limit_str)
            if limit < 0:
                limit = 0
        except (ValueError, TypeError):
            limit = default_limit

        recipes_queryset = obj.recipes.all()[:limit]
        serializer = RecipeShortSerializer(
            recipes_queryset, many=True, context=self.context
        )
        return serializer.data


class SubscriptionCreateDeleteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания подписки.
    Поле 'user' устанавливается автоматически из текущего
    запроса.
    Поле 'author' должно быть передано в параметрах запроса.
    """

    user = serializers.HiddenField(default=CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate_author(self, value):
        request_user = self.context['request'].user
        if request_user == value:
            raise serializers.ValidationError(
                'Вы не можете подписываться на самого себя.'
            )
        return value

    def validate(self, data):
        """
        Проверка того, что подписка ещё не существует при создании,
        или существует при удалении
        """

        request = self.context.get('request')
        user = data['user']
        author = data['author']

        http_method = request.method
        subscription_exists = Subscription.objects.filter(
            user=user, author=author
        ).exists()

        if http_method == 'POST':
            if subscription_exists:
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого пользователя.'
                )
        elif http_method == 'DELETE':
            if not subscription_exists:
                raise serializers.ValidationError(
                    'Вы не были подписаны на этого пользователя'
                )

        return data


class UserRecipeRelationSerializer(serializers.Serializer):
    """
    Сериализатор для валидации данных перед созданием или удалением
    связи User-Recipe (Favorite, ShoppingCart).
    """

    def validate(self, attrs):
        request = self.context.get('request')
        view = self.context.get('view')
        model_class = self.context.get('model_class')

        if not all([request, view, model_class]):
            raise serializers.ValidationError(
                'Нужен контекст запроса, представления и model_class'
            )

        current_user = request.user
        recipe_id_from_url = view.kwargs.get('pk')

        if recipe_id_from_url is None:
            raise serializers.ValidationError(
                "ID рецепта не указан в URL."
            )

        try:
            recipe_to_interact_with = Recipe.objects.get(
                pk=recipe_id_from_url
            )
        except Recipe.DoesNotExist:
            raise serializers.ValidationError(
                "Рецепт с таким ID не найден."
            )

        http_method = request.method
        relation_exists = model_class.objects.filter(
            user=current_user, recipe=recipe_to_interact_with
        ).exists()

        verbose_name_plural = (
            model_class._meta.verbose_name_plural.lower()
        )

        if http_method == 'POST':
            if relation_exists:
                raise serializers.ValidationError(
                    f'Рецепт уже добавлен в {verbose_name_plural}'
                )
        elif http_method == 'DELETE':
            if not relation_exists:
                raise serializers.ValidationError(
                    f'Этого рецепта нет в {verbose_name_plural}'
                )

        return {
            'user': current_user,
            'recipe': recipe_to_interact_with,
            'model_class': model_class
        }
