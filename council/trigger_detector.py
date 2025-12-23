"""
Trigger Detector - Council Convocation Condition Detection

Detects 8 conditions that require council deliberation:
1. Architectural decisions - Design choices, tech stack, migrations
2. Security/risk decisions - Auth, secrets, vulnerabilities
3. Agent disagreements - Multiple conflicting proposals
4. Quality gate failures - TDD, linting, test failures
5. Ethical flags - Privacy, bias, misinformation
6. Low aggregate confidence - Agents uncertain (< 0.75)
7. External commitments - Deploys, API calls, publishing
8. Novel/OOD queries - Out-of-distribution, unfamiliar tasks

Key Functions:
- detect_trigger(): Main entry point for trigger detection
- infer_domain(): Map operation to domain (security, architecture, etc.)
"""

import re
from typing import List, Optional, Tuple

from .schemas import CouncilTrigger, TriggerCondition


# ============================================================================
# Pattern Definitions for Trigger Detection
# ============================================================================

# Pattern format: (regex_pattern, trigger_condition, inferred_domain)
# IMPORTANT: Security patterns come BEFORE architectural patterns (precedence)
TRIGGER_PATTERNS = [
    # 2. SECURITY/RISK DECISIONS (check these FIRST - higher priority)
    (
        r"(auth|authentication|authorization|oauth|jwt|token|session)",
        TriggerCondition.SECURITY,
        "security",
    ),
    (
        r"(secret|credential|password|api.?key|private.?key|certificate)",
        TriggerCondition.SECURITY,
        "security",
    ),
    (
        r"(vulnerabilit|exploit|injection|xss|csrf|security.?audit)",
        TriggerCondition.SECURITY,
        "security",
    ),
    (r"(encrypt|decrypt|hash|sign|verify).*(data|password|token)", TriggerCondition.SECURITY, "security"),
    # 1. ARCHITECTURAL DECISIONS
    (
        r"(design|architect|structure).*(api|service|system|database|schema|migration)",
        TriggerCondition.ARCHITECTURAL,
        "architecture",
    ),
    (
        r"(refactor|restructure|redesign).*(codebase|architecture|system)",
        TriggerCondition.ARCHITECTURAL,
        "architecture",
    ),
    (
        r"(choose|select|decide).*(framework|library|stack|technology|database)",
        TriggerCondition.ARCHITECTURAL,
        "architecture",
    ),
    (r"(migration|migrate).*(database|schema|api)", TriggerCondition.ARCHITECTURAL, "architecture"),
    # 3. QUALITY GATE FAILURES (detected from hook events, not patterns)
    # 4. AGENT DISAGREEMENTS (detected programmatically from proposals)
    # 5. ETHICAL FLAGS
    (
        r"(privacy|gdpr|pii|personal.?data|data.?protection)",
        TriggerCondition.ETHICAL,
        "ethics",
    ),
    (r"(bias|fairness|discriminat|ethical)", TriggerCondition.ETHICAL, "ethics"),
    (
        r"(misinformation|fake|manipulat).*(content|data|user)",
        TriggerCondition.ETHICAL,
        "ethics",
    ),
    # 6. LOW CONFIDENCE (detected from proposal confidence scores)
    # 7. EXTERNAL COMMITMENTS
    (r"git.*(push|deploy|publish)", TriggerCondition.EXTERNAL_COMMITMENT, "deployment"),
    (
        r"(deploy|publish|release).*(production|prod|live)",
        TriggerCondition.EXTERNAL_COMMITMENT,
        "deployment",
    ),
    (
        r"(npm|pypi|docker).*(publish|push|release)",
        TriggerCondition.EXTERNAL_COMMITMENT,
        "deployment",
    ),
    (
        r"(api|http).*(call|request|post|put|delete).*(external|third.?party)",
        TriggerCondition.EXTERNAL_COMMITMENT,
        "api",
    ),
    # 8. NOVEL/OOD QUERIES
    (
        r"(unfamiliar|new|novel|never.?seen|unknown).*(technology|framework|pattern)",
        TriggerCondition.NOVEL_QUERY,
        "general",
    ),
    (
        r"(how.?do.?i|what.?is.?the.?best.?way).*(implement|design|build)",
        TriggerCondition.NOVEL_QUERY,
        "general",
    ),
    (
        r"(should.?we.?use|choose.?between|which.?is.?better)",
        TriggerCondition.NOVEL_QUERY,
        "general",
    ),
]


