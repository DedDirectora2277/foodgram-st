from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator

from constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
    USER_USERNAME_MAX_LENGTH,
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
    username_validator = UnicodeUsernameValidator

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
