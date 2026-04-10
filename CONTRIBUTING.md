# Contributing to zirflow-search

Thank you for your interest in contributing! This project is a multi-source AI search system powering Zirflow's research capabilities. Here's how to get started.

---

## 🏗️ Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/zirflow/zirflow-openclaw-zirflow-search.git
cd zirflow-openclaw-zirflow-search

# 2. Install dependencies
pip install tavily requests feedparser yt-dlp

# 3. Configure API keys
cp config.env.template ~/.openclaw/skills/zirflow-search/config.env
# Then edit config.env and add your Tavily API keys
# Get free keys at: https://tavily.com (1000 searches/day)

# 4. Verify installation
python3 scripts/search.py --help
```

---

## 🔍 Running the Project

```bash
# Standard search
python3 scripts/search.py "your search query"

# Multi-platform simultaneous search
python3 scripts/search.py "query" --all --max 10

# Force specific engine
python3 scripts/search.py "query" --tier 2 --engine github

# News filter
python3 scripts/search.py "query" --tier 1 --topic news --days 7
```

---

## 📐 Code Style

- **Language**: Python 3
- **Style guide**: [PEP 8](https://pep8.org/)
- **Max line length**: 88 characters (Black default)
- **Docstrings**: Google-style for public modules and functions

```bash
# Format your code before committing
pip install black
black scripts/

# Check linting
pip install flake8
flake8 scripts/
```

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

---

## 🔀 Submitting Changes

### Branching Strategy

```
main          ← stable, releases only
├── dev       ← integration branch
└── fix/xxx   ← bug fixes
└── feat/xxx  ← new features
```

### Pull Request Checklist

- [ ] Code follows PEP 8 (run `black` and `flake8`)
- [ ] New features have docstrings
- [ ] Tests pass locally (`pytest tests/`)
- [ ] Commit messages are descriptive (see below)
- [ ] PR description explains *what* and *why*, not just *how*

### Commit Message Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Examples**:
```
feat(search): add V2EX platform router
fix(tavily): handle rate limit with exponential backoff
docs(readme): clarify API key setup steps
```

---

## 🐛 Reporting Issues

Before opening an issue, please check if it already exists.

**Bug reports** should include:
- Python version and OS
- Full error traceback
- Steps to reproduce
- Expected vs. actual behavior

**Feature requests** should include:
- Clear problem statement
- Proposed solution
- Example use case

**Issue template**:
```markdown
## Description
[Concise description of the issue]

## Environment
- OS: [e.g. macOS 14, Ubuntu 22.04]
- Python: [e.g. 3.11]
- Version: [e.g. 1.0.0]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [...]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens — include full error if applicable]
```

---

## 💡 Suggestions

Open a discussion first for significant changes — it saves time for everyone. For small improvements (typos, docs, small fixes), just open a PR directly.

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the project's [MIT-0 License](./LICENSE).
