from rest_framework.permissions import SAFE_METHODS
from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Разрешает доступ только аутентифицированным пользователям.
    Неаутентифицированные пользователи могут только читать данные.
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user and request.user.is_authenticated


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_staff)


class IsAdminOnly(BasePermission):
    """Доступ только для администратора."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class ReadOnly(BasePermission):
    """Только для чтения."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsRegisteredBy(BasePermission):
    def has_object_permission(self, request, view, obj):
        user_field_name = getattr(view, 'author_field', None)
        if user_field_name is None:
            return True
        path = user_field_name.split('__')
        for user_field_name in path:
            obj = getattr(obj, user_field_name)
        return obj == request.user.id


class OwnerOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
