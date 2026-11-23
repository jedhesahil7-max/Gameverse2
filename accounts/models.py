from django.db import models
from django.contrib.auth.models import User


class Tournament(models.Model):

    GAME_CHOICES = [
        ("PUBG", "PUBG"),
        ("BGMI", "BGMI"),
        ("Valorant", "Valorant"),
        ("CS2", "Counter-Strike 2"),
        ("Apex", "Apex Legends"),
        ("Rocket League", "Rocket League"),
        ("EA FC", "EA Sports FC"),
        ("eFootball", "eFootball"),
        ("Fortnite", "Fortnite"),
        ("Warzone", "Call of Duty: Warzone"),
        ("Free Fire", "Free Fire"),
        ("Overwatch 2", "Overwatch 2"),
        ("R6 Siege", "Rainbow Six Siege"),
        ("Dota 2", "Dota 2"),
        ("LoL", "League of Legends"),
    ]

    title = models.CharField(max_length=100)

    game = models.CharField(
        max_length=20,
        choices=GAME_CHOICES
    )

    prize_pool = models.CharField(max_length=50)

    date = models.DateField()

    mode = models.CharField(max_length=50)

    image = models.ImageField(
        upload_to="tournaments/"
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    max_players = models.PositiveIntegerField(
        default=100
    )

    class Meta:
        ordering = ["date", "title"]

    def __str__(self):
        return self.title

    @property
    def registered_count(self):
        return self.registration_set.count()

    @property
    def is_full(self):
        return self.registered_count >= self.max_players


class Registration(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "user",
            "tournament"
        )
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.user.username} - {self.tournament.title}"


class Team(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    game = models.CharField(
        max_length=50
    )

    logo = models.ImageField(
        upload_to="teams/",
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True
    )

    captain = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="captain_teams"
    )

    members = models.ManyToManyField(
        User,
        related_name="teams",
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()


class TournamentResult(models.Model):

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="results"
    )

    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tournament_results"
    )

    position = models.PositiveIntegerField()

    points = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["tournament", "position"]

    def __str__(self):
        return f"{self.player.username} - {self.tournament.title} - Position {self.position}"


class Match(models.Model):

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="matches"
    )

    round_name = models.CharField(
        max_length=50,
        blank=True,
        default="Group Stage"
    )

    team1 = models.CharField(max_length=100)

    team2 = models.CharField(max_length=100)

    match_date = models.DateTimeField()

    winner = models.CharField(
        max_length=100,
        blank=True
    )

    @property
    def team1_display(self):
        val = str(self.team1).strip()
        if val.isdigit():
            team = Team.objects.filter(id=int(val)).first()
            if team:
                return team.name
        return val

    @property
    def team2_display(self):
        val = str(self.team2).strip()
        if val.isdigit():
            team = Team.objects.filter(id=int(val)).first()
            if team:
                return team.name
        return val

    @property
    def winner_display(self):
        val = str(self.winner).strip()
        if val.isdigit():
            team = Team.objects.filter(id=int(val)).first()
            if team:
                return team.name
        return val

    class Meta:
        ordering = ["match_date"]
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.team1_display} vs {self.team2_display} ({self.tournament.title})"
