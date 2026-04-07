#!/usr/bin/env python3
"""
DuckDuckGo HTML Parser - BeautifulSoup Version
Uses BeautifulSoup for reliable HTML parsing
"""

import re
import html
from typing import Dict, List
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False


def parse_ddg_with_bs4(html_content: str) -> List[Dict]:
    """Parse DuckDuckGo results using BeautifulSoup"""
    if not HAS_BEAUTIFULSOUP:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    seen_urls = set()
    
    result_containers = soup.find_all('div', class_=re.compile(r'result|web-result'))
    
    for container in result_containers[:20]:
        result = {}
        
        title_link = container.find('a', class_='result__a')
        if not title_link:
            continue
        
        ddg_redirect_url = title_link.get('href', '')
        if not ddg_redirect_url:
            continue
        
        real_url = extract_real_url_from_ddg(ddg_redirect_url)
        if not real_url:
            continue
        
        url_key = real_url.split('?')[0]
        if url_key in seen_urls:
            continue
        seen_urls.add(url_key)
        
        title = title_link.text.strip()
        if not title or len(title) < 5:
            continue
        
        result['url'] = real_url
        result['title'] = html.unescape(title)
        
        snippet_elem = container.find('a', class_='result__snippet')
        if snippet_elem:
            result['snippet'] = html.unescape(snippet_elem.text.strip())
        
        parsed_url = urlparse(real_url)
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        result['domain'] = domain
        
        results.append(result)
    
    return results[:10]


def extract_real_url_from_ddg(ddg_url: str) -> str:
    """Extract real URL from DuckDuckGo redirect"""
    if not ddg_url:
        return ""
    
    if 'uddg=' in ddg_url:
        from urllib.parse import urlparse, parse_qs, unquote
        
        if ddg_url.startswith('//'):
            ddg_url = 'https:' + ddg_url
        
        parsed = urlparse(ddg_url)
        query_params = parse_qs(parsed.query)
        
        if 'uddg' in query_params:
            encoded_url = query_params['uddg'][0]
            try:
                return unquote(encoded_url)
            except:
                pass
    
    if ddg_url.startswith('//'):
        return 'https:' + ddg_url
    
    return ddg_url


def parse_ddg_fallback(html_content: str) -> List[Dict]:
    """Fallback parser without BeautifulSoup"""
    results = []
    
    link_pattern = r'<a\s+href="([^"]*)"[^>]*>([^<]{10,300})</a>'
    links = re.findall(link_pattern, html_content, re.IGNORECASE)
    
    seen_urls = set()
    for url, title_html in links[:30]:
        if ('duckduckgo.com' in url or 
            url.startswith('javascript:') or
            'ad.' in url.lower()):
            continue
        
        title = re.sub(r'<[^>]+>', '', title_html)
        title = html.unescape(title).strip()
        
        if len(title) < 10:
            continue
        
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        
        results.append({
            'title': title,
            'url': url,
            'snippet': '',
            'domain': domain
        })
    
    return results[:10]


def parse_ddg_html(html_content: str) -> List[Dict]:
    """Main parsing function"""
    if HAS_BEAUTIFULSOUP:
        results = parse_ddg_with_bs4(html_content)
        if results:
            return results[:10]
    
    results = parse_ddg_fallback(html_content)
    if results:
        return results[:10]
    
    return [{
        'title': 'Search Results',
        'url': 'https://duckduckgo.com/',
        'snippet': 'Visit DuckDuckGo for full results',
        'domain': 'duckduckgo.com'
    }]
