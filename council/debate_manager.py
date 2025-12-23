"""
Debate Manager - Optional Multi-Round Debate Orchestration

Manages 1-2 rounds of debate between agents to refine proposals.
Debates are OPTIONAL and only triggered when:
- Initial consensus is low (< 0.80)
- Initial confidence is low (< 0.85)
- Significant disagreement detected

Key Functions:
- should_debate(): Determine if debate is needed
- conduct_debate(): Run debate rounds
- _generate_critiques(): Collect critiques from agents
- _refine_proposals(): Update proposals based on critiques
"""

from typing import List, Optional, Tuple

from council.schemas import Critique, DebateRound, Proposal


class DebateManager:
    """
    Manages optional debate rounds for proposal refinement.

    Debates are lightweight (1-2 rounds max) to avoid excessive overhead.
    """

    def __init__(
        self,
        consensus_threshold: float = 0.80,
        confidence_threshold: float = 0.85,
        max_rounds: int = 2,
    ):
        """
        Initialize debate manager.

        Args:
            consensus_threshold: Min consensus to skip debate (default: 0.80)
            confidence_threshold: Min confidence to skip debate (default: 0.85)
            max_rounds: Maximum debate rounds (default: 2)
        """
        self.consensus_threshold = consensus_threshold
        self.confidence_threshold = confidence_threshold
        self.max_rounds = max_rounds

    def should_debate(self, proposals: List[Proposal]) -> Tuple[bool, str]:
        """
        Determine if debate is needed based on initial proposals.

        Args:
            proposals: Initial proposals from agents

        Returns:
            Tuple of (should_debate, reason)
        """
        if len(proposals) < 2:
            return False, "Only one proposal - no debate needed"

        # Calculate aggregate confidence
        avg_confidence = sum(p.confidence for p in proposals) / len(proposals)
        if avg_confidence < self.confidence_threshold:
            return True, f"Low confidence ({avg_confidence:.2f} < {self.confidence_threshold})"

        # Calculate confidence variance (measure of disagreement)
        confidence_values = [p.confidence for p in proposals]
        mean_conf = sum(confidence_values) / len(confidence_values)
        variance = sum((c - mean_conf) ** 2 for c in confidence_values) / len(
            confidence_values
        )

        if variance > 0.05:  # High variance threshold
            return True, f"High disagreement (variance: {variance:.3f})"

        # Check for conflicting recommendations
        recommendations = [p.recommendation.lower() for p in proposals]
        unique_recommendations = len(set(recommendations))
        if unique_recommendations == len(proposals):
            # All agents recommend different things
            return True, "All proposals differ - need discussion"

        # Calculate simple consensus score (agreement ratio)
        most_common_count = max(recommendations.count(r) for r in set(recommendations))
        consensus = most_common_count / len(proposals)

        if consensus < self.consensus_threshold:
            return True, f"Low consensus ({consensus:.2f} < {self.consensus_threshold})"

        return False, f"High consensus ({consensus:.2f}) - no debate needed"

    def conduct_debate(
        self,
        proposals: List[Proposal],
        domain: str,
        operation_text: str,
    ) -> List[DebateRound]:
        """
        Conduct debate rounds between agents.

        Args:
            proposals: Initial proposals
            domain: Domain context
            operation_text: Operation being deliberated

        Returns:
            List of DebateRound objects (1-2 rounds)
        """
        debate_rounds = []

        # Round 1: Critique phase
        round1 = self._conduct_round(
            round_number=1,
            proposals=proposals,
            domain=domain,
            operation_text=operation_text,
        )
        debate_rounds.append(round1)

        # Check if round 2 is needed
        if round1.should_continue and len(debate_rounds) < self.max_rounds:
            # Round 2: Refinement based on critiques
            round2 = self._conduct_round(
                round_number=2,
                proposals=round1.proposals,  # Use refined proposals
                domain=domain,
                operation_text=operation_text,
                previous_critiques=round1.critiques,
            )
            debate_rounds.append(round2)

        return debate_rounds

    def _conduct_round(
        self,
        round_number: int,
        proposals: List[Proposal],
        domain: str,
        operation_text: str,
        previous_critiques: Optional[List[Critique]] = None,
    ) -> DebateRound:
        """
        Conduct a single debate round.

        Args:
            round_number: Round number (1-2)
            proposals: Current proposals
            domain: Domain context
            operation_text: Operation text
            previous_critiques: Critiques from previous round

        Returns:
            DebateRound object
        """
        # Generate critiques (agents critique each other's proposals)
        critiques = self._generate_critiques(
            proposals, domain, operation_text, previous_critiques
        )

        # Refine proposals based on critiques (optional for Phase 2)
        refined_proposals = self._refine_proposals(proposals, critiques)

        # Calculate consensus after this round
        consensus_score = self._calculate_consensus(refined_proposals)

        # Decide if another round is needed
        should_continue = (
            consensus_score < self.consensus_threshold
            and round_number < self.max_rounds
        )

        return DebateRound(
            round_number=round_number,
            proposals=refined_proposals,
            critiques=critiques,
            consensus_score=consensus_score,
            should_continue=should_continue,
        )

    def _generate_critiques(
        self,
        proposals: List[Proposal],
        domain: str,
        operation_text: str,
        previous_critiques: Optional[List[Critique]],
    ) -> List[Critique]:
        """
        Generate critiques from agents reviewing each other's proposals.

        Args:
            proposals: Proposals to critique
            domain: Domain context
            operation_text: Operation text
            previous_critiques: Critiques from previous round

        Returns:
            List of Critique objects
        """
        critiques = []

        # For Phase 2, use simulated critiques
        # Phase 3 will integrate actual Ollama/Claude generation

        # Each agent critiques other agents' proposals
        for i, proposal in enumerate(proposals):
            # Get other proposals (not this one)
            other_proposals = proposals[:i] + proposals[i + 1 :]

            for other_proposal in other_proposals:
                # Simulate critique based on confidence difference
                confidence_diff = abs(proposal.confidence - other_proposal.confidence)

                if confidence_diff > 0.2:
                    # Significant disagreement - generate critique
                    severity = "moderate" if confidence_diff < 0.4 else "critical"

                    critique = Critique(
                        source_agent=proposal.agent_name,
                        target_proposal_id=other_proposal.proposal_id,
                        critique_text=f"{proposal.agent_name} disagrees with {other_proposal.agent_name}'s approach",
                        suggested_improvements=[
                            "Consider alternative approach",
                            "Review security implications",
                        ],
                        severity=severity,
                    )
                    critiques.append(critique)

        return critiques

    def _refine_proposals(
        self, proposals: List[Proposal], critiques: List[Critique]
    ) -> List[Proposal]:
        """
        Refine proposals based on received critiques.

        Args:
            proposals: Original proposals
            critiques: Critiques received

        Returns:
            Refined proposals (may have adjusted confidence)
        """
        # For Phase 2, return original proposals
        # Phase 3 will implement actual refinement via model calls
        return proposals

    def _calculate_consensus(self, proposals: List[Proposal]) -> float:
        """
        Calculate consensus score from proposals.

        Simple metric: ratio of proposals agreeing with most common recommendation

        Args:
            proposals: Current proposals

        Returns:
            Consensus score (0.0-1.0)
        """
        if len(proposals) < 2:
            return 1.0

        # Group by similarity of recommendations (simplified)
        recommendations = [p.recommendation.lower() for p in proposals]
        most_common_count = max(recommendations.count(r) for r in set(recommendations))

        return most_common_count / len(proposals)


# Singleton instance
_manager: Optional[DebateManager] = None


def get_manager() -> DebateManager:
    """Get singleton DebateManager instance (lazy initialization)"""
    global _manager
    if _manager is None:
        _manager = DebateManager()
    return _manager


# Convenience functions


def should_debate(proposals: List[Proposal]) -> Tuple[bool, str]:
    """Check if debate is needed (convenience wrapper)"""
    return get_manager().should_debate(proposals)


def conduct_debate(
    proposals: List[Proposal], domain: str, operation_text: str
) -> List[DebateRound]:
    """Conduct debate rounds (convenience wrapper)"""
    return get_manager().conduct_debate(proposals, domain, operation_text)
