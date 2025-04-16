from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer
)


User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Сериализатор для создания пользователей.
    Использует все обязательные поля из модели User.
    """

    class Meta(BaseUserCreateSerializer.Meta):
        model = User

        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class UserSerializer(BaseUserSerializer):
    """
    Сериализатор для отображения данных пользователей.
    Включает поле is_subscribed для проверки 
    подписки текущего пользователя.
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
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

        # Если нет запроса или если пользователь анонимный, то не подписан
        if request is None or not request.user.is_authenticated:
            return False

        # Пользователь не может быть подписан сам на себя
        if request.user == obj:
            return False

        # return obj.follower.filter(user=request.user).exists

        print(f'Проверка подписки {request.user} на {obj}. Заглушка!')

        return False
