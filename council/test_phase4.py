#!/usr/bin/env python3
"""
Phase 4 Integration Tests

Tests for:
1. Expertise weights on all agents
2. Memory-keeper bridge (publish/subscribe)
3. Consult-llm bridge (external model consultation)
4. Council + Message Bus integration
5. Coordinator agent readiness
"""

import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
claude_dir = Path.home() / ".claude"
sys.path.insert(0, str(claude_dir))

# Import council modules
import council.expertise_registry as expertise_registry

# Import lib modules
from lib.message_bus import MessageBus, MessageType, SourceType

ExpertiseRegistry = expertise_registry.ExpertiseRegistry


def test_1_expertise_weights():
    """TEST 1: Verify all agents have expertise_weights"""
    print("\n" + "=" * 60)
    print("TEST 1: Expertise Weights on All Agents")
    print("=" * 60)

    registry = ExpertiseRegistry()
    agents_dir = Path.home() / ".claude" / "agents"

    # Get all agent files
    agent_files = list(agents_dir.glob("*.md"))
    print(f"Found {len(agent_files)} agent files")

    agents_without_weights = []
    agents_with_weights = []

    for agent_file in agent_files:
        agent_name = agent_file.stem
        try:
            # Check if agent is in registry
            agent = registry.get_agent_expertise(agent_name)
            if agent:
                agents_with_weights.append(agent_name)
                weights = agent.expertise_weights
                role = agent.council_role
                print(f"  ✓ {agent_name}: {len(weights)} weights, role={role.value}")
            else:
                agents_without_weights.append(agent_name)
                print(f"  ✗ {agent_name}: NOT in registry")
        except Exception as e:
            print(f"  ✗ {agent_name}: ERROR - {e}")
            agents_without_weights.append(agent_name)

    if agents_without_weights:
        print(f"\n❌ TEST 1 FAILED: {len(agents_without_weights)} agents missing expertise_weights")
        for agent in agents_without_weights:
            print(f"  - {agent}")
        return False
    else:
        print(f"\n✅ TEST 1 PASSED: All {len(agents_with_weights)} agents have expertise_weights")
        return True


