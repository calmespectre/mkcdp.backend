import uuid
import secrets
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password or uuid.uuid4().hex)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_email_verified", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=32, unique=True, null=True, blank=True, db_index=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=2, blank=True)
    newsletter = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or (self.username or self.email)


class VerificationCode(TimeStampedModel):
    PURPOSES = [("signup", "Signup"), ("signin", "Signin")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verification_codes")
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=16, choices=PURPOSES, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    used = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "purpose", "used"])]

    @classmethod
    def issue(cls, user, purpose):
        cls.objects.filter(user=user, purpose=purpose, used=False).update(used=True)
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        return cls.objects.create(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()