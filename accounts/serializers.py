import re
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User


USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{2,19}$")
PHONE_RE = re.compile(r"^\+?[\d\s()\-]{7,20}$")


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "country",
            "newsletter",
            "is_email_verified",
            "is_staff",
            "is_superuser",
            "role",
            "created_at",
        )
        read_only_fields = ("id", "is_email_verified", "is_staff", "is_superuser", "created_at")

    def get_role(self, obj):
        if obj.is_superuser:
            return "superuser"
        if obj.is_staff:
            return "staff"
        return "user"

    def update(self, instance, validated):
        if "full_name" in self.initial_data and "full_name" not in validated:
            parts = str(self.initial_data.get("full_name", "")).strip().split(" ", 1)
            instance.first_name = parts[0] if parts else ""
            instance.last_name = parts[1] if len(parts) > 1 else ""
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        return instance


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    date_joined = serializers.DateTimeField(source="created_at", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "country",
            "newsletter",
            "is_email_verified",
            "is_staff",
            "is_superuser",
            "role",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined", "is_email_verified")

    def get_role(self, obj):
        if obj.is_superuser:
            return "superuser"
        if obj.is_staff:
            return "staff"
        return "user"


def _validate_password_rules(value):
    errors = []
    if len(value) < 6:
        errors.append("At least 6 characters.")
    if not re.search(r"[A-Za-z]", value):
        errors.append("Contains a letter.")
    if not re.search(r"[0-9]", value):
        errors.append("Contains a number.")
    if not re.search(r"[^A-Za-z0-9]", value):
        errors.append("Contains a symbol.")
    if errors:
        raise serializers.ValidationError(errors)
    return value


class SignupSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=160)
    username = serializers.CharField(max_length=32)
    country = serializers.CharField(max_length=2, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm = serializers.CharField(write_only=True, required=False, allow_blank=True)
    newsletter = serializers.BooleanField(default=True)
    agree = serializers.BooleanField(required=False, default=True)

    def validate_username(self, value):
        value = value.strip()
        if not USERNAME_RE.match(value):
            raise serializers.ValidationError(
                "3–20 chars, start with a letter. Letters, numbers, _ and - only."
            )
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("That username is taken.")
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_phone(self, value):
        value = (value or "").strip()
        if value and not PHONE_RE.match(value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate(self, attrs):
        confirm = attrs.get("confirm")
        if confirm and attrs["password"] != confirm:
            raise serializers.ValidationError({"confirm": ["Passwords do not match."]})
        _validate_password_rules(attrs["password"])
        if not attrs.get("agree", True):
            raise serializers.ValidationError({"agree": ["You must accept the terms to continue."]})
        return attrs

    def create(self, validated):
        full_name = validated["full_name"].strip()
        parts = full_name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
        return User.objects.create_user(
            email=validated["email"],
            password=validated["password"],
            username=validated["username"],
            first_name=first_name,
            last_name=last_name,
            phone=validated.get("phone", ""),
            country=(validated.get("country") or "").upper(),
            newsletter=validated.get("newsletter", True),
            is_email_verified=False,
        )


class AdminUserCreateSerializer(SignupSerializer):
    is_superuser = serializers.BooleanField(default=False)

    def create(self, validated):
        is_super = bool(validated.pop("is_superuser", False))
        user = super().create(validated)
        user.is_email_verified = True
        if is_super:
            user.is_staff = True
            user.is_superuser = True
        user.save(update_fields=["is_email_verified", "is_staff", "is_superuser", "updated_at"])
        return user


class SigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"].lower().strip(), password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": "Invalid email or password."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is disabled."})
        attrs["user"] = user
        return attrs


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Enter the 6-digit code.")
        return value

    def validate_email(self, value):
        return value.lower().strip()


class ResendSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["signin", "signup"], default="signin")

    def validate_email(self, value):
        return value.lower().strip()