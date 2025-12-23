"""
Council Orchestrator - Main Entry Point for DWA Council System

Coordinates the complete council deliberation workflow:
1. Trigger detection → Select relevant agents
2. Proposal generation → Collect independent proposals
3. Optional debate → 1-2 rounds if needed
4. Voting aggregation → DWA weighted voting
5. Decision finalization → Persist session

Key Functions:
- convene_council(): Main entry point for council deliberation
- _execute_council_workflow(): Full workflow execution
"""

import time
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from council.debate_manager import DebateManager
from council.expertise_registry import ExpertiseRegistry
from council.proposal_generator import ProposalGenerator
from council.schemas import (
    CouncilSession,
    CouncilTrigger,
    Proposal,
    Vote,
    VoteType,
    VotingResult,
)
from council.state_manager import StateManager
from council.voting_aggregator import VotingAggregator


class CouncilOrchestrator:
    """
    Orchestrates complete DWA council deliberation workflow.

    Main responsibilities:
    - Coordinate proposal generation, debate, and voting
    - Manage session lifecycle
    - Handle escalation to external models (o3/Gemini)
    - Persist sessions for audit trail
    """

    def __init__(
        self,
        registry: Optional[ExpertiseRegistry] = None,
        proposal_generator: Optional[ProposalGenerator] = None,
        debate_manager: Optional[DebateManager] = None,
        voting_aggregator: Optional[VotingAggregator] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize orchestrator with component instances.

        Args:
            registry: ExpertiseRegistry (creates if None)
            proposal_generator: ProposalGenerator (creates if None)
            debate_manager: DebateManager (creates if None)
            voting_aggregator: VotingAggregator (creates if None)
            state_manager: StateManager (creates if None)
        """
        self.registry = registry or ExpertiseRegistry()
        self.proposal_generator = proposal_generator or ProposalGenerator(self.registry)
        self.debate_manager = debate_manager or DebateManager()
        self.voting_aggregator = voting_aggregator or VotingAggregator()
        self.state_manager = state_manager or StateManager()

    def convene_council(
        self,
        trigger: CouncilTrigger,
        context: Optional[str] = None,
        max_agents: int = 5,
    ) -> CouncilSession:
        """
        Main entry point: Convene council for deliberation.

        Args:
            trigger: CouncilTrigger describing why council was called
            context: Additional context for agents
            max_agents: Maximum number of agents to participate

        Returns:
            CouncilSession with final decision
        """
        start_time = time.time()

        # Create session
        session = CouncilSession(
            session_id=uuid4(),
            trigger=trigger,
            participating_agents=[],
        )

        try:
            # Execute council workflow
            self._execute_council_workflow(session, context, max_agents)

        except Exception as e:
            # Log error but preserve partial session
            print(f"Council workflow error: {e}")
            session.decision = f"ERROR: {str(e)}"
            session.decision_confidence = 0.0

        finally:
            # Finalize session
            duration_ms = int((time.time() - start_time) * 1000)
            session.total_duration_ms = duration_ms

            # Persist session
            self.state_manager.save_session(session)

        return session

    def _execute_council_workflow(
        self,
        session: CouncilSession,
        context: Optional[str],
        max_agents: int,
    ) -> None:
        """
        Execute complete council workflow.

        Modifies session in-place with results.

        Args:
            session: CouncilSession to populate
            context: Additional context
            max_agents: Max participating agents
        """
        domain = session.trigger.inferred_domain
        operation_text = session.trigger.operation_text

        # Step 1: Generate proposals from relevant agents
        print(f"\n[Council] Generating proposals for {domain}...")
        proposals = self.proposal_generator.generate_proposals(
            domain=domain,
            operation_text=operation_text,
            context=context,
            max_agents=max_agents,
        )

        if not proposals:
            raise ValueError(f"No proposals generated for domain '{domain}'")

        # Track participating agents
        session.participating_agents = [p.agent_name for p in proposals]
        print(f"[Council] {len(proposals)} proposals from: {', '.join(session.participating_agents)}")

        # Step 2: Check if debate is needed
        should_debate, debate_reason = self.debate_manager.should_debate(proposals)

        if should_debate:
            print(f"[Council] Debate triggered: {debate_reason}")
            debate_rounds = self.debate_manager.conduct_debate(
                proposals, domain, operation_text
            )
            session.debate_rounds = debate_rounds

            # Use refined proposals from final round
            if debate_rounds:
                proposals = debate_rounds[-1].proposals
                print(f"[Council] Completed {len(debate_rounds)} debate round(s)")
        else:
            print(f"[Council] Skipping debate: {debate_reason}")

        # Step 3: Generate votes from proposals
        votes = self._generate_votes_from_proposals(proposals, domain)

        # Step 4: Aggregate votes using DWA
        print(f"[Council] Aggregating {len(votes)} votes using DWA...")
        voting_result = self.voting_aggregator.aggregate_votes(
            votes, proposals, session.session_id
        )

        # Store voting result
        session.voting_result = voting_result

        # Step 5: Check for escalation
        if voting_result.needs_escalation:
            print(f"[Council] Escalation needed: {voting_result.escalation_reason}")
            session.escalated_to_external = True

            # Phase 3: Consult external model for tie-breaking or confidence boost
            escalation_result = self._handle_escalation(
                proposals, domain, operation_text, voting_result
            )

            if escalation_result:
                # External model provided additional insight
                print(f"[Council] External consultation result: {escalation_result[:80]}...")
                # Use external result to boost confidence or break tie
                # For now, log it; Phase 4 will integrate into voting

        # Step 6: Finalize decision
        winning_proposal = self.voting_aggregator.get_winning_proposal(
            voting_result, proposals
        )

        if winning_proposal:
            session.decision = winning_proposal.recommendation
            session.decision_confidence = voting_result.aggregate_confidence
            print(f"[Council] Decision: {session.decision[:80]}...")
            print(f"[Council] Confidence: {session.decision_confidence:.2f}")
        else:
            session.decision = "No clear winner - manual review required"
            session.decision_confidence = 0.0

        session.finalize(
            decision=session.decision,
            confidence=session.decision_confidence,
            voting_result=voting_result,
            duration_ms=0,  # Will be set by convene_council
        )

    def _generate_votes_from_proposals(
        self, proposals: List[Proposal], domain: str
    ) -> List[Vote]:
        """
        Generate votes from proposals (each agent votes for own proposal).

        In future phases, agents can vote for other agents' proposals too.

        Args:
            proposals: List of proposals
            domain: Domain context

        Returns:
            List of Vote objects
        """
        votes = []

        for proposal in proposals:
            # Get agent expertise for domain
            agent = self.registry.get_agent_expertise(proposal.agent_name)
            expertise_weight = (
                agent.get_expertise(domain, default=0.5) if agent else 0.5
            )

            # Agent votes for own proposal
            vote = Vote(
                agent_name=proposal.agent_name,
                proposal_id=proposal.proposal_id,
                vote_type=VoteType.APPROVE,
                confidence=proposal.confidence,
                expertise_weight=expertise_weight,
                rationale=f"Own proposal with confidence {proposal.confidence:.2f}",
            )
            votes.append(vote)

        return votes

    def _handle_escalation(
        self,
        proposals: List[Proposal],
        domain: str,
        operation_text: str,
        voting_result: VotingResult,
    ) -> Optional[str]:
        """
        Handle escalation by consulting external model (o3/Gemini/DeepSeek).

        Args:
            proposals: All proposals from agents
            domain: Domain context
            operation_text: Original operation
            voting_result: Voting result that triggered escalation

        Returns:
            External model's recommendation or None if consultation fails
        """
        # Build escalation prompt summarizing proposals and issue
        prompt = self._build_escalation_prompt(
            proposals, domain, operation_text, voting_result
        )

        # Select external model based on domain and cost
        # Returns None for auto-selection by consult-llm
        preferred_model = self._select_escalation_model(domain, voting_result.escalation_reason)

        try:
            model_desc = preferred_model if preferred_model else "auto-selected model"
            print(f"[Council] Consulting {model_desc} for escalation...", file=sys.stderr)

            # Phase 4: Call external model consultation wrapper
            # This wrapper provides bridge to consult-llm MCP
            import subprocess

            wrapper_script = Path(__file__).parent / "consult_external_model.py"
            cmd = ["python3", str(wrapper_script), "--prompt", prompt, "--format", "text"]

            if preferred_model:
                cmd.extend(["--model", preferred_model])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # Allow time for external model processing
            )

            if result.returncode == 0:
                response = result.stdout.strip()
                print(f"[Council] External consultation complete", file=sys.stderr)
                return response
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"[Council] Escalation failed: {error_msg}", file=sys.stderr)
                return None

        except subprocess.TimeoutExpired:
            print(f"[Council] Escalation timed out after 60s", file=sys.stderr)
            return None
        except Exception as e:
            print(f"[Council] Escalation error: {e}", file=sys.stderr)
            return None

    def _build_escalation_prompt(
        self,
        proposals: List[Proposal],
        domain: str,
        operation_text: str,
        voting_result: VotingResult,
    ) -> str:
        """Build prompt for external model escalation"""
        prompt = f"""You are an expert consultant for a multi-agent council.

**ESCALATION CONTEXT**

Domain: {domain}
Operation: {operation_text}
Escalation Reason: {voting_result.escalation_reason}

**PROPOSALS FROM AGENTS**

"""
        for i, proposal in enumerate(proposals, 1):
            prompt += f"""
{i}. {proposal.agent_name} (confidence: {proposal.confidence:.2f})
   Recommendation: {proposal.recommendation}
   Reasoning: {', '.join(proposal.reasoning_chain[:2])}...
"""

        prompt += f"""

**VOTING RESULT**

Aggregate Confidence: {voting_result.aggregate_confidence:.2f}
Winner Score: {voting_result.winning_score:.3f}
Needs Escalation: {voting_result.escalation_reason}

**YOUR TASK**

Review the proposals and provide:
1. Which proposal (if any) you recommend
2. Why you chose it
3. What the council should consider
4. Confidence in your recommendation (0-1)

Be concise but thorough."""

        return prompt

    def _select_escalation_model(self, domain: str, reason: str) -> str:
        """
        Select external model for escalation dynamically.

        Uses environment variables or falls back to intelligent defaults.
        Models are selected based on domain criticality and cost optimization.

        Environment Variables:
            COUNCIL_CRITICAL_MODEL: Model for security/architecture/ethics (default: auto-detect)
            COUNCIL_COMPLEX_MODEL: Model for complex reasoning (default: auto-detect)
            COUNCIL_DEFAULT_MODEL: Model for general escalation (default: auto-detect)

        Args:
            domain: Domain context
            reason: Escalation reason

        Returns:
            Model identifier compatible with consult-llm MCP
        """
        import os

        # Load from environment or use intelligent defaults
        # Default selection: Uses consult-llm's auto-detection if no env vars set
        critical_model = os.getenv("COUNCIL_CRITICAL_MODEL", None)
        complex_model = os.getenv("COUNCIL_COMPLEX_MODEL", None)
        default_model = os.getenv("COUNCIL_DEFAULT_MODEL", None)

        # If no env vars set, use consult-llm's auto-selection
        # consult-llm will choose best available model
        if not any([critical_model, complex_model, default_model]):
            # Return None to let consult-llm auto-select
            # consult-llm will use: o3 > gemini > claude-opus > deepseek based on availability
            if domain in ["security", "architecture", "ethics"]:
                return None  # Let consult-llm choose best critical model
            if "complex" in reason.lower():
                return None  # Let consult-llm choose best reasoning model
            return None  # Let consult-llm choose cost-effective model

        # Use configured models if env vars set
        if domain in ["security", "architecture", "ethics"]:
            return critical_model or None

        if "complex" in reason.lower():
            return complex_model or None

        return default_model or None

    def get_session_summary(self, session_id) -> Optional[dict]:
        """
        Get session summary by ID.

        Args:
            session_id: Session UUID

        Returns:
            Summary dict or None
        """
        return self.state_manager.get_session_summary(session_id)


# Singleton instance
_orchestrator: Optional[CouncilOrchestrator] = None


def get_orchestrator() -> CouncilOrchestrator:
    """Get singleton CouncilOrchestrator instance (lazy initialization)"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CouncilOrchestrator()
    return _orchestrator


# Convenience function


def convene_council(
    trigger: CouncilTrigger, context: Optional[str] = None, max_agents: int = 5
) -> CouncilSession:
    """Convene council for deliberation (convenience wrapper)"""
    return get_orchestrator().convene_council(trigger, context, max_agents)
