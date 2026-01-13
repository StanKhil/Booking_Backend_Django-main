from django.db import models
import uuid, time

# Create your models here.

class UserRole(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=50
    )
    description = models.CharField(max_length=255)

    can_create = models.BooleanField(default=False)
    can_read = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        db_table = "user_roles"

    def __str__(self):
        return self.id
    

class UserData(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    birth_date = models.DateField(null=True, blank=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_data"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class UserAccess(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user_id = models.UUIDField(db_index=True)

    login = models.CharField(
        max_length=150,
        unique=True
    )

    salt = models.CharField(max_length=255)
    dk = models.CharField(
        max_length=255
    )

    user_data = models.ForeignKey(
        "UserData",
        on_delete=models.CASCADE,
        related_name="user_accesses"
    )

    user_role = models.ForeignKey(
        "UserRole",
        on_delete=models.PROTECT,
        related_name="user_accesses"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_access"
        indexes = [
            models.Index(fields=["login"]),
            models.Index(fields=["user_id"]),
        ]

    def __str__(self):
        return self.login



class ItemImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    image_url = models.URLField(null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)

    realty = models.ForeignKey(
        "Realty",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="images"
    )

    realty_group = models.ForeignKey(
        "RealtyGroup",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="images"
    )

    class Meta:
        db_table = "item_images"
        ordering = ["order"]


class AccessToken(models.Model):
    jti = models.CharField(primary_key=True, max_length=255)

    sub = models.UUIDField(null=True, blank=True)
    iat = models.CharField(max_length=50, null=True, blank=True)
    exp = models.CharField(max_length=50, null=True, blank=True)
    nbf = models.CharField(max_length=50, null=True, blank=True)
    aud = models.CharField(max_length=255, null=True, blank=True)
    iss = models.CharField(max_length=255, null=True, blank=True)

    user_access = models.ForeignKey(
        "UserAccess",
        on_delete=models.CASCADE,
        related_name="access_tokens"
    )
    
    class Meta:
        db_table = "access_tokens"


class BookingItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    realty = models.ForeignKey(
        "Realty",
        on_delete=models.CASCADE,
        related_name="booking_items"
    )

    user_access = models.ForeignKey(
        "UserAccess",
        on_delete=models.CASCADE,
        related_name="booking_items"
    )

    class Meta:
        db_table = "booking_items"


class Card(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    number = models.CharField(max_length=20)
    cardholder_name = models.CharField(max_length=150)
    expiration_date = models.DateField()

    user = models.ForeignKey(
        "UserData",
        on_delete=models.CASCADE,
        related_name="cards"
    )

    class Meta:
        db_table = "cards"

class Country(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)

    class Meta:
        db_table = "countries"

    def __str__(self):
        return self.name
    
class City(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)

    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="cities"
    )

    class Meta:
        db_table = "cities"

    def __str__(self):
        return self.name
    

class RealtyGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=150)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    image_url = models.URLField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    parent_group = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children"
    )

    class Meta:
        db_table = "realty_groups"

    def __str__(self):
        return self.name


class Realty(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    deleted_at = models.DateTimeField(null=True, blank=True)

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="realties"
    )

    realty_group = models.ForeignKey(
        RealtyGroup,
        on_delete=models.PROTECT,
        related_name="realties"
    )

    class Meta:
        db_table = "realties"

    def __str__(self):
        return self.name


class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    text = models.TextField()
    rate = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    realty = models.ForeignKey(
        Realty,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    user_access = models.ForeignKey(
        "UserAccess",
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    class Meta:
        db_table = "feedbacks"
