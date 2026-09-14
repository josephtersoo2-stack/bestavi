from rest_framework import serializers
from .models import (
    BotConfig,
    ExtractedOdds,
    BetRecord,
    BotLog,
    AIChatSession,
    AIChatMessage,
    AIDiscoveryMemory,
)
from .security import mask_sensitive_url


def mask_api_key(key: str) -> str:
    """Mask sensitive API key showing only first 6 and last 4 characters."""
    if not key or len(key) < 10:
        return "********" if key else ""
    return f"{key[:6]}...{key[-4:]}"


class BotConfigSerializer(serializers.ModelSerializer):
    game_url = serializers.CharField(required=False, allow_blank=True)
    gemini_api_key = serializers.CharField(required=False, allow_blank=True)
    openrouter_api_key = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = BotConfig
        fields = [
            'id', 'base_stake', 'strategy', 'multiplier', 'auto_cashout',
            'max_stake', 'max_loss_steps', 'stop_loss', 'profit_target',
            'dry_run', 'network_auto_retry', 'network_retry_delay', 'network_max_retries',
            'site', 'platform', 'game', 'game_url',
            'ai_enabled', 'ai_autonomous_mode', 'ai_provider', 'ai_model',
            'gemini_api_key', 'openrouter_api_key', 'ai_risk_tolerance',
            'updated_at'
        ]


    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Decrypt then mask sensitive query parameters (e.g. content=, token=)
        decrypted_url = instance.get_decrypted_game_url()
        ret['game_url'] = mask_sensitive_url(decrypted_url)

        # Mask API keys in API response
        dec_gemini = instance.get_decrypted_gemini_key()
        dec_openrouter = instance.get_decrypted_openrouter_key()
        ret['gemini_api_key'] = mask_api_key(dec_gemini)
        ret['openrouter_api_key'] = mask_api_key(dec_openrouter)
        ret['has_gemini_key'] = bool(dec_gemini)
        ret['has_openrouter_key'] = bool(dec_openrouter)
        return ret

    def validate_base_stake(self, value):
        if value < 1.0 or value > 50000.0:
            raise serializers.ValidationError("Base stake must be between 1.0 and 50,000.0 NGN")
        return round(value, 4)

    def validate_multiplier(self, value):
        if value < 1.01 or value > 100.0:
            raise serializers.ValidationError("Loss multiplier must be between 1.01x and 100.0x")
        return round(value, 4)

    def validate_auto_cashout(self, value):
        if value < 1.01 or value > 100.0:
            raise serializers.ValidationError("Auto cashout must be between 1.01x and 100.0x")
        return round(value, 4)

    def validate_strategy(self, value):
        allowed = {'martingale', 'dalembert', 'flat', 'fibonacci'}
        if value.lower() not in allowed:
            raise serializers.ValidationError(f"Invalid strategy. Must be one of: {', '.join(allowed)}")
        return value.lower()

    def validate_max_loss_steps(self, value):
        if value < 1 or value > 20:
            raise serializers.ValidationError("Max loss steps must be between 1 and 20")
        return value

    def validate_network_retry_delay(self, value):
        if value < 2 or value > 300:
            raise serializers.ValidationError("Retry delay must be between 2 and 300 seconds")
        return value

    def validate_network_max_retries(self, value):
        if value < 1 or value > 50:
            raise serializers.ValidationError("Max retries must be between 1 and 50")
        return value

    def validate(self, attrs):
        base = attrs.get('base_stake') or getattr(self.instance, 'base_stake', 50.0)
        max_s = attrs.get('max_stake') or getattr(self.instance, 'max_stake', 5000.0)
        if max_s < base:
            raise serializers.ValidationError({"max_stake": "Max stake cannot be less than base stake"})
        return attrs

    def update(self, instance, validated_data):
        """Grade-A Credential Protection: prevent masked or redacted keys from corrupting encrypted secrets."""
        # 1. Guard sensitive API keys against masked strings or accidental blank overwrites
        for key_field in ('gemini_api_key', 'openrouter_api_key'):
            if key_field in validated_data:
                val = validated_data[key_field]
                val_str = str(val).strip() if val else ""
                if val_str in ("__CLEAR__", "CLEAR", "REMOVE"):
                    validated_data[key_field] = ""
                elif not val_str or "..." in val_str or "***" in val_str or "REDACTED" in val_str or len(val_str) < 8:
                    # Retain current encrypted key from database instance
                    validated_data[key_field] = getattr(instance, key_field, "")

        # 2. Guard sensitive game_url against masked strings or blank overwrites
        if 'game_url' in validated_data:
            url_val = str(validated_data['game_url']).strip() if validated_data['game_url'] else ""
            if "REDACTED" in url_val or not url_val:
                # Retain current encrypted game_url
                validated_data['game_url'] = instance.game_url

        return super().update(instance, validated_data)



class ExtractedOddsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedOdds
        fields = ['id', 'multiplier', 'site', 'game', 'phase', 'is_under_2x', 'is_over_10x', 'timestamp']


class BetRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetRecord
        fields = [
            'id', 'stake', 'cashout_target', 'crash_multiplier',
            'won', 'profit_loss', 'balance_after', 'site', 'game', 'created_at'
        ]


class BotLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotLog
        fields = ['id', 'level', 'message', 'created_at']


class AIChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatMessage
        fields = ['id', 'session', 'role', 'sender_name', 'content', 'metadata', 'created_at']


class AIChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AIChatSession
        fields = [
            'id', 'title', 'platform', 'game', 'is_pinned',
            'created_at', 'updated_at', 'message_count', 'last_message'
        ]

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {
                'id': last.id,
                'role': last.role,
                'sender_name': last.sender_name,
                'content': last.content[:80],
                'created_at': last.created_at
            }
        return None


class AIDiscoveryMemorySerializer(serializers.ModelSerializer):
    source_session_title = serializers.ReadOnlyField(source="source_session.title")

    class Meta:
        model = AIDiscoveryMemory
        fields = [
            "id",
            "title",
            "category",
            "content",
            "evidence_data",
            "source_session",
            "source_session_title",
            "platform",
            "game",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

