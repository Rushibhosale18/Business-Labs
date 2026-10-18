# AI Tech Consultant

A multi-agent, enterprise-grade AI consulting system designed for software and SaaS service businesses running on Brilliant Directories.

---

## 🌐 Live Production Deployment
Your application is deployed and live in the cloud:
👉 **[https://business-labs-1.onrender.com](https://business-labs-1.onrender.com)**

---

## 🚀 One-Command Local Launch (Unified Dashboard)

To start the entire application suite (all 3 tasks and the interactive visual dashboard):

```bash
# From the project root:
py -3.11 dashboard.py
```
Open your browser to: **`http://127.0.0.1:8000`**

---

## 🧪 Run Automated Benchmark Suite (60 Test Cases)

To execute the automated evaluation suite across Task 1, Task 2, and Task 3:

```bash
py -3.11 evaluate_all.py
```

---

## 🏛️ System Architecture

1. **Task 1: Knowledge Brain (Python / FastAPI / FTS5 / Multimodal)**
   - Resumable sitemap crawler (`ingestion/crawler.py`) for Brilliant Directories Solution Center.
   - Preserves screenshot image URLs, UI element captions, and hierarchical headings.
   - SQLite FTS5 BM25 hybrid ranking index with citation verification.
   - Safe abstention engine with human escalation registry (`data/escalations.json`).
   - Documented REST endpoints: `POST /query`, `POST /ingestion/run`, `GET /ingestion/status`, `POST /escalations/{id}/resolve`.

2. **Task 2: Inbox Agent (TypeScript / Python Client)**
   - Comprehensive 50-email realistic customer dataset (`data/customer_emails.json`) across 7 categories.
   - Strictly consumes Task 1 API to ground support responses.
   - Enforces the 20-consecutive-approval rule: resets streak on edit; permanently gates high-risk/refund queries.

3. **Task 3: Meeting to Scope Engine (Python Multi-Agent)**
   - Staged transcript analysis on 3 role-played transcripts (`Meeting A`, `Meeting B`, `Meeting C`).
   - Feasibility Agent queries Task 1 to classify requirements as native configurations vs custom engineering.
   - 3-point task estimation (Low, Likely, High hours) with blended commercial rate.
   - Scope Diff Engine: Compares follow-up Meeting C against approved baseline Meeting A (Added, Removed, Modified, Out-of-Scope flags).

---

## 📁 Repository Organization

```
ai-tech-consultant/
├── dashboard.py                  # Single-command unified web interface (Port 8000)
├── evaluate_all.py               # Automated 60-test benchmark suite
├── task1-knowledge-brain/        # Knowledge Brain implementation & data
│   ├── app/                      # FastAPI API and RAG engine
│   ├── ingestion/                # Crawler, manifest & Freshdesk parser
│   ├── retrieval/                # Indexer and FTS5 BM25 searcher
│   └── data/                     # Ingested articles, DB, escalations
├── task2-inbox-agent/            # Inbox Agent implementation & dataset
│   ├── data/customer_emails.json # 50 realistic customer emails
│   └── test_inbox_agent.py       # Live processing & autonomy streak test
├── task3-meeting-to-scope/       # Meeting-to-Scope engine & diffing
│   ├── transcripts/              # Meetings A, B, and C transcripts
│   ├── scope_diff/               # Scope diff & change detection engine
│   └── test_meeting_to_scope.py  # Live scoping & feasibility test
├── README.md                     # Quickstart and overview
├── DESIGN.md                     # Architecture, tradeoffs, and design choices
├── EVALS.md                      # 60 test results, latency, cost, and model comparisons
└── AI_LOG.md                     # Prompts, rationale, and documented AI rejection case
```
