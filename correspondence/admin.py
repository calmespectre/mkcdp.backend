from django.contrib import admin
from .models import Letter


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ("user", "child", "direction", "subject", "created_at")
    list_filter = ("direction",)
    search_fields = ("user__email", "subject", "body")