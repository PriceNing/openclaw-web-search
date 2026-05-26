---
name: web-search
description: Free, privacy-focused web search using DuckDuckGo HTML parsing and GitHub API (issues/PRs + repositories). No API keys required.
homepage: https://github.com/PriceNing/openclaw-web-search
---

# Web Search Skill

Free, open-source web search using DuckDuckGo HTML parsing and GitHub REST API. No API keys or paid services required.

## Features

- 🦆 **DuckDuckGo Search** - HTML parsing for general web search
- 🐙 **GitHub Issues/PRs** - Technical issue and code discussion search
- 📦 **GitHub Repositories** - Search repositories by name, description, language, stars
- 🔒 **Privacy First** - No tracking, no personal data collection
- 🆓 **Completely Free** - No usage limits or costs
- 🎯 **Smart Routing** - Automatically chooses best source for query type

## Requirements

- Python 3.8+ with `requests` (recommended) or `curl` fallback

```bash
# Install requests (recommended)
pip install requests
```

## Quick Start

```bash
# Search DuckDuckGo
python3 scripts/search.py --query "llama.cpp question mark output"

# Search GitHub issues
python3 scripts/search.py --query "repo:ggml-org/llama.cpp bug" --source github

# Search GitHub repositories by name
python3 scripts/search.py --query "openai whisper" --source repo

# Smart search (auto-detect)
python3 scripts/search.py --query "qwen3.5:9b multimodal image analysis bug"
```

### Windows (Encoding Fix)

On Windows, the console may default to GBK encoding. Set the environment variable to avoid Unicode errors:

```bash
set PYTHONIOENCODING=utf-8
python3 scripts/search.py --query "你的搜索词"
```

Or use the full Python path:

```bash
C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe scripts/search.py --query "你的搜索词"
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Search query (required) | |
| `--source` | `-s` | Source: `duckduckgo`, `github`, `repo`, `auto` | `auto` |
| `--format` | `-f` | Output: `text`, `json`, `markdown` | `text` |
| `--limit` | `-l` | Max results to return | `10` |
| `--timeout` | `-t` | Request timeout in seconds | `30` |
| `--verbose` | `-v` | Show debug info | |

### Source Types

| Source | Description |
|--------|-------------|
| `duckduckgo` | General web search via DuckDuckGo HTML |
| `github` | Search GitHub issues and pull requests |
| `repo` | Search GitHub repositories (by name, description, stars) |
| `auto` | Automatically detect best source based on query |

**Auto-detection rules:**
- `repo:` / `github.com/` / `issue` / `pr` / `pull request` → `github` (issues/PRs)
- `repo ` / `repository ` / `project ` / `stars:` / `language:` → `repo` (repositories)
- Everything else → `duckduckgo`

## Examples

```bash
# DuckDuckGo: general web search
python3 scripts/search.py -q "Python asyncio tutorial"

# GitHub issues: find bugs in a repo
python3 scripts/search.py -q "repo:ggml-org/llama.cpp segfault" -s github

# GitHub repos: find popular projects
python3 scripts/search.py -q "whisper speech recognition" -s repo

# JSON output for programmatic use
python3 scripts/search.py -q "fastapi tutorial" -f json

# Markdown output with rich formatting
python3 scripts/search.py -q "LLM gateway" -s repo -f markdown -l 5
```

## License

MIT License - Free to use and modify.
