import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    Поле DRF для обработки изображений, закодированных в Base64
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')

                ext = format.split('/')[-1]

                filename = f'{uuid.uuid4()}.{ext}'

                decoded_file = base64.b64decode(imgstr)
            except (ValueError, TypeError, base64.binascii.Error) as e:
                raise serializers.ValidationError(
                    'Некорректный формат Base64 изображения'
                ) from e

            data = ContentFile(decoded_file, name=filename)

        return super().to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None

        request = self.context.get('request', None)

        if request is not None:
            return request.build_absolute_uri(value.url)
        return value.url
