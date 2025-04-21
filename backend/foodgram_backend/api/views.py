from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Exists, OuterRef, Sum
from django.views import View

from rest_framework import (
    status, viewsets, permissions, filters
)
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from djoser.views import UserViewSet as DjoserUserViewSet

from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    RecipeIngredient
)
from subscriptions.models import Subscription

from .serializers import (
    RecipeShortSerializer,
    UserSerializer,
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    SubscriptionSerializer
)
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter, IngredientNameSearchFilter
from .utils import (
    encode_base62, decode_base62, generate_shopping_list_content
)


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """
    ViewSet для модели User. Наследуется от Djoser для сохранения
    стандартных эндпоинтов. Добавляет действия для управления аватаром.
    """

    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_permissions(self):
        """
        Возвращает IsAuthenticatedOrReadOnly для list и retrieve,
        а для остальных действий полагается на
        стандартную логику Djoser/DRF.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticatedOrReadOnly()]

        return super().get_permissions()

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[permissions.IsAuthenticated],
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
                user, data=request.data
            )
            serializer.is_valid(raise_exception=True)

            serializer.save()

            response_serializer = AvatarSerializer(
                user, context={'request': request}
            )
            return Response(
                response_serializer.data, status=status.HTTP_200_OK
            )

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """
        Подписывает или отписывает текущего пользователя
        от пользователя по id.
        """

        user = request.user
        author = get_object_or_404(User, id=id)

        if user == author:
            return Response(
                {'detail': 'Вы не можете подписываться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription_exists = Subscription.objects.filter(
            user=user, author=author
        ).exists()

        if request.method == 'POST':
            if subscription_exists:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)

            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not subscription_exists:
                return Response(
                    {
                        'detail':
                        'Вы не были подписаны на этого пользователя'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            deleted_count, _ = Subscription.objects.filter(
                user=user, author=author
            ).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(
            follower__user=user
        ).prefetch_related('recipes')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)


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
    filter_backends = [IngredientNameSearchFilter]
    search_fields = ['^name']


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
        queryset = (
            Recipe.objects
            .select_related('author')
            .prefetch_related('recipe_ingredients__ingredient')
        )
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user,
                                            recipe_id=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects
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
                    {'detail': f'Рецепт уже добавлен в '
                     f'{model._meta.verbose_name_plural}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

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
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[permissions.AllowAny]
    )
    def get_short_link(self, request, pk=None):
        """
        Возвращает абсолютную короткую ссылку для данного рецепта.
        Формат: "http://<домен>/s/<base62_id>/"
        """

        recipe = self.get_object()
        short_id = encode_base62(recipe.id)

        relative_short_path = f'/s/{short_id}/'
        absolute_short_link = request.build_absolute_uri(
            relative_short_path
        )
        return Response(
            {'short-link': absolute_short_link},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """
        Формирует и возвращает текстовый файл со списком покупок
        для текущего пользователя.
        """
        user = request.user

        ingredients_summary = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list_content = generate_shopping_list_content(
            ingredients_summary
        )

        response = HttpResponse(
            shopping_list_content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response


class RecipeShortLinkRedirectView(View):
    """
    View для обработки коротких ссылок
    /s/<short_id>/.
    Декодирует short_id, находит рецепт и редиректит
    на страницу рецепта.
    """

    def get(self, request, short_id=None):
        if short_id is None:
            raise Http404("Короткий идентификатор не предоставлен.")
        try:
            recipe_id = decode_base62(short_id)
        except ValueError:
            raise Http404("Некорректная короткая ссылка.")

        recipe = get_object_or_404(Recipe, pk=recipe_id)

        frontend_recipe_path = f"/recipes/{recipe.id}/"

        absolute_frontend_url = request.build_absolute_uri(
            frontend_recipe_path
        )

        return redirect(absolute_frontend_url)
