from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsStaffOrSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))

class ReadOnlyOrStaff(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))

class IsSafeguardingOfficer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.groups.filter(name="safeguarding").exists()))