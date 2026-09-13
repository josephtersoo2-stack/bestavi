from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BotConfigView,
    BotControlView,
    BotStatusView,
    ExtractedOddsViewSet,
    BetRecordViewSet,
    BotLogViewSet,
    AnalyticsView,
    SafeZoneAnalyticsView,
    ExportOddsView,
)
from .ai_views import (
    PlatformsListView,
    AIModelsListView,
    AIStatusView,
    AIRiskAnalysisView,
    AIStrategyRecommendView,
    AIChatCopilotView,
)
from .chat_views import (
    AIChatSessionListCreateView,
    AIChatSessionDetailView,
    AIChatMessageSendView,
    AISwarmStatusView,
    AISwarmEvaluateView,
)

router = DefaultRouter()
router.register(r'odds', ExtractedOddsViewSet, basename='odds')
router.register(r'bets', BetRecordViewSet, basename='bets')
router.register(r'logs', BotLogViewSet, basename='logs')

urlpatterns = [
    path('settings/', BotConfigView.as_view(), name='bot-settings'),
    path('bot/control/', BotControlView.as_view(), name='bot-control'),
    path('bot/status/', BotStatusView.as_view(), name='bot-status'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('analytics/safezone/', SafeZoneAnalyticsView.as_view(), name='safezone-analytics'),
    path('export/odds/', ExportOddsView.as_view(), name='export-odds'),

    # Platform Addons & AI Copilot Endpoints
    path('platforms/', PlatformsListView.as_view(), name='platforms-list'),
    path('ai/models/', AIModelsListView.as_view(), name='ai-models'),
    path('ai/status/', AIStatusView.as_view(), name='ai-status'),
    path('ai/analyze/', AIRiskAnalysisView.as_view(), name='ai-analyze'),
    path('ai/recommend/', AIStrategyRecommendView.as_view(), name='ai-recommend'),
    path('ai/chat/', AIChatCopilotView.as_view(), name='ai-chat'),

    # Multi-Thread Chat & Enterprise Multi-Agent Swarm
    path('ai/chats/', AIChatSessionListCreateView.as_view(), name='ai-chats-list'),
    path('ai/chats/<int:session_id>/', AIChatSessionDetailView.as_view(), name='ai-chat-detail'),
    path('ai/chats/<int:session_id>/message/', AIChatMessageSendView.as_view(), name='ai-chat-message'),
    path('ai/swarm/status/', AISwarmStatusView.as_view(), name='ai-swarm-status'),
    path('ai/swarm/evaluate/', AISwarmEvaluateView.as_view(), name='ai-swarm-evaluate'),

    path('', include(router.urls)),
]
