from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import Tournament, Registration, Team, Match, TournamentResult


class GameVerseBackendTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="gamer1",
            email="gamer1@example.com",
            password="Password123!"
        )
        self.other_user = User.objects.create_user(
            username="gamer2",
            email="gamer2@example.com",
            password="Password123!"
        )

        self.tournament = Tournament.objects.create(
            title="BGMI Championship 2026",
            game="BGMI",
            prize_pool="₹50,000",
            date=timezone.now().date() + timedelta(days=7),
            mode="Squad",
            description="Official BGMI Tournament",
            max_players=4,
            is_active=True
        )

        self.team = Team.objects.create(
            name="Shadow Wolves",
            game="BGMI",
            description="Competitive BGMI roster",
            captain=self.user
        )
        self.team.members.add(self.user)

    def test_home_page(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BGMI Championship 2026")

    def test_tournament_search_and_filter(self):
        # Search by game
        response = self.client.get(reverse("home") + "?game=BGMI")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BGMI Championship 2026")

        # Search with non-matching term
        response = self.client.get(reverse("home") + "?search=NonExistentTournamentXYZ")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "BGMI Championship 2026")

    def test_user_registration(self):
        response = self.client.post(reverse("register"), {
            "username": "newplayer",
            "email": "newplayer@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newplayer").exists())

    def test_user_registration_duplicate_username(self):
        response = self.client.post(reverse("register"), {
            "username": "gamer1",
            "email": "diff@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already taken")

    def test_user_login_and_logout(self):
        response = self.client.post(reverse("login"), {
            "username": "gamer1",
            "password": "Password123!"
        })
        self.assertEqual(response.status_code, 302)

        # Access dashboard
        dashboard_res = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard_res.status_code, 200)

        # Logout
        logout_res = self.client.get(reverse("logout"))
        self.assertEqual(logout_res.status_code, 302)

    def test_join_tournament(self):
        self.client.login(username="gamer1", password="Password123!")
        response = self.client.get(reverse("join_tournament", args=[self.tournament.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Registration.objects.filter(user=self.user, tournament=self.tournament).exists())

        # Attempt to join again
        response2 = self.client.get(reverse("join_tournament", args=[self.tournament.id]))
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(Registration.objects.filter(user=self.user, tournament=self.tournament).count(), 1)

    def test_tournament_full_capacity(self):
        # Fill capacity
        u1 = User.objects.create_user("u1", "u1@test.com", "Password123!")
        u2 = User.objects.create_user("u2", "u2@test.com", "Password123!")
        u3 = User.objects.create_user("u3", "u3@test.com", "Password123!")
        u4 = User.objects.create_user("u4", "u4@test.com", "Password123!")
        Registration.objects.create(user=u1, tournament=self.tournament)
        Registration.objects.create(user=u2, tournament=self.tournament)
        Registration.objects.create(user=u3, tournament=self.tournament)
        Registration.objects.create(user=u4, tournament=self.tournament)

        self.client.login(username="gamer1", password="Password123!")
        response = self.client.get(reverse("join_tournament", args=[self.tournament.id]))
        self.assertEqual(response.status_code, 302)
        # Should not register gamer1 because max_players=4 is reached
        self.assertFalse(Registration.objects.filter(user=self.user, tournament=self.tournament).exists())

    def test_team_flow(self):
        self.client.login(username="gamer2", password="Password123!")
        # Join team
        response = self.client.get(reverse("join_team", args=[self.team.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.team.members.filter(id=self.other_user.id).exists())

        # Leave team
        response_leave = self.client.get(reverse("leave_team", args=[self.team.id]))
        self.assertEqual(response_leave.status_code, 302)
        self.assertFalse(self.team.members.filter(id=self.other_user.id).exists())

    def test_leaderboard(self):
        Registration.objects.create(user=self.user, tournament=self.tournament)
        TournamentResult.objects.create(
            tournament=self.tournament,
            player=self.user,
            position=1,
            points=250
        )
        response = self.client.get(reverse("leaderboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "gamer1")
        # 100 participation pts + 250 result pts = 350 pts
        self.assertContains(response, "350")

    def test_match_display_with_team_id(self):
        match = Match.objects.create(
            tournament=self.tournament,
            round_name="Semi-Finals",
            team1=str(self.team.id),
            team2="Global Titans",
            match_date=timezone.now() + timedelta(days=1)
        )
        self.assertEqual(match.team1_display, "Shadow Wolves")
        self.assertEqual(match.team2_display, "Global Titans")

    def test_generate_ai_crest(self):
        self.client.login(username="gamer1", password="Password123!")
        response = self.client.post(
            reverse("generate_ai_crest"),
            {"team_name": "TITANS", "theme": "purple", "mascot": "dragon", "prompt": "cyber dragon"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("media_url", data)
        self.assertIn("relative_path", data)

    def test_create_team_with_ai_crest(self):
        self.client.login(username="gamer1", password="Password123!")
        # 1. Generate crest
        gen_res = self.client.post(
            reverse("generate_ai_crest"),
            {"team_name": "VALIANT", "theme": "cyan", "mascot": "wolf"},
            content_type="application/json"
        )
        ai_path = gen_res.json()["relative_path"]

        # 2. Submit form with ai_logo_path
        res = self.client.post(reverse("create_team"), {
            "name": "Valiant Esports",
            "game": "Valorant",
            "description": "Top tier squad",
            "ai_logo_path": ai_path
        })
        self.assertEqual(res.status_code, 302)
        created_team = Team.objects.get(name="Valiant Esports")
        self.assertEqual(created_team.logo.name, ai_path)

