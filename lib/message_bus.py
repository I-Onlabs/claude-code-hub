"""
Message Bus - memory-keeper MCP Channel Communication

Provides message formatting, channel operations, and pub/sub patterns for
agent-to-agent communication via memory-keeper MCP.

Channel Structure:
- bus:coordination - Broadcast announcements to all agents
- bus:registry - Agent registration and discovery
- bus:task-queue - Pending task assignments
- bus:results - Task completion results
- bus:agent:{id} - Point-to-point agent messages
- bus:hooks - Hook events (tool use, sessions)
- bus:skills - Skill invocation events

Message Format:
{
  "message_id": "uuid",
  "timestamp": "ISO-8601",
  "message_type": "request|response|broadcast|event",
  "source": {"type": "agent|hook|skill", "id": "agent-name"},
  "target": {"type": "agent|channel", "id": "target-name"},
  "correlation_id": "uuid (for request/response pairing)",
  "payload": {
    "action": "task_assign|task_complete|critique|vote|...",
    "data": {}
  }
}
"""

import json
import subprocess
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


class MessageType(Enum):
    """Message types for bus communication"""

    REQUEST = "request"  # Agent requests action
    RESPONSE = "response"  # Response to request
    BROADCAST = "broadcast"  # One-to-many announcement
    EVENT = "event"  # Hook/skill event notification


class SourceType(Enum):
    """Source types for messages"""

    AGENT = "agent"
    HOOK = "hook"
    SKILL = "skill"
    SYSTEM = "system"


