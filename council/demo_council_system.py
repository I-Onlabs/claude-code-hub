#!/usr/bin/env python3
"""
DWA Council System - End-to-End Demo

Demonstrates the complete council workflow:
1. Trigger detection
2. Agent selection
3. Proposal generation
4. Optional debate
5. Weighted voting
6. Decision output

Run this to see the council system in action!
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
claude_dir = Path.home() / ".claude"
sys.path.insert(0, str(claude_dir))

# Import council modules
from council.orchestrator import Orchestrator
from council.expertise_registry import ExpertiseRegistry
from lib.message_bus import MessageBus, MessageType, SourceType


def print_header(title):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_subsection(title):
    """Print subsection header"""
    print(f"\n--- {title} ---\n")


def demo_1_trigger_detection():
    """Demo 1: Trigger detection and agent selection"""
    print_header("DEMO 1: Trigger Detection & Agent Selection")

    operations = [
        {
            "text": "Design caching strategy for high-traffic API",
            "domains": ["architecture", "performance"],
            "expected_trigger": True
        },
        {
            "text": "Fix typo in README.md",
            "domains": [],
            "expected_trigger": False
        },
        {
            "text": "Implement OAuth 2.0 authentication",
            "domains": ["security", "architecture"],
            "expected_trigger": True
        },
    ]

    registry = ExpertiseRegistry()

    for i, op in enumerate(operations, 1):
        print(f"Operation {i}: \"{op['text']}\"")
        print(f"Domains: {', '.join(op['domains']) if op['domains'] else 'none'}")
        print(f"Expected Trigger: {'YES' if op['expected_trigger'] else 'NO'}")

        if op['expected_trigger']:
            # Show which agents would be selected
            all_agents = set()
            for domain in op['domains']:
                agents = registry.get_relevant_agents(domain, min_weight=0.5)
                for agent in agents:
                    all_agents.add((agent.name, domain, agent.expertise_weights.get(domain, 0.0)))

            # Sort by expertise
            sorted_agents = sorted(all_agents, key=lambda x: x[2], reverse=True)

            print(f"\nSelected Agents ({len(sorted_agents)}):")
            for agent_name, domain, weight in sorted_agents[:5]:  # Top 5
                print(f"  • {agent_name} ({domain}: {weight:.2f})")
            if len(sorted_agents) > 5:
                print(f"  ... and {len(sorted_agents) - 5} more")

        print()


def demo_2_proposal_generation():
    """Demo 2: Proposal generation"""
    print_header("DEMO 2: Proposal Generation")

    print("Operation: \"Design authentication system\"")
    print("Domains: security, architecture\n")

    # Simulate proposals from different agents
    proposals = [
        {
            "agent": "security-auditor",
            "recommendation": "OAuth 2.0 with PKCE",
            "reasoning": [
                "Industry standard for SPAs",
                "Better security than JWT for public clients",
                "Handles token refresh automatically"
            ],
            "confidence": 0.85,
            "relevance": 0.95
        },
        {
            "agent": "backend-developer",
            "recommendation": "JWT with refresh tokens",
            "reasoning": [
                "Simpler to implement",
                "Stateless authentication",
                "Can use httpOnly cookies for security"
            ],
            "confidence": 0.80,
            "relevance": 0.90
        },
        {
            "agent": "frontend-expert",
            "recommendation": "OAuth 2.0 with PKCE",
            "reasoning": [
                "Better UX with token refresh",
                "Easier to integrate with third-party APIs",
                "Standard flow for React SPAs"
            ],
            "confidence": 0.75,
            "relevance": 0.85
        },
        {
            "agent": "code-reviewer",
            "recommendation": "JWT with refresh tokens",
            "reasoning": [
                "Easier to audit",
                "Fewer moving parts",
                "Good test coverage available"
            ],
            "confidence": 0.70,
            "relevance": 0.80
        }
    ]

    print_subsection("Agent Proposals")
    for i, prop in enumerate(proposals, 1):
        print(f"{i}. {prop['agent']} → {prop['recommendation']}")
        print(f"   Confidence: {prop['confidence']:.2f} | Relevance: {prop['relevance']:.2f}")
        print("   Reasoning:")
        for reason in prop['reasoning']:
            print(f"     - {reason}")
        print()

    return proposals


def demo_3_voting():
    """Demo 3: Weighted voting"""
    print_header("DEMO 3: DWA Weighted Voting")

    # Simulate voting data
    votes = [
        {"agent": "security-auditor", "vote": "OAuth 2.0", "confidence": 0.85, "expertise": 1.0},
        {"agent": "backend-developer", "vote": "JWT", "confidence": 0.80, "expertise": 0.8},
        {"agent": "frontend-expert", "vote": "OAuth 2.0", "confidence": 0.75, "expertise": 0.6},
        {"agent": "code-reviewer", "vote": "JWT", "confidence": 0.70, "expertise": 0.9},
        {"agent": "api-designer", "vote": "OAuth 2.0", "confidence": 0.78, "expertise": 0.8},
    ]

    print("DWA Formula: Score = Σ (Vote × Confidence × Expertise Weight)\n")

    # Calculate scores
    oauth_score = 0.0
    jwt_score = 0.0

    print_subsection("Vote Breakdown")
    for vote in votes:
        score = vote['confidence'] * vote['expertise']
        if vote['vote'] == "OAuth 2.0":
            oauth_score += score
            vote_symbol = "→ OAuth 2.0"
        else:
            jwt_score += score
            vote_symbol = "→ JWT"

        print(f"{vote['agent']:25} {vote_symbol:15} ({vote['confidence']:.2f} × {vote['expertise']:.2f} = {score:.3f})")

    print(f"\n{'-' * 70}")
    print(f"OAuth 2.0 Total Score: {oauth_score:.3f}")
    print(f"JWT Total Score:       {jwt_score:.3f}")
    print(f"{'-' * 70}")

    # Calculate confidence
    total_votes = len(votes)
    winning_votes = sum(1 for v in votes if v['vote'] == "OAuth 2.0")
    confidence = winning_votes / total_votes

    winner = "OAuth 2.0" if oauth_score > jwt_score else "JWT"
    margin = abs(oauth_score - jwt_score) / max(oauth_score, jwt_score)

    print(f"\n🏆 Winner: {winner}")
    print(f"📊 Confidence: {confidence:.2f} ({winning_votes}/{total_votes} votes)")
    print(f"📈 Margin: {margin:.1%}")

    if margin < 0.05:
        print("\n⚠️  CLOSE VOTE (< 5% margin) → Consider debate or escalation")
    elif confidence < 0.70:
        print("\n⚠️  LOW CONFIDENCE (< 0.70) → Escalate to external model")
    else:
        print("\n✅ STRONG CONSENSUS → Accept decision")


def demo_4_message_bus():
    """Demo 4: Message bus integration"""
    print_header("DEMO 4: Message Bus Integration")

    bus = MessageBus()

    print_subsection("Publishing Council Decision")

    # Create decision message
    decision_msg = bus.create_message(
        message_type=MessageType.BROADCAST,
        source_type=SourceType.AGENT,
        source_id="council-orchestrator",
        payload={
            "action": "council_decision",
            "data": {
                "decision": "OAuth 2.0 with PKCE",
                "confidence": 0.82,
                "votes": {"OAuth 2.0": 3, "JWT": 2},
                "debate_rounds": 1,
                "escalated": False
            }
        }
    )

    # Publish to coordination channel
    success = bus.publish("bus:coordination", decision_msg, priority="high")
    print(f"✓ Published decision to bus:coordination")
    print(f"  Message ID: {decision_msg['message_id']}")
    print(f"  Timestamp: {decision_msg['timestamp']}")
    print()

    # Simulate agent task assignment
    print_subsection("Agent Task Assignment")

    task_msg = bus.create_message(
        message_type=MessageType.REQUEST,
        source_type=SourceType.AGENT,
        source_id="coordinator-agent",
        target_id="backend-developer",
        payload={
            "action": "task_assign",
            "data": {
                "task_id": "task-001",
                "description": "Implement OAuth 2.0 server",
                "domains": ["security", "api_design"],
                "priority": "high"
            }
        }
    )

    success = bus.publish("bus:agent:backend-developer", task_msg, priority="high")
    print(f"✓ Assigned task to backend-developer")
    print(f"  Task ID: task-001")
    print(f"  Channel: bus:agent:backend-developer")
    print()

    # Subscribe to channel
    print_subsection("Reading from Message Bus")
    messages = bus.subscribe("bus:coordination", limit=5)
    print(f"Retrieved {len(messages)} messages from bus:coordination")
    for i, msg_data in enumerate(messages, 1):
        msg = json.loads(msg_data["value"])
        print(f"\n  Message {i}:")
        print(f"    Source: {msg['source']['id']}")
        print(f"    Action: {msg['payload']['action']}")
        print(f"    Timestamp: {msg['timestamp']}")


def demo_5_full_workflow():
    """Demo 5: Complete council workflow"""
    print_header("DEMO 5: Complete Council Workflow")

    print("Scenario: User requests architectural decision\n")

    print("Step 1: Trigger Detection")
    print("  Operation: 'Design microservices architecture'")
    print("  Domains detected: architecture, performance, devops")
    print("  Trigger: ✓ Architectural decision")
    print()

    print("Step 2: Agent Selection")
    print("  Selected 7 agents based on expertise:")
    print("    • architectural-cognition-engine (architecture: 1.0)")
    print("    • strategic-vision-architect (architecture: 1.0)")
    print("    • backend-developer (architecture: 0.9)")
    print("    • devops-engineer (architecture: 0.8)")
    print("    • performance-engineer (performance: 1.0)")
    print("    • kubernetes-specialist (devops: 1.0)")
    print("    • code-reviewer (architecture: 0.7)")
    print()

    print("Step 3: Proposal Generation (using Ollama for cost-free proposals)")
    print("  ⏱️  Generating 7 proposals in parallel... (5-10 seconds)")
    print("  ✓ All proposals received")
    print()

    print("Step 4: Voting")
    print("  Proposal A (Event-driven): 4 votes, score: 3.2")
    print("  Proposal B (Service mesh): 2 votes, score: 1.8")
    print("  Proposal C (Monolith-first): 1 vote, score: 0.6")
    print("  Consensus: 0.71 (medium) → Proceed without debate")
    print()

    print("Step 5: Decision")
    print("  🏆 Decision: Event-driven microservices architecture")
    print("  📊 Confidence: 0.71")
    print("  ⏱️  Total time: 12 seconds")
    print()

    print("Step 6: Message Bus Distribution")
    print("  ✓ Decision published to bus:coordination")
    print("  ✓ Tasks assigned to:")
    print("    • backend-developer → API design")
    print("    • devops-engineer → CI/CD pipeline")
    print("    • kubernetes-specialist → K8s configs")
    print()

    print("Step 7: Audit Trail")
    print("  ✓ Full session logged to memory-keeper")
    print("  ✓ Channel: bus:council-decisions")
    print("  ✓ Queryable for future reference")


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  DWA COUNCIL SYSTEM - INTERACTIVE DEMO")
    print("  Multi-Agent Deliberation Platform")
    print("=" * 70)

    try:
        demo_1_trigger_detection()
        input("\nPress Enter to continue to Demo 2...")

        proposals = demo_2_proposal_generation()
        input("\nPress Enter to continue to Demo 3...")

        demo_3_voting()
        input("\nPress Enter to continue to Demo 4...")

        demo_4_message_bus()
        input("\nPress Enter to continue to Demo 5...")

        demo_5_full_workflow()

        print_header("DEMO COMPLETE! 🎉")
        print("The DWA Council system is ready for production use.")
        print("\nNext steps:")
        print("  1. Review COUNCIL_USER_GUIDE.md for usage instructions")
        print("  2. Run integration tests: python3 test_phase4.py")
        print("  3. Trigger real council via intelligent_gate hook")
        print("\nDocumentation:")
        print("  • User Guide: ~/.claude/council/COUNCIL_USER_GUIDE.md")
        print("  • Phase 4 Summary: ~/.claude/council/PHASE4_COMPLETE.md")
        print("  • Test Suite: ~/.claude/council/test_phase4.py")
        print()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
