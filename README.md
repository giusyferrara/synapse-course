<p align="center">
  <img src="icons/butterfly_logo_bright.svg" alt="SYNAPSE" width="140">
</p>

<h1 align="center">SYNAPSE</h1>

<p align="center"><strong>An accessibility-first, multi-LLM AI tutor for secure software development education.</strong></p>

<p align="center"><em>Learning designed for focused, creative minds.</em></p>

<p align="center">🔗 <a href="https://synapse-course.com">synapse-course.com</a></p>

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.20480483"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20480483-blue.svg" alt="DOI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://synapse-course.com"><img src="https://img.shields.io/badge/demo-live-brightgreen.svg" alt="Live demo"></a>
  <a href="https://youtu.be/9R17KC47qQI"><img src="https://img.shields.io/badge/screencast-YouTube-red.svg" alt="Screencast"></a>
  <a href="https://orcid.org/0009-0005-3669-8396"><img src="https://img.shields.io/badge/ORCID-0009--0005--3669--8396-A6CE39.svg?logo=orcid" alt="ORCID"></a>
</p>

<p align="center">
  <strong><a href="https://synapse-course.com">Live platform</a></strong> ·
  <a href="https://youtu.be/9R17KC47qQI">Screencast</a> ·
  <a href="https://doi.org/10.5281/zenodo.20480483">Archived release (DOI)</a> ·
  <a href="CITATION.cff">Cite this work</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

**An accessibility-first, multi-LLM AI tutor for secure software development education.**

*Learning designed for focused, creative minds.*

🔗 **Live platform:** https://synapse-course.com

---

## Evaluating SYNAPSE (for reviewers)

The fastest way to try SYNAPSE is the **live instance — no installation required**:

- 🔗 **Live platform:** https://synapse-course.com
- ▶️ **Demo video:** https://youtu.be/9R17KC47qQI
- 🔑 **Reviewer access:** registration is free and open

To run it locally instead, see **Running locally** below. Note that local execution needs
your own Anthropic, OpenAI and Google API keys; the live instance above needs none.

## Overview

SYNAPSE is a publicly deployed adaptive tutoring platform for Java programming, Python for cybersecurity and forensics, and secure software development. It pairs hands-on secure-coding practice with a neurodivergent-first interface designed for learners with ADHD and executive-function needs, and a multi-LLM orchestration layer that coordinates several language models behind a single pedagogical workflow.

## Key features

- **Multi-LLM orchestration via MCP** — coordinates Claude, GPT-4o, and Gemini through the Model Context Protocol, routing each interaction by pedagogical intent (Socratic guidance, worked examples, conceptual explanation).
- **Three-stage Socratic hint policy** — withholds direct answers and guides reasoning in progressively more specific stages to reduce over-reliance.
- **Neurodivergent-first accessibility layer** — always-visible support throughout the platform: dyslexia-friendly fonts, focus mode, idle-aware encouragement, calming audio, and adaptive interface controls.
- **ShopSecure** — a purpose-built, deliberately vulnerable Flask web application whose exercises map to six OWASP Top 10 (2021) categories, where learners practise the detect–understand–remediate loop on a working system.
- **Dual-language code execution** — Python runs in a restricted server-side sandbox; Java compiles and runs as an isolated OpenJDK 21 subprocess under resource limits.

## Architecture

An asynchronous Python (aiohttp) backend behind an Nginx/Cloudflare reverse proxy, with five interacting subsystems:

- an AI tutor layer coordinated by an MCP server (Claude → GPT-4o → Gemini)
- a course-content engine
- a persistent accessibility layer
- a dual-language code executor
- ShopSecure, running in an isolated Docker container

Persistent storage uses PostgreSQL.

## Repository structure

- `ai/`, `ai_clients/` — MCP router and provider clients (Claude, OpenAI, Gemini, DALL·E)
- `core/` — tutoring engine, course content, idle/emotion logic
- `web/` — HTTP request handlers (auth, course, research, labs, metrics)
- `database/` — models and schema
- `labs/` — containerised lab environment (Docker session management)
- `templates/`, `static/` — frontend (HTML, JS/CSS, course-content JSON, accessibility assets)
- `app.py` — application entry point

## Running locally

> Requires Python 3.12, PostgreSQL, OpenJDK 21, and Docker (for ShopSecure / labs). You will need your own API keys for Anthropic, OpenAI, and Google.

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and `claude_desktop_config.example.json` to `claude_desktop_config.json`, then fill in your own API keys and database credentials.
4. Create an empty PostgreSQL database (e.g. `createdb security_tutor`), set `DATABASE_URL` in `.env`, then create the tables: `python -m database.init_db`
5. Start the app: `python app.py`

(OpenJDK 21 and Docker are only needed for the code-execution sandbox and ShopSecure/labs — not to run and explore the tutor.)

## Citation

If you use SYNAPSE in your work, please cite the archived software:

> Ferrara, G. (2026). *SYNAPSE: A Multi-LLM Orchestrated AI Tutor for Secure Software Development Education.* Zenodo. https://doi.org/10.5281/zenodo.20480483

A tool-demonstration paper describing SYNAPSE has been submitted to ICSME 2026.

## License

Released under the MIT License — see [LICENSE](LICENSE). © 2026 Giusy Ferrara.

## Acknowledgements

Developed and evaluated under the supervision of Prof. Ashkan Sami, Edinburgh Napier University.
