from django.urls import path
from . import views

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Authentication
    path("register/", views.register, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),

    # Dashboard & Profile
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),

    # Tournaments
    path("tournament/<int:tournament_id>/", views.tournament_detail, name="tournament_detail"),
    path("join/<int:tournament_id>/", views.join_tournament, name="join_tournament"),
    path("my-tournaments/", views.my_tournaments, name="my_tournaments"),

    # Teams
    path("teams/", views.team_list, name="team_list"),
    path("teams/create/", views.create_team, name="create_team"),
    path("teams/generate-ai-crest/", views.generate_ai_crest, name="generate_ai_crest"),
    path("teams/<int:team_id>/", views.team_detail, name="team_detail"),
    path("teams/<int:team_id>/join/", views.join_team, name="join_team"),
    path("teams/<int:team_id>/leave/", views.leave_team, name="leave_team"),

    # Leaderboard & Matches
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("match-schedule/", views.match_schedule, name="match_schedule"),
    path("matches/", views.match_list, name="match_list"),
]
