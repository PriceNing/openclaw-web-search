#!/usr/bin/env python3
"""
OpenClaw Web Search Skill
Free web search using DuckDuckGo HTML parsing and GitHub API.
No API keys required, completely open source.

Usage:
    python3 search.py --query "search terms"
    python3 search.py -q "llama.cpp bug" --source github --format json
    python3 search.py -q "openai whisper" --source repo --format text

Author: OpenClaw Assistant
Created: 2026-03-11
License: MIT
"""

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional
import html
import io

# ===================== Encoding Fix =====================
# Ensure UTF-8 output on all platforms (especially Windows with GBK console)
if sys.stdout.encoding and sys.stdout.encoding.upper() not in ('UTF-8', 'UTF8'):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        else:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass
# ========================================================

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import subprocess


# ===================== Configuration =====================
CACHE_DIR = Path.home() / ".cache" / "openclaw" / "web-search"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (compatible; OpenClaw-Web-Search/1.0; +https://docs.openclaw.ai)"

# GitHub Issue/PR Search API
GITHUB_API_URL = "https://api.github.com/search/issues"
# GitHub Repository Search API
GITHUB_REPO_API_URL = "https://api.github.com/search/repositories"
GITHUB_RATE_LIMIT_WAIT = 60  # seconds

# DuckDuckGo Configuration
DDG_URL = "https://html.duckduckgo.com/html/"
DDG_PARAMS = {"kl": "us-en", "kz": "-1"}
# ====================================================


def get_cached_content(cache_key: str, max_age_seconds: int = 1800) -> Optional[str]:
    """Get content from cache"""
    cache_file = CACHE_DIR / f"{hash(cache_key)}.cache"

    if cache_file.exists():
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age < max_age_seconds:
            try:
                return cache_file.read_text(encoding='utf-8')
            except:
                pass
    return None


def save_to_cache(cache_key: str, content: str):
    """Save content to cache"""
    cache_file = CACHE_DIR / f"{hash(cache_key)}.cache"
    cache_file.write_text(content, encoding='utf-8')


def fetch_url(url: str, headers: Dict = None, timeout: int = 30, max_retries: int = 3) -> str:
    """Fetch URL content with retry support"""
    headers_str = json.dumps(headers, sort_keys=True) if headers else ""
    cache_key = f"{url}_{headers_str}"
    cached = get_cached_content(cache_key)
    if cached:
        return cached

    last_error = None
    for attempt in range(max_retries):
        if attempt > 0:
            wait_time = 2 ** attempt
            print(f"Retry {attempt + 1}/{max_retries}, waiting {wait_time}s...", file=sys.stderr)
            time.sleep(wait_time)

        if HAS_REQUESTS:
            try:
                response = requests.get(
                    url,
                    headers=headers or {"User-Agent": USER_AGENT},
                    timeout=timeout
                )
                if response.status_code == 429:
                    print(f"Rate limited, waiting 60s...", file=sys.stderr)
                    time.sleep(60)
                    continue
                response.raise_for_status()
                content = response.text
                save_to_cache(cache_key, content)
                return content
            except Exception as e:
                last_error = e
                continue
        else:
            try:
                cmd = ["curl", "-s", "-L", "-A", USER_AGENT, url]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                if result.returncode == 0:
                    content = result.stdout
                    save_to_cache(cache_key, content)
                    return content
            except Exception as e:
                last_error = e
                continue

    return ""


def parse_ddg_html(html_content: str) -> List[Dict]:
    """Parse DuckDuckGo HTML results"""
    import re
    results = []

    # Find result links (with rel="nofollow" class="result__a")
    url_pattern = r'<a\s+rel="nofollow"\s+class="result__a"\s+href="([^"]+)"[^>]*>'
    urls = re.findall(url_pattern, html_content)

    # Find titles
    title_pattern = r'class="result__a"[^>]*>(.*?)</a>'
    titles = re.findall(title_pattern, html_content, re.DOTALL)

    # Find snippets
    snippet_pattern = r'class="result__snippet"[^>]*>(.*?)</a>'
    snippets = re.findall(snippet_pattern, html_content, re.DOTALL)

    count = min(len(urls), len(titles))

    for i in range(count):
        # Clean title
        title = re.sub(r'<[^>]+>', '', titles[i]).strip()
        title = html.unescape(title)

        # Decode DuckDuckGo redirect URL
        raw_url = urls[i]
        uddg_match = re.search(r'uddg=([^&]+)', raw_url)
        url = urllib.parse.unquote(uddg_match.group(1)) if uddg_match else raw_url

        # Get snippet
        snippet = ''
        if i < len(snippets):
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            snippet = html.unescape(snippet)

        results.append({
            'title': title,
            'url': url,
            'snippet': snippet
        })

    if not results:
        results.append({
            'title': 'Search Results',
            'url': 'https://duckduckgo.com/',
            'snippet': 'Visit DuckDuckGo for full results'
        })

    return results[:15]


def search_duckduckgo(query: str, limit: int = 10, verbose: bool = False, timeout: int = 30) -> List[Dict]:
    """Search DuckDuckGo"""
    print(f"Searching DuckDuckGo: {query}", file=sys.stderr)

    params = DDG_PARAMS.copy()
    params['q'] = query

    url = DDG_URL + "?" + urllib.parse.urlencode(params)

    if verbose:
        print(f"Request URL: {url}", file=sys.stderr)

    html_content = fetch_url(url, timeout=timeout)

    if not html_content:
        return [{"error": "Failed to get DuckDuckGo results", "query": query}]

    results = parse_ddg_html(html_content)

    if verbose:
        print(f"Parsed {len(results)} results", file=sys.stderr)

    return results[:limit]


def search_github(query: str, limit: int = 10, verbose: bool = False, timeout: int = 30) -> List[Dict]:
    """Search GitHub issues and pull requests"""
    print(f"Searching GitHub Issues: {query}", file=sys.stderr)

    search_query = urllib.parse.quote(query)
    url = f"{GITHUB_API_URL}?q={search_query}&per_page={limit}"

    if verbose:
        print(f"Request URL: {url}", file=sys.stderr)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github.v3+json"
    }

    response_text = fetch_url(url, headers=headers, timeout=timeout)

    if not response_text:
        return [{"error": "Failed to get GitHub results", "query": query}]

    try:
        data = json.loads(response_text)

        if "items" not in data:
            if "message" in data:
                return [{"error": f"GitHub API error: {data['message']}", "query": query}]
            return []

        results = []
        for item in data["items"][:limit]:
            body = item.get("body") or ""
            snippet = (body[:200] + "...") if len(body) > 200 else body
            result = {
                "title": item.get("title", ""),
                "url": item.get("html_url", ""),
                "snippet": snippet,
                "type": "pull_request" if "pull_request" in item else "issue",
                "state": item.get("state", ""),
                "number": item.get("number", ""),
                "user": item.get("user", {}).get("login", ""),
                "created_at": item.get("created_at", ""),
                "updated_at": item.get("updated_at", "")
            }
            results.append(result)

        if verbose:
            print(f"Found {len(results)} GitHub results", file=sys.stderr)

        return results

    except json.JSONDecodeError as e:
        return [{"error": f"Parse error: {e}", "raw": response_text[:200]}]


