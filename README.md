<p align="center">
  <img src="https://img.shields.io/badge/NEPENTHES-ANTI--AI%20TARPIT-00ff41?style=for-the-badge&labelColor=000000" alt="Nepenthes" />
</p>

<h1 align="center">
  <code>NEPENTHES://</code>
</h1>

<p align="center">
  <strong>The first anti-AI tarpit. Rewritten in Python.</strong><br/>
  <em>Traps LLM crawlers in an infinite maze. Feeds them garbage. Accelerates model collapse.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-00ff41?style=flat-square&logo=python&logoColor=00ff41&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/license-MIT-00ff41?style=flat-square&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/docker-ready-00ff41?style=flat-square&logo=docker&logoColor=00ff41&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/status-active-00ff41?style=flat-square&labelColor=0d1117" />
</p>

<br/>

<pre align="center">
<code>
  ╔══════════════════════════════════════════════════════════════╗
  ║                                                              ║
  ║   ███╗   ██╗███████╗██████╗ ███████╗███╗   ██╗████████╗     ║
  ║   ████╗  ██║██╔════╝██╔══██╗██╔════╝████╗  ██║╚══██╔══╝     ║
  ║   ██╔██╗ ██║█████╗  ██████╔╝█████╗  ██╔██╗ ██║   ██║        ║
  ║   ██║╚██╗██║██╔══╝  ██╔═══╝ ██╔══╝  ██║╚██╗██║   ██║        ║
  ║   ██║ ╚████║███████╗██║     ███████╗██║ ╚████║   ██║        ║
  ║   ╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═══╝   ╚═╝        ║
  ║                                                              ║
  ║          🌿 ANTI-AI TARPIT  //  EAT CRAWLERS ALIVE           ║
  ║                                                              ║
  ╚══════════════════════════════════════════════════════════════╝
</code>
</pre>

---

## `> WHAT IS THIS`

