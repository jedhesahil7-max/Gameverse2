from django.contrib import admin
from .models import Tournament, Registration, Team, TournamentResult, Match

admin.site.site_header = "🎮 GameVerse Admin"
admin.site.site_title = "GameVerse Management"
admin.site.index_title = "Esports & Community Control Hub"


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "game",
        "prize_pool",
        "date",
        "mode",
        "max_players",
        "registered_count",
        "is_active",
    )
    list_filter = ("game", "is_active", "mode", "date")
    search_fields = ("title", "game", "description")
    list_editable = ("is_active",)
    ordering = ["date", "title"]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "tournament", "joined_at")
    list_filter = ("tournament", "joined_at")
    search_fields = ("user__username", "user__email", "tournament__title")
    ordering = ["-joined_at"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "game", "captain", "member_count", "created_at")
    list_filter = ("game", "created_at")
    search_fields = ("name", "game", "captain__username")
    filter_horizontal = ("members",)
    ordering = ["-created_at"]


@admin.register(TournamentResult)
class TournamentResultAdmin(admin.ModelAdmin):
    list_display = ("tournament", "player", "position", "points", "created_at")
    list_filter = ("tournament", "position")
    search_fields = ("player__username", "tournament__title")
    ordering = ["tournament", "position"]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "tournament",
        "round_name",
        "team1_display",
        "team2_display",
        "match_date",
        "winner_display",
    )
    list_filter = ("tournament", "round_name", "match_date")
    search_fields = ("team1", "team2", "tournament__title", "winner", "round_name")
    ordering = ["match_date"]
