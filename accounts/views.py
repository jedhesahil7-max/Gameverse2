import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Tournament, Registration, Team, Match, TournamentResult
from .forms import UserRegisterForm, UserLoginForm, TeamForm
from .ai_generator import generate_esports_crest


# =====================================================
# RANKING HELPERS
# =====================================================

def _get_rank_info(points):
    """Return (rank_name, rank_color, next_tier_points, progress_pct) for a points value."""
    TIERS = [
        (0,    "Unranked",  "secondary", 1,    0),
        (1,    "Bronze",    "bronze",    500,  1),
        (500,  "Silver",    "silver",    1000, 500),
        (1000, "Gold",      "gold",      2500, 1000),
        (2500, "Diamond",   "cyan",      5000, 2500),
        (5000, "Champion",  "purple",    None, 5000),
    ]
    for min_pts, name, color, next_pts, tier_start in reversed(TIERS):
        if points >= min_pts:
            if next_pts is None:
                progress = 100
            else:
                span = next_pts - tier_start
                progress = int(min(((points - tier_start) / span) * 100, 100))
            return {
                "rank": name,
                "rank_color": color,
                "next_tier": next_pts,
                "rank_progress": progress,
            }
    return {"rank": "Unranked", "rank_color": "secondary", "next_tier": 1, "rank_progress": 0}


def _calc_user_stats(user):
    """Return dict of stats for a given user (points from results only, wins, placements)."""
    results = TournamentResult.objects.filter(player=user)
    points = results.aggregate(total=Sum("points"))["total"] or 0
    wins   = results.filter(position=1).count()
    top3   = results.filter(position__lte=3).count()
    played = results.count()
    tournaments_joined = Registration.objects.filter(user=user).count()
    return {
        "points": points,
        "wins": wins,
        "top3": top3,
        "matches_played": played,
        "total_joined": tournaments_joined,
        **_get_rank_info(points),
    }


# =====================================================
# HOME
# =====================================================

