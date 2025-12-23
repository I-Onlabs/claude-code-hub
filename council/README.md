# DWA Council System

**Multi-Agent Deliberation Platform for Claude Code**

---

## Overview

The DWA (Debate-Weighted Aggregation) Council is a production-ready multi-agent coordination system that enables 21 specialized agents to deliberate on critical decisions through structured voting, optional debate, and autonomous escalation.

**Status:** ✅ Production Ready (Phase 4 Complete)
**Test Results:** 6/6 integration tests passing (100% pass rate)

---

## Quick Start

### 1. Install Files

Copy the council system to your Claude Code configuration:

```bash
# Copy council system
cp -r council ~/.claude/

# Copy library files
cp -r lib ~/.claude/

# Copy enhanced agents (21 agents with expertise_weights)
cp -r agents/* ~/.claude/agents/

# Verify installation
python3 ~/.claude/council/test_phase4.py
# Expected: 6/6 tests passing
```

### 2. Run Interactive Demo

```bash
python3 ~/.claude/council/demo_council_system.py
```

This demo shows:
- Trigger detection
- Agent selection by expertise
- Proposal generation
- DWA weighted voting
- Message bus integration
- Complete council workflow

### 3. Read Documentation

- **User Guide:** `COUNCIL_USER_GUIDE.md` - Comprehensive usage instructions
- **Phase 4 Summary:** `PHASE4_COMPLETE.md` - Technical implementation details
- **Project Summary:** `PROJECT_SUMMARY.md` - Complete project overview

---

## What's Included

### Council Core System (8 files)

1. **orchestrator.py** - Main entry point, convenes council
2. **expertise_registry.py** - Loads agent expertise from YAML frontmatter
3. **trigger_detector.py** - Detects 8 trigger conditions
4. **voting_aggregator.py** - DWA formula implementation
5. **proposal_generator.py** - Ollama-powered proposal generation
6. **debate_manager.py** - Optional debate orchestration (1-2 rounds)
7. **state_manager.py** - Memory-keeper persistence
8. **consult_external_model.py** - External model consultation bridge

**Total:** ~1,750 lines

### Message Bus System (2 files)

1. **message_bus.py** (in lib/) - Pub/sub message utilities
2. **memory_keeper_bridge.py** (in lib/) - Memory-keeper MCP bridge

**Total:** ~400 lines

### Enhanced Agents (21 agents)

All agents updated with:
- `expertise_weights` - Domain-specific capabilities (0.0-1.0)
- `council_role` - proposer/reviewer/abstainer

**Key agents:**
- coordinator-agent.md (NEW) - Central task coordinator
- architectural-cognition-engine.md - Deep architecture analysis
- research-oracle.md - External resource research
- task-orchestrator.md - Task breakdown and parallelization
- ... 17 more with expertise weights

### Testing & Documentation (6 files)

1. **test_phase4.py** - Integration test suite (6 tests)
2. **demo_council_system.py** - Interactive demo
3. **COUNCIL_USER_GUIDE.md** - User guide (650+ lines)
4. **PHASE4_COMPLETE.md** - Phase 4 summary (580+ lines)
5. **PROJECT_SUMMARY.md** - Complete overview (500+ lines)
6. **README.md** - This file

---

## How It Works

```
USER REQUEST
     ↓
TRIGGER DETECTION (intelligent_gate.py - 8 conditions)
     ↓
COUNCIL or SINGLE AGENT?
     ↓
COUNCIL PROCESS:
  1. Agent Selection (expertise_registry)
  2. Proposals (proposal_generator)
  3. Optional Debate (debate_manager)
  4. Weighted Voting (voting_aggregator)
  5. Escalation if needed (consult_external_model)
     ↓
MESSAGE BUS (coordinator dispatches tasks)
     ↓
SPECIALIZED AGENTS (execute tasks)
     ↓
RESULT CONSOLIDATION
     ↓
DECISION + AUDIT TRAIL
```