class TriggerDetector:
    """
    Detects conditions requiring council convocation.

    Analyzes tool calls, operation text, and risk levels to determine
    if multi-agent deliberation is needed.
    """

    def __init__(self):
        """Initialize trigger detector with compiled patterns"""
        self.patterns = [
            (re.compile(pattern, re.IGNORECASE), condition, domain)
            for pattern, condition, domain in TRIGGER_PATTERNS
        ]

    def detect_trigger(
        self,
        tool_name: str,
        operation_text: str,
        risk_level: Optional[str] = None,
    ) -> Optional[CouncilTrigger]:
        """
        Main entry point for trigger detection.

        Args:
            tool_name: Name of tool being invoked (e.g., 'Bash', 'Write', 'Edit')
            operation_text: Text description of operation (e.g., command, file content)
            risk_level: Risk level from intelligent_gate (LOW/MEDIUM/HIGH/CRITICAL)

        Returns:
            CouncilTrigger if condition detected, None otherwise
        """
        # High/Critical risk always triggers council
        if risk_level in ("HIGH", "CRITICAL"):
            condition, domain = self._match_patterns(operation_text)
            if condition is None:
                # Default to security for high-risk operations
                condition = TriggerCondition.SECURITY
                domain = "security"

            return CouncilTrigger(
                condition=condition,
                tool_name=tool_name,
                operation_text=operation_text[:500],  # Truncate for storage
                inferred_domain=domain,
                risk_level=risk_level,
            )

        # Pattern-based detection
        condition, domain = self._match_patterns(operation_text)
        if condition is not None:
            return CouncilTrigger(
                condition=condition,
                tool_name=tool_name,
                operation_text=operation_text[:500],
                inferred_domain=domain,
                risk_level=risk_level,
            )

        # No trigger detected
        return None

    def _match_patterns(
        self, text: str
    ) -> Tuple[Optional[TriggerCondition], Optional[str]]:
        """
        Match operation text against trigger patterns.

        Returns:
            Tuple of (TriggerCondition, domain) if match found, (None, None) otherwise
        """
        for pattern, condition, domain in self.patterns:
            if pattern.search(text):
                return condition, domain

        return None, None

    def detect_quality_failure(
        self, failure_type: str, details: str
    ) -> CouncilTrigger:
        """
        Create trigger for quality gate failure.

        Args:
            failure_type: Type of failure (e.g., 'tdd_violation', 'linting_error')
            details: Failure details

        Returns:
            CouncilTrigger for quality failure
        """
        return CouncilTrigger(
            condition=TriggerCondition.QUALITY_FAILURE,
            tool_name="quality_gate",
            operation_text=f"{failure_type}: {details[:400]}",
            inferred_domain="quality",
            risk_level="MEDIUM",
        )

    def detect_low_confidence(
        self, aggregate_confidence: float, context: str
    ) -> CouncilTrigger:
        """
        Create trigger for low aggregate confidence.

        Args:
            aggregate_confidence: Mean confidence across proposals
            context: Context of low confidence

        Returns:
            CouncilTrigger for low confidence
        """
        return CouncilTrigger(
            condition=TriggerCondition.LOW_CONFIDENCE,
            tool_name="confidence_check",
            operation_text=f"Aggregate confidence {aggregate_confidence:.2f} < 0.75: {context[:400]}",
            inferred_domain="general",
            risk_level="MEDIUM",
        )

    def detect_disagreement(
        self, agent_proposals: List[str], conflict_summary: str
    ) -> CouncilTrigger:
        """
        Create trigger for agent disagreement.

        Args:
            agent_proposals: List of conflicting agent names
            conflict_summary: Description of conflict

        Returns:
            CouncilTrigger for disagreement
        """
        agents_str = ", ".join(agent_proposals)
        return CouncilTrigger(
            condition=TriggerCondition.DISAGREEMENT,
            tool_name="disagreement_detector",
            operation_text=f"Agents disagree ({agents_str}): {conflict_summary[:400]}",
            inferred_domain="general",
            risk_level="MEDIUM",
        )

    def infer_domain(self, text: str) -> str:
        """
        Infer primary domain from operation text.

        Args:
            text: Operation text to analyze

        Returns:
            Domain name (e.g., 'security', 'architecture', 'api_design')
        """
        # Try pattern matching first
        for pattern, _, domain in self.patterns:
            if pattern.search(text):
                return domain

        # Keyword-based inference
        text_lower = text.lower()

        if any(
            kw in text_lower
            for kw in ["api", "endpoint", "rest", "graphql", "openapi"]
        ):
            return "api_design"

        if any(
            kw in text_lower
            for kw in ["database", "query", "schema", "migration", "sql"]
        ):
            return "database"

        if any(kw in text_lower for kw in ["test", "testing", "pytest", "unittest"]):
            return "testing"

        if any(
            kw in text_lower for kw in ["performance", "optimize", "cache", "speed"]
        ):
            return "performance"

        if any(kw in text_lower for kw in ["deploy", "docker", "kubernetes", "ci/cd"]):
            return "devops"

        if any(
            kw in text_lower
            for kw in ["frontend", "react", "vue", "angular", "svelte", "component", "ui", "css"]
        ):
            return "frontend"

        if any(
            kw in text_lower
            for kw in ["backend", "server", "fastapi", "django", "flask"]
        ):
            return "backend"

        # Default
        return "general"


# Singleton instance
_detector: Optional[TriggerDetector] = None


def get_detector() -> TriggerDetector:
    """Get singleton TriggerDetector instance (lazy initialization)"""
    global _detector
    if _detector is None:
        _detector = TriggerDetector()
    return _detector


# Convenience functions


def detect_trigger(
    tool_name: str, operation_text: str, risk_level: Optional[str] = None
) -> Optional[CouncilTrigger]:
    """Detect council trigger (convenience wrapper)"""
    return get_detector().detect_trigger(tool_name, operation_text, risk_level)


def infer_domain(text: str) -> str:
    """Infer domain from text (convenience wrapper)"""
    return get_detector().infer_domain(text)
