"""
Expertise Registry - Agent Expertise Weight Management

Loads and manages agent expertise profiles from YAML frontmatter.
Provides agent selection based on domain relevance.

Key Functions:
- load_agent_expertise(): Parse YAML frontmatter from agent files
- get_relevant_agents(domain, min_weight): Find experts for a domain
- get_agent_expertise(agent_name): Retrieve specific agent profile
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .schemas import AgentExpertise, CouncilRole


class ExpertiseRegistry:
    """
    Registry of agent expertise profiles loaded from YAML frontmatter.

    Agents are defined in ~/.claude/agents/*.md with YAML frontmatter:

    ---
    name: security-auditor
    expertise_weights:
      security: 1.0
      architecture: 0.7
      performance: 0.4
    council_role: proposer
    ---
    """

    def __init__(self, agents_dir: Optional[Path] = None):
        """
        Initialize registry and load agent profiles.

        Args:
            agents_dir: Path to agents directory (default: ~/.claude/agents)
        """
        if agents_dir is None:
            agents_dir = Path.home() / ".claude" / "agents"

        self.agents_dir = Path(agents_dir)
        self._cache: Dict[str, AgentExpertise] = {}
        self._load_all_agents()

    def _load_all_agents(self) -> None:
        """Scan agents directory and load all agent profiles"""
        if not self.agents_dir.exists():
            raise FileNotFoundError(
                f"Agents directory not found: {self.agents_dir}. "
                "Expected at ~/.claude/agents/"
            )

        # Load top-level agents
        for agent_file in self.agents_dir.glob("*.md"):
            self._load_agent_file(agent_file)

        # Load agents in subdirectories (e.g., hoa/hoa-orchestrator.md)
        for agent_file in self.agents_dir.rglob("**/*.md"):
            if agent_file.parent != self.agents_dir:  # Skip if already loaded
                self._load_agent_file(agent_file)

    def _load_agent_file(self, file_path: Path) -> None:
        """
        Parse YAML frontmatter from agent markdown file.

        Expected format:
        ---
        name: agent-name
        expertise_weights:
          domain1: 0.9
          domain2: 0.7
        council_role: proposer
        model: sonnet
        ---
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract YAML frontmatter (between --- markers)
            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---", content, re.DOTALL | re.MULTILINE
            )

            if not frontmatter_match:
                # No frontmatter - skip this file
                return

            frontmatter_text = frontmatter_match.group(1)
            data = yaml.safe_load(frontmatter_text)

            if not data or "name" not in data:
                # Invalid frontmatter - skip
                return

            # Parse into AgentExpertise model
            agent_name = data["name"]
            expertise = AgentExpertise(
                name=agent_name,
                expertise_weights=data.get("expertise_weights", {}),
                council_role=CouncilRole(data.get("council_role", "proposer")),
                model_tier=data.get("model", "sonnet"),
                description=data.get("description"),
            )

            self._cache[agent_name] = expertise

        except Exception as e:
            # Log error but don't fail entire registry load
            print(f"Warning: Failed to load agent from {file_path}: {e}")

    def get_relevant_agents(
        self, domain: str, min_weight: float = 0.5
    ) -> List[AgentExpertise]:
        """
        Find agents with expertise in a given domain.

        Args:
            domain: Domain to search for (e.g., 'security', 'architecture')
            min_weight: Minimum expertise weight threshold (default: 0.5)

        Returns:
            List of AgentExpertise objects sorted by expertise (highest first)
        """
        relevant = []

        for agent in self._cache.values():
            # Skip abstainers
            if agent.council_role == CouncilRole.ABSTAINER:
                continue

            # Check domain expertise
            expertise_weight = agent.get_expertise(domain, default=0.0)
            if expertise_weight >= min_weight:
                relevant.append(agent)

        # Sort by expertise weight (descending)
        relevant.sort(
            key=lambda a: a.get_expertise(domain, default=0.0), reverse=True
        )

        return relevant

    def get_agent_expertise(self, agent_name: str) -> Optional[AgentExpertise]:
        """
        Retrieve expertise profile for a specific agent.

        Args:
            agent_name: Agent name (e.g., 'security-auditor')

        Returns:
            AgentExpertise object or None if not found
        """
        return self._cache.get(agent_name)

    def list_all_agents(self) -> List[str]:
        """Get names of all loaded agents"""
        return sorted(self._cache.keys())

    def get_domains(self) -> List[str]:
        """Get all unique domains across all agents"""
        domains = set()
        for agent in self._cache.values():
            domains.update(agent.expertise_weights.keys())
        return sorted(domains)

    def get_proposers(self) -> List[AgentExpertise]:
        """Get all agents with proposer role"""
        return [
            agent
            for agent in self._cache.values()
            if agent.council_role == CouncilRole.PROPOSER
        ]

    def reload(self) -> None:
        """Reload all agent profiles from disk"""
        self._cache.clear()
        self._load_all_agents()


# Singleton instance
_registry: Optional[ExpertiseRegistry] = None


def get_registry() -> ExpertiseRegistry:
    """Get singleton ExpertiseRegistry instance (lazy initialization)"""
    global _registry
    if _registry is None:
        _registry = ExpertiseRegistry()
    return _registry


# Convenience functions


def get_relevant_agents(domain: str, min_weight: float = 0.5) -> List[AgentExpertise]:
    """Find agents with expertise in domain (convenience wrapper)"""
    return get_registry().get_relevant_agents(domain, min_weight)


def get_agent_expertise(agent_name: str) -> Optional[AgentExpertise]:
    """Get expertise profile for agent (convenience wrapper)"""
    return get_registry().get_agent_expertise(agent_name)
