# Best Practices: Using Enhanced Agents (2025-12-21)

## Executive Summary

**Best approach: Let agents work autonomously** with occasional strategic manual delegation for complex multi-agent workflows.

---

## The Golden Rules

### 1. Default to Autonomous 🤖

**BEST:** Let Claude choose agents automatically
```
You: "Add rate limiting to the API"
→ Claude auto-delegates to backend-developer (Sonnet)
→ Cost-effective, fast, correct agent
```

**AVOID:** Over-specifying unless needed
```
You: "Use backend-developer with Sonnet model and full tools to add rate limiting"
→ Unnecessary - this happens automatically
```

**When to manually specify:**
- Complex workflows requiring specific sequence
- Testing specific agent behavior
- Debugging agent delegation

---

### 2. Trust the Three-Tier Model 💰

**How it works automatically:**
```
Security review → Opus (critical, worth the cost)
Standard coding → Sonnet (fast, cost-effective)
Simple queries → Haiku (future, ultra-fast)
```

**Cost savings: 40-72% vs all-Opus**

**Best practice:**
- ✅ Let agents use their assigned models
- ✅ Monitor costs weekly to verify savings
- ❌ Don't override model assignments unless testing

---

### 3. Leverage Tool Restrictions 🔒

**Read-only agents (security feature):**
- code-reviewer, qa-expert, security-auditor
- **Can analyze, cannot modify**
- Prevents accidental changes during review

**Full-access agents (productivity):**
- All development agents
- **Can read AND write**
- Enables actual implementation

**Best practice:**
- ✅ Use code-reviewer AFTER development complete
- ✅ Use security-auditor BEFORE commits
- ❌ Don't try to have reviewers implement fixes (they can't)

---

### 4. Embrace ReAct Methodology 🔄

**What happens automatically:**
```
THINK: Agent analyzes requirements
ACT: Agent implements solution
OBSERVE: Agent checks results
REPEAT: Agent refines until production-ready
```

**Benefits:**
- Fewer bugs (systematic approach)
- Better solutions (self-correcting)
- Faster overall (less rework)

**Best practice:**
- ✅ Be patient - ReAct takes a bit longer upfront
- ✅ Trust the process - fewer rework cycles saves time
- ❌ Don't rush agents with "just do it quickly"

---

## Optimal Workflows

### Workflow 1: Feature Development (Best Practice)

**Request:** "Add user profile editing feature"

**Automatic delegation sequence:**
```
1. task-orchestrator (Opus)
   → Breaks down into subtasks

2. api-designer (Sonnet)
   → Designs API endpoints
   → Uses ReAct: THINK (patterns) → ACT (design) → OBSERVE (validate)

3. backend-developer (Sonnet)
   → Implements endpoints
   → Uses ReAct: RED (test) → GREEN (code) → REFACTOR

4. frontend-expert (Sonnet)
   → Builds UI components
   → Uses ReAct: THINK (UX) → ACT (build) → OBSERVE (test)

5. code-reviewer (Opus)
   → Reviews everything
   → Read-only tools ensure safe review

6. qa-expert (Sonnet)
   → Verifies tests
   → Read-only tools
```

**Cost:** ~$3-15/1M tokens (mostly Sonnet)
**Quality:** High (Opus gates at critical points)
**Time:** Optimal (parallel where possible)

---

### Workflow 2: Bug Fixing (Best Practice)

**Request:** "Fix authentication failing intermittently"

**Automatic delegation:**
```
1. error-detective (Opus)
   → Uses ReAct to find root cause
   → THINK: Analyze symptoms
   → ACT: Investigate, add logging
   → OBSERVE: Found race condition
   → REPEAT: Verify hypothesis

2. backend-developer (Sonnet)
   → Implements fix
   → Uses ReAct with TDD

3. code-reviewer (Opus)
   → Verifies fix quality
   → Read-only review
```

**Why Opus for debugging?** Complex reasoning worth the cost
**Why Sonnet for implementation?** Standard coding task

---

### Workflow 3: Security Review (Best Practice)

**Request:** "Review this code before deploying"

**Automatic delegation:**
```
1. security-auditor (Opus)
   → Comprehensive security scan
   → Read-only tools (safe)
   → CRITICAL work deserves Opus

2. code-reviewer (Opus)
   → Quality assessment
   → Read-only tools

3. qa-expert (Sonnet)
   → Test coverage check
   → Read-only tools
```

**All reviewers use read-only tools** → Cannot accidentally modify code
**Critical reviews use Opus** → Worth the cost for production safety

---

## When to Override Defaults

### Manual Delegation Scenarios

**1. Complex Multi-Agent Workflows**
```
You: "Use vibe-coding-coordinator to prepare, then backend-developer to implement"
→ Strategic sequence for complex features
```

**2. Testing Specific Agents**
```
You: "Have python-pro implement this, show me the ReAct process"
→ See how ReAct works
```

