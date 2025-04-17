from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet


router_v1 = DefaultRouter()

router_v1.register(
    r'users',
    UserViewSet,
    basename='users'
)


urlpatterns = [
    path('', include(router_v1.urls))
]
