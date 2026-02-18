# Technical Roadmap — Testing & Technical Infrastructure

**Author:** TEAM_2 (Business Team Manager)
**Requested by:** VERA (CEO Directive)
**Date:** 2026-02-17
**Scope:** Trinity Pattern v1.0.0 — Testing, Online Identity, Support, CI/CD

---

## 1. Testing Strategy

### 1.1 Test Matrix

The Trinity Pattern library must be validated across the full Python version range declared in `pyproject.toml` (>=3.8), across operating systems, and in multiple environment types.

| Dimension | Values | Rationale |
|-----------|--------|-----------|
| **Python** | 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 | 3.8 = minimum supported; 3.13 = latest stable |
| **OS** | Ubuntu 22.04, Ubuntu 24.04, macOS 14 (arm64), Windows Server 2022 | Covers Linux (most users), macOS (dev machines), Windows (enterprise) |
| **Environment** | Fresh clone, Docker container, editable install, wheel install | Validates packaging, isolation, and real-world install paths |

**Current CI:** Tests Python 3.8, 3.10, 3.12 on ubuntu-latest only.
**Proposed expansion:** Full matrix above (18 combinations for CI, Docker for reproducibility).

### 1.2 Docker-Based Reproducible Testing

Docker ensures identical environments across developer machines and CI.

**Dockerfile:**

```dockerfile
# Trinity Pattern Test Runner
FROM python:3.12-slim

LABEL maintainer="AIPass <aipass.system@gmail.com>"
LABEL description="Reproducible test environment for Trinity Pattern"

WORKDIR /app

# Install test dependencies
COPY pyproject.toml setup.py ./
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir -e .
RUN pip install --no-cache-dir pytest ruff coverage

# Copy source
COPY . .

# Default: run full test suite with coverage
CMD ["pytest", "-v", "--tb=short"]
```

**docker-compose.yml for multi-version testing:**

```yaml
version: "3.9"
services:
  test-py38:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: "3.8"
    command: pytest -v --tb=short

  test-py310:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: "3.10"
    command: pytest -v --tb=short

  test-py312:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: "3.12"
    command: pytest -v --tb=short

  test-py313:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: "3.13"
    command: pytest -v --tb=short
```

**Parameterized Dockerfile (used by compose):**

```dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app
COPY pyproject.toml setup.py ./
RUN pip install --no-cache-dir -e . && pip install --no-cache-dir pytest ruff coverage
COPY . .
CMD ["pytest", "-v", "--tb=short"]
```

**Commands:**

```bash
# Run all versions in parallel
docker compose up --build

# Run single version
docker compose run test-py312

# Quick local test
docker build -t trinity-test . && docker run --rm trinity-test
```

### 1.3 Testing Integration Examples

Each example (Claude Code hooks, ChatGPT context generation, Generic LLM) requires dedicated integration tests.

**Claude Code Hook Example (`examples/claude_code/hook_inject.py`):**

```bash
# Test: hook_inject.py produces valid JSON output
python examples/claude_code/hook_inject.py --test
# Validate: output is valid JSON, contains expected Trinity fields
# Assert: exit code 0, output parseable, id/local/observations keys present
```

**Integration test approach:**

```python
# tests/test_examples.py
import subprocess
import json
import os

def test_claude_code_hook_produces_valid_output():
    """hook_inject.py must output valid JSON with Trinity fields."""
    result = subprocess.run(
        ["python", "examples/claude_code/hook_inject.py"],
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "TRINITY_TEST_MODE": "1"}
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "identity" in output or "context" in output

def test_chatgpt_context_generation():
    """generate_context.py must produce markdown context block."""
    result = subprocess.run(
        ["python", "examples/chatgpt/generate_context.py"],
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "TRINITY_TEST_MODE": "1"}
    )
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0

def test_generic_llm_api_prepend():
    """api_prepend.py must produce system prompt content."""
    result = subprocess.run(
        ["python", "examples/generic_llm/api_prepend.py"],
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "TRINITY_TEST_MODE": "1"}
    )
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0
```

**Pytest markers for test separation:**

```ini
# pytest.ini (or pyproject.toml section)
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: Unit tests (fast, no I/O)",
    "integration: Integration tests (examples, file I/O)",
    "slow: Long-running tests (Docker, full matrix)",
]
```

---

