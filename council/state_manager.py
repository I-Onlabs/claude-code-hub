"""
State Manager - Council Session Persistence via memory-keeper MCP

Persists council sessions to memory-keeper MCP for:
- Audit trail and compliance
- Historical analysis
- Learning from past decisions
- Session recovery

Key Functions:
- save_session(): Persist complete council session
- load_session(): Retrieve session by ID
- list_sessions(): Query recent sessions
- get_session_summary(): Condensed session overview
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from council.schemas import CouncilSession, VotingResult


class StateManager:
    """
    Manages council session persistence via memory-keeper MCP.

    Uses memory-keeper channels for structured storage:
    - council:sessions - Full session data
    - council:audit - Audit trail
    - council:decisions - Decision index
    """

    def __init__(self):
        """Initialize state manager with memory-keeper integration"""
        self.channel_prefix = "council"
        # MCP integration will be added in Phase 3
        # For Phase 2, use in-memory storage for testing
        self._sessions: Dict[str, CouncilSession] = {}

    def save_session(self, session: CouncilSession) -> bool:
        """
        Persist council session to memory-keeper.

        Args:
            session: CouncilSession to persist

        Returns:
            True if saved successfully
        """
        try:
            session_id = str(session.session_id)

            # Serialize session to JSON
            session_data = self._serialize_session(session)

            # Save to memory-keeper (Phase 3: use MCP)
            # For Phase 2: in-memory storage
            self._sessions[session_id] = session

            # Also save to audit channel
            self._save_audit_entry(session)

            # Index decision for quick lookup
            self._index_decision(session)

            return True

        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
            return False

    def load_session(self, session_id: UUID) -> Optional[CouncilSession]:
        """
        Load council session by ID.

        Args:
            session_id: Session UUID

        Returns:
            CouncilSession or None if not found
        """
        session_id_str = str(session_id)

        # Phase 2: in-memory lookup
        return self._sessions.get(session_id_str)

    def list_sessions(
        self,
        limit: int = 10,
        domain: Optional[str] = None,
        min_confidence: Optional[float] = None,
        since: Optional[datetime] = None,
    ) -> List[CouncilSession]:
        """
        Query recent council sessions with filters.

        Args:
            limit: Maximum sessions to return
            domain: Filter by domain (e.g., 'security')
            min_confidence: Minimum decision confidence
            since: Only sessions after this datetime

        Returns:
            List of CouncilSession objects
        """
        sessions = list(self._sessions.values())

        # Apply filters
        if domain:
            sessions = [
                s for s in sessions if s.trigger.inferred_domain == domain
            ]

        if min_confidence is not None:
            sessions = [
                s
                for s in sessions
                if s.decision_confidence and s.decision_confidence >= min_confidence
            ]

        if since:
            sessions = [s for s in sessions if s.created_at >= since]

        # Sort by creation time (newest first)
        sessions.sort(key=lambda s: s.created_at, reverse=True)

        return sessions[:limit]

    def get_session_summary(self, session_id: UUID) -> Optional[Dict]:
        """
        Get condensed summary of session.

        Args:
            session_id: Session UUID

        Returns:
            Summary dict or None
        """
        session = self.load_session(session_id)
        if not session:
            return None

        return {
            "session_id": str(session.session_id),
            "created_at": session.created_at.isoformat(),
            "trigger_condition": session.trigger.condition.value,
            "domain": session.trigger.inferred_domain,
            "participating_agents": session.participating_agents,
            "debate_rounds": len(session.debate_rounds),
            "decision": session.decision,
            "confidence": session.decision_confidence,
            "duration_ms": session.total_duration_ms,
            "escalated": session.escalated_to_external,
        }

    def get_domain_statistics(self, domain: str, days: int = 30) -> Dict:
        """
        Get statistics for a domain over time period.

        Args:
            domain: Domain to analyze
            days: Days to look back

        Returns:
            Statistics dict
        """
        since = datetime.utcnow() - timedelta(days=days)
        sessions = self.list_sessions(domain=domain, since=since, limit=1000)

        if not sessions:
            return {
                "domain": domain,
                "total_sessions": 0,
                "avg_confidence": 0.0,
                "escalation_rate": 0.0,
            }

        total_sessions = len(sessions)
        confidences = [
            s.decision_confidence for s in sessions if s.decision_confidence
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        escalations = sum(1 for s in sessions if s.escalated_to_external)
        escalation_rate = escalations / total_sessions if total_sessions > 0 else 0.0

        return {
            "domain": domain,
            "total_sessions": total_sessions,
            "avg_confidence": round(avg_confidence, 2),
            "escalation_rate": round(escalation_rate, 2),
            "avg_duration_ms": round(
                sum(s.total_duration_ms or 0 for s in sessions) / total_sessions, 0
            )
            if total_sessions > 0
            else 0,
        }

    def _serialize_session(self, session: CouncilSession) -> str:
        """
        Serialize session to JSON string.

        Args:
            session: CouncilSession object

        Returns:
            JSON string
        """
        # Convert to dict (Pydantic model_dump)
        session_dict = session.model_dump(mode="json")

        # Convert UUIDs to strings
        return json.dumps(session_dict, indent=2, default=str)

    def _save_audit_entry(self, session: CouncilSession) -> None:
        """
        Save audit trail entry.

        Args:
            session: CouncilSession
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": str(session.session_id),
            "trigger": session.trigger.condition.value,
            "domain": session.trigger.inferred_domain,
            "risk_level": session.trigger.risk_level,
            "agents": session.participating_agents,
            "decision": session.decision,
            "confidence": session.decision_confidence,
        }

        # Phase 3: Save to memory-keeper council:audit channel
        # For Phase 2: log to stderr for visibility
        print(
            f"AUDIT: {audit_entry['trigger']} in {audit_entry['domain']} "
            f"→ {audit_entry['decision'][:50] if audit_entry['decision'] else 'pending'}..."
        )

    def _index_decision(self, session: CouncilSession) -> None:
        """
        Index decision for quick lookup.

        Args:
            session: CouncilSession
        """
        if not session.decision:
            return

        index_entry = {
            "session_id": str(session.session_id),
            "domain": session.trigger.inferred_domain,
            "decision": session.decision,
            "confidence": session.decision_confidence,
            "timestamp": session.created_at.isoformat(),
        }

        # Phase 3: Save to memory-keeper council:decisions channel
        # For Phase 2: in-memory only
        pass

    def clear_cache(self) -> None:
        """Clear in-memory session cache (for testing)"""
        self._sessions.clear()


# Singleton instance
_manager: Optional[StateManager] = None


def get_manager() -> StateManager:
    """Get singleton StateManager instance (lazy initialization)"""
    global _manager
    if _manager is None:
        _manager = StateManager()
    return _manager


# Convenience functions


def save_session(session: CouncilSession) -> bool:
    """Save session (convenience wrapper)"""
    return get_manager().save_session(session)


def load_session(session_id: UUID) -> Optional[CouncilSession]:
    """Load session (convenience wrapper)"""
    return get_manager().load_session(session_id)


def list_sessions(limit: int = 10, **filters) -> List[CouncilSession]:
    """List sessions (convenience wrapper)"""
    return get_manager().list_sessions(limit, **filters)
