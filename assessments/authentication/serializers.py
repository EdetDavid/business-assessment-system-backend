from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

    def create(self, validated_data):
        # Create username from email
        email = validated_data.get('email')
        username = email

        # Check for username uniqueness
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                {"email": "This email is already in use."})

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        return user


class UserAdminSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(source='is_staff', read_only=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_admin', 'is_active', 'date_joined', 'last_login')
        read_only_fields = ('id', 'username', 'date_joined', 'last_login')

    def update(self, instance, validated_data):
        # Handle nested is_admin field
        if 'is_staff' in validated_data:
            is_admin = validated_data.pop('is_staff')
            instance.is_staff = is_admin
            instance.is_superuser = is_admin  # Also update superuser status

        return super().update(instance, validated_data)
