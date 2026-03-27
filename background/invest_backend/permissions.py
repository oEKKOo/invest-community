from rest_framework.permissions import BasePermission


class IsModeratorOrAdmin(BasePermission):
    """允许 MODERATOR/ADMIN 访问"""
    message = '无权限'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in ['MODERATOR', 'ADMIN'])


class IsAdminOnly(BasePermission):
    """仅允许 ADMIN 访问"""
    message = '仅管理员可访问'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == 'ADMIN')
