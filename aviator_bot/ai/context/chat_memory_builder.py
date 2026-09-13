from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("aviator_bot.ai.context.chat_memory")


def build_chat_memory_context(
    current_session_messages: list[dict[str, Any]],
    past_sessions_summary: list[dict[str, Any]] | None = None,
) -> str:
    """Build a unified memory prompt block containing cross-session history & current conversation."""
    sections = []

    # 1. Cross-session contextual memory
    if past_sessions_summary:
        sections.append("### CROSS-SESSION HISTORICAL MEMORY (Past User Threads):")
        for sess in past_sessions_summary[:5]:  # include up to 5 most recent past sessions
            title = sess.get("title", "Previous Session")
            msg_count = sess.get("msg_count", 0)
            sample_exchanges = sess.get("sample_exchanges", [])
            date_str = sess.get("updated_at", "")[:10]

            sections.append(f"Thread [{title}] ({date_str}, {msg_count} msgs):")
            for ex in sample_exchanges[:3]:
                role = ex.get("role", "user")
                content = (ex.get("content", "")).replace("\n", " ")[:120]
                sections.append(f"  - {role.upper()}: {content}")
        sections.append(
            "Note: The user may reference questions, strategies, or decisions made in the above past threads. "
            "Maintain continuity and acknowledge established context seamlessly."
        )

    # 2. Current session context
    if current_session_messages:
        sections.append("\n### ACTIVE CONVERSATION HISTORY:")
        for msg in current_session_messages[-10:]:  # last 10 messages of current thread
            sender = msg.get("sender_name") or msg.get("role", "User")
            content = msg.get("content", "")
            sections.append(f"[{sender}]: {content}")

    return "\n".join(sections)


def build_discovery_memories_context(discovery_memories: list[dict[str, Any]] | None = None) -> str:
    """Format active user discoveries & empirical findings into a high-priority knowledge bank."""
    if not discovery_memories:
        return ""

    lines = [
        "### PERMANENT DISCOVERY MEMORY BANK & STRATEGIC VAULT:",
        "The following empirical findings, streak timing patterns, and strategic rules were discovered by the user and confirmed by the swarm. You MUST remember, factor in, and respect these rules in all evaluations and replies:",
    ]
    for mem in discovery_memories[:15]:
        title = mem.get("title", "Untitled Discovery")
        category = mem.get("category", "GENERAL")
        content = mem.get("content", "")
        lines.append(f"- [{category}] **{title}**: {content}")

    lines.append(
        "DIRECTIVE: Always acknowledge, reference, and synthesize these past discoveries when answering questions, analyzing risk, or predicting outcomes."
    )
    return "\n".join(lines)

