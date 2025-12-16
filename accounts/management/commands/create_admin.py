from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Create default admin user if not exists"

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME")
        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")

        if not username or not password:
            self.stdout.write("Admin env vars not set, skipping.")
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write("Admin user already exists.")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(self.style.SUCCESS("Superuser created successfully"))
