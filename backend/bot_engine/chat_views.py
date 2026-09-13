from __future__ import annotations

import logging
from typing import Any
from django.shortcuts import get_object_or_404
from rest_framework import views, status, permissions
from rest_framework.response import Response

from rest_framework.authentication import SessionAuthentication
from .models import BotConfig, ExtractedOdds, BetRecord, AIChatSession, AIChatMessage
from .serializers import AIChatSessionSerializer, AIChatMessageSerializer
from .security import AdminApiKeyAuthentication, IsAdminApiKey
from .service import DjangoBotService
from aviator_bot.ai.ai_engine import AIEngine
from aviator_bot.ai.config import AIConfig

logger = logging.getLogger("aviator_bot.backend.chat")
ai_engine = AIEngine()


def _get_active_telemetry(config: BotConfig) -> dict[str, Any]:
    """Compile rich live telemetry for agent evaluation."""
    recent_odds = list(
        ExtractedOdds.objects.filter(site=config.platform).order_by("-timestamp")[:100].values("multiplier", "timestamp")
    )
    # Reverse to chronological order for cluster sequence tracking
    recent_odds.reverse()

    bot_svc = DjangoBotService.get_instance()
    bankroll_data = {
        "balance": bot_svc.balance if bot_svc.balance is not None else 25000.0,
        "base_stake": config.base_stake,
        "current_stake": bot_svc.current_stake if bot_svc.is_running else config.base_stake,
        "loss_streak": bot_svc.loss_streak if bot_svc.is_running else 0,
        "auto_cashout": config.auto_cashout,
        "recent_bets": list(BetRecord.objects.filter(site=config.platform).order_by("-created_at")[:10].values()),
    }

    return {
        "odds_records": recent_odds,
        "strategy": config.strategy,
        "auto_cashout": config.auto_cashout,
        "base_stake": config.base_stake,
        "max_stake": config.max_stake,
        "max_loss_steps": config.max_loss_steps,
        "stop_loss": config.stop_loss,
        "profit_target": config.profit_target,
        "session_profit": bot_svc.session_profit if bot_svc.is_running else 0.0,
        "bankroll_data": bankroll_data,
        "bot_running": bot_svc.is_running,
        "bot_paused": bot_svc.is_paused,
    }


class AIChatSessionListCreateView(views.APIView):
    """List all user chat sessions or create a new conversation thread."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def get(self, request: views.Request) -> Response:
        sessions = AIChatSession.objects.all().order_by("-is_pinned", "-updated_at")
        serializer = AIChatSessionSerializer(sessions, many=True)
        return Response({"sessions": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request: views.Request) -> Response:
        config = BotConfig.get_active()
        title = request.data.get("title", "").strip() or "New Conversation"
        platform = request.data.get("platform", "").strip() or config.platform
        game = request.data.get("game", "").strip() or config.game

        session = AIChatSession.objects.create(
            title=title,
            platform=platform,
            game=game,
        )
        serializer = AIChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AIChatSessionDetailView(views.APIView):
    """Retrieve full message history, rename, pin, or delete a chat session."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def get(self, request: views.Request, session_id: int) -> Response:
        session = get_object_or_404(AIChatSession, id=session_id)
        session_data = AIChatSessionSerializer(session).data
        messages = session.messages.all().order_by("created_at")
        session_data["messages"] = AIChatMessageSerializer(messages, many=True).data
        return Response(session_data, status=status.HTTP_200_OK)

    def patch(self, request: views.Request, session_id: int) -> Response:
        session = get_object_or_404(AIChatSession, id=session_id)
        if "title" in request.data:
            session.title = str(request.data["title"]).strip()[:255]
        if "is_pinned" in request.data:
            session.is_pinned = bool(request.data["is_pinned"])
        session.save()
        return Response(AIChatSessionSerializer(session).data, status=status.HTTP_200_OK)

    def delete(self, request: views.Request, session_id: int) -> Response:
        session = get_object_or_404(AIChatSession, id=session_id)
        session.delete()
        return Response({"deleted": True, "session_id": session_id}, status=status.HTTP_200_OK)


