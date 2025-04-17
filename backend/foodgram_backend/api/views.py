from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Exists, OuterRef
from rest_framework import status, viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart
)

from .serializers import (
    UserSerializer,
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer
)
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter


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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра ингредиентов.
    Доступен всем ролям пользователей.
    Поддерживает поиск по названию.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name'] # Поиск по началу названия


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления рецептами"""

    queryset = Recipe.objects.all()

    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ['^name']

    def get_queryset(self):
        """
        Аннотирование queryset статусами для авторизованных пользователей
        """
        
        user = self.request.user
        queryset = Recipe.objects.select_related('author')\
            .prefetch_related('recipe_ingredients__ingredient')
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user,
                                            recipe_id=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects\
                        .filter(user=user, recipe_id=OuterRef('pk'))
                )
            )
        return queryset
    
    def get_serializer_class(self, *args, **kwargs):
        """Выбор сериализатора в зависимости от действия"""

        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer
    
    def perform_create(self, serializer):
        """Установка автора при создании рецепта"""
        
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self._manage_user_recipe_relation(request, pk, Favorite)
    
    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self._manage_user_recipe_relation(request, pk,
                                                 ShoppingCart)
    
    def _manage_user_recipe_relation(self, request, pk, model):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        relation_exists = model.objects.filter(
            user=user, recipe=recipe
        ).exists()

        if request.method == 'POST':
            if relation_exists:
                return Response(
                    {'detail': f'Рецепт уже добавлен в'
                     '{model._meta.verbose_name_plural}.'},
                     status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeReadSerializer(recipe, context={
                'request': request
            })
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'DELETE':
            if not relation_exists:
                return Response(
                    {'detail':
                     f'Рецепта нет в {model._meta.verbose_name_plural}.'},
                     status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        return Response(
            {'detail': 'Функионал не разработан'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