---

## 8 Trigger Conditions

The council automatically convenes when `intelligent_gate.py` detects:

1. **Architectural decisions** - Design choices, tech stack, migrations
2. **Security/risk operations** - Auth, secrets, vulnerabilities
3. **Agent disagreements** - Conflicting proposals
4. **Quality gate failures** - Failing tests, linting
5. **Ethical concerns** - Privacy, bias, misinformation
6. **Low confidence** - Aggregate < 0.75
7. **External commitments** - Deploys, API calls, publishing
8. **Novel/OOD queries** - Unfamiliar tech, edge cases

---

## 21 Agents by Role

### Proposers (11) - Generate Recommendations
- backend-developer, devops-engineer, python-pro
- api-designer, frontend-expert, database-architect
- performance-engineer, security-auditor
- kubernetes-specialist, data-engineer, error-detective
- strategic-vision-architect

### Reviewers (5) - Critique & Validate
- code-reviewer, qa-expert, documentation-engineer
- research-oracle, architectural-cognition-engine

### Abstainers (5) - Coordinate Without Bias
- coordinator-agent, bootstrap-orchestrator
- vibe-coding-coordinator, task-orchestrator

---

## Expertise Weights Example

**Security Domain** (8 agents with weights ≥ 0.5):
- security-auditor: 1.0
- code-reviewer: 0.9
- kubernetes-specialist: 0.9
- backend-developer: 0.8
- devops-engineer: 0.7
- performance-engineer: 0.6
- database-architect: 0.6
- frontend-expert: 0.5

When a security decision is needed, agents with higher weights have more influence in voting.

---

## DWA Voting Formula

```python
Score = Σ (Vote × Confidence × Expertise Weight)

# Example
security-auditor:    1.0 × 0.85 × 1.0 = 0.85
backend-developer:   1.0 × 0.80 × 0.8 = 0.64
code-reviewer:       1.0 × 0.75 × 0.9 = 0.675
# ... 5 more agents
Total Score: 4.92 / 8 agents = 0.615
```

The option with the highest total score wins.

---

## Message Bus Channels

| Channel | Purpose |
|---------|---------|
| `bus:coordination` | Broadcast announcements |
| `bus:registry` | Agent registration state |
| `bus:task-queue` | Pending task assignments |
| `bus:results` | Task completion results |
| `bus:agent:{id}` | Point-to-point messages |
| `bus:hooks` | Hook execution events |
| `bus:skills` | Skill execution events |

---

## Usage Examples

### Example 1: Automatic Council

```
User: "Design authentication system for our SPA"

→ Triggers: security + architecture
→ Selects: 5 agents (security-auditor, backend-developer,
           frontend-expert, code-reviewer, api-designer)
→ Proposals: 3 vote OAuth 2.0, 2 vote JWT
→ Debate: 1 round (hybrid approach discussed)
→ Decision: "OAuth 2.0 with PKCE + httpOnly cookies"
→ Time: 45 seconds
→ Cost: $0.12
```

### Example 2: Escalation

```
User: "Implement real-time collaborative editing with CRDTs"

→ Triggers: novel/OOD + architectural
→ Selects: 4 agents
→ Confidence: 0.55 (low - unfamiliar domain)
→ Escalates: Consult o3
→ o3 Response: "Use Yjs (CRDT library)"
→ Decision: "Use Yjs for collaborative editing"
→ Time: 65 seconds
→ Cost: $0.18 ($0.06 o3 + $0.12 council)
```

---

## Configuration

### Environment Variables

```bash
# Critical decisions
export COUNCIL_CRITICAL_MODEL="o3"

# Complex reasoning
export COUNCIL_COMPLEX_MODEL="gemini-2.0-flash-thinking-exp-1219"

# Code proposals (local Ollama - free)
export COUNCIL_PROPOSAL_CODE="qwen3-coder:30b"

# Auto-select (default)
export COUNCIL_PROPOSAL_DEFAULT=""
```

