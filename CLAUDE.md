# ScribeVault

ScribeVault is a PySide6 desktop application for audio recording, transcription, and intelligent summarization with configurable cost-optimized processing.

## Repository Structure

```
src/                  # Application source
  gui/                # GUI components (PySide6)
  audio/              # Audio recording and processing
  transcription/      # Whisper integration (API + local)
  ai/                 # OpenAI summarization
  config/             # Configuration management
  assets/             # UI assets and resources
  export/             # Export and markdown generation
config/               # User configuration files
tests/                # pytest test suite
docs/                 # Documentation
ai/                   # AI team workspace (context, outputs, beans, tasks)
.claude/              # Claude Code config (assembled symlinks)
  kit/                # claude-kit submodule (shared across projects)
  local/              # Project-specific skills, commands, agents
scripts/              # Helper scripts (claude-sync, claude-link, claude-publish)
```

## AI Team

| Persona | Role | Agent | Output Directory |
|---------|------|-------|------------------|
| Team Lead | Coordinates work, decomposes beans, assigns tasks | `.claude/agents/team-lead.md` | `ai/outputs/team-lead/` |
| BA | Requirements, user stories, acceptance criteria | `.claude/agents/ba.md` | `ai/outputs/ba/` |
| Architect | System design, ADRs, module boundaries | `.claude/agents/architect.md` | `ai/outputs/architect/` |
| Developer | Implementation, refactoring, code changes | `.claude/agents/developer.md` | `ai/outputs/developer/` |
| Tech QA | Test plans, test implementation, quality gates | `.claude/agents/tech-qa.md` | `ai/outputs/tech-qa/` |

## Beans Workflow

A **Bean** is a unit of work (feature, enhancement, bug fix, or epic). Beans live in `ai/beans/BEAN-NNN-<slug>/`.

**Lifecycle:** Unapproved → Approved → In Progress → Done

1. Create a bean from `ai/beans/_bean-template.md` (status: `Unapproved`)
2. User reviews and approves beans (status: `Approved`)
3. Team Lead picks approved beans from the backlog (`ai/beans/_index.md`)
4. Team Lead decomposes into tasks with owners and dependencies
5. Each persona claims tasks, produces outputs, creates handoffs
6. Team Lead verifies outputs against acceptance criteria
7. Bean marked Done

See the bean template at `ai/beans/_bean-template.md` for the lifecycle specification.

## Tech Stack

- **Python** >=3.8, **PySide6**, **OpenAI**, **Whisper**, **PyAudio**
- **GUI:** PySide6
- **Deps:** `pip` with `requirements.txt`
- **Lint:** `flake8`, `black`, `isort`
- **Type Check:** `mypy`
- **Tests:** `pytest` (testpaths = tests/, coverage target 80%)

## Key Commands

```bash
pytest tests/                          # Run all tests
pytest tests/test_foo.py -v            # Run one test file
flake8 src/ tests/                     # Lint check
black src/ tests/                      # Format code
isort src/ tests/                      # Sort imports
mypy src/                              # Type check
python main.py                         # Launch PySide6 GUI
```

## Claude Kit (Submodule)

The `.claude/` directory uses a **submodule + local** pattern:

- **`.claude/kit/`** — shared config from `beekeeper-lab/claude-kit` (git submodule)
- **`.claude/local/`** — project-specific commands, skills, agents (not shared)
- **`.claude/commands/`, `.claude/skills/`, `.claude/agents/`** — assembled symlinks pointing into `kit/` and `local/`
- **`.claude/hooks`**, **`.claude/settings.json`** — symlinked from `kit/`

```bash
# Pull latest kit + rebuild symlinks
./scripts/claude-sync.sh

# Rebuild symlinks after adding/removing local assets
./scripts/claude-link.sh

# Push kit changes + parent repo
./scripts/claude-publish.sh
```

To promote a local asset to the shared kit, move it from `.claude/local/` into `.claude/kit/`, commit inside the submodule, push, then bump the submodule pointer in this repo.

## Rules

- **All AI outputs** go to `ai/outputs/<persona>/`
- **Run tests** before marking any task done (`pytest tests/`)
- **Run lint** before committing (`flake8 src/ tests/`)
- **Bean tasks** live in `ai/beans/BEAN-NNN-<slug>/tasks/`
- **ADRs** go in `docs/` or relevant bean output directories
