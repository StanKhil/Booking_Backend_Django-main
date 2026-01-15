from django.core.management.base import BaseCommand
from uuid import UUID
from datetime import datetime

from main.models import (
    RealtyGroup,
    Country,
    City,
    UserRole,
    UserData,
    UserAccess,
)


class Command(BaseCommand):
    help = "Seed initial data (groups, countries, cities, users)"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding data...")

        self.seed_groups()
        self.seed_countries_and_cities()
        self.seed_roles_and_admin()

        self.stdout.write(self.style.SUCCESS("✅ Seed completed"))

    def seed_groups(self):
        groups = [
            {
                "id": UUID("f1ea6b3f-0021-417b-95c8-f6cd333d7207"),
                "name": "Hotels",
                "description": "Multi-room hotels",
                "slug": "hotels",
                "image_url": "hotel.jpg",
            },
            {
                "id": UUID("8806ca58-8daa-4576-92ba-797de42ffaa7"),
                "name": "Apartments",
                "description": "Apartments",
                "slug": "apartments",
                "image_url": "apartment.jpg",
            },
            {
                "id": UUID("97191468-a02f-4a78-927b-9ea660e9ea36"),
                "name": "Houses",
                "description": "Houses",
                "slug": "houses",
                "image_url": "house.jpg",
            },
            {
                "id": UUID("6a1d3de4-0d78-4d7d-8f6a-9e52694ff2ee"),
                "name": "Villas",
                "description": "Villas",
                "slug": "villas",
                "image_url": "villa.jpg",
            },
        ]

        for g in groups:
            RealtyGroup.objects.get_or_create(
                id=g["id"],
                defaults=g,
            )

    def seed_countries_and_cities(self):
        ukraine, _ = Country.objects.get_or_create(
            id=UUID("7687bebd-e8a3-4b28-abc8-8fc9cc403a8d"),
            defaults={"name": "Ukraine"},
        )

        Country.objects.get_or_create(
            id=UUID("bdf41cd9-c0f1-4349-8a44-4e67755d0415"),
            defaults={"name": "Poland"},
        )

        cities = [
            ("59b082e4-19ab-4d7f-a061-4fbc08c59778", "Kyiv"),
            ("923a6af0-30be-41aa-ae79-fdf41b7bb1b6", "Odesa"),
            ("03767d46-aab3-4cc4-989c-a696a7fdd434", "Lviv"),
        ]

        for city_id, name in cities:
            City.objects.get_or_create(
                id=UUID(city_id),
                defaults={
                    "name": name,
                    "country": ukraine,
                },
            )

    def seed_roles_and_admin(self):
        admin_role, _ = UserRole.objects.get_or_create(
            id="admin",
            defaults={
                "description": "Administrator",
                "can_create": True,
                "can_read": True,
                "can_update": True,
                "can_delete": True,
            },
        )

        roles = [
            ("employee", "Employee", False, True, True, False),
            ("self_registered", "Self Registered", False, True, True, False),
            ("moderator", "Moderator", True, True, True, True),
        ]

        for r in roles:
            UserRole.objects.get_or_create(
                id=r[0],
                defaults={
                    "description": r[1],
                    "can_create": r[2],
                    "can_read": r[3],
                    "can_update": r[4],
                    "can_delete": r[5],
                },
            )

        user_data, _ = UserData.objects.get_or_create(
            email="admin@booking.local",
            defaults={
                "first_name": "Admin",
                "last_name": "User",
                "registered_at": datetime.utcnow(),
            },
        )

        UserAccess.objects.get_or_create(
            login="admin",
            defaults={
                "user_data": user_data,
                "user_role": admin_role,
                "salt": "seed",
                "dk": "seed",
            },
        )
