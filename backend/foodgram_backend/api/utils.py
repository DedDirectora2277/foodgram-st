import string
import base64


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