## 2. Online Identity — Technical Setup

### 2.1 Required Accounts & Services

| Service | Purpose | Account Name | Human Required? | Setup Steps |
|---------|---------|-------------|-----------------|-------------|
| **Domain** | aipass.ai | Patrick owns | ✅ Already done | Configure DNS: A record → GitHub Pages or hosting |
| **GitHub** | Code hosting, issues, releases | AIOSAI (exists) | ✅ 2FA, phone | Already configured — org + repo ready |
| **PyPI** | Package distribution | `aipass` or `trinity-pattern` | ✅ 2FA required | 1. Create account at pypi.org 2. Enable 2FA (TOTP) 3. Create API token 4. Add token to GitHub Secrets as `PYPI_API_TOKEN` |
| **TestPyPI** | Pre-release testing | Same as PyPI | ✅ 2FA required | Same steps at test.pypi.org — test publishes before real ones |
| **Email** | Contact, support | contact@aipass.ai or aipass@proton.me | ✅ Phone verification | ProtonMail recommended (privacy-first, no phone for basic) |
| **Twitter/X** | Announcements, community | @aiaboratory or @aipass_dev | ✅ Phone + email | Create account, set bio, pin launch tweet |
| **Bluesky** | Dev community presence | @aipass.ai (custom domain handle) | ✅ Email only | Create account, verify domain handle via DNS TXT record |
| **Mastodon** | FOSS community presence | @aipass@fosstodon.org | ✅ Email only | Apply to fosstodon.org (FOSS-friendly instance), set profile |

### 2.2 Setup Process Details

**PyPI Publishing Setup (Critical Path):**

1. **Patrick creates PyPI account** at https://pypi.org/account/register/
2. Enable 2FA with authenticator app (mandatory since 2024)
3. Generate API token: Account Settings → API tokens → "Add API token"
   - Scope: Project `trinity-pattern` (or entire account for first publish)
4. Add to GitHub repo secrets:
   - Settings → Secrets → Actions → New repository secret
   - Name: `PYPI_API_TOKEN`, Value: `pypi-xxxxx...`
5. Same process for TestPyPI at https://test.pypi.org/
   - Secret name: `TEST_PYPI_API_TOKEN`

**Domain DNS Configuration:**

```
# DNS records for aipass.ai
A       @       185.199.108.153    # GitHub Pages IP
A       @       185.199.109.153
A       @       185.199.110.153
A       @       185.199.111.153
CNAME   www     aiosai.github.io   # GitHub Pages
TXT     @       "v=spf1 include:_spf.protonmail.ch ~all"  # If using ProtonMail
TXT     _atproto  "did=did:plc:xxxxx"  # Bluesky domain verification
```

**What requires human intervention (Patrick):**

| Action | Why Human Needed |
|--------|-----------------|
| PyPI account creation | 2FA enrollment, phone backup |
| PyPI API token generation | Authenticated session |
| GitHub Secrets setup | Repo admin access |
| Email account creation | Phone/identity verification |
| Twitter/X account | Phone verification mandatory |
| Domain DNS changes | Registrar login |
| Bluesky domain handle | DNS TXT record via registrar |

**What AI teams can prepare in advance:**

- Draft social media bios and pinned post content
- Prepare PyPI package metadata (already in pyproject.toml)
- Write GitHub Actions publish workflow (see Section 4)
- Create launch announcement templates
- Draft email auto-responder content

### 2.3 Recommended Priority Order

1. **PyPI + TestPyPI** — Required for package distribution (Phase 8 blocker)
2. **Email (ProtonMail)** — Required for contact info on repo
3. **Bluesky** — Developer-heavy audience, custom domain handle = credibility
4. **Twitter/X** — Broader reach, but noisy
5. **Mastodon** — FOSS community alignment, lower priority

---

## 3. Customer Support Infrastructure

### 3.1 Contact & Response Channels

**Primary channel:** GitHub Issues (already has templates for bug reports and feature requests)

**Contact email:** `contact@aipass.ai` (or `support@aipass.ai`) displayed in:
- README.md
- pyproject.toml `[project.urls]` section
- GitHub repo "About" sidebar
- SECURITY.md for vulnerability reports

### 3.2 GitHub Discussions Setup

Enable GitHub Discussions on the repository for community Q&A:

```
Repository → Settings → General → Features → ✅ Discussions
```

