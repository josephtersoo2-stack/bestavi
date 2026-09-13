from __future__ import annotations

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication

from aviator_bot.platforms.registry import PlatformRegistry
from aviator_bot.ai.ai_engine import AIEngine
from aviator_bot.ai.config import AIConfig
from .models import BotConfig, ExtractedOdds, BetRecord, BotLog
from .service import DjangoBotService
from .security import AdminApiKeyAuthentication, IsAdminApiKey, sanitize_log

logger = logging.getLogger("bot_engine.ai_views")


from rest_framework import permissions

class PlatformsListView(APIView):
    """Return all registered platform addons and their supported game types."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):

        registry = PlatformRegistry.get_instance()
        platforms = registry.list_platforms()
        return Response({
            "platforms": platforms,
            "default_platform": "ilotbet",
            "default_game": "aviator",
        })


class AIModelsListView(APIView):
    """Dynamically fetch all available models from Gemini or OpenRouter."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def get(self, request):
        config = BotConfig.get_active()
        provider = request.query_params.get("provider") or config.ai_provider or "gemini"
        provider = provider.lower().strip()

        # Decrypt corresponding API key
        if "openrouter" in provider:
            api_key = config.get_decrypted_openrouter_key()
        else:
            api_key = config.get_decrypted_gemini_key()

        if not api_key:
            return Response(
                {"error": f"No API key configured for {provider}. Please configure your API key in Settings."},
                status=status.HTTP_400_BAD_REQUEST
            )

        engine = AIEngine()
        try:
            models = engine.fetch_available_models(provider, api_key)
            return Response({
                "provider": provider,
                "count": len(models),
                "models": models,
            })
        except Exception as exc:
            clean_err = sanitize_log(str(exc))
            logger.error("Failed to fetch models: %s", clean_err)
            return Response(
                {"error": f"Failed to fetch models from {provider}: {clean_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIStatusView(APIView):
    """Return AI Copilot status and active configurations."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def get(self, request):
        config = BotConfig.get_active()
        gemini_key = config.get_decrypted_gemini_key()
        openrouter_key = config.get_decrypted_openrouter_key()

        return Response({
            "ai_enabled": config.ai_enabled,
            "ai_autonomous_mode": config.ai_autonomous_mode,
            "ai_provider": config.ai_provider,
            "ai_model": config.ai_model,
            "has_gemini_key": bool(gemini_key),
            "has_openrouter_key": bool(openrouter_key),
            "ai_risk_tolerance": config.ai_risk_tolerance,
        })


class AIRiskAnalysisView(APIView):
    """Analyze real-time crash multiplier patterns and evaluate loss-cluster risk."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def post(self, request):
        config = BotConfig.get_active()
        platform = request.data.get("platform") or config.platform or "ilotbet"
        game = request.data.get("game") or config.game or "aviator"
        limit = int(request.data.get("sample_size") or 200)

        # Retrieve recent extracted odds
        qs = ExtractedOdds.objects.filter(site=platform, game=game).order_by("timestamp")
        if not qs.exists():
            # Fallback if site filter yields empty
            qs = ExtractedOdds.objects.all().order_by("timestamp")
        odds_records = list(qs.values("multiplier", "timestamp")[:limit])

        # Current bankroll status
        service = DjangoBotService.get_instance()
        current_status = service.get_status()
        recent_bets = list(BetRecord.objects.all().order_by("-created_at").values()[:10])

        bankroll_data = {
            "balance": current_status.get("balance"),
            "base_stake": config.base_stake,
            "current_stake": current_status.get("current_stake"),
            "loss_streak": current_status.get("loss_streak"),
            "auto_cashout": config.auto_cashout,
            "recent_bets": recent_bets,
        }

        # Resolve API Key
        provider = config.ai_provider or "gemini"
        api_key = config.get_decrypted_openrouter_key() if "openrouter" in provider else config.get_decrypted_gemini_key()

        ai_config = AIConfig(
            enabled=config.ai_enabled,
            provider=provider,
            model_name=config.ai_model or ("deepseek/deepseek-chat" if "openrouter" in provider else "gemini-flash-latest"),
            api_key=api_key,
            risk_tolerance=config.ai_risk_tolerance,
            autonomous_mode=config.ai_autonomous_mode,
        )

        engine = AIEngine()
        try:
            analysis = engine.assess_risk(odds_records, bankroll_data, ai_config)

            # Check if autonomous safety pause should be triggered
            if config.ai_autonomous_mode and analysis.get("autonomous_pause_advised"):
                if service.controller and service.controller.is_authorized:
                    service.pause_staking()
                    msg = f"[AI Autonomous Action] Staking paused automatically due to critical loss clustering risk ({analysis.get('risk_score')}/100)."
                    BotLog.objects.create(level="WARNING", message=msg)
                    analysis["autonomous_action_taken"] = "PAUSED_STAKING"

            return Response(analysis)
        except Exception as exc:
            clean_err = sanitize_log(str(exc))
            logger.error("AI Risk Analysis failed: %s", clean_err)
            return Response({"error": f"AI Risk Analysis error: {clean_err}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIStrategyRecommendView(APIView):
    """Generate optimized staking parameters tailored to the actual odds distribution."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def post(self, request):
        config = BotConfig.get_active()
        platform = request.data.get("platform") or config.platform or "ilotbet"
        game = request.data.get("game") or config.game or "aviator"

        qs = ExtractedOdds.objects.filter(site=platform, game=game).order_by("timestamp")
        if not qs.exists():
            qs = ExtractedOdds.objects.all().order_by("timestamp")
        odds_records = list(qs.values("multiplier", "timestamp")[:300])

        current_settings = {
            "base_stake": config.base_stake,
            "auto_cashout": config.auto_cashout,
            "multiplier": config.multiplier,
            "max_loss_steps": config.max_loss_steps,
            "stop_loss": config.stop_loss,
            "profit_target": config.profit_target,
            "ai_risk_tolerance": config.ai_risk_tolerance,
        }

        provider = config.ai_provider or "gemini"
        api_key = config.get_decrypted_openrouter_key() if "openrouter" in provider else config.get_decrypted_gemini_key()

        ai_config = AIConfig(
            enabled=config.ai_enabled,
            provider=provider,
            model_name=config.ai_model or ("deepseek/deepseek-chat" if "openrouter" in provider else "gemini-flash-latest"),
            api_key=api_key,
        )

        engine = AIEngine()
        try:
            recommendation = engine.recommend_strategy(odds_records, current_settings, ai_config)
            return Response(recommendation)
        except Exception as exc:
            clean_err = sanitize_log(str(exc))
            logger.error("AI Strategy Recommendation failed: %s", clean_err)
            return Response({"error": f"AI Strategy error: {clean_err}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIChatCopilotView(APIView):
    """Interactive question answering grounded in live odds telemetry."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def post(self, request):
        user_message = request.data.get("message", "").strip()
        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        config = BotConfig.get_active()
        platform = request.data.get("platform") or config.platform or "ilotbet"
        game = request.data.get("game") or config.game or "aviator"

        qs = ExtractedOdds.objects.filter(site=platform, game=game).order_by("timestamp")
        if not qs.exists():
            qs = ExtractedOdds.objects.all().order_by("timestamp")
        odds_records = list(qs.values("multiplier", "timestamp")[:200])

        provider = config.ai_provider or "gemini"
        api_key = config.get_decrypted_openrouter_key() if "openrouter" in provider else config.get_decrypted_gemini_key()

        ai_config = AIConfig(
            enabled=config.ai_enabled,
            provider=provider,
            model_name=config.ai_model or ("deepseek/deepseek-chat" if "openrouter" in provider else "gemini-flash-latest"),
            api_key=api_key,
        )

        engine = AIEngine()
        try:
            reply = engine.chat_copilot(user_message, odds_records, platform, game, ai_config)
            return Response({"reply": reply})
        except Exception as exc:
            clean_err = sanitize_log(str(exc))
            logger.error("AI Chat failed: %s", clean_err)
            return Response({"error": f"AI Chat error: {clean_err}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

