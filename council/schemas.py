"""
Pydantic schemas for DWA Council System

Defines data models for:
- Agent expertise profiles
- Proposals with confidence scoring
- Debate rounds and critiques
- Voting results and aggregation
- Council session state
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class CouncilRole(str, Enum):
    """Agent's role in council deliberation"""

    PROPOSER = "proposer"  # Generates proposals and votes
    REVIEWER = "reviewer"  # Reviews but doesn't propose
    ABSTAINER = "abstainer"  # Cannot participate


class TriggerCondition(str, Enum):
    """Conditions that trigger council convocation"""

    ARCHITECTURAL = "architectural"  # Design choices, tech stack
    SECURITY = "security"  # Auth, secrets, vulnerabilities
    DISAGREEMENT = "disagreement"  # Agent conflicts
    QUALITY_FAILURE = "quality_failure"  # TDD, linting, test failures
    ETHICAL = "ethical"  # Privacy, bias concerns
    LOW_CONFIDENCE = "low_confidence"  # Uncertainty < 0.75
    EXTERNAL_COMMITMENT = "external_commitment"  # Deploys, API calls
    NOVEL_QUERY = "novel_query"  # Out-of-distribution tasks


class VoteType(str, Enum):
    """Types of votes in DWA system"""

    APPROVE = "approve"  # Vote for this recommendation
    REJECT = "reject"  # Vote against
    ABSTAIN = "abstain"  # No opinion


# ============================================================================
# Agent Expertise Models
# ============================================================================


class AgentExpertise(BaseModel):
    """Agent expertise profile loaded from YAML frontmatter"""

    name: str = Field(..., description="Agent name (e.g., 'security-auditor')")
    expertise_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Domain expertise weights (0-1), e.g., {'security': 1.0, 'api_design': 0.7}",
    )
    council_role: CouncilRole = Field(
        default=CouncilRole.PROPOSER, description="Role in council deliberation"
    )
    model_tier: str = Field(
        default="sonnet", description="Model tier: opus, sonnet, haiku"
    )
    description: Optional[str] = Field(None, description="Agent description from YAML")

    @field_validator("expertise_weights")
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Ensure all weights are between 0 and 1"""
        for domain, weight in v.items():
            if not 0 <= weight <= 1:
                raise ValueError(
                    f"Expertise weight for '{domain}' must be between 0 and 1, got {weight}"
                )
        return v

    def get_expertise(self, domain: str, default: float = 0.0) -> float:
        """Get expertise weight for domain, with fallback"""
        return self.expertise_weights.get(domain, default)


# ============================================================================
# Proposal Models
# ============================================================================


class Proposal(BaseModel):
    """Agent proposal with reasoning chain and confidence"""

    proposal_id: UUID = Field(default_factory=uuid4, description="Unique proposal ID")
    agent_name: str = Field(..., description="Agent that generated this proposal")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Proposal creation time"
    )

    # Proposal content
    recommendation: str = Field(
        ..., description="Recommended action or decision", min_length=10
    )
    reasoning_chain: List[str] = Field(
        ..., description="Step-by-step reasoning (chain-of-thought)", min_items=1
    )

    # Confidence scoring
    confidence: float = Field(
        ...,
        description="Confidence in this recommendation (0-1)",
        ge=0.0,
        le=1.0,
    )
    domain_relevance: float = Field(
        ...,
        description="Relevance to agent's expertise domain (0-1)",
        ge=0.0,
        le=1.0,
    )

    # Metadata
    model_used: str = Field(
        ..., description="Model used for generation (e.g., 'llama3.2', 'opus')"
    )
    generation_time_ms: Optional[int] = Field(
        None, description="Time to generate proposal in milliseconds"
    )

    @property
    def weighted_confidence(self) -> float:
        """Confidence weighted by domain relevance"""
        return self.confidence * self.domain_relevance


# ============================================================================
# Debate Models
# ============================================================================


class Critique(BaseModel):
    """Critique of another agent's proposal during debate"""

    critique_id: UUID = Field(default_factory=uuid4)
    source_agent: str = Field(..., description="Agent providing critique")
    target_proposal_id: UUID = Field(..., description="Proposal being critiqued")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    critique_text: str = Field(..., description="Critique content", min_length=10)
    suggested_improvements: List[str] = Field(
        default_factory=list, description="Suggested changes"
    )
    severity: str = Field(
        default="minor", description="Critique severity: minor, moderate, critical"
    )


