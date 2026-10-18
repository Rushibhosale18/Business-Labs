# AI Interaction & Prompt Engineering Log

## 1. Five High-Impact Engineering Prompts Used

### Prompt 1: Resumable Ingestion & Manifest Checkpointing (Task 1)
> *"Design a Python crawler for Brilliant Directories Solution Center sitemap that maintains an `ingestion_manifest.json` tracking URL, `lastmod`, and content SHA-256 hashes. If interrupted, the crawler must resume from the saved manifest without re-fetching unchanged articles or creating duplicate chunks."*
- **Outcome**: Created `crawler.py` with polite rate limiting, exponential backoff, and idempotent indexing.

### Prompt 2: Freshdesk Multimodal DOM Parsing (Task 1)
> *"Parse Freshdesk `<article class='article-body'>` containers preserving structural headings (`h2`, `h3`), instructional steps, and screenshot `img` tags with their immediate parent captions, ignoring navigation icons and SVG logos."*
- **Outcome**: Extracted 105 structured chunks and screenshot references with clean UI captions.

### Prompt 3: Strict Citation Grounding & Abstention (Task 1)
> *"Write a RAG prompting contract that returns valid JSON containing `answer`, `confidence`, `sources`, and `needs_human`. If retrieved evidence is below relevance threshold or outside product capabilities, the model must abstain and register an escalation ID."*
- **Outcome**: Successfully passed 100% of out-of-domain abstention tests (e.g. drone couriers, NFT minting) by safely escalating to `escalations.json`.

### Prompt 4: 20-Consecutive-Approval Autonomy Gate (Task 2)
> *"Implement the autonomy rule in TypeScript/Python: Track consecutive unedited sends per category. Reset the streak to 0 if a human reviewer modifies any draft text. Permanently gate High-Risk categories (Refunds, Policy) from ever being sent autonomously regardless of streak count."*
- **Outcome**: Prevented unauthorized financial commitments while enabling controlled autonomy for routine How-To queries.

### Prompt 5: Baseline vs. Follow-up Scope Diffing (Task 3)
> *"Create a diff algorithm comparing follow-up Meeting C transcripts against approved baseline Meeting A. Categorize items into: ADDED, REMOVED, MODIFIED, and OUT-OF-SCOPE. Compute net hours delta and update total project cost."*
- **Outcome**: Correctly detected the removal of the 40-hr AI feature, addition of 5-hr branded CSS, and flagged the native mobile app as an out-of-scope exclusion.

---

## 2. Documented AI Rejection Case

### What the AI Proposed:
During the initial design of Task 2 (Inbox Agent), the AI assistant proposed embedding a local copy of product help articles directly inside Task 2's dataset folder and running a local regex lookup to draft email replies faster and avoid network calls to Task 1.

### Why It Was Rejected:
This proposal violated the fundamental architectural mandate specified in Section 1 of the capstone brief:
> *"Tasks 2 and 3 must consume Task 1 through its API. They must not duplicate Task 1's internal implementation. This makes the knowledge service reusable for other businesses."*

Duplicating knowledge files in Task 2 would cause data drift: when help articles are updated or deleted in Task 1, Task 2 would continue generating outdated, incorrect advice.

### Corrective Action Taken:
The suggestion was rejected. Task 2 was implemented strictly as a client consuming Task 1's `/query` endpoint. Any updates to Task 1's database immediately reflect across both Task 2 and Task 3 without data duplication.
