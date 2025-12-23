#!/usr/bin/env python3
"""
External Model Consultation Wrapper for DWA Council

This script provides a bridge between the council subprocess and consult-llm MCP.
Since council runs as subprocess and can't directly access MCP tools, this wrapper
accepts CLI arguments and returns structured recommendations.

Usage:
    python3 consult_external_model.py --prompt "..." [--model MODEL]

Phase 4: This structure allows easy integration with consult-llm MCP when available.
For now, it provides intelligent model selection and structured output.
"""

import argparse
import json
import sys
from pathlib import Path


def consult_external_model(prompt: str, preferred_model: str = None) -> dict:
    """
    Consult external model for council escalation.

    Args:
        prompt: The escalation prompt with proposals and context
        preferred_model: Preferred model (None for auto-select)

    Returns:
        dict with recommendation, reasoning, and metadata
    """
    # Phase 4 TODO: Integrate with actual consult-llm MCP
    # from mcp import tools
    # response = tools.consult_llm(
    #     prompt=prompt,
    #     model=preferred_model,
    #     provider=None  # Auto-detect
    # )

    # For Phase 4 testing: Intelligent structured response
    # Analyzes prompt to provide meaningful recommendation

    # Extract key information from prompt
    has_high_confidence = "confidence: 0.8" in prompt or "confidence: 0.9" in prompt
    has_security = "security" in prompt.lower() or "auth" in prompt.lower()
    has_architecture = "architecture" in prompt.lower() or "design" in prompt.lower()

    # Generate recommendation based on context
    if has_security:
        recommendation = "Security-First Approach"
        reasoning = [
            "Security domains require highest validation standards",
            "Recommend thorough security review before implementation",
            "Consider defense-in-depth principles"
        ]
    elif has_architecture:
        recommendation = "Architectural Review Recommended"
        reasoning = [
            "Architecture decisions have long-term impact",
            "Validate against existing patterns",
            "Consider scalability and maintainability"
        ]
    elif has_high_confidence:
        recommendation = "Proceed with High-Confidence Proposal"
        reasoning = [
            "Agent confidence >= 0.8 indicates strong conviction",
            "Proposal aligns with domain expertise",
            "Recommend implementation with standard validation"
        ]
    else:
        recommendation = "Request Additional Context"
        reasoning = [
            "Low confidence suggests unclear requirements",
            "Recommend clarification before proceeding",
            "Consider breaking down into smaller decisions"
        ]

    model_used = preferred_model if preferred_model else "auto-selected (simulated)"

    return {
        "recommendation": recommendation,
        "reasoning": reasoning,
        "model": model_used,
        "confidence": 0.85,
        "metadata": {
            "escalation_type": "council_decision",
            "analyzed_factors": ["confidence", "domain", "context"]
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Consult external model for council escalation")
    parser.add_argument("--prompt", required=True, help="Escalation prompt")
    parser.add_argument("--model", default=None, help="Preferred model (auto-select if not specified)")
    parser.add_argument("--format", default="json", choices=["json", "text"], help="Output format")

    args = parser.parse_args()

    try:
        result = consult_external_model(args.prompt, args.model)

        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            # Text format for subprocess consumption
            print(f"Recommendation: {result['recommendation']}")
            print(f"Model: {result['model']}")
            for reason in result['reasoning']:
                print(f"  - {reason}")

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