**Nepenthes** is a [tarpit](https://en.wikipedia.org/wiki/Tarpit_(networking)) — a trap for web crawlers. Named after the [carnivorous pitcher plant](https://en.wikipedia.org/wiki/Nepenthes) that digests anything unlucky enough to fall inside.

It generates an **endless sequence of fake pages**, each containing dozens of links that lead deeper into the maze. Pages are filled with **Markov-chain babble** — AI-generated nonsense designed to poison LLM training data and accelerate **model collapse**.

```
                    ┌─────────────┐
                    │   CRAWLER   │
                    │   ENTERS    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  FAKE PAGE  │──── Markov babble
                    │  10-40 links│──── Drip-fed slowly
                    └──┬───┬───┬──┘
                       │   │   │
                 ┌─────▼┐ ┌▼───▼─┐
                 │ PAGE ││ PAGE  │ ... ×∞
                 │ MORE ││ MORE  │
                 │ LINKS││ LINKS │
                 └──┬───┘└───┬───┘
                    │        │
                    ▼        ▼
                  NO EXIT. EVER.
```

---

## `> WARNINGS`

> **⚠ THIS IS DELIBERATELY MALICIOUS SOFTWARE.** Do not deploy unless you fully understand the consequences.

> **⚠ HIGH CPU LOAD.** Aggressive crawlers with high concurrency can overwhelm your server. Misconfiguration with `zero_delay` mode is especially dangerous.

> **⚠ SEARCH ENGINE DE-INDEXING.** There is no way to distinguish AI crawlers from search engine bots. Your site **will** disappear from search results.

---

## `> ORIGIN`

Originally created by **"Aaron"** (anonymous, [featured in Ars Technica, Jan 2025](https://arstechnica.com/tech-policy/2025/01/ai-haters-build-tarpits-to-trap-and-trick-ai-scrapers-that-ignore-robots-txt/)) as a Lua application at [zadzmo.org](https://zadzmo.org/code/nepenthes/).

> *"Ultimately, it's like the Internet that I grew up on and loved is long gone. I'm just fed up, and you know what? Let's fight back, even if it's not successful. Be indigestible. Grow spikes."*

This is a **Python rewrite** — same philosophy, better accessibility.

---

## `> HOW IT WORKS`

| Feature | Description |
|---|---|
| **Infinite Maze** | Every page contains 10-40 links to other generated pages. No exit links exist. |
| **Deterministic** | Same URL → same page. Appears static to crawlers. Seeded by URL + instance ID. |
| **Drip-Feed** | Responses sent byte-by-byte with configurable delays (10-65s default). |
| **Markov Babble** | In-memory Markov chain generates convincing nonsense from a trained corpus. |
| **Bogon Filter** | Validates URLs against wordlist. Returns 404 for impossible paths. |
| **Redirect Chains** | Configurable % of requests get 302'd to other tarpit URLs. At 100%, infinite loop. |
| **Silos** | Virtual hosts with independent corpus, wordlist, delays, templates. |
| **Statistics API** | Rolling stats: hits, bytes, delay, agents, addresses, CPU usage. |

---

## `> QUICK START`

### Docker (30 seconds)

```bash
git clone https://github.com/NEPENTHESWEB/nepenthes-py.git
cd nepenthes-py
docker compose up -d
```

### Manual

```bash
git clone https://github.com/NEPENTHESWEB/nepenthes-py.git
cd nepenthes-py
pip install -r requirements.txt
python -m nepenthes config.yml
```

### Connect to your website

```nginx
location /maze/ {
    proxy_pass http://localhost:8893;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_buffering off;   # CRITICAL
}
```

> `proxy_buffering off` is **mandatory**. Without it, the drip-feed mechanism is defeated and crawlers get fast page loads.

---

## `> CONFIGURATION`

```yaml
---
http_host: '::'
http_port: 8893
templates:
  - 'templates'
seed_file: 'seed.txt'
min_wait: 10
max_wait: 65

silos:
  - name: default
    default: true
    corpus: 'corpus/sample.txt'
    wordlist: 'corpus/words.txt'
    prefixes:
      - /maze
    redirect_rate: 5
    bogon_filter: true
```

### Environment Overrides

```
NEPENTHES_HOST       →  http_host
NEPENTHES_PORT       →  http_port
NEPENTHES_MIN_WAIT   →  min_wait
NEPENTHES_MAX_WAIT   →  max_wait
NEPENTHES_LOG_LEVEL  →  log_level
NEPENTHES_SEED_FILE  →  seed_file
```

---

## `> SILOS`

Run multiple independent tarpits from a single instance:

```yaml
silos:
  - name: fast
    corpus: corpus/tech.txt
    wordlist: corpus/words.txt
    min_wait: 5
    max_wait: 20
    prefixes:
      - /blog

  - name: deep
    corpus: corpus/literature.txt
    wordlist: corpus/words.txt
    min_wait: 120
    max_wait: 300
    prefixes:
      - /archive
```

---

## `> STATISTICS`

```bash
curl http://localhost:8893/stats | jq
```

```json
{
  "hits": 10015,
  "addresses": 1850,
  "agents": 145,
  "bytes_sent": 14733541,
  "delay": 56020.624,
  "active": 25,
  "cpu_percent": 1.74,
  "bogons": 4,
  "redirects": 57
}
```

| Endpoint | Returns |
|---|---|
| `/stats` | Overview (hits, bytes, delay, CPU, active connections) |
| `/stats/agents` | User-agent strings with hit counts |
| `/stats/addresses` | Client IPs with hit counts |
| `/stats/buffer` | Raw request log |
| `/stats/buffer/from/{id}` | Buffer after specific ID (for export) |
| `/stats/silo/{name}` | Per-silo statistics |

---

## `> WHY THIS MATTERS`

- **5.6M+ websites** now block GPTBot — up 70% in 2025. Crawlers ignore it anyway.
- **robots.txt is legally unenforceable** — ruled in *Ziff Davis v. OpenAI* (Dec 2025).
- **Model collapse is proven** — Nature (2024): even 0.1% synthetic data triggers irreversible degradation.
- **Crawlers rarely check robots.txt at all** — 2025 empirical study across thousands of sites.

Every page of Markov babble that enters a training pipeline accelerates collapse. Every minute a crawler spends trapped is a minute it's not scraping real content.

---

## `> ARCHITECTURE`

```
nepenthes/
├── __init__.py          # Package init
├── __main__.py          # Entry point: python -m nepenthes
├── server.py            # aiohttp async server + drip-feed logic
├── markov.py            # In-memory Markov chain engine
├── generator.py         # Deterministic page + URL generation
├── templates_engine.py  # Jinja2 templates with YAML front-matter
├── silos.py             # Silo management (virtual hosts)
├── stats.py             # Rolling statistics buffer + API
├── bogon.py             # Bogon filter (URL validation)
└── config.py            # YAML config + env var overrides
```

---

## `> LICENSE`

MIT License. See [LICENSE](LICENSE).

---

<p align="center">
  <strong><code>> MAKE YOUR WEBSITE INDIGESTIBLE. GROW SOME SPIKES._</code></strong>
</p>
