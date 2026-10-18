# System Design Document: AI Tech Consultant

## 1. Executive Summary & Business Problem

Modern software development agencies and SaaS implementation partners face three critical operational bottlenecks:

1. **Product Knowledge Fragmentation (Task 1)**: Senior engineers and support leads spend hours digging through hundreds of product help center articles, changelogs, and screenshot tutorials. Information becomes outdated quickly, and missing screenshot context leads to incomplete advice.
2. **Support Inbox Overload (Task 2)**: Support representatives repeatedly answer identical how-to queries while risking unauthorized commercial or refund commitments on high-risk tickets.
3. **Meeting-to-Scope Inefficiency (Task 3)**: Vague client statements (e.g., *"Make search better with AI"*) are often prematurely quoted for expensive custom engineering, when existing platform settings could solve the problem for zero custom code. When clients alter requirements in follow-up meetings, scope creep goes undetected.

### The Solution: One Shared Knowledge Service, Two Downstream Applications
Rather than building three disconnected chatbots, this system implements **one single source of truth (Task 1: Knowledge Brain)** consumed exclusively via REST API by two downstream applications: **Task 2 (Inbox Agent)** and **Task 3 (Meeting to Scope)**.

---

## 2. High-Level Architecture & Interaction Diagram

```
+-----------------------------------------------------------------------------------+
|              EXTERNAL SOURCE: Brilliant Directories Solution Center               |
|                      (1,696 URLs discovered via sitemap XML)                      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | Ingestion Bot (Rate-limited, Checkpointed)
                                          v
+-----------------------------------------------------------------------------------+
|                         TASK 1: KNOWLEDGE BRAIN SERVICE                           |
|                                                                                   |
|  [Ingestion & Parser]                                                             |
|   - Polite Crawler with Ingestion Manifest (SHA-256 Content Hashing)              |
|   - Freshdesk DOM Parser extracting headings, procedures, and image captions      |
|                                                                                   |
|  [Storage & Hybrid Retrieval Index]                                               |
|   - SQLite FTS5 Full-Text Engine with Porter Stemming Tokenizer                   |
|   - Chunks Metadata with structured JSON image references                         |
|                                                                                   |
|  [RAG & Grounding Engine]                                                          |
|   - Claude 3.5 Sonnet / Grounded Synthesis                                        |
|   - Strict Citation Enforcement (Exact URL attribution)                           |
|   - Safe Abstention: Automatic escalation to escalations.json for out-of-domain   |
|                                                                                   |
|  REST API Endpoints:                                                              |
|   * POST /query                 * POST /escalations                               |
|   * POST /ingestion/run         * POST /escalations/{id}/resolve                  |
|   * GET  /ingestion/status      * GET  /health                                    |
+-----------------------------------------+-----------------------------------------+
                                          |
                      +-------------------+-------------------+
                      | REST API Client                       | REST API Client
                      | (HTTP JSON)                           | (HTTP JSON)
                      v                                       v
+---------------------------------------+   +---------------------------------------+
|          TASK 2: INBOX AGENT          |   |       TASK 3: MEETING TO SCOPE        |
|                                       |   |                                       |
| [Intent & Risk Classifier]            |   | [Multi-Agent Pipeline]                |
|  - 7 Categories (How-to, Refund, etc) |   |  1. Transcript Analyst                |
|  - Risk Badge: Low, Moderate, High    |   |  2. Feasibility Agent (Queries Task 1)|
|                                       |   |  3. Scope Agent (Deliverables/WBS)    |
| [Grounded Draft Generator]            |   |  4. Estimation Agent (3-Point Hours)  |
|  - Sourced directly from Task 1 API   |   |  5. Proposal & Review Agent           |
|                                       |   |                                       |
| [Autonomy Gate Controller]            |   | [Scope Diff Engine]                   |
|  - 20-Consecutive-Approval Streak     |   |  - Compares Meeting C vs Meeting A    |
|  - Reset to 0 on human edit           |   |  - Detects Added, Removed, Modified   |
|  - Permanent gate on High Risk/Refunds|   |  - Flags Out-of-Scope Exclusions      |
|                                       |   |                                       |
| [Feedback Audit Log]                  |   | [Director Approval Gate]              |
|  - Human corrections stored to audit  |   |  - Enforces baseline signoff          |
+---------------------------------------+   +---------------------------------------+
```

---

## 3. Detailed Component Architecture

