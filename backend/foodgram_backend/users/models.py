import re
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

from constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
    USER_USERNAME_MAX_LENGTH,
    USERNAME_INVALID_MESSAGE,
    ALLOW_UNICODE_USERNAMES
)


validate_username_regex = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message=USERNAME_INVALID_MESSAGE,
    flags=re.ASCII if not ALLOW_UNICODE_USERNAMES else 0
)


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Наследует все поля AbstractUser.
    Переопределяет поле email, чтобы сделать его обязательным.
    Переопределяет поля AbstractUser для их перевода.
    Добавляет поле avatar.
    """

    # Валидатор используется ниже для username
    username_validator = validate_username_regex

    # Переопределение поля email, чтобы сделать его уникальным
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True,
        max_length=USER_EMAIL_MAX_LENGTH
    )

    # Переопределение username
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=USER_USERNAME_MAX_LENGTH,
        unique=True,
        help_text=(
            'Обязательное поле. Не более 150 символов. '
            'Только буквы, цифры и символы @/./+/-/_'
        ),
        validators=[username_validator],
        error_messages={
            'unique': (
                'Пользователь с таким именем пользователя '
                'уже существует'
            )
        }
    )

    # Переопределение first_name
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=USER_FIRST_NAME_MAX_LENGTH
    )

    # Переопределение last_name
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=USER_LAST_NAME_MAX_LENGTH
    )

    # Переопределение is_staff
    is_staff = models.BooleanField(
        verbose_name='Статус персонала',
        default=False,
        help_text=(
            'Определяет, имеет ли пользователь доступ '
            'к панели администратора'
        )
    )

    # Переопределение is_active
    is_active = models.BooleanField(
        verbose_name='Активный',
        default=True,
        help_text=(
            'Определяет, следует ли считать этого пользователя активным.\n'
            'Снимите этот флажок вместо удаления учетной записи.'
        )
    )

    # Переопределение is_superuser
    is_superuser = models.BooleanField(
        verbose_name='Статус администратора',
        default=False,
        help_text=(
            'Определяет, что пользователь имеет все права '
            'без явного их назначения.'
        )
    )

    # Определение поля для аватара
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='Загрузите ваш аватар'
    )

    # Для аутентификации используется поле, указанное ниже
    USERNAME_FIELD = 'email'

    # Обязательные поля для регистрации
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username
