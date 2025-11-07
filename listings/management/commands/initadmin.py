from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


# pylint: disable=no-member
# pylint: disable=invalid-name
class Command(BaseCommand):
    """Create an admin user if none exists"""
    help = "Create an admin user if none exists"

    def handle(self, *args, **options):
        User = get_user_model()
        first_name="Admin"
        last_name="User"
        email = "admin@example.com"
        password = "adminpass"

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(first_name, last_name, email, password)
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{first_name}{last_name}' created successfully!")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Superuser '{first_name}{last_name}' already exists. Skipping creation."
                )
            )
