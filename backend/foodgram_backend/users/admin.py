from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Кастомизация панели администратора для модели User.
    """

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
    )

    search_fields = ('username', 'email')

    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'email', 'avatar')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name',
                       'last_name', 'avatar', 'is_staff',
                       'is_superuser', 'groups',
                       'user_permissions'),
        }),
    )