def search_github_repos(query: str, limit: int = 10, verbose: bool = False, timeout: int = 30) -> List[Dict]:
    """Search GitHub repositories by name/description"""
    print(f"Searching GitHub Repos: {query}", file=sys.stderr)

    search_query = urllib.parse.quote(query)
    url = f"{GITHUB_REPO_API_URL}?q={search_query}&per_page={limit}&sort=stars&order=desc"

    if verbose:
        print(f"Request URL: {url}", file=sys.stderr)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github.v3+json"
    }

    response_text = fetch_url(url, headers=headers, timeout=timeout)

    if not response_text:
        return [{"error": "Failed to get GitHub repo results", "query": query}]

    try:
        data = json.loads(response_text)

        if "items" not in data:
            if "message" in data:
                return [{"error": f"GitHub API error: {data['message']}", "query": query}]
            return []

        results = []
        for item in data["items"][:limit]:
            description = item.get("description") or ""
            snippet = (description[:200] + "...") if len(description) > 200 else description
            topics = item.get("topics", [])

            result = {
                "title": item.get("full_name", ""),
                "url": item.get("html_url", ""),
                "snippet": snippet,
                "type": "repo",
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language", ""),
                "topics": ", ".join(topics[:5]) if topics else "",
                "owner": item.get("owner", {}).get("login", ""),
                "fork": item.get("fork", False),
                "updated_at": item.get("updated_at", "")
            }
            results.append(result)

        if verbose:
            print(f"Found {len(results)} GitHub repos", file=sys.stderr)

        return results

    except json.JSONDecodeError as e:
        return [{"error": f"Parse error: {e}", "raw": response_text[:200]}]