### Thresholds (orchestrator.py)

```python
MIN_AGENTS = 3                    # Minimum for council
ESCALATION_CONFIDENCE = 0.70      # Escalate if below
SKIP_DEBATE_CONSENSUS = 0.80      # Skip debate if above
MAX_DEBATE_ROUNDS = 2             # Maximum debates
```

---

## Testing

### Run Integration Tests

```bash
python3 ~/.claude/council/test_phase4.py
```

**Expected Results:**
- TEST 1: Expertise Weights ✅
- TEST 2: Memory-Keeper Bridge ✅
- TEST 3: Consult-LLM Bridge ✅
- TEST 4: Message Bus Integration ✅
- TEST 5: Expertise Matching ✅
- TEST 6: Coordinator Readiness ✅

**Pass Rate:** 6/6 (100%)

---

## Performance

### Token Usage

| Operation | Tokens | Cost (Opus) |
|-----------|--------|-------------|
| Council (3 agents, no debate) | ~3,500 | $0.05 |
| Council (5 agents, 1 debate) | ~8,000 | $0.12 |
| With escalation (o3) | ~12,000 | $0.18 |

**Cost Optimization:** Local Ollama for proposals = **$0 cost**

### Latency

- Trigger detection: <100ms
- Proposals (parallel): 5-15 seconds
- Debate round: 10-20 seconds
- **Total:** 30-60 seconds

---

## Architecture

### Directory Structure

```
~/.claude/
├── council/                      # Council system
│   ├── orchestrator.py
│   ├── expertise_registry.py
│   ├── trigger_detector.py
│   ├── voting_aggregator.py
│   ├── proposal_generator.py
│   ├── debate_manager.py
│   ├── state_manager.py
│   ├── consult_external_model.py
│   └── test_phase4.py
├── lib/                          # Libraries
│   ├── message_bus.py
│   └── memory_keeper_bridge.py
└── agents/                       # 21 agents
    ├── coordinator-agent.md
    └── ... (20 more with expertise)
```

---

## Documentation Files

| File | Lines | Purpose |
|------|-------|---------|
| COUNCIL_USER_GUIDE.md | 650+ | Comprehensive usage guide |
| PHASE4_COMPLETE.md | 580+ | Technical implementation |
| PROJECT_SUMMARY.md | 500+ | Complete overview |
| README.md | 300+ | This quick start |

---

## Next Steps

1. **Install:** Copy files to `~/.claude/`
2. **Test:** Run `test_phase4.py` (expect 6/6 pass)
3. **Demo:** Run `demo_council_system.py`
4. **Learn:** Read `COUNCIL_USER_GUIDE.md`
5. **Use:** Council auto-triggers on critical decisions

---

## Support

### Common Issues

**"Agents not loading"**
- Check YAML frontmatter syntax
- Run `test_phase4.py` to identify issues

**"Council not triggering"**
- Verify `intelligent_gate.py` hook registered
- Check trigger patterns match your operation

**"Low confidence"**
- Add more domain-specific agents
- Increase expertise weights
- Lower `ESCALATION_CONFIDENCE` threshold

### Resources

- User Guide: Comprehensive documentation
- Phase 4 Summary: Technical details
- Integration Tests: Verify installation
- Interactive Demo: See system in action

---

## Key Features

✅ **21 specialized agents** with domain expertise
✅ **Automatic trigger detection** (8 conditions)
✅ **Cost-optimized** (local Ollama for proposals)
✅ **Autonomous escalation** (o3/Gemini when needed)
✅ **Message bus integration** (7 channels)
✅ **Full audit trail** (memory-keeper persistence)
✅ **Production-ready** (100% test pass rate)

---

**The DWA Council handles complex decisions so you don't have to!** 🎉

For detailed usage, see `COUNCIL_USER_GUIDE.md`.
