"""
Proposal Generator - Agent Proposal Collection

Collects independent proposals from relevant agents using:
- Ollama MCP for local models (cost-free: llama3.2, devstral, qwen3-coder)
- Claude Opus fallback for critical domains (security, architecture)

Key Functions:
- generate_proposals(): Collect proposals from selected agents
- _generate_single_proposal(): Generate proposal from one agent
- _select_model_for_domain(): Choose Ollama vs Claude based on domain
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

# Add parent directory to path for MCP imports
sys.path.insert(0, str(Path.home() / ".claude"))

from council.expertise_registry import ExpertiseRegistry
from council.schemas import AgentExpertise, Proposal


class ProposalGenerator:
    """
    Generates proposals from relevant agents using Ollama MCP.

    Optimizes cost by using local models for most proposals,
    falling back to Claude Opus only for critical security/architecture decisions.
    """

    def __init__(self, registry: Optional[ExpertiseRegistry] = None):
        """
        Initialize proposal generator.

        Args:
            registry: ExpertiseRegistry instance (creates new if None)
        """
        self.registry = registry or ExpertiseRegistry()

        # Model selection strategy
        self.critical_domains = ["security", "architecture", "ethics"]
        self.local_models = {
            "fast": "llama3.2",  # Ultra-fast, good for simple reasoning
            "code": "devstral:24b",  # Code understanding
            "reasoning": "qwen3-coder:30b",  # Long-context analysis
            "deep": "gpt-oss:20b",  # Deeper reasoning
        }

    def generate_proposals(
        self,
        domain: str,
        operation_text: str,
        context: Optional[str] = None,
        max_agents: int = 5,
        min_expertise: float = 0.5,
    ) -> List[Proposal]:
        """
        Generate proposals from relevant agents.

        Args:
            domain: Domain requiring deliberation (e.g., 'security', 'api_design')
            operation_text: Text of operation being evaluated
            context: Additional context for agents
            max_agents: Maximum number of agents to query
            min_expertise: Minimum expertise weight threshold

        Returns:
            List of Proposal objects from agents
        """
        # Select relevant agents
        relevant_agents = self.registry.get_relevant_agents(domain, min_expertise)
        selected_agents = relevant_agents[:max_agents]

        if not selected_agents:
            # Fallback: get top proposers if no domain experts
            all_proposers = self.registry.get_proposers()
            selected_agents = all_proposers[:min(3, len(all_proposers))]

        # Generate proposals in parallel (simulate for now)
        proposals = []
        for agent in selected_agents:
            try:
                proposal = self._generate_single_proposal(
                    agent, domain, operation_text, context
                )
                if proposal:
                    proposals.append(proposal)
            except Exception as e:
                print(
                    f"Warning: Failed to generate proposal from {agent.name}: {e}",
                    file=sys.stderr,
                )
                continue

        return proposals

    def _generate_single_proposal(
        self,
        agent: AgentExpertise,
        domain: str,
        operation_text: str,
        context: Optional[str],
    ) -> Optional[Proposal]:
        """
        Generate a single proposal from an agent.

        Args:
            agent: AgentExpertise object
            domain: Domain for this proposal
            operation_text: Operation being evaluated
            context: Additional context

        Returns:
            Proposal object or None if generation fails
        """
        # Select model based on domain criticality
        model = self._select_model_for_domain(domain)

        # Build prompt for agent
        prompt = self._build_proposal_prompt(
            agent, domain, operation_text, context
        )

        # Generate proposal using selected model
        try:
            if model.startswith("claude"):
                # Use Claude API (future: integrate with consult-llm MCP)
                response = self._generate_with_claude(prompt, model)
            else:
                # Use Ollama MCP
                response = self._generate_with_ollama(prompt, model)

            # Parse structured response
            return self._parse_proposal_response(agent, response, model, domain)

        except Exception as e:
            print(
                f"Error generating proposal with {model} for {agent.name}: {e}",
                file=sys.stderr,
            )
            return None

    def _select_model_for_domain(self, domain: str) -> str:
        """
        Select appropriate model based on domain criticality.

        Uses environment variables for model mapping, falls back to intelligent defaults.

        Environment Variables:
            COUNCIL_PROPOSAL_CRITICAL: Model for critical domains (default: auto-detect)
            COUNCIL_PROPOSAL_CODE: Model for code domains (default: devstral:24b)
            COUNCIL_PROPOSAL_REASONING: Model for complex reasoning (default: qwen3-coder:30b)
            COUNCIL_PROPOSAL_FAST: Model for general proposals (default: llama3.2)

        Args:
            domain: Domain requiring proposal

        Returns:
            Model identifier compatible with Ollama or consult-llm
        """
        import os

        # Load from environment or use defaults
        critical_model = os.getenv("COUNCIL_PROPOSAL_CRITICAL", None)
        code_model = os.getenv("COUNCIL_PROPOSAL_CODE", self.local_models["code"])
        reasoning_model = os.getenv("COUNCIL_PROPOSAL_REASONING", self.local_models["reasoning"])
        fast_model = os.getenv("COUNCIL_PROPOSAL_FAST", self.local_models["fast"])

        # Critical domains can use external models if configured
        # Default: Use fast local model (cost-free)
        if domain in self.critical_domains:
            return critical_model or fast_model  # Fallback to local if not configured

        # Code/API domains
        if domain in ["api_design", "backend", "frontend"]:
            return code_model

        # Complex reasoning
        if domain in ["architecture", "database", "performance"]:
            return reasoning_model

        # Default: fast local model
        return fast_model

    def _build_proposal_prompt(
        self,
        agent: AgentExpertise,
        domain: str,
        operation_text: str,
        context: Optional[str],
    ) -> str:
        """
        Build structured prompt for agent proposal generation.

        Args:
            agent: Agent generating proposal
            domain: Domain context
            operation_text: Operation text
            context: Additional context

        Returns:
            Formatted prompt string
        """
        expertise_level = agent.get_expertise(domain, default=0.5)

        prompt = f"""You are {agent.name}, an expert in {domain} (expertise: {expertise_level:.1f}/1.0).

