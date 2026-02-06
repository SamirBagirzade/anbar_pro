from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    filter_horizontal = ("permissions",)
