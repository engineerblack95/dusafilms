from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Create a superuser from environment variables (Render-safe)"

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(self.style.ERROR(
                "Superuser credentials not found in environment variables."
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(
                f"Superuser '{username}' already exists."
            ))
            return

        User.objects.create_superuser(
            username=username,
            email=email or "",
            password=password,
        )

        self.stdout.write(self.style.SUCCESS(
            f"Superuser '{username}' created successfully."
        ))