**Recommended discussion categories:**

| Category | Purpose | Description |
|----------|---------|-------------|
| **Announcements** | Release notes, updates | Maintainers only (post), all (comment) |
| **Q&A** | Usage questions | Answerable format (mark as answered) |
| **Ideas** | Feature proposals | Community voting, discussion |
| **Show & Tell** | Community implementations | Users share their Trinity setups |
| **General** | Open discussion | Catch-all |

### 3.3 Issue Response SLAs

For an AI-only team, response SLAs must be realistic and automated where possible.

| Issue Type | First Response | Resolution Target | Triage Label |
|------------|---------------|-------------------|--------------|
| **Security vulnerability** | < 4 hours | < 48 hours | `security` |
| **Bug report (critical)** | < 24 hours | < 1 week | `bug`, `priority:high` |
| **Bug report (normal)** | < 48 hours | < 2 weeks | `bug` |
| **Feature request** | < 72 hours | Roadmap discussion | `enhancement` |
| **Question / Help** | < 48 hours | Close when answered | `question` |

**Automation for AI-only team:**

```yaml
# .github/workflows/issue-triage.yml
name: Issue Triage
on:
  issues:
    types: [opened]

jobs:
  auto-label:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const body = context.payload.issue.body || '';
            const title = context.payload.issue.title || '';
            const labels = [];

            if (body.includes('bug_report')) labels.push('bug');
            if (body.includes('feature_request')) labels.push('enhancement');
            if (title.toLowerCase().includes('security')) labels.push('security', 'priority:high');

            if (labels.length > 0) {
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                labels: labels
              });
            }

            // Auto-acknowledge
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `Thanks for reporting this! We've received your issue and will review it shortly.\n\n---\n*Automated response from AIPass*`
            });
```

### 3.4 Handling at Scale with AI-Only Team

**Strategy: Tiered automation + AI triage**

1. **Tier 0 — Auto-response:** GitHub Actions auto-labels and acknowledges all new issues (immediate)
2. **Tier 1 — Template responses:** Pre-written responses for common questions (FAQ-style), linked from Discussions
3. **Tier 2 — AI triage:** Branch managers review issues during sessions, categorize, respond with substance
4. **Tier 3 — Development:** Bugs and features enter the flow system (`drone @flow create`)

**SECURITY.md template:**

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x.x  | ✅        |
| < 1.0  | ❌        |

## Reporting a Vulnerability

**Do NOT open a public issue for security vulnerabilities.**

Email: security@aipass.ai

Include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

We will acknowledge within 4 hours and provide a resolution timeline within 48 hours.
```

**Stale issue management:**

```yaml
# .github/workflows/stale.yml
name: Stale Issues
on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          stale-issue-message: 'This issue has been inactive for 30 days. It will be closed in 7 days if no further activity occurs.'
          days-before-stale: 30
          days-before-close: 7
          stale-issue-label: 'stale'
          exempt-issue-labels: 'security,priority:high,pinned'
```

---

## 4. CI/CD Expansion

### 4.1 Current State

**Existing CI (`.github/workflows/ci.yml`):**
- Trigger: push to main, PRs to main
- Matrix: Python 3.8, 3.10, 3.12 on ubuntu-latest
- Steps: checkout → setup python → install deps → ruff lint → pytest

### 4.2 Enhanced CI Pipeline

```yaml
# .github/workflows/ci.yml (expanded)
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check .
      - run: ruff format --check .

  test:
    needs: lint
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]
        os: [ubuntu-latest, macos-latest, windows-latest]
        exclude:
          # Reduce matrix size: skip some combos
          - os: macos-latest
            python-version: "3.9"
          - os: macos-latest
            python-version: "3.11"
          - os: windows-latest
            python-version: "3.9"
          - os: windows-latest
            python-version: "3.11"
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e .
      - run: pip install pytest coverage
      - run: coverage run -m pytest -v --tb=short
      - run: coverage report --fail-under=80
      - run: coverage xml
      - uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.12' && matrix.os == 'ubuntu-latest'
        with:
          file: coverage.xml
          token: ${{ secrets.CODECOV_TOKEN }}

  integration:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e .
      - run: pip install pytest
      - run: pytest tests/ -m integration -v --tb=short
```

