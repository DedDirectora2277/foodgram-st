import string


BASE62_ALPHABET = string.digits + string.ascii_letters
BASE = len(BASE62_ALPHABET)


def encode_base62(number):
    """Кодирует положительное целое число в строку Base62"""

    if not isinstance(number, int) or number < 0:
        raise ValueError('Число должно быть неотрицательным целым.')
    if number == 0:
        return BASE62_ALPHABET[0]

    encoded = ''
    while number > 0:
        number, remainder = divmod(number, BASE)
        encoded = BASE62_ALPHABET[remainder] + encoded
    return encoded


def decode_base62(encoded_str):
    """Декодирует строку Base62 в целое число"""

    decoded = 0
    length = len(encoded_str)
    for i, char in enumerate(encoded_str):
        power = length - (i + 1)
        try:
            index = BASE62_ALPHABET.index(char)
        except ValueError:
            raise ValueError(
                f'Недопустимый символ "{char}" в строке Base62'
            )
        decoded += index * (BASE ** power)

    return decoded


def generate_shopping_list_content(ingredients_queryset):
    """
    Генерирует текстовое содержимое для файла списка покупок.
    Принимает queryset с агрегированными данными ингредиентов.
    Queryset должен содержать словари с ключами:
    'ingredient__name', 'ingredient__measurement_unit', 'total_amount'.
    """

    shopping_list_parts = ['Список покупок:\n']

    if not ingredients_queryset:
        shopping_list_parts.append('Ваш список пуст.')
    else:
        for item in ingredients_queryset:
            name = item.get('ingredient__name', 'Без названия')
            unit = item.get('ingredient__measurement_unit', 'шт.')
            total_amount = item.get('total_amount', 0)
            shopping_list_parts.append(
                f'\n- {name} ({unit}) — {total_amount}'
            )
    return "".join(shopping_list_parts)
