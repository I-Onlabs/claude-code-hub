# Claude Code Hub

**Modular backup and sharing hub for Claude Code agents, skills, and configurations.**

## Architecture

This hub uses a **modular structure** where each component is independently managed:

```
claude-code-hub/
├── agents/          [Separate repo - 20 enhanced agents]
├── skills/          [Separate repo - 154 methodology skills]
├── hooks/           [Future - Custom hooks]
├── templates/       [Future - Project templates]
└── configs/         [Future - Shared configurations]
```

### Why Modular?

- **Independent versioning** - Each component has its own history
- **Selective restore** - Just drag and drop what you need
- **Easy sharing** - Share agents without skills or vice versa
- **Clean organization** - No monolithic structure
- **Future-proof** - Easy to add new component types

## Quick Start

### Backup from Local

```bash
# Sync agents from ~/.claude/agents/
cd agents && ./sync-from-local.sh

# Sync skills from ~/.claude/skills/
cd skills && ./sync-from-local.sh
```

### Restore to Local

```bash
# Restore agents
cp -r agents/*.md ~/.claude/agents/

# Restore skills
cp -r skills/*/ ~/.claude/skills/
```

## Components

### Agents (20 enhanced)
- **7 Opus agents** - Critical work (security, debugging, reviews)
- **13 Sonnet agents** - Standard development
- **3 Read-only agents** - Safe reviewers
- **9 ReAct-enabled** - Systematic problem-solving

[See agents/README.md](agents/README.md)

### Skills (154 total)
- **Workflow skills** - systematic-debugging, TDD, pipelines
- **Pattern libraries** - API design, Python practices
- **Automation** - Task tracking, quality gates
- **Domain-specific** - Security, performance, data engineering

[See skills/README.md](skills/README.md)

## Enhancements

All agents enhanced with community-proven patterns:

1. **Three-Tier Models** (40-72% cost savings)
   - Opus for critical work
   - Sonnet for standard development

2. **Minimal Tools** (security)
   - Read-only for reviewers
   - Full access for developers

3. **ReAct Prompting** (quality)
   - Think → Act → Observe → Repeat
   - Systematic problem-solving

## Documentation

- [Best Practices](docs/BEST-PRACTICES-AGENT-USAGE.md)
- [Enhancement Summary](docs/AGENT-ENHANCEMENT-COMPLETE.md)
- [Test Results](docs/ENHANCEMENT-TEST-RESULTS.md)
- [Community Analysis](docs/COMMUNITY-PATTERNS-ANALYSIS.md)

## License

MIT License - See [LICENSE](LICENSE) for details

## Contributing

Contributions welcome! See each component's README for specific guidelines.

---

**Created:** 2025-12-21
**Status:** Production-ready modular backup system
