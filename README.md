# Coordination Infrastructure (Council + Message Bus)

**Multi-Agent Coordination Platform for Claude Code**

A production-ready DWA (Debate-Weighted Aggregation) Council system enabling 21 specialized agents to deliberate on critical decisions through structured voting, debate, and autonomous escalation.

---

## What's Included

This repository contains the **coordination infrastructure**:

- **DWA Council System** (~1,750 lines) - Multi-agent voting with expertise weights
- **Message Bus** (~400 lines) - Pub/sub coordination via memory-keeper MCP
- **Integration Tests** (6/6 passing) - 100% validation coverage
- **Comprehensive Documentation** (~3,000 lines)

**Status:** ✅ Production Ready (Phase 4 Complete)

---

## Quick Start

### 1. Install the Council System

```bash
# Clone repository
cd /Users/mac/Projects
git clone https://github.com/I-Onlabs/claude-code-hub.git

# Copy to Claude Code configuration
cp -r claude-code-hub/council ~/.claude/
cp -r claude-code-hub/lib ~/.claude/

# Verify installation
python3 ~/.claude/council/test_phase4.py
# Expected: 6/6 tests passing
```

### 2. Run Interactive Demo

```bash
python3 ~/.claude/council/demo_council_system.py
```

### 3. Configure Agents (Required)

The council works with **any agents** that have `expertise_weights` in their YAML frontmatter:

```yaml
---
name: your-agent
expertise_weights:
  security: 0.9
  architecture: 0.7
council_role: proposer
---
```

You can:
- Use your own custom agents
- Use agents from [claude-code-agents](https://github.com/I-Onlabs/claude-code-agents) (21 pre-configured)
- Mix both

The council automatically discovers all agents in `~/.claude/agents/` with expertise weights.

---

## Architecture

### Modular Design

```
┌──────────────────────────────────────────┐
│ Coordination Infrastructure (THIS REPO)  │
│ ├── council/     Council system          │
│ └── lib/         Message bus             │
└──────────────────────────────────────────┘
              ↓ works with ↓
┌──────────────────────────────────────────┐
│ Your agents (REQUIRED)                   │
│ └── Any agents with expertise_weights    │
└──────────────────────────────────────────┘
```

**Design Philosophy:**

- **Infrastructure only** - This repo provides coordination, not agents
- **Agent-agnostic** - Works with any agents following the expertise_weights pattern
- **User choice** - Use your own agents, community agents, or both
- **No dependencies** - Council system is self-contained

---

## How It Works

```
USER REQUEST
     ↓
TRIGGER DETECTION (8 conditions)
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

## Key Features

✅ **21 specialized agents** with domain expertise (0.0-1.0)
✅ **8 trigger conditions** for automatic convening
✅ **DWA voting formula** (`Score = Σ(Vote × Confidence × Expertise)`)
✅ **Optional debate** (1-2 rounds for consensus)
✅ **Autonomous escalation** to o3/Gemini when needed
✅ **Cost-optimized** with local Ollama proposals ($0)
✅ **7 message bus channels** for agent coordination
✅ **100% test pass rate** (6/6 integration tests)

---

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](council/README.md) | Quick start guide (404 lines) |
| [COUNCIL_USER_GUIDE.md](council/COUNCIL_USER_GUIDE.md) | Comprehensive usage (757 lines) |
| [PHASE4_COMPLETE.md](council/PHASE4_COMPLETE.md) | Technical implementation (593 lines) |
| [PROJECT_SUMMARY.md](council/PROJECT_SUMMARY.md) | Complete overview (679 lines) |
| [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) | Final status (469 lines) |

---

## 8 Trigger Conditions

The council automatically convenes when:

1. **Architectural decisions** - Design choices, tech stack, migrations
2. **Security/risk operations** - Auth, secrets, vulnerabilities
3. **Agent disagreements** - Conflicting proposals
4. **Quality gate failures** - Failing tests, linting
5. **Ethical concerns** - Privacy, bias, misinformation
6. **Low confidence** - Aggregate < 0.75
7. **External commitments** - Deploys, API calls, publishing
8. **Novel/OOD queries** - Unfamiliar tech, edge cases

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

## Testing

```bash
# Run integration tests
python3 ~/.claude/council/test_phase4.py

# Expected output:
# ✅ TEST 1 PASSED: All 21 agents have expertise_weights
# ✅ TEST 2 PASSED: Memory-keeper bridge working
# ✅ TEST 3 PASSED: Consult-llm bridge working
# ✅ TEST 4 PASSED: Message bus integration working
# ✅ TEST 5 PASSED: Expertise matching working correctly
# ✅ TEST 6 PASSED: Coordinator agent ready
# Passed: 6/6
```

---

## Optional: Community Agents & Skills

If you prefer not to create your own agents, you can use community resources:

| Repository | Description | Size |
|------------|-------------|------|
| [claude-code-agents](https://github.com/I-Onlabs/claude-code-agents) | 21 pre-configured agents (optional) | 85 KB |
| [claude-code-skills](https://github.com/I-Onlabs/claude-code-skills) | 166+ methodology skills (optional) | 20.5 MB |

**Note:** The council system works with **any** agents that have `expertise_weights` in their frontmatter.

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**Created:** December 23, 2025
**Status:** Production Ready ✅
**Repository:** https://github.com/I-Onlabs/claude-code-hub

**The DWA Council handles complex decisions so you don't have to!** 🎉
