# --- Users ---
USER_EMAIL_MAX_LENGTH = 254
USER_USERNAME_MAX_LENGTH = 150
USER_FIRST_NAME_MAX_LENGTH = 150
USER_LAST_NAME_MAX_LENGTH = 150
USERNAME_INVALID_MESSAGE = (
    "Имя пользователя может содержать только буквы (a-z, A-Z, включая "
    "русские), цифры (0-9) и символы @ . + - _"
)
ALLOW_UNICODE_USERNAMES = True

# --- Recipes ---
RECIPE_NAME_MAX_LENGTH = 200
MIN_COOKING_TIME_VALUE = 1
MIN_AMOUNT_VALUE = 1

# --- Ingredients ---
INGREDIENT_NAME_MAX_LENGTH = 200
INGREDIENT_UNIT_MAX_LENGTH = 50

# Лимит списка рецептов в подписках
RECIPES_LIMIT_IN_SUBSCRIPTION_DEFAULT = 3