def test_2_memory_keeper_bridge():
    """TEST 2: Memory-keeper bridge publish/subscribe"""
    print("\n" + "=" * 60)
    print("TEST 2: Memory-Keeper Bridge (Publish/Subscribe)")
    print("=" * 60)

    bridge_script = Path.home() / ".claude" / "lib" / "memory_keeper_bridge.py"
    channel = "test:phase4"
    key = str(uuid4())
    value = json.dumps({"test": "phase4", "data": "integration"})

    # Test publish
    print(f"Publishing to channel {channel}...")
    result = subprocess.run(
        [
            "python3",
            str(bridge_script),
            "publish",
            "--channel", channel,
            "--key", key,
            "--value", value,
            "--priority", "normal"
        ],
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.returncode != 0:
        print(f"❌ TEST 2 FAILED: Publish failed - {result.stderr}")
        return False

    print(f"  ✓ Published successfully")

    # Test subscribe
    print(f"Subscribing to channel {channel}...")
    result = subprocess.run(
        [
            "python3",
            str(bridge_script),
            "subscribe",
            "--channel", channel,
            "--limit", "10"
        ],
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.returncode != 0:
        print(f"❌ TEST 2 FAILED: Subscribe failed - {result.stderr}")
        return False

    messages = json.loads(result.stdout)
    print(f"  ✓ Retrieved {len(messages)} messages")

    # Verify our message is there
    found = False
    for msg in messages:
        if msg.get("key") == key:
            found = True
            print(f"  ✓ Found our message: {msg['value']}")
            break

    if not found:
        print(f"❌ TEST 2 FAILED: Published message not found in subscribe results")
        return False

    print(f"\n✅ TEST 2 PASSED: Memory-keeper bridge working")
    return True


def test_3_consult_llm_bridge():
    """TEST 3: Consult-llm bridge (external model consultation)"""
    print("\n" + "=" * 60)
    print("TEST 3: Consult-LLM Bridge (External Model)")
    print("=" * 60)

    wrapper_script = Path.home() / ".claude" / "council" / "consult_external_model.py"
    prompt = """Test escalation prompt for Phase 4 integration.

**PROPOSALS FROM AGENTS**
1. security-auditor (confidence: 0.75)
   Recommendation: Implement JWT with RS256
   Reasoning: Industry standard, secure token handling

2. backend-developer (confidence: 0.80)
   Recommendation: Use OAuth 2.0 with PKCE
   Reasoning: Modern standard, better security for SPAs
"""

    print(f"Consulting external model...")

    # Test with auto-select
    result = subprocess.run(
        [
            "python3",
            str(wrapper_script),
            "--prompt", prompt,
            "--format", "text"
        ],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        print(f"❌ TEST 3 FAILED: Consultation failed - {result.stderr}")
        return False

    response = result.stdout.strip()
    print(f"  ✓ Response received:\n{response}")

    # Verify response has required fields
    if "Recommendation:" in response and "Model:" in response:
        print(f"\n✅ TEST 3 PASSED: Consult-llm bridge working")
        return True
    else:
        print(f"❌ TEST 3 FAILED: Response missing required fields")
        return False


def test_4_message_bus_integration():
    """TEST 4: Message bus with memory-keeper integration"""
    print("\n" + "=" * 60)
    print("TEST 4: Message Bus Integration")
    print("=" * 60)

    bus = MessageBus()

    # Create test message
    message = bus.create_message(
        message_type=MessageType.BROADCAST,
        source_type=SourceType.AGENT,
        source_id="test-agent",
        payload={"action": "test", "data": {"test_id": "phase4"}}
    )

    print(f"Publishing via MessageBus...")
    success = bus.publish("bus:test-phase4", message, priority="normal")

    if not success:
        print(f"❌ TEST 4 FAILED: MessageBus publish failed")
        return False

    print(f"  ✓ Published message {message['message_id']}")

    # Subscribe via MessageBus
    print(f"Subscribing via MessageBus...")
    messages = bus.subscribe("bus:test-phase4", limit=10)

    if not messages:
        print(f"❌ TEST 4 FAILED: No messages retrieved")
        return False

    print(f"  ✓ Retrieved {len(messages)} messages")

    # Verify our message
    found = False
    for msg_data in messages:
        # Parse the stored JSON value
        try:
            stored_msg = json.loads(msg_data["value"])
            if stored_msg["message_id"] == message["message_id"]:
                found = True
                print(f"  ✓ Found our message in bus")
                break
        except (json.JSONDecodeError, KeyError):
            pass

    if not found:
        print(f"❌ TEST 4 FAILED: Published message not found via subscribe")
        return False

    print(f"\n✅ TEST 4 PASSED: Message bus integration working")
    return True


def test_5_expertise_matching():
    """TEST 5: Expertise-based agent matching"""
    print("\n" + "=" * 60)
    print("TEST 5: Expertise-Based Agent Matching")
    print("=" * 60)

    registry = ExpertiseRegistry()

    # Test domain matching
    test_cases = [
        ("security", ["security-auditor", "backend-developer", "devops-engineer"]),
        ("architecture", ["architectural-cognition-engine", "strategic-vision-architect"]),
        ("testing", ["qa-expert", "error-detective"]),
        ("frontend", ["frontend-expert"]),
        ("database", ["database-architect", "data-engineer"]),
    ]

    all_passed = True
    for domain, expected_agents in test_cases:
        agents_list = registry.get_relevant_agents(domain, min_weight=0.5)
        agent_names = [a.name for a in agents_list]

        print(f"\nDomain '{domain}' → {len(agents_list)} agents:")
        for agent in agents_list[:3]:  # Show top 3
            expertise = agent.expertise_weights.get(domain, 0.0)
            print(f"  - {agent.name} (expertise: {expertise:.2f})")

        # Check if expected agents are present
        for expected in expected_agents:
            if expected not in agent_names:
                print(f"  ✗ Expected agent '{expected}' not found!")
                all_passed = False

    if all_passed:
        print(f"\n✅ TEST 5 PASSED: Expertise matching working correctly")
        return True
    else:
        print(f"\n❌ TEST 5 FAILED: Some expected agents not matched")
        return False


def test_6_coordinator_readiness():
    """TEST 6: Coordinator agent configuration readiness"""
    print("\n" + "=" * 60)
    print("TEST 6: Coordinator Agent Readiness")
    print("=" * 60)

    coordinator_file = Path.home() / ".claude" / "agents" / "coordinator-agent.md"

    if not coordinator_file.exists():
        print(f"❌ TEST 6 FAILED: Coordinator agent file not found")
        return False

    print(f"  ✓ Coordinator agent file exists")

    # Check for key sections
    content = coordinator_file.read_text()

    required_sections = [
        "Registry Management",
        "Task Dispatch",
        "select_agent_for_task",
        "expertise_weights",
        "council_role"
    ]

    missing = []
    for section in required_sections:
        if section in content:
            print(f"  ✓ Section found: {section}")
        else:
            print(f"  ✗ Section missing: {section}")
            missing.append(section)

    if missing:
        print(f"\n❌ TEST 6 FAILED: Missing required sections: {missing}")
        return False

    print(f"\n✅ TEST 6 PASSED: Coordinator agent ready")
    return True


def main():
    """Run all Phase 4 integration tests"""
    print("\n" + "=" * 60)
    print("PHASE 4 INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        test_1_expertise_weights,
        test_2_memory_keeper_bridge,
        test_3_consult_llm_bridge,
        test_4_message_bus_integration,
        test_5_expertise_matching,
        test_6_coordinator_readiness,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ TEST EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for i, (test_func, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"Test {i} ({test_func.__name__}): {status}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 4 integration complete.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