class DebateRound(BaseModel):
    """Single round of debate with proposals and critiques"""

    round_number: int = Field(..., ge=1, description="Debate round number (1-2)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    proposals: List[Proposal] = Field(
        default_factory=list, description="Proposals in this round"
    )
    critiques: List[Critique] = Field(
        default_factory=list, description="Critiques exchanged"
    )

    # Round statistics
    consensus_score: Optional[float] = Field(
        None, description="Consensus level (0-1), computed after round", ge=0.0, le=1.0
    )
    should_continue: bool = Field(
        default=True, description="Whether to continue debate"
    )


# ============================================================================
# Voting Models
# ============================================================================


class Vote(BaseModel):
    """Single vote in DWA aggregation"""

    vote_id: UUID = Field(default_factory=uuid4)
    agent_name: str = Field(..., description="Voting agent")
    proposal_id: UUID = Field(..., description="Proposal being voted on")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    vote_type: VoteType = Field(..., description="Approve/Reject/Abstain")
    confidence: float = Field(
        ..., description="Voter's confidence (0-1)", ge=0.0, le=1.0
    )
    expertise_weight: float = Field(
        ..., description="Voter's domain expertise (0-1)", ge=0.0, le=1.0
    )

    # Reasoning
    rationale: Optional[str] = Field(None, description="Why this vote was cast")

    @property
    def weighted_score(self) -> float:
        """DWA formula: Vote × Confidence × Expertise"""
        vote_value = 1.0 if self.vote_type == VoteType.APPROVE else 0.0
        return vote_value * self.confidence * self.expertise_weight


class VotingResult(BaseModel):
    """Aggregated voting results with winner and statistics"""

    session_id: UUID = Field(..., description="Council session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Vote tallies
    votes: List[Vote] = Field(..., description="All votes cast")
    proposal_scores: Dict[str, float] = Field(
        ..., description="Proposal ID → weighted score"
    )

    # Winner
    winning_proposal_id: Optional[UUID] = Field(None, description="Winning proposal")
    winning_score: float = Field(default=0.0, description="Winner's DWA score")

    # Statistics
    aggregate_confidence: float = Field(
        ..., description="Mean confidence across votes", ge=0.0, le=1.0
    )
    vote_concentration_hhi: float = Field(
        ..., description="Herfindahl-Hirschman Index (0-1)", ge=0.0, le=1.0
    )
    is_tie: bool = Field(
        default=False, description="Whether results are tied (within 5%)"
    )

    # Escalation flags
    needs_escalation: bool = Field(
        default=False, description="Whether to escalate (low confidence or tie)"
    )
    escalation_reason: Optional[str] = Field(
        None, description="Why escalation is needed"
    )


# ============================================================================
# Council Session Models
# ============================================================================


class CouncilTrigger(BaseModel):
    """Information about why council was triggered"""

    condition: TriggerCondition = Field(..., description="Trigger condition type")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    tool_name: Optional[str] = Field(None, description="Tool that triggered council")
    operation_text: str = Field(..., description="Text of operation being performed")
    inferred_domain: str = Field(
        ..., description="Inferred domain (e.g., 'security', 'architecture')"
    )
    risk_level: Optional[str] = Field(
        None, description="Risk level from intelligent_gate: LOW/MEDIUM/HIGH/CRITICAL"
    )


class CouncilSession(BaseModel):
    """Complete council deliberation session"""

    session_id: UUID = Field(default_factory=uuid4, description="Unique session ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Trigger information
    trigger: CouncilTrigger = Field(..., description="Why council was convened")

    # Participating agents
    participating_agents: List[str] = Field(
        ..., description="Agents selected for this council"
    )

    # Deliberation phases
    debate_rounds: List[DebateRound] = Field(
        default_factory=list, description="Debate rounds (0-2)"
    )
    voting_result: Optional[VotingResult] = Field(
        None, description="Final voting outcome"
    )

    # Final decision
    decision: Optional[str] = Field(None, description="Final council decision")
    decision_confidence: Optional[float] = Field(
        None, description="Aggregate confidence in decision", ge=0.0, le=1.0
    )

    # Execution metadata
    total_duration_ms: Optional[int] = Field(
        None, description="Total time from trigger to decision"
    )
    tokens_used: Optional[int] = Field(None, description="Total tokens consumed")
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")

    # Escalation
    escalated_to_external: bool = Field(
        default=False, description="Whether escalated to o3/Gemini/DeepSeek"
    )
    external_model_used: Optional[str] = Field(
        None, description="External model if escalated"
    )

    def add_debate_round(self, round: DebateRound) -> None:
        """Add a debate round to session"""
        self.debate_rounds.append(round)

    def finalize(
        self,
        decision: str,
        confidence: float,
        voting_result: VotingResult,
        duration_ms: int,
    ) -> None:
        """Mark session as complete"""
        self.completed_at = datetime.utcnow()
        self.decision = decision
        self.decision_confidence = confidence
        self.voting_result = voting_result
        self.total_duration_ms = duration_ms
