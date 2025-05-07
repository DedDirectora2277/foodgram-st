from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from constants import (
    RECIPE_NAME_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_UNIT_MAX_LENGTH,
    MIN_AMOUNT_VALUE,
    MIN_COOKING_TIME_VALUE
)


User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента"""

    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        db_index=True,
    )

    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=INGREDIENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_unit'
            )
        ]  # Гарантия уникальности пары Название + Ед. измер.

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )

    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=RECIPE_NAME_MAX_LENGTH,
        db_index=True
    )

    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes',
        help_text='Загрузите изображение рецепта'
    )

    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Введите описание рецепта'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(
            MIN_COOKING_TIME_VALUE,
            'Время должно быть не меньше 1 минуты'
        )],
        help_text='Укажите время приготовления в минутах'
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return f'{self.name} (Автор: {self.author.username})'


class RecipeIngredient(models.Model):
    """
    Связывает модель Recipe и Ingredient, добавляя количество.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент'
    )

    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(
            MIN_AMOUNT_VALUE,
            'Количество должно быть не меньше 1'
        )],
        help_text='Укажите количество ингредиента'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit} '
                f'для "{self.recipe.name}"')


class UserRecipeRelationBase(models.Model):
    """Абстрактная базовая модель для Favorite и ShoppingCart"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    added_date = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ['-added_date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(app_label)s_%(class)s_unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Favorite(UserRecipeRelationBase):
    """Модель для избранных рецептов пользователя"""

    class Meta(UserRecipeRelationBase.Meta):
        default_related_name = 'favorited_by'
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(UserRecipeRelationBase):
    """Модель для рецептов в списке покупок пользователя"""

    class Meta(UserRecipeRelationBase.Meta):
        default_related_name = 'in_shopping_cart'
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