**COUNCIL DELIBERATION TASK**

An operation requires multi-agent deliberation:

**Domain:** {domain}
**Operation:** {operation_text}

{f'**Context:** {context}' if context else ''}

**YOUR TASK:**
Provide a structured proposal with:

1. **Recommendation** (1-2 sentences): Your recommended action/decision
2. **Reasoning Chain** (3-5 bullet points): Step-by-step logic
3. **Confidence** (0.0-1.0): How confident are you in this recommendation?
4. **Domain Relevance** (0.0-1.0): How relevant is this to your expertise?

**OUTPUT FORMAT (JSON):**
{{
  "recommendation": "Your concise recommendation here",
  "reasoning_chain": [
    "First reasoning step",
    "Second reasoning step",
    "Third reasoning step"
  ],
  "confidence": 0.85,
  "domain_relevance": 0.90
}}

**IMPORTANT:**
- Be honest about confidence (don't overstate certainty)
- Domain relevance should reflect your expertise in {domain}
- Reasoning should be clear and logical
- Output ONLY valid JSON
"""

        return prompt

    def _generate_with_ollama(self, prompt: str, model: str) -> str:
        """
        Generate response using Ollama MCP.

        Args:
            prompt: Prompt text
            model: Ollama model name

        Returns:
            Generated text response
        """
        # Phase 3: Use Ollama MCP server for better integration
        # The MCP server provides ollama_generate and ollama_chat tools
        # For Phase 3, we'll use subprocess with --json for structured output
        import subprocess

        try:
            # Call ollama with JSON format enforcement
            # This ensures we get valid JSON responses for parsing
            result = subprocess.run(
                [
                    "ollama",
                    "run",
                    model,
                    "--format", "json",  # Force JSON output
                    prompt,
                ],
                capture_output=True,
                text=True,
                timeout=60,  # Increased timeout for larger models
            )

            if result.returncode == 0:
                response = result.stdout.strip()

                # Ollama with --format json should return pure JSON
                # But some models may still wrap it, so handle both cases
                if response.startswith("```"):
                    # Strip markdown if present
                    lines = response.split("\n")
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    response = "\n".join(lines).strip()

                return response
            else:
                raise Exception(f"Ollama error: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise Exception(f"Ollama generation timeout (60s) for {model}")
        except FileNotFoundError:
            raise Exception("Ollama not installed or not in PATH")

    def _generate_with_claude(self, prompt: str, model: str) -> str:
        """
        Generate response using Claude API.

        Args:
            prompt: Prompt text
            model: Claude model name

        Returns:
            Generated text response
        """
        # Placeholder for Claude API integration
        # Will integrate with consult-llm MCP in Phase 3
        raise NotImplementedError(
            "Claude API integration pending (Phase 3). "
            "Use Ollama models for Phase 2 testing."
        )

    def _parse_proposal_response(
        self, agent: AgentExpertise, response: str, model: str, domain: str
    ) -> Proposal:
        """
        Parse model response into Proposal object.

        Args:
            agent: Agent that generated proposal
            response: Raw model response
            model: Model used
            domain: Domain context

        Returns:
            Proposal object

        Raises:
            ValueError: If response cannot be parsed
        """
        # Extract JSON from response (handle markdown code blocks)
        json_str = response.strip()

        # Remove markdown code fences if present
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            json_str = "\n".join(lines)

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from {model}: {e}")

        # Validate required fields
        required_fields = [
            "recommendation",
            "reasoning_chain",
            "confidence",
            "domain_relevance",
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' in response")

        # Create Proposal object
        return Proposal(
            agent_name=agent.name,
            recommendation=data["recommendation"],
            reasoning_chain=data["reasoning_chain"],
            confidence=float(data["confidence"]),
            domain_relevance=float(data["domain_relevance"]),
            model_used=model,
        )


# Singleton instance
_generator: Optional[ProposalGenerator] = None


def get_generator() -> ProposalGenerator:
    """Get singleton ProposalGenerator instance (lazy initialization)"""
    global _generator
    if _generator is None:
        _generator = ProposalGenerator()
    return _generator


# Convenience function


def generate_proposals(
    domain: str,
    operation_text: str,
    context: Optional[str] = None,
    max_agents: int = 5,
) -> List[Proposal]:
    """Generate proposals from relevant agents (convenience wrapper)"""
    return get_generator().generate_proposals(
        domain, operation_text, context, max_agents
    )
