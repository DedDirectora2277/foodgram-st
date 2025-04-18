from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    IngredientViewSet,
    RecipeViewSet,
)


router_v1 = DefaultRouter()

router_v1.register(
    r'users',
    UserViewSet,
    basename='users'
)

router_v1.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients'
)

router_v1.register(
    r'recipes',
    RecipeViewSet,
    basename='recipes'
)

urlpatterns = [
    path('', include(router_v1.urls)),

]
