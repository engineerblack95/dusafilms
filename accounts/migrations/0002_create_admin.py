from django.db import migrations
import os

def create_admin(apps, schema_editor):
    User = apps.get_model("auth", "User")

    username = os.environ.get("ADMIN_USERNAME")
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")

    if not username or not password:
        return

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
