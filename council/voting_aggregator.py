"""
Voting Aggregator - DWA Formula Implementation

Implements Debate-Weighted Aggregation (DWA) voting system:
- Weighted voting: Score = Σ (Vote × Confidence × Expertise)
- Escalation checks: Low confidence (<0.7), ties, high disagreement
- Herfindahl-Hirschman Index (HHI) for vote concentration

Key Functions:
- aggregate_votes(): Compute DWA scores and determine winner
- check_escalation(): Determine if escalation is needed
- compute_hhi(): Calculate vote concentration index
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID

from .schemas import Proposal, Vote, VoteType, VotingResult


class VotingAggregator:
    """
    DWA Voting System Implementation

    Computes weighted vote scores and determines winners with escalation logic.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        tie_threshold: float = 0.05,
        hhi_threshold: float = 0.3,
    ):
        """
        Initialize voting aggregator with thresholds.

        Args:
            confidence_threshold: Minimum aggregate confidence (default: 0.7)
            tie_threshold: Max difference for tie (default: 0.05 = 5%)
            hhi_threshold: Min HHI for high disagreement (default: 0.3)
        """
        self.confidence_threshold = confidence_threshold
        self.tie_threshold = tie_threshold
        self.hhi_threshold = hhi_threshold

    def aggregate_votes(
        self, votes: List[Vote], proposals: List[Proposal], session_id: UUID
    ) -> VotingResult:
        """
        Aggregate votes using DWA formula and determine winner.

        Args:
            votes: List of Vote objects
            proposals: List of Proposal objects being voted on
            session_id: Council session ID

        Returns:
            VotingResult with winner, scores, and escalation flags
        """
        if not votes:
            raise ValueError("Cannot aggregate empty vote list")

        # Compute DWA scores for each proposal
        proposal_scores = self._compute_dwa_scores(votes)

        # Find winner (highest score)
        if not proposal_scores:
            raise ValueError("No valid proposals to vote on")

        winning_proposal_id, winning_score = max(
            proposal_scores.items(), key=lambda x: x[1]
        )

        # Compute statistics
        aggregate_confidence = self._compute_aggregate_confidence(votes)
        vote_concentration_hhi = self._compute_hhi(votes)

        # Check for tie
        is_tie = self._check_tie(proposal_scores, winning_score)

        # Determine if escalation is needed
        needs_escalation, escalation_reason = self._check_escalation(
            aggregate_confidence, is_tie, vote_concentration_hhi
        )

        return VotingResult(
            session_id=session_id,
            votes=votes,
            proposal_scores={str(k): v for k, v in proposal_scores.items()},
            winning_proposal_id=UUID(winning_proposal_id)
            if winning_proposal_id
            else None,
            winning_score=winning_score,
            aggregate_confidence=aggregate_confidence,
            vote_concentration_hhi=vote_concentration_hhi,
            is_tie=is_tie,
            needs_escalation=needs_escalation,
            escalation_reason=escalation_reason,
        )

    def _compute_dwa_scores(self, votes: List[Vote]) -> Dict[str, float]:
        """
        Compute DWA weighted scores for each proposal.

        Formula: Score = Σ (Vote × Confidence × Expertise Weight)
        Where:
        - Vote = 1.0 for APPROVE, 0.0 for REJECT/ABSTAIN
        - Confidence = voter's confidence (0-1)
        - Expertise Weight = voter's domain expertise (0-1)

        Returns:
            Dict mapping proposal_id (str) → weighted_score (float)
        """
        scores: Dict[str, float] = {}

        for vote in votes:
            proposal_id = str(vote.proposal_id)

            # Initialize score if first vote for this proposal
            if proposal_id not in scores:
                scores[proposal_id] = 0.0

            # Add weighted score
            scores[proposal_id] += vote.weighted_score

        return scores

    def _compute_aggregate_confidence(self, votes: List[Vote]) -> float:
        """
        Compute mean confidence across all votes.

        Args:
            votes: List of Vote objects

        Returns:
            Mean confidence (0-1)
        """
        if not votes:
            return 0.0

        total_confidence = sum(vote.confidence for vote in votes)
        return total_confidence / len(votes)

    def _compute_hhi(self, votes: List[Vote]) -> float:
        """
        Compute Herfindahl-Hirschman Index (HHI) for vote concentration.

        HHI measures how concentrated votes are:
        - HHI = 1.0: All votes on single proposal (complete consensus)
        - HHI → 0.0: Votes evenly distributed (high disagreement)

        Formula: HHI = Σ (share_i)^2
        Where share_i = proportion of votes for proposal i

        Args:
            votes: List of Vote objects

        Returns:
            HHI score (0-1)
        """
        if not votes:
            return 0.0

        # Count APPROVE votes per proposal
        vote_counts: Dict[str, int] = {}
        total_approvals = 0

        for vote in votes:
            if vote.vote_type == VoteType.APPROVE:
                proposal_id = str(vote.proposal_id)
                vote_counts[proposal_id] = vote_counts.get(proposal_id, 0) + 1
                total_approvals += 1

        if total_approvals == 0:
            return 0.0  # No approvals = max disagreement

        # Compute HHI
        hhi = sum((count / total_approvals) ** 2 for count in vote_counts.values())

        return hhi

    def _check_tie(self, proposal_scores: Dict[str, float], winning_score: float) -> bool:
        """
        Check if results are tied (within threshold).

        Args:
            proposal_scores: Dict of proposal_id → score
            winning_score: Highest score

        Returns:
            True if multiple proposals within 5% of winner
        """
        if len(proposal_scores) < 2:
            return False

        # Find second-highest score
        sorted_scores = sorted(proposal_scores.values(), reverse=True)
        if len(sorted_scores) < 2:
            return False

        second_score = sorted_scores[1]

        # Check if within threshold
        score_diff = winning_score - second_score
        return score_diff <= self.tie_threshold * winning_score

    def _check_escalation(
        self, aggregate_confidence: float, is_tie: bool, hhi: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if escalation to external model is needed.

        Escalation triggers:
        1. Low aggregate confidence (< 0.7)
        2. Tie vote (within 5%)
        3. High disagreement (HHI < 0.3)

        Args:
            aggregate_confidence: Mean confidence across votes
            is_tie: Whether results are tied
            hhi: Vote concentration index

        Returns:
            Tuple of (needs_escalation, reason)
        """
        reasons = []

        if aggregate_confidence < self.confidence_threshold:
            reasons.append(
                f"Low confidence ({aggregate_confidence:.2f} < {self.confidence_threshold})"
            )

        if is_tie:
            reasons.append("Tie vote (within 5%)")

        if hhi < self.hhi_threshold:
            reasons.append(
                f"High disagreement (HHI {hhi:.2f} < {self.hhi_threshold})"
            )

        if reasons:
            return True, "; ".join(reasons)

        return False, None

    def get_winning_proposal(
        self, voting_result: VotingResult, proposals: List[Proposal]
    ) -> Optional[Proposal]:
        """
        Retrieve the winning Proposal object from voting result.

        Args:
            voting_result: VotingResult object
            proposals: List of all proposals

        Returns:
            Winning Proposal object or None
        """
        if voting_result.winning_proposal_id is None:
            return None

        for proposal in proposals:
            if proposal.proposal_id == voting_result.winning_proposal_id:
                return proposal

        return None


# Singleton instance
_aggregator: Optional[VotingAggregator] = None


def get_aggregator() -> VotingAggregator:
    """Get singleton VotingAggregator instance (lazy initialization)"""
    global _aggregator
    if _aggregator is None:
        _aggregator = VotingAggregator()
    return _aggregator


# Convenience functions


def aggregate_votes(
    votes: List[Vote], proposals: List[Proposal], session_id: UUID
) -> VotingResult:
    """Aggregate votes using DWA formula (convenience wrapper)"""
    return get_aggregator().aggregate_votes(votes, proposals, session_id)


def get_winning_proposal(
    voting_result: VotingResult, proposals: List[Proposal]
) -> Optional[Proposal]:
    """Get winning proposal (convenience wrapper)"""
    return get_aggregator().get_winning_proposal(voting_result, proposals)
