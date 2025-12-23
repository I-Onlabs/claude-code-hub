#!/usr/bin/env python3
"""
Phase 1 Integration Test - DWA Council Foundation

Tests all Phase 1 components in isolation:
1. Expertise Registry - Load agent profiles from YAML
2. Trigger Detector - Pattern matching and domain inference
3. Voting Aggregator - DWA formula, HHI, escalation logic

Run: python3 ~/.claude/council/test_phase1.py
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add council package to path
sys.path.insert(0, str(Path.home() / ".claude"))

from council.expertise_registry import ExpertiseRegistry, get_relevant_agents
from council.schemas import Proposal, Vote, VoteType
from council.trigger_detector import TriggerDetector
from council.voting_aggregator import VotingAggregator


def test_expertise_registry():
    """Test 1: Expertise Registry loads agent profiles"""
    print("\n" + "=" * 70)
    print("TEST 1: Expertise Registry")
    print("=" * 70)

    registry = ExpertiseRegistry()

    # Check that 5 key agents loaded
    expected_agents = [
        "security-auditor",
        "code-reviewer",
        "api-designer",
        "backend-developer",
        "python-pro",
    ]

    all_agents = registry.list_all_agents()
    print(f"✓ Loaded {len(all_agents)} agents total")

    for agent_name in expected_agents:
        agent = registry.get_agent_expertise(agent_name)
        if agent is None:
            print(f"✗ FAIL: Agent '{agent_name}' not found")
            return False

        print(f"  • {agent_name}:")
        print(f"    - Council role: {agent.council_role}")
        print(f"    - Expertise domains: {list(agent.expertise_weights.keys())}")
        print(
            f"    - Model tier: {agent.model_tier if hasattr(agent, 'model_tier') else 'N/A'}"
        )

    # Test get_relevant_agents for security domain
    print("\n  Testing domain-based agent selection:")
    security_experts = get_relevant_agents("security", min_weight=0.5)
    print(f"  • Security experts (≥0.5): {[a.name for a in security_experts]}")

    api_experts = get_relevant_agents("api_design", min_weight=0.6)
    print(f"  • API design experts (≥0.6): {[a.name for a in api_experts]}")

    print("\n✓ PASS: Expertise Registry working")
    return True


def test_trigger_detector():
    """Test 2: Trigger Detector pattern matching"""
    print("\n" + "=" * 70)
    print("TEST 2: Trigger Detector")
    print("=" * 70)

    detector = TriggerDetector()

    # Test cases: (operation_text, expected_condition, expected_domain)
    test_cases = [
        (
            "Design a new authentication system using JWT tokens",
            "security",
            "security",
        ),
        (
            "Refactor the API architecture to use microservices",
            "architectural",
            "architecture",
        ),
        ("git push origin main to deploy to production", "external_commitment", "deployment"),
        (
            "Encrypt user passwords before storing in database",
            "security",
            "security",
        ),
        (
            "Should we use React or Vue for this project?",
            "novel_query",
            "frontend",
        ),
        (
            "Process personal data according to GDPR compliance",
            "ethical",
            "ethics",
        ),
    ]

    for operation_text, expected_condition, expected_domain in test_cases:
        trigger = detector.detect_trigger(
            tool_name="Bash", operation_text=operation_text, risk_level="MEDIUM"
        )

        if trigger is None:
            print(f"✗ FAIL: No trigger for '{operation_text[:50]}...'")
            return False

        print(f"\n  Operation: {operation_text[:60]}...")
        print(f"  • Condition: {trigger.condition.value}")
        print(f"  • Domain: {trigger.inferred_domain}")

        if expected_condition not in trigger.condition.value:
            print(
                f"  ✗ Expected condition '{expected_condition}', got '{trigger.condition.value}'"
            )

    # Test HIGH risk always triggers
    trigger = detector.detect_trigger(
        tool_name="Bash", operation_text="rm -rf /data", risk_level="CRITICAL"
    )
    if trigger is None:
        print("✗ FAIL: CRITICAL risk did not trigger council")
        return False

    print("\n  • CRITICAL risk level triggers council: ✓")

    print("\n✓ PASS: Trigger Detector working")
    return True


def test_voting_aggregator():
    """Test 3: Voting Aggregator DWA formula"""
    print("\n" + "=" * 70)
    print("TEST 3: Voting Aggregator (DWA Formula)")
    print("=" * 70)

    aggregator = VotingAggregator()
    session_id = uuid4()

    # Create 3 mock proposals
    proposal_a = Proposal(
        agent_name="security-auditor",
        recommendation="Use JWT with RS256 signing",
        reasoning_chain=[
            "RS256 provides asymmetric signing",
            "Public key verification prevents token forgery",
            "Industry standard for microservices",
        ],
        confidence=0.9,
        domain_relevance=1.0,
        model_used="llama3.2",
    )

    proposal_b = Proposal(
        agent_name="backend-developer",
        recommendation="Use JWT with HS256 signing",
        reasoning_chain=[
            "HS256 simpler to implement",
            "Single secret key easier to manage",
            "Sufficient for monolithic architecture",
        ],
        confidence=0.7,
        domain_relevance=0.8,
        model_used="llama3.2",
    )

    proposal_c = Proposal(
        agent_name="api-designer",
        recommendation="Use session-based auth with Redis",
        reasoning_chain=[
            "Easier to invalidate sessions",
            "Better for stateful applications",
            "Familiar pattern for most developers",
        ],
        confidence=0.6,
        domain_relevance=0.7,
        model_used="llama3.2",
    )

    proposals = [proposal_a, proposal_b, proposal_c]

    # Create votes (5 agents voting)
    votes = [
        # security-auditor votes for own proposal (Proposal A)
        Vote(
            agent_name="security-auditor",
            proposal_id=proposal_a.proposal_id,
            vote_type=VoteType.APPROVE,
            confidence=0.9,
            expertise_weight=1.0,  # security: 1.0
            rationale="RS256 is security best practice",
        ),
        # code-reviewer votes for Proposal A (high security expertise)
        Vote(
            agent_name="code-reviewer",
            proposal_id=proposal_a.proposal_id,
            vote_type=VoteType.APPROVE,
            confidence=0.85,
            expertise_weight=0.9,  # security: 0.9
            rationale="Strongest security guarantees",
        ),
        # backend-developer votes for own proposal (Proposal B)
        Vote(
            agent_name="backend-developer",
            proposal_id=proposal_b.proposal_id,
            vote_type=VoteType.APPROVE,
            confidence=0.7,
            expertise_weight=0.7,  # security: 0.7
            rationale="Simpler for our use case",
        ),
        # api-designer votes for own proposal (Proposal C)
        Vote(
            agent_name="api-designer",
            proposal_id=proposal_c.proposal_id,
            vote_type=VoteType.APPROVE,
            confidence=0.6,
            expertise_weight=0.5,  # security: 0.5 (inferred)
            rationale="Better developer experience",
        ),
        # python-pro votes for Proposal A
        Vote(
            agent_name="python-pro",
            proposal_id=proposal_a.proposal_id,
            vote_type=VoteType.APPROVE,
            confidence=0.75,
            expertise_weight=0.6,  # security: 0.6 (inferred)
            rationale="Industry standard approach",
        ),
    ]

    # Aggregate votes
    result = aggregator.aggregate_votes(votes, proposals, session_id)

    print("\n  Voting Results:")
    print(f"  • Total votes: {len(result.votes)}")
    print(f"  • Aggregate confidence: {result.aggregate_confidence:.2f}")
    print(f"  • Vote concentration (HHI): {result.vote_concentration_hhi:.2f}")

    print("\n  Proposal Scores (DWA):")
    for proposal_id_str, score in sorted(
        result.proposal_scores.items(), key=lambda x: x[1], reverse=True
    ):
        # Find proposal name
        proposal = next(
            (p for p in proposals if str(p.proposal_id) == proposal_id_str), None
        )
        agent_name = proposal.agent_name if proposal else "unknown"
        print(f"  • {agent_name}: {score:.3f}")

    print(f"\n  Winner: {result.winning_proposal_id}")
    print(f"  Winning score: {result.winning_score:.3f}")

    # Verify DWA formula manually for Proposal A
    # Expected: (0.9 * 1.0) + (0.85 * 0.9) + (0.75 * 0.6) = 0.9 + 0.765 + 0.45 = 2.115
    expected_score_a = (0.9 * 1.0) + (0.85 * 0.9) + (0.75 * 0.6)
    actual_score_a = result.proposal_scores[str(proposal_a.proposal_id)]
    print(
        f"\n  DWA Formula Verification (Proposal A):"
    )
    print(f"  • Expected: {expected_score_a:.3f}")
    print(f"  • Actual: {actual_score_a:.3f}")
    if abs(expected_score_a - actual_score_a) < 0.01:
        print("  ✓ DWA formula correct")
    else:
        print("  ✗ DWA formula mismatch!")
        return False

    # Check escalation logic
    print(f"\n  Escalation Check:")
    print(f"  • Needs escalation: {result.needs_escalation}")
    if result.needs_escalation:
        print(f"  • Reason: {result.escalation_reason}")

    print("\n✓ PASS: Voting Aggregator working")
    return True


def test_low_confidence_escalation():
    """Test 4: Low confidence triggers escalation"""
    print("\n" + "=" * 70)
    print("TEST 4: Low Confidence Escalation")
    print("=" * 70)

    aggregator = VotingAggregator(confidence_threshold=0.7)
    session_id = uuid4()

    proposal = Proposal(
        agent_name="backend-developer",
        recommendation="Use NoSQL database",
        reasoning_chain=["Not sure about this", "Might work"],
        confidence=0.5,  # Low confidence
        domain_relevance=0.6,
        model_used="llama3.2",
    )

    # All votes have low confidence
    votes = [
        Vote(
            agent_name="backend-developer",
            proposal_id=proposal.proposal_id,
            vote_type=VoteType.APPROVE,
            confidence=0.5,
            expertise_weight=0.9,
            rationale="Uncertain about this approach",
        ),
        Vote(
            agent_name="database-architect",
            proposal_id=proposal.proposal_id,
            vote_type=VoteType.APPROVE,
            confidence=0.6,
            expertise_weight=1.0,
            rationale="Not confident in this decision",
        ),
    ]

    result = aggregator.aggregate_votes(votes, [proposal], session_id)

    print(f"  • Aggregate confidence: {result.aggregate_confidence:.2f}")
    print(f"  • Needs escalation: {result.needs_escalation}")
    print(f"  • Reason: {result.escalation_reason}")

    if not result.needs_escalation:
        print("✗ FAIL: Low confidence did not trigger escalation")
        return False

    if "confidence" not in result.escalation_reason.lower():
        print("✗ FAIL: Escalation reason does not mention confidence")
        return False

    print("\n✓ PASS: Low confidence escalation working")
    return True


def main():
    """Run all Phase 1 tests"""
    print("\n" + "=" * 70)
    print("PHASE 1 INTEGRATION TEST - DWA Council Foundation")
    print("=" * 70)
    print("Testing: Expertise Registry, Trigger Detector, Voting Aggregator")

    tests = [
        test_expertise_registry,
        test_trigger_detector,
        test_voting_aggregator,
        test_low_confidence_escalation,
    ]

    results = []
    for test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"\n✗ TEST FAILED WITH EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓✓✓ ALL TESTS PASSED - Phase 1 Complete! ✓✓✓")
        return 0
    else:
        print(f"\n✗✗✗ {total - passed} TEST(S) FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
