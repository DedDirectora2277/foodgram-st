from rest_framework.views import (
    exception_handler as drf_exception_handler
)
from rest_framework import status
from django.http import Http404
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
    NotFound
)


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для API.
    Русифицирует стандартные сообщения об ошибках DRF.
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, (NotAuthenticated)):
            custom_data = {
                'detail': 'Учетные данные не'
                'были предоставлены.'
            }
            response.data = custom_data
            response.status_code = status.HTTP_401_UNAUTHORIZED

        elif isinstance(exc, PermissionDenied):
            custom_data = {
                'detail': 'У вас недостаточно прав для '
                'выполнения данного действия.'
            }
            response.data = custom_data
            response.status_code = status.HTTP_403_FORBIDDEN

        elif isinstance(exc, (NotFound, Http404)):
            custom_data = {'detail': 'Страница не найдена.'}
            response.data = custom_data
            response.status_code = status.HTTP_404_NOT_FOUND

    return response