class MessageBus:
    """
    Message bus for agent coordination via memory-keeper MCP.

    Uses memory-keeper channels for persistent, queryable messaging.
    """

    # Standard channel names
    CHANNEL_COORDINATION = "bus:coordination"
    CHANNEL_REGISTRY = "bus:registry"
    CHANNEL_TASK_QUEUE = "bus:task-queue"
    CHANNEL_RESULTS = "bus:results"
    CHANNEL_HOOKS = "bus:hooks"
    CHANNEL_SKILLS = "bus:skills"

    def __init__(self):
        """Initialize message bus"""
        # Add lib path for imports
        sys.path.insert(0, str(Path.home() / ".claude"))

    def create_message(
        self,
        message_type: MessageType,
        source_type: SourceType,
        source_id: str,
        payload: Dict[str, Any],
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a formatted message for bus transmission.

        Args:
            message_type: Type of message (request/response/broadcast/event)
            source_type: Type of source (agent/hook/skill)
            source_id: Source identifier
            payload: Message payload with action and data
            target_type: Optional target type (agent/channel)
            target_id: Optional target identifier
            correlation_id: Optional correlation ID for request/response

        Returns:
            Formatted message dict
        """
        message = {
            "message_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message_type": message_type.value,
            "source": {"type": source_type.value, "id": source_id},
            "payload": payload,
        }

        if target_type and target_id:
            message["target"] = {"type": target_type, "id": target_id}

        if correlation_id:
            message["correlation_id"] = correlation_id

        return message

    def publish(
        self, channel: str, message: Dict[str, Any], priority: str = "normal"
    ) -> bool:
        """
        Publish message to memory-keeper channel.

        Args:
            channel: Channel name (e.g., "bus:coordination")
            message: Formatted message dict
            priority: Message priority (high/normal/low)

        Returns:
            True if published successfully
        """
        try:
            # Use memory-keeper context_save to publish to channel
            # Key format: {channel}:{message_id}
            key = f"{message['message_id']}"
            value = json.dumps(message)

            # Phase 4: Use memory-keeper bridge
            priority_map = {"high": "high", "normal": "normal", "low": "low"}
            bridge_script = Path(__file__).parent / "memory_keeper_bridge.py"

            cmd = [
                "python3",
                str(bridge_script),
                "publish",
                "--channel", channel,
                "--key", key,
                "--value", value,
                "--priority", priority_map.get(priority, "normal")
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print(
                    f"[MessageBus] Published to {channel}: {message['payload'].get('action', 'unknown')}",
                    file=sys.stderr,
                )
                return True
            else:
                print(f"[MessageBus] Publish failed: {result.stderr}", file=sys.stderr)
                return False

        except Exception as e:
            print(f"[MessageBus] Publish failed: {e}", file=sys.stderr)
            return False

    def subscribe(
        self,
        channel: str,
        message_filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Subscribe to channel and retrieve messages.

        Args:
            channel: Channel name
            message_filter: Optional filter criteria
            limit: Max messages to retrieve

        Returns:
            List of messages from channel
        """
        try:
            # Phase 4: Use memory-keeper bridge
            bridge_script = Path(__file__).parent / "memory_keeper_bridge.py"

            cmd = [
                "python3",
                str(bridge_script),
                "subscribe",
                "--channel", channel,
                "--limit", str(limit)
            ]

            if message_filter:
                cmd.extend(["--filter", json.dumps(message_filter)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                messages = json.loads(result.stdout.strip() or "[]")
                print(f"[MessageBus] Retrieved {len(messages)} messages from {channel}", file=sys.stderr)
                return messages
            else:
                print(f"[MessageBus] Subscribe failed: {result.stderr}", file=sys.stderr)
                return []

        except Exception as e:
            print(f"[MessageBus] Subscribe failed: {e}", file=sys.stderr)
            return []

    def get_agent_channel(self, agent_id: str) -> str:
        """Get point-to-point channel name for agent"""
        return f"bus:agent:{agent_id}"

    def broadcast_coordination(self, announcement: str, sender_id: str) -> bool:
        """
        Broadcast coordination announcement to all agents.

        Args:
            announcement: Announcement text
            sender_id: Sender identifier

        Returns:
            True if broadcast succeeded
        """
        message = self.create_message(
            message_type=MessageType.BROADCAST,
            source_type=SourceType.SYSTEM,
            source_id=sender_id,
            payload={"action": "coordination_announcement", "data": {"announcement": announcement}},
        )
        return self.publish(self.CHANNEL_COORDINATION, message, priority="high")

    def publish_task_assignment(
        self, agent_id: str, task: Dict[str, Any], coordinator_id: str = "coordinator"
    ) -> bool:
        """
        Publish task assignment to task queue.

        Args:
            agent_id: Target agent
            task: Task details (task_id, description, context, etc.)
            coordinator_id: Coordinator assigning task

        Returns:
            True if published
        """
        message = self.create_message(
            message_type=MessageType.REQUEST,
            source_type=SourceType.AGENT,
            source_id=coordinator_id,
            payload={"action": "task_assign", "data": task},
            target_type="agent",
            target_id=agent_id,
        )

        # Publish to both task queue and agent's personal channel
        queue_success = self.publish(self.CHANNEL_TASK_QUEUE, message)
        agent_success = self.publish(self.get_agent_channel(agent_id), message)

        return queue_success and agent_success

    def publish_task_result(
        self, task_id: str, result: Dict[str, Any], agent_id: str
    ) -> bool:
        """
        Publish task completion result.

        Args:
            task_id: Task identifier
            result: Task result data
            agent_id: Agent completing task

        Returns:
            True if published
        """
        message = self.create_message(
            message_type=MessageType.RESPONSE,
            source_type=SourceType.AGENT,
            source_id=agent_id,
            payload={"action": "task_complete", "data": {"task_id": task_id, "result": result}},
            correlation_id=task_id,  # Correlate with original task
        )
        return self.publish(self.CHANNEL_RESULTS, message, priority="high")

    def register_agent(self, agent_id: str, capabilities: List[str]) -> bool:
        """
        Register agent in registry channel.

        Args:
            agent_id: Agent identifier
            capabilities: List of agent capabilities/domains

        Returns:
            True if registered
        """
        message = self.create_message(
            message_type=MessageType.EVENT,
            source_type=SourceType.AGENT,
            source_id=agent_id,
            payload={
                "action": "agent_register",
                "data": {"agent_id": agent_id, "capabilities": capabilities, "status": "active"},
            },
        )
        return self.publish(self.CHANNEL_REGISTRY, message)

    def publish_hook_event(self, hook_name: str, event_data: Dict[str, Any]) -> bool:
        """
        Publish hook event to hooks channel.

        Args:
            hook_name: Hook name (e.g., "post_tool_use")
            event_data: Event details

        Returns:
            True if published
        """
        message = self.create_message(
            message_type=MessageType.EVENT,
            source_type=SourceType.HOOK,
            source_id=hook_name,
            payload={"action": "hook_event", "data": event_data},
        )
        return self.publish(self.CHANNEL_HOOKS, message)

    def publish_skill_event(self, skill_name: str, event_data: Dict[str, Any]) -> bool:
        """
        Publish skill invocation event.

        Args:
            skill_name: Skill name
            event_data: Event details

        Returns:
            True if published
        """
        message = self.create_message(
            message_type=MessageType.EVENT,
            source_type=SourceType.SKILL,
            source_id=skill_name,
            payload={"action": "skill_event", "data": event_data},
        )
        return self.publish(self.CHANNEL_SKILLS, message)


# Singleton instance
_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get singleton MessageBus instance (lazy initialization)"""
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus
