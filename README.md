# Y2S — Web Vulnerability Scanner

Y2S is an asynchronous, modular web vulnerability scanner written in Python. It is designed for authorized penetration testing, bug bounty reconnaissance, and security research. The scanner covers a broad attack surface across more than 50 vulnerability categories, produces structured JSON and HTML reports, and includes tooling for PoC generation and HackerOne report drafting.

**This scanner was built by Claude (Anthropic)** in collaboration with its user as part of a security research and learning project.

---

## Legal Notice

**Use Y2S only on systems you own or have explicit written permission to test.** Unauthorized scanning is illegal in most jurisdictions and may violate the Computer Fraud and Abuse Act (CFAA), the Computer Misuse Act, and equivalent laws worldwide. The authors accept no liability for misuse of this tool.

---

## Features

### Core Capabilities

- Fully asynchronous scanning engine built on `httpx` and `asyncio`
- Intelligent web crawler that discovers URLs, forms, API endpoints, JS-embedded paths, robots.txt, sitemap.xml, and common paths automatically
- Pre-scan target health checking with WAF/rate-limit/ban-page detection
- Randomized, realistic browser header rotation with device fingerprinting
- Proxy support including proxy file loading with latency-based ranking and automatic rotation
- Session authentication support (login URL + credentials)
- Custom request headers and scope headers for bug bounty programs
- Baseline-anchored false positive reduction across all scanners
- JSON and HTML report generation with auto-save
- PoC code generator (curl + Python) for confirmed findings
- CVSS v3 scoring for all vulnerability results
- HackerOne report generator with Markdown output
- Termux/mobile compatible

### Vulnerability Modules

| Category | Vulnerabilities Covered |
|---|---|
| Injection | SQL Injection (error, boolean, time, UNION, OOB, header, stacked), NoSQL Injection, LDAP Injection, XML Injection, SSI Injection, CRLF Injection |
| Client-Side | XSS (reflected, stored, DOM, CSP bypass), SSTI / CSTI, Prototype Pollution, Clickjacking, postMessage |
| File Handling | LFI / Path Traversal, RFI, File Upload, Directory Listing |
| Server-Side | RCE, SSRF, XXE, HTTP Request Smuggling, WebSocket Injection, Log4Shell (CVE-2021-44228), Spring4Shell (CVE-2022-22965), Shellshock (CVE-2014-6271) |
| Access Control | IDOR, IDOR Advanced, CSRF, CSRF Advanced, Business Logic, Mass Assignment, BOPLA |
| Authentication | JWT Vulnerability, JWT Algorithm Confusion, 2FA/OTP Bypass, Account Enumeration, Broken Authentication, OAuth Misconfiguration |
| Infrastructure | Security Misconfiguration, Security Headers, CORS, Host Header Injection, HTTP Verb Tampering, HTTP Parameter Pollution, API Versioning Abuse |
| Advanced | Cache Poisoning, DNS Rebinding, Subdomain Takeover, GraphQL Misconfiguration, Race Condition, Insecure Deserialization, Open Redirect, TLS/SSL Issues, WordPress Vulnerabilities, Sensitive Data Exposure |

**Total: 55+ vulnerability types, 500+ unique payloads.**

### Scanning Modes

| Mode | Description |
|---|---|
| 1 | Full comprehensive scan (all modules) on single URL |
| 2 | Batch scan from file with module selection |
| 3–32 | Individual module scans (SQLi, XSS, RCE, LFI, ...) |
| 33–55 | Extended module scans (SSTI, NoSQLi, LDAP, XML, ...) |
| 56 | Blind SQL extractor — extracts DB name and version |
| 57 | PoC generator — produces curl and Python code for a finding |
| 58 | HTML report generator from saved JSON results |
| 59 | Rate limit detection |
| 60 | DoS protection detection |
| 61 | HackerOne report generator |
| 90 | Crawl-only mode |
| 91 | WAF fingerprinting only |
| 92 | TLS/SSL analysis only |
| 95 | Infrastructure / misconfiguration scan |
| 99 | Full scan with progressive module-by-module output |

---

## Installation

### Requirements

- Python 3.9 or higher
- Works on Linux, macOS, Windows, and Termux (Android)

### Install Dependencies

```bash
pip install httpx rich beautifulsoup4
```

Or with the `--break-system-packages` flag on Termux / Debian-based systems:

```bash
pip install httpx rich beautifulsoup4 --break-system-packages
```

### Run

```bash
python3 y2s.py
```

No configuration file is required. All settings are set interactively from the menu.

---

## Usage

Start the scanner and select a mode from the interactive menu:

```
python3 y2s.py
```

**Single URL scan:**
```
Mode: 1
URL: https://example.com/page?id=1
```

**Batch scan from file:**
```
Mode: 2
File path: targets.txt
```

Each line in the targets file should be a full URL, one per line.

**SQL Injection only:**
```
Mode: 3
URL: https://example.com/search?q=test
```

**Full scan with progressive output:**
```
Mode: 99
URL: https://example.com
```

---

## Settings Menu

Press `S` from the main menu to access settings:

