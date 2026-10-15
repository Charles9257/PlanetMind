from django.contrib import admin

from .models import Organization, TeamMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "organization", "role", "created_at")
    list_filter = ("role", "organization")