class AIChatMessageSendView(views.APIView):
    """Send user message to a chat thread, ground in cross-session memory and live swarm, and receive response."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def post(self, request: views.Request, session_id: int) -> Response:
        session = get_object_or_404(AIChatSession, id=session_id)
        user_content = request.data.get("content", "").strip()
        if not user_content:
            return Response({"error": "Message content cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Record User Message
        user_msg = AIChatMessage.objects.create(
            session=session,
            role="user",
            sender_name="User",
            content=user_content,
        )

        # 2. Update session title if default
        if session.title in ("New Conversation", "New Chat") and len(user_content) > 3:
            session.title = user_content[:45] + ("..." if len(user_content) > 45 else "")
            session.save(update_fields=["title", "updated_at"])

        # 3. Build Cross-Session Memory from past threads
        past_sessions = AIChatSession.objects.exclude(id=session.id).order_by("-updated_at")[:5]
        past_summary = []
        for s in past_sessions:
            recent_msgs = list(s.messages.order_by("created_at")[:4].values("role", "content"))
            past_summary.append({
                "title": s.title,
                "msg_count": s.messages.count(),
                "sample_exchanges": recent_msgs,
                "updated_at": s.updated_at.isoformat(),
            })

        # 4. Gather active conversation messages
        current_msgs = list(session.messages.order_by("created_at").values("role", "sender_name", "content"))

        # 5. Compile live telemetry & run Swarm Consensus
        config = BotConfig.get_active()
        telemetry = _get_active_telemetry(config)
        swarm_result = ai_engine.evaluate_swarm(telemetry)

        # 6. Resolve API credentials
        provider = config.ai_provider
        api_key = config.get_decrypted_openrouter_key() if provider == "openrouter" else config.get_decrypted_gemini_key()
        model_name = config.ai_model

        ai_cfg = AIConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            temperature=0.4,
        )

        # 7. Generate Swarm response
        try:
            assistant_reply = ai_engine.chat_copilot(
                user_message=user_content,
                odds_records=telemetry["odds_records"],
                platform=session.platform,
                game=session.game,
                config=ai_cfg,
                current_messages=current_msgs,
                past_sessions_summary=past_summary,
                swarm_consensus=swarm_result,
            )
        except Exception as exc:
            logger.exception("AI Copilot generation failed: %s", exc)
            assistant_reply = (
                f"**Swarm Consensus Alert ({swarm_result['consensus_score']}% agreement):**\n"
                f"- Directive: **{swarm_result['consensus_directive']}**\n"
                f"- Executive Summary: {swarm_result['consensus_summary']}\n\n"
                f"*Note: Remote LLM query encountered temporary error ({type(exc).__name__}). "
                f"Quantitative agents remain fully active and monitoring.*"
            )

        # 8. Record Assistant Message
        assistant_msg = AIChatMessage.objects.create(
            session=session,
            role="assistant",
            sender_name=f"Swarm Supervisor ({model_name})",
            content=assistant_reply,
            metadata={
                "provider": provider,
                "model": model_name,
                "consensus_directive": swarm_result["consensus_directive"],
                "consensus_score": swarm_result["consensus_score"],
                "recommendations": swarm_result.get("recommendations", []),
            },
        )

        session.save(update_fields=["updated_at"])

        return Response({
            "user_message": AIChatMessageSerializer(user_msg).data,
            "assistant_message": AIChatMessageSerializer(assistant_msg).data,
            "swarm": swarm_result,
        }, status=status.HTTP_201_CREATED)


class AISwarmStatusView(views.APIView):
    """Retrieve real-time multi-agent swarm status and consensus directive."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def get(self, request: views.Request) -> Response:
        config = BotConfig.get_active()
        telemetry = _get_active_telemetry(config)
        swarm_result = ai_engine.evaluate_swarm(telemetry)

        return Response({
            "status": "ok",
            "autonomous_mode": config.ai_autonomous_mode,
            "consensus": swarm_result,
            "platform": config.platform,
            "game": config.game,
        }, status=status.HTTP_200_OK)


class AISwarmEvaluateView(views.APIView):
    """Trigger immediate multi-agent evaluation and update live recommendations."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def post(self, request: views.Request) -> Response:
        config = BotConfig.get_active()
        telemetry = _get_active_telemetry(config)
        swarm_result = ai_engine.evaluate_swarm(telemetry)

        return Response({
            "status": "ok",
            "consensus": swarm_result,
        }, status=status.HTTP_200_OK)
