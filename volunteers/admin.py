from django.contrib import admin
from .models import Opportunity, VolunteerApplication

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "org", "location", "commitment", "published", "archived", "created_at")
    list_filter = ("published", "archived")
    search_fields = ("code", "title", "org", "location")

@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "opportunity", "availability", "status", "created_at")
    list_filter = ("status", "opportunity")
    search_fields = ("full_name", "phone", "email")