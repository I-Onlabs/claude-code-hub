"""
DWA Council System - Multi-Agent Debate-Weighted Aggregation

This package implements a sophisticated multi-agent deliberation system using
Debate-Weighted Aggregation (DWA) for critical decision-making.

Components:
- schemas: Pydantic models for proposals, votes, and council sessions
- expertise_registry: Agent expertise weight management
- trigger_detector: Detects conditions requiring council deliberation
- voting_aggregator: DWA formula implementation with escalation logic
- proposal_generator: Collects agent proposals (Ollama integration)
- debate_manager: Manages optional debate rounds
- state_manager: Persists sessions via memory-keeper MCP
- orchestrator: Main entry point for council convocation
"""

__version__ = "0.1.0"
__all__ = [
    "schemas",
    "expertise_registry",
    "trigger_detector",
    "voting_aggregator",
    "proposal_generator",
    "debate_manager",
    "state_manager",
    "orchestrator",
]