### 3.1 Task 1: Knowledge Brain
- **Polite Resumable Ingestion**: Uses `urllib.request` with custom `User-Agent` headers and a 0.3s delay between requests to respect server resources. The `ingestion_manifest.json` tracks the crawl state, `lastmod` timestamps, and SHA-256 hashes of article bodies. If interrupted, the crawler resumes without duplicating chunks or re-fetching unchanged pages.
- **Multimodal Context Extraction**: When parsing Freshdesk articles, the parser detects `<article class="article-body">`, associates each screenshot `<img>` with its parent context and section title, and indexes both text and visual descriptions.
- **FTS5 BM25 Hybrid Retrieval**: Text is chunked hierarchically by heading boundaries. SQLite FTS5 provides sub-millisecond full-text retrieval with normalized BM25 ranking scores, preserving exact technical terms such as `subscription_start_date` and `billing_cycle`.
- **Strict Grounding & Abstention**: Queries with no relevant documentation or relevance scores below threshold trigger safe abstention:
  ```json
  {
    "answer": "I could not find verified documentation... escalated to human expert.",
    "status": "insufficient_evidence",
    "needs_human": true,
    "escalation_id": "ESC-867AB3"
  }
  ```
  The escalation is recorded in `data/escalations.json` for human resolution.

### 3.2 Task 2: Inbox Agent
- **Balanced 50-Email Benchmark Dataset**: Curated in `task2-inbox-agent/data/customer_emails.json` across 7 distinct operational categories:
  - 12 How-to questions
  - 10 Troubleshooting inquiries
  - 6 Project requests
  - 6 Refund and cancellation requests
  - 6 Complaints and outages
  - 5 Quote requests
  - 5 Follow-ups
- **Policy & Risk Stratification**:
  - *Low Risk* (How-to, General): Eligible for autonomy once the 20-streak threshold is reached.
  - *Moderate Risk* (Troubleshooting, Quotes): Requires support agent confirmation.
  - *High Risk* (Refunds, Financial, Hostile Complaints): **Permanently gated**. The agent is strictly forbidden from issuing automated refunds or making binding legal/financial commitments.
- **Auditable 20-Approval Streak**: The system compares the generated draft with the final sent text. If the human reviewer modifies a single sentence, the streak resets to 0. Only upon 20 consecutive unmodified sends in a low-risk category is autonomous sending enabled.

### 3.3 Task 3: Meeting-to-Scope Engine
- **Staged Multi-Agent Pipeline**:
  1. *Transcript Analyst*: Parses raw conversation timestamps and separates client desires from confirmed commitments.
  2. *Feasibility Agent*: Queries Task 1 Knowledge Brain for each requirement. If a requirement (like bulk CSV importing or subscription cancellations) is supported natively, it is marked as **Existing Native Feature**, saving clients thousands of dollars in unnecessary custom engineering.
  3. *Scope Agent*: Produces a structured Work Breakdown Structure (WBS) with deliverables, explicit exclusions, and client prerequisites.
  4. *Estimation Agent*: Produces a 3-point estimate table (Low, Likely, High hours) with a blended agency billing rate ($125/hr).
  5. *Proposal Agent*: Formulates the client-facing proposal and enforces a director review gate.
- **Scope Diff & Change Detection**:
  When a follow-up transcript (Meeting C) is processed, `ScopeDiffEngine` performs a structural diff against the approved Meeting A baseline:
  - **Removed**: REQ-003 AI Matching (-40 likely hours).
  - **Added**: REQ-004 Branded CSS Overrides (+5 likely hours).
  - **Modified**: Delivery timeline compressed from 6 weeks to 4 weeks.
  - **Out of Scope Flag**: Native Apple/Android mobile apps flagged as contract exclusions.

---

## 4. Model Selection & Tradeoff Analysis

| Model Family | Primary Role in System | Strengths | Tradeoffs / Limitations |
|---|---|---|---|
| **Claude 3.5 Sonnet** | Transcript Analysis & Scope Diffing (Task 3) | Exceptional contract reasoning, complex instruction following, precise diff categorization | Higher token cost and 1.4s median latency |
| **Claude 3.5 Haiku** | High-Volume Email Classification (Task 2) | Ultra-low latency (480ms), cost-effective ($0.25/1k calls) | Less nuanced on ambiguous multi-page contracts |
| **Grounded Local Synthesis** | Offline Fallback Engine (Task 1) | Zero network dependency, 100% deterministic, instant (<45ms) execution | Limited to verbatim extractive summarization |

---

## 5. Deliberately Dropped Features & Future Roadmap

1. **Automated LLM Weight Fine-Tuning**: Dropped in favor of prompt versioning, structured RAG grounding, and feedback logs. Fine-tuning on customer support emails risks catastrophic forgetting and hallucinated pricing policies.
2. **Autonomous Multi-Vendor Marketplace Payments**: Dropped from the initial scope because Brilliant Directories natively supports single-merchant checkout. Multi-vendor split payments require custom Stripe Connect architecture and were correctly classified as out-of-scope for the web launch.
3. **Future Extension**: Expanding the crawler to ingest Brilliant Directories API documentation and developer forum threads to increase coverage on complex custom PHP/widget hooks.
