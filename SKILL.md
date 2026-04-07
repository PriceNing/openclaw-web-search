---
name: web-search
description: Free, privacy-focused web search using DuckDuckGo HTML parsing and GitHub API. No API keys required.
homepage: https://github.com/PriceNing/openclaw-web-search
metadata:
  {
    "openclaw":
      {
        "emoji": "🔍",
        "requires": {"bins": ["python3"]},
        "install": [
          {"id": "check-python", "kind": "shell", "command": "which python3"}
        ]
      }
  }
---

# Web Search Skill

Free, open-source web search using DuckDuckGo HTML parsing and GitHub REST API. No API keys or paid services required.

## Features

- 🦆 **DuckDuckGo Search** - HTML parsing for general web search
- 🐙 **GitHub API** - Technical issue and code search
- 🔒 **Privacy First** - No tracking, no personal data collection
- 🆓 **Completely Free** - No usage limits or costs
- 🎯 **Smart Routing** - Automatically chooses best source for query type

## Quick Start

```bash
# Search DuckDuckGo
python3 scripts/search.py --query "llama.cpp question mark output"

# Search GitHub issues
python3 scripts/search.py --query "repo:ggml-org/llama.cpp infinite question mark" --source github

# Smart search (auto-detect)
python3 scripts/search.py --query "qwen3.5:9b multimodal image analysis bug"
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Search query (required) | |
| `--source` | `-s` | Source: `duckduckgo`, `github`, `auto` | `auto` |
| `--format` | `-f` | Output: `text`, `json`, `markdown` | `text` |
| `--limit` | `-l` | Max results to return | `10` |

## License

MIT License - Free to use and modify.
