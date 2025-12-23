#!/usr/bin/env python3
"""
Memory Keeper MCP Bridge for Message Bus

This script provides a CLI bridge between message bus code and memory-keeper MCP.
Since message bus runs in subprocess context, this wrapper accepts CLI arguments
and provides memory-keeper operations (save, get, search, watch).

Usage:
    # Publish message
    python3 memory_keeper_bridge.py publish --channel CHANNEL --key KEY --value VALUE [--priority PRIORITY]

    # Subscribe/retrieve messages
    python3 memory_keeper_bridge.py subscribe --channel CHANNEL [--limit LIMIT]

Phase 4: This structure allows easy integration with memory-keeper MCP when available.
For now, it provides simulated channel operations with JSON file storage.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class MemoryKeeperBridge:
    """Bridge to memory-keeper MCP for message bus operations"""

    def __init__(self):
        # Temporary storage for Phase 4 testing
        # In production, this would use memory-keeper MCP directly
        self.storage_dir = Path.home() / ".claude" / "council" / "bus_storage"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def publish(
        self,
        channel: str,
        key: str,
        value: str,
        priority: str = "normal"
    ) -> bool:
        """
        Publish message to memory-keeper channel.

        Phase 4 TODO: Replace with actual MCP call:
        from mcp import tools
        tools.mcp__memory_keeper__context_save(
            channel=channel,
            key=key,
            value=value,
            priority=priority
        )
        """
        try:
            # Simulated channel storage
            channel_file = self.storage_dir / f"{channel}.jsonl"

            message = {
                "key": key,
                "value": value,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            with open(channel_file, "a") as f:
                f.write(json.dumps(message) + "\n")

            return True

        except Exception as e:
            print(f"Publish error: {e}", file=sys.stderr)
            return False

    def subscribe(
        self,
        channel: str,
        limit: int = 100,
        message_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Subscribe to channel and retrieve messages.

        Phase 4 TODO: Replace with actual MCP call:
        from mcp import tools
        result = tools.mcp__memory_keeper__context_get(
            channel=channel,
            limit=limit
        )
        """
        try:
            channel_file = self.storage_dir / f"{channel}.jsonl"

            if not channel_file.exists():
                return []

            messages = []
            with open(channel_file, "r") as f:
                for line in f:
                    if line.strip():
                        msg = json.loads(line)
                        messages.append(msg)

            # Apply filter if provided
            if message_filter:
                filtered = []
                for msg in messages:
                    if all(msg.get(k) == v for k, v in message_filter.items()):
                        filtered.append(msg)
                messages = filtered

            # Apply limit
            return messages[-limit:]

        except Exception as e:
            print(f"Subscribe error: {e}", file=sys.stderr)
            return []


def main():
    parser = argparse.ArgumentParser(description="Memory Keeper MCP bridge for message bus")
    subparsers = parser.add_subparsers(dest="operation", required=True)

    # Publish command
    publish_parser = subparsers.add_parser("publish", help="Publish message to channel")
    publish_parser.add_argument("--channel", required=True, help="Channel name")
    publish_parser.add_argument("--key", required=True, help="Message key")
    publish_parser.add_argument("--value", required=True, help="Message value (JSON)")
    publish_parser.add_argument("--priority", default="normal", choices=["high", "normal", "low"])

    # Subscribe command
    subscribe_parser = subparsers.add_parser("subscribe", help="Subscribe to channel")
    subscribe_parser.add_argument("--channel", required=True, help="Channel name")
    subscribe_parser.add_argument("--limit", type=int, default=100, help="Max messages to retrieve")
    subscribe_parser.add_argument("--filter", help="JSON filter criteria")

    args = parser.parse_args()
    bridge = MemoryKeeperBridge()

    try:
        if args.operation == "publish":
            success = bridge.publish(
                channel=args.channel,
                key=args.key,
                value=args.value,
                priority=args.priority
            )
            if success:
                print(json.dumps({"status": "published", "channel": args.channel}))
            else:
                sys.exit(1)

        elif args.operation == "subscribe":
            message_filter = json.loads(args.filter) if args.filter else None
            messages = bridge.subscribe(
                channel=args.channel,
                limit=args.limit,
                message_filter=message_filter
            )
            print(json.dumps(messages, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