def detect_source(query: str) -> str:
    """Auto-detect best search source"""
    query_lower = query.lower()

    # GitHub issues/PR keywords
    github_keywords = [
        r"repo:", r"github\.com/", r"\bissue\b", r"\bpr\b", r"pull request",
        r"\.git\b", r"commit ", r"branch", r"workflow"
    ]

    # GitHub repo search keywords
    repo_keywords = [
        r"^repo ", r"^repository ", r"^project ",
        r" stars?:", r" language:",
    ]

    import re
    for keyword in repo_keywords:
        if re.search(keyword, query_lower):
            return "repo"

    for keyword in github_keywords:
        if re.search(keyword, query_lower):
            return "github"

    return "duckduckgo"


def format_results(results: List[Dict], format_type: str = "text") -> str:
    """Format search results"""
    if not results:
        return "No results found"

    if format_type == "json":
        return json.dumps(results, indent=2, ensure_ascii=False)

    elif format_type == "markdown":
        output = []
        for i, result in enumerate(results, 1):
            if "error" in result:
                output.append(f"**Error**: {result['error']}")
                continue

            title = result.get('title', 'No title')
            url = result.get('url', '#')
            snippet = result.get('snippet', '')

            output.append(f"{i}. **{title}**")

            # Repo-specific fields
            if result.get('type') == 'repo':
                meta_parts = []
                if result.get('stars'):
                    meta_parts.append(f"⭐ {result['stars']} stars")
                if result.get('language'):
                    meta_parts.append(f"🔧 {result['language']}")
                if result.get('topics'):
                    meta_parts.append(f"🏷️ {result['topics']}")
                if meta_parts:
                    output.append(f"   {' | '.join(meta_parts)}")

            if snippet:
                output.append(f"   {snippet}")

            output.append(f"   {url}\n")

        return "\n".join(output)

    else:  # text format (default)
        output = []
        for i, result in enumerate(results, 1):
            if "error" in result:
                output.append(f"[Error] {result['error']}")
                continue

            title = result.get('title', 'No title')
            url = result.get('url', '#')
            snippet = result.get('snippet', '')

            output.append(f"{i}. {title}")
            output.append(f"   {url}")

            # Repo-specific fields
            if result.get('type') == 'repo':
                meta_parts = []
                if result.get('stars'):
                    meta_parts.append(f"⭐ {result['stars']} stars")
                if result.get('language'):
                    meta_parts.append(f"[{result['language']}]")
                if meta_parts:
                    output.append(f"   {' '.join(meta_parts)}")
            else:
                if result.get('type'):
                    output.append(f"   [{result['type']}] {result.get('state', '')}")

            if snippet:
                output.append(f"   {snippet}")
            output.append("")

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Free web search tool (DuckDuckGo + GitHub Issues + GitHub Repos)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("-q", "--query", required=True, help="Search query")
    parser.add_argument("-s", "--source", choices=["auto", "github", "duckduckgo", "repo"],
                       default="auto", help="Search source: duckduckgo, github (issues/PRs), repo (repositories), auto (default: auto)")
    parser.add_argument("-f", "--format", choices=["text", "json", "markdown"],
                       default="text", help="Output format (default: text)")
    parser.add_argument("-l", "--limit", type=int, default=10,
                       help="Max results (default: 10)")
    parser.add_argument("-t", "--timeout", type=int, default=30,
                       help="Request timeout in seconds (default: 30)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Show debug info")

    args = parser.parse_args()

    # Determine search source
    if args.source == "auto":
        source = detect_source(args.query)
        if args.verbose:
            print(f"Auto-selected source: {source}", file=sys.stderr)
    else:
        source = args.source

    # Execute search
    if source == "github":
        results = search_github(args.query, args.limit, args.verbose, args.timeout)
    elif source == "repo":
        results = search_github_repos(args.query, args.limit, args.verbose, args.timeout)
    else:  # duckduckgo
        results = search_duckduckgo(args.query, args.limit, args.verbose, args.timeout)

    # Format and output
    output = format_results(results, args.format)
    print(output)


if __name__ == "__main__":
    main()