**3. Cost-Sensitive Prototyping**
```
You: "Use Sonnet for this quick prototype"
→ Override Opus agent for draft work
```

**4. Learning/Training**
```
You: "Show me how error-detective debugs this"
→ Educational purposes
```

---

## Anti-Patterns (What NOT to Do)

### ❌ Anti-Pattern 1: Over-Specifying
```
BAD: "Use backend-developer with Sonnet model, full tools, and ReAct
      methodology to create a POST /users endpoint"

GOOD: "Create a POST /users endpoint"
→ Same result, less typing
```

### ❌ Anti-Pattern 2: Bypassing Reviews
```
BAD: "Skip code review, just deploy"

GOOD: "Implement feature, then review before deploying"
→ Code-reviewer (Opus) catches issues
→ Read-only tools ensure safe review
```

### ❌ Anti-Pattern 3: Fighting ReAct
```
BAD: "Just fix it quickly, don't overthink"

GOOD: "Fix this bug" (let agent use ReAct)
→ THINK phase finds root cause
→ Prevents symptom fixes
```

### ❌ Anti-Pattern 4: Wrong Agent for Task
```
BAD: "Use qa-expert to implement this feature"
→ qa-expert has read-only tools, can't implement

GOOD: "Implement this feature" → auto-delegates to developer
       "Review the tests" → auto-delegates to qa-expert
```

---

## Cost Optimization Tips

### 1. Use Pipeline Skills for Large Features
```
You: "Build user management system"

→ Activates pipeline-* skills:
   - pipeline-pm-spec (INVEST user stories)
   - pipeline-arch-review (Architecture design)
   - pipeline-implement (TDD implementation)
   - pipeline-test-verify (Quality gates)

→ Structured approach saves tokens
→ Quality gates prevent rework
```

### 2. Batch Similar Tasks
```
BETTER: "Add rate limiting, caching, and logging"
→ One backend-developer session

vs

WORSE: "Add rate limiting" → "Add caching" → "Add logging"
→ Three separate sessions
```

### 3. Use Right Agent for Right Phase
```
Planning: task-orchestrator (Opus) - worth it for good plan
Implementation: backend-developer (Sonnet) - cost-effective
Review: code-reviewer (Opus) - worth it for quality gate
```

---

## Measuring Success

### Track These Metrics

**Cost Savings:**
```bash
# Before enhancements
All Opus: ~$15/1M tokens

# After enhancements
Mixed: ~$3-6/1M tokens (50-60% savings)
```

**Quality Improvement:**
```
- Fewer bug reports after deployment
- Less rework needed
- Faster code review cycles (read-only prevents accidental mods)
```

**Productivity:**
```
- Features delivered faster (ReAct prevents rework)
- Clearer code (systematic approach)
- Better documentation (agents follow patterns)
```

---

## The Ultimate Best Practice

### **Natural Language + Trust**

```
You: "I need user authentication"
→ Claude handles:
   ✅ Chooses right agents
   ✅ Uses right models
   ✅ Applies right tools
   ✅ Follows ReAct methodology

You: "Review this before deploying"
→ Claude handles:
   ✅ Uses Opus reviewers (critical)
   ✅ Read-only tools (safe)
   ✅ Systematic review process

You: "Fix this bug"
→ Claude handles:
   ✅ Uses Opus debugger (complex reasoning)
   ✅ ReAct finds root cause
   ✅ Implements proper fix
```

**Just describe WHAT you want, Claude handles HOW.**

---

## Quick Reference Card

| Scenario | Best Approach | Why |
|----------|---------------|-----|
| New feature | "Build X feature" | Auto-delegates, uses pipeline |
| Bug fix | "Fix this bug" | error-detective (Opus) finds root cause |
| Review code | "Review before deploying" | code-reviewer (Opus) + read-only tools |
| Security check | "Security audit" | security-auditor (Opus) + read-only |
| API design | "Design API for X" | api-designer (Sonnet) with ReAct |
| Optimize perf | "Optimize performance" | performance-engineer (Sonnet) |
| Python code | "Implement X in Python" | python-pro (Sonnet) with ReAct |

**Pattern:** Natural language request → Automatic optimal delegation

---

## Conclusion

**Best = Autonomous + Trust**

1. ✅ Use natural language
2. ✅ Let agents auto-delegate
3. ✅ Trust three-tier models (cost/quality balance)
4. ✅ Trust tool restrictions (security)
5. ✅ Trust ReAct methodology (quality)
6. ✅ Review critical work (use Opus reviewers)

**The system is designed to be invisible** - just describe what you want, and the enhancements work behind the scenes to deliver optimal cost, security, and quality.

---

**Created:** 2025-12-21
**Status:** Production Best Practices
**TL;DR:** Natural language + autonomous delegation = best results
