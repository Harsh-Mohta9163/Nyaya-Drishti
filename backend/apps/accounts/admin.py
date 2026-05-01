from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("NyayaDrishti", {"fields": ("role", "department", "language")} ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("NyayaDrishti", {"fields": ("email", "role", "department", "language")} ),
    )
    list_display = ("email", "username", "role", "department", "is_staff")
    search_fields = ("email", "username", "department")
