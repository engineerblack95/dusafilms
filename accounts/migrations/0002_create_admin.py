from django.db import migrations
from django.contrib.auth import get_user_model
import os

def create_admin(apps, schema_editor):
    User = get_user_model()

    username = os.environ.get("ADMIN_USERNAME", "admin")
    email = os.environ.get("ADMIN_EMAIL", "admin@dusa.com")
    password = os.environ.get("ADMIN_PASSWORD", "StrongPassword123")

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_admin),
    ]
