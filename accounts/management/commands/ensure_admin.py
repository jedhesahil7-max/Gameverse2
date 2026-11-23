
import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create or update the GameVerse production admin account"

    def handle(self, *args, **options):

        username = os.environ.get("ADMIN_USERNAME")
        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")

        if not all([username, email, password]):
            raise CommandError(
                "ADMIN_USERNAME, ADMIN_EMAIL and ADMIN_PASSWORD "
                "must be configured."
            )

        if len(password) < 12:
            raise CommandError(
                "ADMIN_PASSWORD must contain at least 12 characters."
            )

        User = get_user_model()

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email}
        )

        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS("Admin account created.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Admin account updated.")
            )