def home(request):
    search_query = request.GET.get("search", "").strip()
    game_filter = request.GET.get("game", "").strip()

    tournaments = Tournament.objects.filter(is_active=True)

    if search_query:
        tournaments = tournaments.filter(
            Q(title__icontains=search_query) |
            Q(game__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if game_filter:
        tournaments = tournaments.filter(game__iexact=game_filter)

    return render(
        request,
        "accounts/home.html",
        {
            "tournaments": tournaments,
            "search_query": search_query,
            "game_filter": game_filter,
            "game_choices": Tournament.GAME_CHOICES,
        }
    )


# =====================================================
# AUTHENTICATION: REGISTER
# =====================================================

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to GameVerse, {user.username}! Your gamer profile has been created.")
            return redirect("dashboard")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = UserRegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )


# =====================================================
# AUTHENTICATION: LOGIN
# =====================================================

def login_user(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                
                next_url = request.GET.get("next") or request.POST.get("next")
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password. Please try again.")
        else:
            messages.error(request, "Please fill in all required fields.")
    else:
        form = UserLoginForm()

    return render(
        request,
        "accounts/login.html",
        {"form": form}
    )


# =====================================================
# AUTHENTICATION: LOGOUT
# =====================================================

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully. See you in the next match!")
    return redirect("home")


# =====================================================
# DASHBOARD
# =====================================================

@login_required
def dashboard(request):
    stats = _calc_user_stats(request.user)

    user_teams = Team.objects.filter(members=request.user)

    recent_tournaments = (
        Registration.objects.filter(user=request.user)
        .select_related("tournament")
        .order_by("-joined_at")[:4]
    )

    user_tournament_ids = Registration.objects.filter(
        user=request.user
    ).values_list("tournament_id", flat=True)

    upcoming_matches = (
        Match.objects.filter(tournament_id__in=user_tournament_ids)
        .select_related("tournament")
        .order_by("match_date")[:3]
    )

    # Recent placement results
    recent_results = (
        TournamentResult.objects.filter(player=request.user)
        .select_related("tournament")
        .order_by("-created_at")[:5]
    )

    return render(
        request,
        "accounts/dashboard.html",
        {
            **stats,
            "teams": user_teams,
            "recent_tournaments": recent_tournaments,
            "upcoming_matches": upcoming_matches,
            "recent_results": recent_results,
        }
    )


# =====================================================
# USER PROFILE
# =====================================================

@login_required
def profile(request):
    registrations = (
        Registration.objects.filter(user=request.user)
        .select_related("tournament")
        .order_by("-joined_at")
    )
    stats = _calc_user_stats(request.user)
    teams = Team.objects.filter(members=request.user).prefetch_related("members")

    achievements = []
    if stats["total_joined"] >= 1:
        achievements.append({"icon": "🏆", "title": "First Tournament", "desc": "Entered your first competitive tournament"})
    if stats["total_joined"] >= 5:
        achievements.append({"icon": "🔥", "title": "Tournament Veteran", "desc": "Joined 5 or more tournaments"})
    if teams.count() >= 1:
        achievements.append({"icon": "👥", "title": "Squad Leader", "desc": "Joined or founded a competitive team"})
    if stats["wins"] >= 1:
        achievements.append({"icon": "🥇", "title": "Winner", "desc": "Finished 1st place in a tournament"})
    if stats["wins"] >= 3:
        achievements.append({"icon": "👑", "title": "Triple Champion", "desc": "Won 3 or more tournaments"})
    if stats["points"] >= 1000:
        achievements.append({"icon": "💎", "title": "Gold Legend", "desc": "Reached Gold league with 1000+ points"})
    if stats["points"] >= 2500:
        achievements.append({"icon": "⚡", "title": "Diamond Elite", "desc": "Reached Diamond league with 2500+ points"})
    if stats["points"] >= 5000:
        achievements.append({"icon": "🏅", "title": "Champion", "desc": "Reached the pinnacle — Champion tier!"})

    return render(
        request,
        "accounts/profile.html",
        {
            **stats,
            "tournaments_joined": stats["total_joined"],
            "teams_joined": teams.count(),
            "teams": teams,
            "achievements": achievements,
            "registrations": registrations,
        }
    )


# =====================================================
# TOURNAMENT DETAIL
# =====================================================

def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    participants = tournament.registered_count
    is_full = tournament.is_full

    joined = False
    if request.user.is_authenticated:
        joined = Registration.objects.filter(
            user=request.user,
            tournament=tournament
        ).exists()

    tournament_matches = Match.objects.filter(
        tournament=tournament
    ).order_by("match_date")

    results = TournamentResult.objects.filter(
        tournament=tournament
    ).select_related("player").order_by("position")

    return render(
        request,
        "accounts/tournament_detail.html",
        {
            "tournament": tournament,
            "participants": participants,
            "joined": joined,
            "is_full": is_full,
            "matches": tournament_matches,
            "results": results,
        }
    )


# =====================================================
# JOIN TOURNAMENT
# =====================================================

@login_required
def join_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    # 1. Check if active
    if not tournament.is_active:
        messages.error(request, f"Registration for '{tournament.title}' is currently closed.")
        return redirect("tournament_detail", tournament_id=tournament.id)

    # 2. Check if user already joined
    existing = Registration.objects.filter(user=request.user, tournament=tournament).first()
    if existing:
        messages.warning(request, f"You are already registered for '{tournament.title}'.")
        return redirect("my_tournaments")

    # 3. Check capacity
    if tournament.is_full:
        messages.error(request, f"'{tournament.title}' has reached its maximum capacity of {tournament.max_players} players.")
        return redirect("tournament_detail", tournament_id=tournament.id)

    # 4. Create registration
    Registration.objects.create(user=request.user, tournament=tournament)
    messages.success(request, f"🎉 You have successfully registered for {tournament.title}! Get ready to compete!")
    return redirect("my_tournaments")


# =====================================================
# MY TOURNAMENTS
# =====================================================

@login_required
def my_tournaments(request):
    registrations = (
        Registration.objects.filter(user=request.user)
        .select_related("tournament")
        .order_by("-joined_at")
    )

    return render(
        request,
        "accounts/my_tournaments.html",
        {"registrations": registrations}
    )


# =====================================================
# TEAMS: LIST
# =====================================================

def team_list(request):
    search_query = request.GET.get("search", "").strip()
    teams = Team.objects.all().prefetch_related("members", "captain")

    if search_query:
        teams = teams.filter(
            Q(name__icontains=search_query) |
            Q(game__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    return render(
        request,
        "accounts/team_list.html",
        {
            "teams": teams,
            "search_query": search_query,
        }
    )


# =====================================================
# TEAMS: CREATE & AI CREST GENERATOR
# =====================================================

@login_required
def generate_ai_crest(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required"}, status=405)

    try:
        if request.content_type == "application/json":
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = request.POST

        team_name = data.get("team_name", "SQUAD").strip() or "SQUAD"
        theme = data.get("theme", "cyan").strip().lower()
        mascot = data.get("mascot", "wolf").strip().lower()
        prompt = data.get("prompt", "").strip()

        result = generate_esports_crest(
            team_name=team_name,
            theme_name=theme,
            mascot_type=mascot,
            prompt=prompt
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def create_team(request):
    if request.method == "POST":
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            team = form.save(commit=False)
            team.captain = request.user

            # If user generated an AI logo and did not upload a separate file
            ai_logo_path = request.POST.get("ai_logo_path", "").strip()
            if not team.logo and ai_logo_path:
                team.logo = ai_logo_path

            team.save()
            team.members.add(request.user)
            messages.success(request, f"Squad '{team.name}' created successfully!")
            return redirect("team_detail", team_id=team.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = TeamForm()

    return render(
        request,
        "accounts/create_team.html",
        {"form": form}
    )


# =====================================================
# TEAMS: DETAIL
# =====================================================

def team_detail(request, team_id):
    team = get_object_or_404(
        Team.objects.prefetch_related("members", "captain"),
        id=team_id
    )

    is_member = False
    is_captain = False
    if request.user.is_authenticated:
        is_member = team.members.filter(id=request.user.id).exists()
        is_captain = (team.captain == request.user)

    # Fixtures involving this team
    team_matches = Match.objects.filter(
        Q(team1=str(team.id)) |
        Q(team2=str(team.id)) |
        Q(team1__iexact=team.name) |
        Q(team2__iexact=team.name)
    ).select_related("tournament").order_by("match_date")

    return render(
        request,
        "accounts/team_detail.html",
        {
            "team": team,
            "is_member": is_member,
            "is_captain": is_captain,
            "team_matches": team_matches,
        }
    )


# =====================================================
# TEAMS: JOIN
# =====================================================

@login_required
def join_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)

    if team.members.filter(id=request.user.id).exists():
        messages.warning(request, f"You are already a member of {team.name}.")
    else:
        team.members.add(request.user)
        messages.success(request, f"Welcome aboard! You have joined {team.name}!")

    return redirect("team_detail", team_id=team.id)


# =====================================================
# TEAMS: LEAVE
# =====================================================

@login_required
def leave_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)

    if team.captain == request.user:
        messages.warning(request, "As captain, you cannot leave your own squad. You can manage or disband the team from admin.")
        return redirect("team_detail", team_id=team.id)

    if team.members.filter(id=request.user.id).exists():
        team.members.remove(request.user)
        messages.success(request, f"You have left squad {team.name}.")
    else:
        messages.info(request, "You are not a member of this squad.")

    return redirect("team_list")


# =====================================================
# LEADERBOARD
# =====================================================

def leaderboard(request):
    users = User.objects.all()
    leaderboard_data = []

    for user in users:
        stats = _calc_user_stats(user)
        leaderboard_data.append({
            "username": user.username,
            "tournaments_joined": stats["total_joined"],
            "points": stats["points"],
            "wins": stats["wins"],
            "matches_played": stats["matches_played"],
            "rank_tier": stats["rank"],
        })

    # Sort descending by points, then wins, then tournaments joined
    leaderboard_data.sort(
        key=lambda x: (x["points"], x["wins"], x["tournaments_joined"]),
        reverse=True,
    )

    for index, player in enumerate(leaderboard_data, start=1):
        player["rank"] = index

    return render(
        request,
        "accounts/leaderboard.html",
        {"leaderboard": leaderboard_data}
    )


# =====================================================
# MATCH SCHEDULE & LIST
# =====================================================

def match_schedule(request):
    matches = Match.objects.select_related("tournament").order_by("match_date")
    return render(
        request,
        "accounts/match_schedule.html",
        {"matches": matches}
    )


def match_list(request):
    search_query = request.GET.get("search", "").strip()
    matches = Match.objects.select_related("tournament").order_by("-match_date")

    if search_query:
        matches = matches.filter(
            Q(team1__icontains=search_query) |
            Q(team2__icontains=search_query) |
            Q(tournament__title__icontains=search_query) |
            Q(round_name__icontains=search_query)
        )

    return render(
        request,
        "accounts/match_list.html",
        {
            "matches": matches,
            "search_query": search_query,
        }
    )
