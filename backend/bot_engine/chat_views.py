import json
import logging
import re
from typing import Any
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import views, status, permissions
from rest_framework.response import Response

from rest_framework.authentication import SessionAuthentication
from .models import BotConfig, ExtractedOdds, BetRecord, AIChatSession, AIChatMessage, AIDiscoveryMemory
from .serializers import AIChatSessionSerializer, AIChatMessageSerializer, AIDiscoveryMemorySerializer
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

        # 4.5. Retrieve active Knowledge Vault / Discovery Memories for platform & game
        active_memories = list(
            AIDiscoveryMemory.objects.filter(
                platform=session.platform,
                game=session.game,
                is_active=True,
            ).order_by("-updated_at")[:15].values("id", "title", "category", "content")
        )

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
                discovery_memories=active_memories,
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

        # 7.5. Intercept and persist any memory_save block emitted by the AI model
        saved_memory_data = None
        memory_match = re.search(r"```memory_save\s*(\{.*?\})\s*```", assistant_reply, re.DOTALL)
        if memory_match:
            raw_json = memory_match.group(1).strip()
            try:
                mem_dict = json.loads(raw_json)
                mem_title = str(mem_dict.get("title", "Discovered Pattern")).strip()
                mem_category = str(mem_dict.get("category", "GENERAL")).strip().upper()
                mem_content = str(mem_dict.get("content", "")).strip()

                valid_categories = dict(AIDiscoveryMemory.CATEGORY_CHOICES).keys()
                if mem_category not in valid_categories:
                    mem_category = "GENERAL"

                if mem_title and mem_content:
                    mem_obj = AIDiscoveryMemory.objects.create(
                        title=mem_title,
                        category=mem_category,
                        content=mem_content,
                        source_session=session,
                        platform=session.platform,
                        game=session.game,
                        is_active=True,
                        evidence_data={
                            "source": "swarm_chat_command",
                            "sample_rounds": len(telemetry["odds_records"]),
                            "directive": swarm_result.get("consensus_directive"),
                        },
                    )
                    saved_memory_data = AIDiscoveryMemorySerializer(mem_obj).data
                    # Clean the raw block out of the rendered text so chat stays sleek
                    assistant_reply = assistant_reply.replace(memory_match.group(0), "").strip()
            except Exception as parse_err:
                logger.warning("Failed to parse memory_save JSON: %s", parse_err)

        # Fallback command detection if user explicitly said "save to memory" / "remember this"
        # and LLM confirmed but forgot the exact block
        if saved_memory_data is None:
            user_lower = user_content.lower()
            save_triggers = ["save that to memory", "save to memory", "remember this", "save this discovery", "save our finding", "add to memory"]
            if any(trig in user_lower for trig in save_triggers):
                # Find previous assistant or current reply finding
                content_to_save = assistant_reply[:500] if len(assistant_reply) > 20 else user_content
                fallback_title = user_content[:40].replace("save that to memory", "").replace("save to memory", "").strip(" :,-")
                if not fallback_title:
                    fallback_title = "User & Swarm Discovery"

                category_guess = "GENERAL"
                if "time" in user_lower or "hour" in user_lower or "streak" in user_lower or "in a roll" in user_lower or "in a row" in user_lower:
                    category_guess = "STREAK_TIMING"
                elif "strategy" in user_lower or "cashout" in user_lower:
                    category_guess = "STRATEGY_RULE"

                mem_obj = AIDiscoveryMemory.objects.create(
                    title=fallback_title.capitalize(),
                    category=category_guess,
                    content=content_to_save,
                    source_session=session,
                    platform=session.platform,
                    game=session.game,
                    is_active=True,
                    evidence_data={"source": "user_explicit_command"},
                )
                saved_memory_data = AIDiscoveryMemorySerializer(mem_obj).data

        # 8. Record Assistant Message
        assistant_metadata = {
            "provider": provider,
            "model": model_name,
            "consensus_directive": swarm_result["consensus_directive"],
            "consensus_score": swarm_result["consensus_score"],
            "recommendations": swarm_result.get("recommendations", []),
        }
        if saved_memory_data:
            assistant_metadata["saved_memory"] = saved_memory_data

        assistant_msg = AIChatMessage.objects.create(
            session=session,
            role="assistant",
            sender_name=f"Swarm Supervisor ({model_name})",
            content=assistant_reply,
            metadata=assistant_metadata,
        )

        session.save(update_fields=["updated_at"])

        resp_data = {
            "user_message": AIChatMessageSerializer(user_msg).data,
            "assistant_message": AIChatMessageSerializer(assistant_msg).data,
            "swarm": swarm_result,
        }
        if saved_memory_data:
            resp_data["saved_memory"] = saved_memory_data

        return Response(resp_data, status=status.HTTP_201_CREATED)


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


class AIDiscoveryMemoryListCreateView(views.APIView):
    """List all saved discoveries or manually create a new discovery in the Knowledge Vault."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def get(self, request: views.Request) -> Response:
        category = request.query_params.get("category", "").strip()
        is_active = request.query_params.get("is_active", "").strip()
        search = request.query_params.get("search", "").strip()

        qs = AIDiscoveryMemory.objects.all().order_by("-is_active", "-updated_at")
        if category:
            qs = qs.filter(category=category.upper())
        if is_active in ("true", "1"):
            qs = qs.filter(is_active=True)
        elif is_active in ("false", "0"):
            qs = qs.filter(is_active=False)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

        serializer = AIDiscoveryMemorySerializer(qs, many=True)
        return Response({"memories": serializer.data, "count": qs.count()}, status=status.HTTP_200_OK)

    def post(self, request: views.Request) -> Response:
        config = BotConfig.get_active()
        data = request.data.copy()
        if "platform" not in data or not data["platform"]:
            data["platform"] = config.platform
        if "game" not in data or not data["game"]:
            data["game"] = config.game

        serializer = AIDiscoveryMemorySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIDiscoveryMemoryDetailView(views.APIView):
    """Retrieve, update, toggle active status, or delete a saved discovery memory."""
    authentication_classes = [AdminApiKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAdminApiKey]
    throttle_scope = "ai_endpoints"

    def get(self, request: views.Request, memory_id: int) -> Response:
        memory = get_object_or_404(AIDiscoveryMemory, id=memory_id)
        return Response(AIDiscoveryMemorySerializer(memory).data, status=status.HTTP_200_OK)

    def patch(self, request: views.Request, memory_id: int) -> Response:
        memory = get_object_or_404(AIDiscoveryMemory, id=memory_id)
        serializer = AIDiscoveryMemorySerializer(memory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: views.Request, memory_id: int) -> Response:
        memory = get_object_or_404(AIDiscoveryMemory, id=memory_id)
        memory.delete()
        return Response({"deleted": True, "memory_id": memory_id}, status=status.HTTP_200_OK)

