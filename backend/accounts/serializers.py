import re

from django.contrib.auth.models import User
from rest_framework import serializers

from lottery.models import LotteryGame
from .models import SavedPrediction


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, min_length=3)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "使用者名稱只能包含英文字母、數字和底線。"
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("此使用者名稱已被使用。")
        return value

    def validate_password(self, value):
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("密碼需包含至少一個大寫字母。")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("密碼需包含至少一個小寫字母。")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("密碼需包含至少一個數字。")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]', value):
            raise serializers.ValidationError("密碼需包含至少一個特殊符號。")
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "兩次密碼不一致。"}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = fields


class SavedPredictionSerializer(serializers.ModelSerializer):
    game_code = serializers.SlugRelatedField(
        source='game',
        slug_field='code',
        queryset=LotteryGame.objects.filter(is_active=True),
    )

    class Meta:
        model = SavedPrediction
        fields = [
            'id', 'game_code', 'numbers', 'special_number',
            'strategy', 'created_at',
            'checked_term', 'matched_count', 'special_matched', 'checked_at',
        ]
        read_only_fields = [
            'id', 'created_at',
            'checked_term', 'matched_count', 'special_matched', 'checked_at',
        ]