| Option | Description |
|---|---|
| 1 | Set request delay and concurrency |
| 2 | Set custom User-Agent |
| 3 | Set proxy (e.g. `http://127.0.0.1:8080`) |
| 4 | Set cookie string |
| 5 | Set Authorization header (Bearer token, Basic auth) |
| 6 | Set login URL for automatic session authentication |
| 7 | Set login form fields |
| 8 | Set bug bounty scope header |
| 9 | Set arbitrary custom headers |
| 10 | Load proxy list from file with latency testing |

---

## Output

All results are saved automatically to a timestamped directory:

```
y2s_results/
  results/
    scan_<timestamp>.json     # Machine-readable JSON
  reports/
    report_<timestamp>.txt    # Human-readable text report
  h1_reports/
    h1_<vuln>_<timestamp>.md  # HackerOne-ready Markdown reports
```

Use mode `57` to generate PoC code for a specific finding, or mode `58` to convert a saved JSON file to an HTML report.

---

## Payload Coverage

### SQL Injection

- Error-based (MySQL, PostgreSQL, MSSQL, SQLite, Oracle, DB2)
- Boolean-blind (true/false branch comparison)
- Time-based blind (SLEEP, pg_sleep, WAITFOR DELAY, IF)
- UNION-based (1–5 column enumeration, schema extraction)
- OOB via DNS (LOAD_FILE, xp_dirtree)
- Stacked queries and second-order injection
- WAF evasion (comment padding, hex encoding, tab/newline substitution, case variation, null-byte termination)
- Header injection (X-Forwarded-For, Referer, User-Agent, CF-Connecting-IP)

### XSS

- Script tag injection and context breakout
- Event handler injection (onerror, onload, onfocus, onmouseover, ontoggle, onbegin, and 20+ more)
- SVG, MathML, and HTML5 element vectors
- DOM XSS (document.write, location, eval, Function constructor)
- CSP bypass attempts (srcdoc, data: URI, nonce bypass)
- Polyglot payloads covering HTML, attribute, JS, and URL contexts simultaneously
- WAF bypass via Unicode escape, base64 eval, charcode, string concatenation, bracket notation

### SSTI

- Detection probes for Jinja2, Twig, Mako, Freemarker, Velocity, ERB, Smarty, Nunjucks, Thymeleaf, Handlebars, Pebble
- RCE chains for each engine where applicable
- Config/secret object leak detection for Flask and Django

### NoSQL Injection

- MongoDB operator injection (`$gt`, `$ne`, `$regex`, `$where`, `$in`, `$nin`, `$exists`, `$type`, `$not`)
- URL bracket notation (`[$gt]=`, `[$ne]=invalid`, etc.)
- JSON body injection on login endpoints
- Auth bypass detection via status code and response body comparison

### SSRF

- AWS, GCP, Azure, and Alibaba Cloud metadata endpoint probing
- IP obfuscation (hex, integer, short form, IPv6-mapped, IPv6 loopback)
- Internal port scanning (Redis, MongoDB, Elasticsearch, Docker API, Jupyter, Memcached)
- Protocol smuggling (Gopher, Dict, SFTP, LDAP, TFTP)
- Blind SSRF via differential timing

---

## Architecture

```
y2s.py
├── WebCrawler              — Async crawler with JS extraction and common path probing
├── TargetHealthChecker     — Pre-scan health, WAF, and rate-limit detection
├── WAFDetector             — Identifies WAF vendor from headers and body patterns
├── SQLiScanner             — Error, boolean, time-based, UNION, header, OOB SQLi
├── XSSScanner              — Reflected and stored XSS with executable context guard
├── RCEScanner              — Command injection with dual-baseline time verification
├── LFIScanner              — Path traversal, PHP wrappers, null byte, cloud cred files
├── SSRFScanner             — Metadata probing, IP obfuscation, blind timing detection
├── SSTIScanner             — Template engine detection and RCE chains
├── NoSQLiScanner           — MongoDB operator injection via URL params and JSON body
├── [40+ additional scanners]
├── CVSSScorer              — CVSS v3 vector and score calculation
├── PoCGenerator            — curl + Python PoC code from VulnerabilityResult
├── HackerOneReportGenerator — Markdown report in H1 submission format
├── HTMLReportGenerator     — Self-contained HTML report
├── FileHandler             — Auto-save results to timestamped directories
└── ProxyManager            — Load, test latency, and rotate proxies
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `httpx` | Async HTTP client with HTTP/2 support |
| `rich` | Terminal UI (tables, trees, progress bars, panels) |
| `beautifulsoup4` | HTML form and link extraction |

All are installable with a single `pip install` command. No external tools are required.

---

## Limitations

- Does not support JavaScript rendering. Single-page applications that require a headless browser for full interaction may yield incomplete crawl results.
- Time-based detection is sensitive to network latency. Results on high-latency targets should be treated as indicative rather than confirmed.
- Stored XSS and second-order SQL injection require manual verification in most cases.
- The scanner does not perform brute-force or fuzzing in the classical sense. It uses a curated, targeted payload set optimized for low noise.

---

## Contributing

Contributions are welcome. To add a new scanner module, implement a class with an async `scan_url(self, client, url) -> List[VulnerabilityResult]` method and register it in the `ComprehensiveScanner` and main menu. Payload additions should include a subtype label and an impact description.

---

## License

This project is released for educational and authorized security testing purposes only. All rights reserved by the author.
