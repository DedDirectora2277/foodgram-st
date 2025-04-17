from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet

from .serializers import UserSerializer, AvatarSerializer


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """
    ViewSet для модели User. Наследуется от Djoser для сохранения
    стандартных эндпоинтов. Добавляет действия для управления аватаром.
    """

    serializer_class = UserSerializer

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
        parser_classes=[JSONParser]
    )
    def avatar(self, request, *args, **kwargs):
        """
        PUT - загрузка аватара через Base64.
        DELETE - удаление аватара.
        """

        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)

            serializer.save()

            response_serializer = self.get_serializer(user)
            return Response(
                response_serializer.data, status=status.HTTP_200_OK
            )
        
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)

            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
