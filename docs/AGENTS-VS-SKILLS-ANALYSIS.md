# Agents vs Skills: Architecture Analysis

## Executive Summary

**Agents** and **Skills** are fundamentally different:
- **Agents** = WHO executes work (specialists with tools and models)
- **Skills** = HOW to approach work (methodology, no execution)

**Three-tier enhancements apply ONLY to agents**, not skills.

---

## Architectural Differences

### Agents (20 total)

**Purpose:** Specialized executors that perform work

**Structure:**
```yaml
---
name: backend-developer
description: Senior backend engineer specializing in...
model: sonnet              # ← EXECUTES with specific model
tools: Read, Write, Edit   # ← USES tools to perform work
---

# Agent content: capabilities, workflows, communication protocols
```

**Characteristics:**
- Execute tasks directly
- Use tools (Read, Write, Edit, Bash, etc.)
- Run with specific models (Opus/Sonnet/Haiku)
- Produce outputs (code, configs, docs)
- Delegated to by name (→ backend-developer)

**Examples:**
- `python-pro` - Writes Python code with type hints
- `security-auditor` - Analyzes code for vulnerabilities
- `devops-engineer` - Creates CI/CD pipelines

---

### Skills (154 total)

**Purpose:** Methodological guidance that shapes Claude's approach

**Structure:**
```yaml
---
name: systematic-debugging
description: Four-phase debugging framework...
triggers:                   # ← AUTO-ACTIVATES on context
  - bug
  - test failure
  - unexpected behavior
---

# Skill content: methodology, patterns, when to use, examples
```

**Characteristics:**
- Provide methodology, not execution
- No tool usage (describe what to do)
- No model assignment (guide current model)
- Auto-activate based on context/triggers
- Pure guidance/patterns

**Examples:**
- `systematic-debugging` - Four-phase framework (root cause → pattern → hypothesis → implement)
- `test-driven-development` - RED-GREEN-REFACTOR cycle
- `api-design-patterns` - 5-layer API pattern (models → services → routers → tests → docs)

---

## Enhancement Applicability

### 1. Three-Tier Model Strategy

**Agents:** ✅ APPLICABLE
- Agents execute with specific models
- Opus for critical work, Sonnet for standard, Haiku for simple
- Reduces cost by 40-60%

**Skills:** ❌ NOT APPLICABLE
- Skills don't execute, they guide
- Current Claude model uses skill's guidance
- No model assignment needed

**Verdict:** Agent-only enhancement

---

### 2. Minimal Tool Assignment

**Agents:** ✅ APPLICABLE
- Agents use tools directly (Read, Write, Edit, Bash)
- Least-privilege security (reviewers read-only, developers full)
- Prevents accidental modifications

**Skills:** ❌ NOT APPLICABLE
- Skills describe what Claude should do
- Claude uses tools based on skill guidance
- Tool restrictions belong to agents, not skills

**Verdict:** Agent-only enhancement

---

### 3. ReAct Prompting Pattern

**Agents:** ✅ APPLICABLE
- Agents benefit from systematic Think → Act → Observe → Repeat
- Prevents rushed implementations
- Self-correcting behavior

**Skills:** ⚠️ PARTIALLY APPLICABLE
- Some skills already have systematic frameworks:
  - `systematic-debugging`: 4-phase framework
  - `test-driven-development`: RED-GREEN-REFACTOR
  - `pipeline-implement`: TDD enforcement
- Many skills are pattern libraries, not workflows
- ReAct-like patterns already exist where beneficial

**Verdict:** Already addressed in workflow-oriented skills

---

## Skill Categories Analysis

### Workflow Skills (Already Have Systematic Patterns)

✅ **systematic-debugging**
- Phase 1: Root Cause Investigation
- Phase 2: Pattern Analysis
- Phase 3: Hypothesis Testing
- Phase 4: Implementation
*(This IS ReAct, just named differently)*

✅ **test-driven-development**
- RED: Write failing test
- GREEN: Make it pass
- REFACTOR: Improve code
*(This IS ReAct for TDD)*

✅ **pipeline-* skills** (4 skills)
- PM Spec → Arch Review → Implement → Test Verify
- Sequential workflow with quality gates
*(Pipeline IS ReAct for features)*

### Pattern Skills (Don't Need ReAct)

❌ **api-design-patterns**
- 5-layer pattern reference
- Model/Service/Router/Test/Docs
- Not a workflow, just patterns

❌ **python-best-practices**
- Type hints guide
- Pythonic idioms
- Not a workflow, just best practices

❌ **token-optimization**
- Efficiency patterns
- Progressive disclosure
- Not a workflow, just techniques

### Tool Skills (Don't Need ReAct)

❌ **local-models**
- When to use Ollama vs Claude
- Model selection guide
- Not a workflow, just decision tree

❌ **escalation-reasoning**
- 5-tier escalation ladder
- When to use /think, /megathink, etc.
- Not a workflow, just escalation guide

---

## Summary

### What Was Enhanced

✅ **Agents (20):**
- Three-tier model strategy (Opus/Sonnet/Haiku)
- Minimal tool assignment (read-only vs full)
- ReAct prompting methodology

### What Doesn't Need Enhancement

✅ **Skills (154):**
- No model assignment needed (they guide, not execute)
- No tool assignment needed (they describe, not use)
- Workflow skills already have ReAct-like patterns
- Pattern/tool skills don't need workflows

---

## Validation

**Checked:**
- 0 skills have `model:` field (correct - not needed)
- 0 skills have `tools:` field (correct - not needed)
- 0 skills have "ReAct" keyword (correct - they use domain-specific names)

**But:**
- `systematic-debugging` has 4-phase framework ✅
- `test-driven-development` has RED-GREEN-REFACTOR ✅
- `pipeline-*` skills have sequential workflow ✅
- Other skills are pattern libraries (no workflow needed) ✅

---

## Conclusion

**Skills are already optimally structured:**
1. Workflow skills have systematic patterns (ReAct equivalents)
2. Pattern skills provide reference guides (no workflow needed)
3. Tool skills provide decision frameworks (no workflow needed)

**No further enhancement needed for skills.**

The three-tier agent enhancements are **agent-specific** and do not apply to skills due to their fundamentally different architecture.

---

**Analysis Date:** 2025-12-21
**Skills Reviewed:** 154
**Agents Enhanced:** 20
**Verdict:** Agent enhancements complete, skills already optimal