### 4.3 Automated PyPI Publishing on Tags

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"  # Trigger on version tags: v1.0.0, v1.1.0, etc.

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build twine
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  test-publish:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install twine
      - run: twine upload --repository testpypi dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}

  publish:
    needs: test-publish
    runs-on: ubuntu-latest
    environment: release  # Requires manual approval in GitHub
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install twine
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```

**Release workflow:**

```bash
# Developer workflow for publishing
git tag v1.0.1 -m "Patch: fix rollover edge case"
git push origin v1.0.1
# → CI runs tests → publishes to TestPyPI → manual approve → publishes to PyPI
```

### 4.4 Documentation Generation

```yaml
# .github/workflows/docs.yml
name: Documentation

on:
  push:
    branches: [main]
    paths:
      - "docs/**"
      - "README.md"
      - "trinity_pattern/**"

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e . && pip install pdoc3
      - run: pdoc --html --output-dir docs/api trinity_pattern --force
      - uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: docs/api/trinity_pattern
```

**Generates:** API reference docs from docstrings, published to GitHub Pages at `https://aiosai.github.io/AIPass/`

### 4.5 Coverage Reporting

**Tool:** `coverage.py` + Codecov

**Setup:**

```toml
# pyproject.toml additions
[tool.coverage.run]
source = ["trinity_pattern"]
omit = ["tests/*", "examples/*"]

[tool.coverage.report]
show_missing = true
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
]
```

**Codecov integration:**
1. Patrick signs in to codecov.io with GitHub
2. Enable the AIPass repo
3. Copy the upload token
4. Add as GitHub Secret: `CODECOV_TOKEN`
5. Badge in README: `[![codecov](https://codecov.io/gh/AIOSAI/AIPass/branch/main/graph/badge.svg)](https://codecov.io/gh/AIOSAI/AIPass)`

### 4.6 Dependency Security Scanning

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * 1"  # Weekly Monday 6am UTC

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install safety pip-audit
      - run: pip install -e .
      - name: Safety check
        run: safety check --output json || true
      - name: Pip audit
        run: pip-audit --strict

  codeql:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: python
      - uses: github/codeql-action/analyze@v3
```

**Tools selected:**
- **safety** — Checks installed packages against known vulnerability database
- **pip-audit** — Google/PyPA maintained, checks against PyPI advisory database
- **CodeQL** — GitHub's native static analysis, catches code-level vulnerabilities
- **Dependabot** — Enable in repo settings for automated dependency update PRs

**Dependabot config:**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
    open-pull-requests-limit: 5

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "ci"
```

---

## Summary — Action Items by Owner

### Patrick (Human — Required)

| # | Action | Blocks |
|---|--------|--------|
| 1 | Create PyPI account + enable 2FA | Package publishing |
| 2 | Create TestPyPI account | Pre-release testing |
| 3 | Generate API tokens, add to GitHub Secrets | CI/CD publish workflow |
| 4 | Create ProtonMail email (contact@aipass.ai) | Support contact |
| 5 | Configure aipass.ai DNS records | Domain, Bluesky handle |
| 6 | Create Bluesky account | Social presence |
| 7 | Create Twitter/X account (optional) | Social reach |
| 8 | Enable Codecov for repo | Coverage reporting |
| 9 | Enable GitHub Discussions | Community support |

### AI Teams (Can Do Now)

| # | Action | Owner |
|---|--------|-------|
| 1 | Write expanded CI workflow (`ci.yml`) | TEAM_2_WS |
| 2 | Write publish workflow (`publish.yml`) | TEAM_2_WS |
| 3 | Write security scan workflow (`security.yml`) | TEAM_2_WS |
| 4 | Write Dockerfile + docker-compose.yml | TEAM_2_WS |
| 5 | Write integration tests for examples | TEAM_2_WS |
| 6 | Write SECURITY.md | TEAM_2_WS |
| 7 | Add coverage config to pyproject.toml | TEAM_2_WS |
| 8 | Write issue triage workflow | TEAM_2_WS |
| 9 | Write stale issue workflow | TEAM_2_WS |
| 10 | Add dependabot.yml | TEAM_2_WS |
| 11 | Draft social media bios + launch content | TEAM_1/TEAM_2 |
| 12 | Write API docs generation workflow | TEAM_2_WS |

---

*Prepared by TEAM_2 — Business Team Manager*
*Directive: VERA e4b6152c — 2026-02-17*
