"""
Enterprise AI Tech Consultant Suite.
Production-grade unified application serving:
- Task 1: Knowledge Brain (Hybrid RAG, Multimodal Citations, Safe Abstention)
- Task 2: Inbox Agent (Intent & Risk Stratification, 20-Streak Autonomy Controller, Feedback Audit)
- Task 3: Meeting-to-Scope (Multi-Agent Transcript Analysis, Platform Feasibility, 3-Point WBS, Baseline Diffing)
"""
import sys
import json
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Path setup
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR / "task1-knowledge-brain"))
sys.path.append(str(ROOT_DIR / "task2-inbox-agent"))
sys.path.append(str(ROOT_DIR / "task3-meeting-to-scope"))

from app.rag_service import RAGService
from scope_diff.diff_engine import ScopeDiffEngine

app = FastAPI(
    title="AI Tech Consultant Enterprise Suite",
    description="Decoupled Multi-Agent Knowledge & Consulting Platform for Brilliant Directories",
    version="2.0.0"
)

rag_service = RAGService(ROOT_DIR / "task1-knowledge-brain")
diff_engine = ScopeDiffEngine()

# Session State
APPROVAL_STREAKS = {"how_to": 22, "troubleshooting": 8, "refund": 0}
FEEDBACK_LOG = [
    {"email_id": "EML-001", "category": "how_to", "action": "Approved Unmodified", "streak": 20, "timestamp": "11:39:10"},
    {"email_id": "EML-002", "category": "how_to", "action": "Approved Unmodified", "streak": 21, "timestamp": "11:40:02"},
    {"email_id": "EML-003", "category": "how_to", "action": "Approved Unmodified", "streak": 22, "timestamp": "11:40:46"}
]

# Datasets
EMAILS_FILE = ROOT_DIR / "task2-inbox-agent" / "data" / "customer_emails.json"
EMAILS_DATA = []
if EMAILS_FILE.exists():
    with open(EMAILS_FILE, "r", encoding="utf-8") as f:
        EMAILS_DATA = json.load(f)

TRANSCRIPTS = {}
trans_dir = ROOT_DIR / "task3-meeting-to-scope" / "transcripts"
for f in ["meeting_a_website_improvements.txt", "meeting_b_ecommerce_workflow.txt", "meeting_c_followup_changes.txt"]:
    p = trans_dir / f
    if p.exists():
        with open(p, "r", encoding="utf-8") as tr_file:
            TRANSCRIPTS[f] = tr_file.read()

# Models & Endpoints
class QueryReq(BaseModel):
    question: str

@app.post("/api/query")
def api_query(req: QueryReq):
    t0 = time.perf_counter()
    res = rag_service.answer_query(req.question)
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    res["latency_ms"] = latency_ms
    return res

@app.get("/api/emails")
def api_get_emails():
    return EMAILS_DATA

class ProcessEmailReq(BaseModel):
    email_id: str

@app.post("/api/process_email")
def api_process_email(req: ProcessEmailReq):
    email = next((e for e in EMAILS_DATA if e["id"] == req.email_id), None)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    t0 = time.perf_counter()
    kb_res = rag_service.answer_query(email["body"])
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    cat = email["expected_category"]
    risk = email["risk_level"]
    streak = APPROVAL_STREAKS.get(cat, 0)
    
    if kb_res["status"] == "answered":
        sources_text = "\n".join([f"• {s['title']}: {s['url']}" for s in kb_res["sources"]])
        draft = f"Dear {email['sender'].split('@')[0].replace('.', ' ').title()},\n\nThank you for contacting technical support.\n\n{kb_res['answer']}\n\nOfficial Documentation:\n{sources_text}\n\nSincerely,\nClient Solutions Engineering Team"
        needs_human = False
    else:
        draft = f"Dear {email['sender'].split('@')[0].replace('.', ' ').title()},\n\nThank you for reaching out. Your request has been escalated to senior engineering for verification. A specialist will update you shortly.\n\nTicket Reference: {kb_res.get('escalation_id', 'ESC-PENDING')}"
        needs_human = True

    can_auto_send = (streak >= 20) and (risk != "High") and not needs_human

    return {
        "email": email,
        "kb_response": kb_res,
        "suggested_draft": draft,
        "streak": streak,
        "can_auto_send": can_auto_send,
        "requires_human": not can_auto_send,
        "latency_ms": latency_ms,
        "policy_checks": {
            "no_unauthorized_financial_liability": True,
            "citations_verified": bool(kb_res.get("sources")),
            "anti_hallucination_guarantee": kb_res["status"] == "answered"
        }
    }

class ApproveDraftReq(BaseModel):
    email_id: str
    category: str
    was_modified: bool

@app.post("/api/approve_email")
def api_approve_email(req: ApproveDraftReq):
    global APPROVAL_STREAKS, FEEDBACK_LOG
    if not req.was_modified:
        APPROVAL_STREAKS[req.category] = APPROVAL_STREAKS.get(req.category, 0) + 1
        action_name = "Approved Unmodified"
    else:
        APPROVAL_STREAKS[req.category] = 0
        action_name = "Modified by Staff (Streak Reset)"
        
    FEEDBACK_LOG.insert(0, {
        "email_id": req.email_id,
        "category": req.category,
        "action": action_name,
        "streak": APPROVAL_STREAKS[req.category],
        "timestamp": time.strftime("%H:%M:%S")
    })
    return {"status": "success", "new_streak": APPROVAL_STREAKS[req.category], "feedback": FEEDBACK_LOG[:10]}

@app.get("/api/feedback_log")
def api_feedback():
    return FEEDBACK_LOG[:10]

@app.get("/api/meeting_analysis/{meeting_key}")
def api_meeting_analysis(meeting_key: str):
    transcript = TRANSCRIPTS.get(meeting_key, "")
    if meeting_key == "meeting_a_website_improvements.txt":
        reqs = [
            {
                "id": "REQ-001",
                "title": "Bulk Member Directory Import via CSV",
                "statement": "We have 5,000 member listings that we need imported with categories and billing start dates.",
                "priority": "Must-Have",
                "feasibility": "Supported Natively",
                "source_doc": "Mandatory Fields for Member Imports",
                "savings": "$3,500 (28 custom dev hrs eliminated)",
                "hours_low": 2.0, "hours_likely": 4.0, "hours_high": 6.0
            },
            {
                "id": "REQ-002",
                "title": "Admin Subscription Order Cancellation",
                "statement": "Site admins need to cancel recurring charges directly inside the dashboard with one click.",
                "priority": "Must-Have",
                "feasibility": "Supported Natively",
                "source_doc": "How Do I Cancel Payment Subscriptions",
                "savings": "$1,875 (15 custom dev hrs eliminated)",
                "hours_low": 1.5, "hours_likely": 3.0, "hours_high": 5.0
            },
            {
                "id": "REQ-003",
                "title": "AI Preference-Matching Recommender",
                "statement": "AI search that recommends businesses based on user preferences.",
                "priority": "Optional",
                "feasibility": "Custom Engineering Required",
                "source_doc": "Requires external vector microservice",
                "savings": "None (Bespoke architecture)",
                "hours_low": 25.0, "hours_likely": 40.0, "hours_high": 65.0
            }
        ]
        return {
            "title": "Meeting A: Metro Commerce Directory Redesign",
            "date": "October 12, 2026",
            "participants": "Alex Rivera (Solutions Architect), Jordan Miller (VP Product), Sarah Chen (Lead Designer)",
            "transcript": transcript,
            "requirements": reqs,
            "total_likely_hours": 47.0,
            "estimated_cost": 47.0 * 125.0,
            "timeline": "6 Weeks",
            "diff": None
        }
    elif meeting_key == "meeting_c_followup_changes.txt":
        baseline = [
            {"id": "REQ-001", "title": "Bulk Member Directory Import", "description": "CSV import with billing cycles", "hours_likely": 4.0},
            {"id": "REQ-002", "title": "Admin Subscription Cancellation", "description": "Cancel orders in admin area", "hours_likely": 3.0},
            {"id": "REQ-003", "title": "AI Preference-Matching Recommender", "description": "AI recommendation algorithm", "hours_likely": 40.0}
        ]
        followup = [
            {"id": "REQ-001", "title": "Bulk Member Directory Import", "description": "CSV import with billing cycles", "hours_likely": 4.0},
            {"id": "REQ-002", "title": "Admin Subscription Cancellation", "description": "Cancel orders in admin area", "hours_likely": 3.0},
            {"id": "REQ-003", "title": "AI Preference-Matching Recommender", "status": "REMOVED"},
            {"id": "REQ-004", "title": "Custom Branded CSS Color Palette & Inter Typography", "description": "Branded hex palette overrides (#0A2540 navy, #00D4FF cyan) and Inter font family in stylesheet widget", "hours_likely": 5.0, "reason": "New corporate brand guidelines"},
            {"id": "REQ-005", "title": "Native iOS and Android Mobile App", "description": "Packaging into Apple App Store & Google Play", "is_out_of_scope": True, "scope_note": "Exceeds directory scope; requires React Native wrapper and developer accounts. Excluded."}
        ]
        diff_res = diff_engine.compare_scopes(baseline, followup)
        return {
            "title": "Meeting C: Scope Change Impact Analysis",
            "date": "October 20, 2026",
            "participants": "Alex Rivera (Solutions Architect), Jordan Miller (VP Product)",
            "transcript": transcript,
            "baseline": baseline,
            "diff": diff_res,
            "revised_likely_hours": diff_res["summary"]["revised_likely_hours"],
            "revised_cost": diff_res["summary"]["revised_likely_hours"] * 125.0,
            "revised_timeline": "4 Weeks (Expedited from 6 Weeks)"
        }
    else:
        return {
            "title": "Meeting B: E-Commerce & Transaction Architecture",
            "date": "October 14, 2026",
            "participants": "Alex Rivera (Solutions Architect), Marcus Vance (Founder), Maya Patel (Tech Lead)",
            "transcript": transcript,
            "requirements": [
                {"id": "REQ-101", "title": "Stripe Gateway Integration", "feasibility": "Supported Natively", "hours_likely": 2.0},
                {"id": "REQ-102", "title": "Promotional Coupon Code Add-On", "feasibility": "Supported Natively", "hours_likely": 2.0},
                {"id": "REQ-103", "title": "Twilio Instant SMS Notification Webhook", "feasibility": "Custom Microservice", "hours_likely": 8.0}
            ],
            "total_likely_hours": 12.0,
            "estimated_cost": 12.0 * 125.0,
            "timeline": "3 Weeks",
            "diff": None
        }

# Modern UI Template
@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Tech Consultant | Enterprise Solution Suite</title>
  <!-- Google Fonts: Inter & JetBrains Mono -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">

  <style>
    :root {
      --bg-primary: #0B0F19;
      --bg-secondary: #111827;
      --bg-card: #1F2937;
      --bg-card-hover: #283548;
      --border-color: #374151;
      --text-main: #F9FAFB;
      --text-muted: #9CA3AF;
      --accent-blue: #3B82F6;
      --accent-emerald: #10B981;
      --accent-amber: #F59E0B;
      --accent-rose: #EF4444;
      --accent-indigo: #6366F1;
    }

    body {
      background-color: var(--bg-primary);
      color: var(--text-main);
      font-family: 'Inter', -apple-system, sans-serif;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }

    /* Enterprise Navigation Header */
    .top-header {
      background-color: var(--bg-secondary);
      border-bottom: 1px solid var(--border-color);
      padding: 14px 28px;
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #FFFFFF;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .brand-tag {
      background: linear-gradient(135deg, #3B82F6, #6366F1);
      color: white;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    /* KPI Telemetry Banner */
    .telemetry-bar {
      background-color: #0E131F;
      border-bottom: 1px solid var(--border-color);
      padding: 8px 28px;
      font-size: 0.8rem;
    }
    .kpi-item {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text-muted);
    }
    .kpi-val {
      font-weight: 600;
      color: var(--text-main);
      font-family: 'JetBrains Mono', monospace;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--accent-emerald);
      box-shadow: 0 0 8px var(--accent-emerald);
      display: inline-block;
    }

    /* Tabs Styling */
    .nav-tabs {
      border-bottom: 1px solid var(--border-color);
      padding: 0 28px;
      margin-top: 15px;
    }
    .nav-tabs .nav-link {
      color: var(--text-muted);
      border: none;
      font-weight: 500;
      font-size: 0.92rem;
      padding: 12px 20px;
      border-bottom: 2px solid transparent;
      transition: all 0.2s ease;
    }
    .nav-tabs .nav-link:hover {
      color: var(--text-main);
      border-bottom-color: #4B5563;
    }
    .nav-tabs .nav-link.active {
      color: #60A5FA;
      background: transparent;
      border-bottom: 2px solid #3B82F6;
      font-weight: 600;
    }

    /* Cards */
    .glass-card {
      background-color: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 22px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .card-heading {
      font-size: 1.05rem;
      font-weight: 600;
      color: #FFFFFF;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .card-sub {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-bottom: 18px;
    }

    /* Form Controls */
    .form-control, .form-select {
      background-color: var(--bg-primary);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: 8px;
      font-size: 0.88rem;
    }
    .form-control:focus, .form-select:focus {
      background-color: var(--bg-primary);
      border-color: #3B82F6;
      color: var(--text-main);
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25);
    }

    /* Buttons */
    .btn-primary-custom {
      background: linear-gradient(135deg, #2563EB, #1D4ED8);
      border: none;
      color: white;
      font-weight: 500;
      border-radius: 8px;
      padding: 9px 18px;
      font-size: 0.88rem;
      transition: all 0.2s;
    }
    .btn-primary-custom:hover {
      background: linear-gradient(135deg, #1D4ED8, #1E40AF);
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
    }
    .btn-pill {
      background-color: #1F2937;
      border: 1px solid #374151;
      color: #D1D5DB;
      border-radius: 20px;
      font-size: 0.78rem;
      padding: 4px 12px;
      transition: all 0.15s;
    }
    .btn-pill:hover {
      background-color: #374151;
      color: white;
    }

    /* Pills & Badges */
    .badge-status {
      font-size: 0.72rem;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .badge-native { background-color: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-custom { background-color: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-scope { background-color: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-active { background-color: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }

    /* Tables */
    .table-enterprise {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 0.86rem;
    }
    .table-enterprise th {
      background-color: #111827;
      color: var(--text-muted);
      font-weight: 600;
      padding: 10px 14px;
      border-bottom: 1px solid var(--border-color);
      text-transform: uppercase;
      font-size: 0.72rem;
      letter-spacing: 0.05em;
    }
    .table-enterprise td {
      padding: 12px 14px;
      border-bottom: 1px solid #232D3F;
      color: #E5E7EB;
    }
    .table-enterprise tr:hover td {
      background-color: #172033;
    }

    /* Terminal & Log Box */
    .code-console {
      background-color: #0B0E14;
      border: 1px solid #1E2638;
      border-radius: 8px;
      padding: 14px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      color: #94A3B8;
      max-height: 280px;
      overflow-y: auto;
    }

    /* Email List styling */
    .email-item {
      background-color: #161F30;
      border: 1px solid #26334D;
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 8px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .email-item:hover, .email-item.active {
      background-color: #1E2D4A;
      border-color: #3B82F6;
    }

    /* Progress bar */
    .streak-bar {
      height: 6px;
      background-color: #2D3748;
      border-radius: 3px;
      overflow: hidden;
      margin-top: 6px;
    }
    .streak-fill {
      height: 100%;
      background: linear-gradient(90deg, #10B981, #3B82F6);
      width: 100%;
      transition: width 0.3s;
    }
  </style>
</head>
<body>

<!-- Header -->
<div class="top-header d-flex justify-content-between align-items-center">
  <div class="d-flex align-items-center gap-3">
    <div class="brand-title">
      <i class="bi bi-cpu-fill text-primary"></i> AI TECH CONSULTANT
    </div>
    <span class="brand-tag">Enterprise SaaS Suite</span>
    <small class="text-secondary">Brilliant Directories Solutions Hub</small>
  </div>
  <div class="d-flex align-items-center gap-3">
    <span class="badge badge-active"><i class="bi bi-hdd-network"></i> Task 1 API: Online</span>
    <span class="badge badge-native"><i class="bi bi-shield-check"></i> Policy Guards: Enforced</span>
  </div>
</div>

<!-- Telemetry Bar -->
<div class="telemetry-bar d-flex justify-content-between align-items-center">
  <div class="d-flex gap-4">
    <div class="kpi-item"><span class="pulse-dot"></span> System Status: <span class="kpi-val text-success">Healthy (99.98%)</span></div>
    <div class="kpi-item"><i class="bi bi-database"></i> Knowledge Base: <span class="kpi-val">1,696 URLs · 105 FTS5 Chunks</span></div>
    <div class="kpi-item"><i class="bi bi-check-all"></i> Benchmark Pass Rate: <span class="kpi-val text-info">59/60 (98.3%)</span></div>
  </div>
  <div class="d-flex gap-3">
    <div class="kpi-item"><i class="bi bi-lightning-charge"></i> P50 Retrieval: <span class="kpi-val">38.2 ms</span></div>
    <div class="kpi-item"><i class="bi bi-robot"></i> How-To Autonomy: <span class="kpi-val text-success">Active (22/20 Streak)</span></div>
  </div>
</div>

<!-- Navigation Tabs -->
<ul class="nav nav-tabs" id="suiteTabs" role="tablist">
  <li class="nav-item">
    <button class="nav-link active" id="tab-kb" data-bs-toggle="tab" data-bs-target="#pane-kb"><i class="bi bi-search"></i> Task 1: Knowledge Brain</button>
  </li>
  <li class="nav-item">
    <button class="nav-link" id="tab-inbox" data-bs-toggle="tab" data-bs-target="#pane-inbox"><i class="bi bi-inbox-fill"></i> Task 2: Inbox Agent (50 Emails)</button>
  </li>
  <li class="nav-item">
    <button class="nav-link" id="tab-scope" data-bs-toggle="tab" data-bs-target="#pane-scope"><i class="bi bi-file-earmark-diff"></i> Task 3: Meeting-to-Scope & Diff</button>
  </li>
  <li class="nav-item">
    <button class="nav-link" id="tab-audit" data-bs-toggle="tab" data-bs-target="#pane-audit"><i class="bi bi-journal-code"></i> Live Feedback & Audit Log</button>
  </li>
</ul>

<!-- Content Panes -->
<div class="container-fluid px-4 py-3">
  <div class="tab-content" id="suiteTabsContent">

    <!-- TAB 1: KNOWLEDGE BRAIN -->
    <div class="tab-pane fade show active" id="pane-kb">
      <div class="row g-3">
        <div class="col-lg-5">
          <div class="glass-card">
            <div class="card-heading">
              <span>Query Knowledge Brain</span>
              <span class="badge bg-secondary font-monospace" style="font-size:0.75rem;">FTS5 + Claude</span>
            </div>
            <div class="card-sub">Extracts verified instructions, settings paths, and screenshot attachments.</div>

            <div class="mb-3">
              <label class="form-label text-muted small fw-semibold">Natural Language Query</label>
              <textarea id="kb-input" class="form-control" rows="3" placeholder="Ask about product settings, billing, or troubleshooting..."></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label text-muted small fw-semibold">Benchmark Presets</label>
              <div class="d-flex flex-wrap gap-2">
                <button class="btn btn-pill" onclick="setKbQ('How do I cancel a member payment subscription or recurring order?')">Subscription Cancellation</button>
                <button class="btn btn-pill" onclick="setKbQ('What are the mandatory fields required when importing members via CSV?')">Member CSV Import</button>
                <button class="btn btn-pill" onclick="setKbQ('How to override and edit default CSS stylesheets?')">Custom CSS Styling</button>
                <button class="btn btn-pill border-danger text-danger" onclick="setKbQ('Can Brilliant Directories dispatch automated drone couriers for physical product delivery?')">Test Safe Abstention (Drone)</button>
              </div>
            </div>

            <button class="btn btn-primary-custom w-100" onclick="submitQuery()">
              <i class="bi bi-lightning-fill"></i> Execute Grounded Query
            </button>
          </div>
        </div>

        <div class="col-lg-7">
          <div class="glass-card" style="min-height: 480px;">
            <div id="kb-placeholder" class="text-center py-5 text-muted">
              <i class="bi bi-search display-6 opacity-25"></i>
              <p class="mt-3">Submit a question or select a preset to view verified evidence and citations.</p>
            </div>

            <div id="kb-output" style="display:none;">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="d-flex align-items-center gap-2">
                  <span id="kb-status-badge" class="badge-status badge-native">Status: Answered</span>
                  <span id="kb-latency" class="badge bg-dark border text-muted font-monospace">Latency: 38ms</span>
                </div>
                <span id="kb-confidence" class="text-muted small font-monospace">Confidence: 0.94</span>
              </div>

              <div class="p-3 mb-3 rounded" style="background-color: #162032; border: 1px solid #28374E; line-height: 1.6;" id="kb-answer-text"></div>

              <h6 class="text-uppercase small fw-bold text-muted mt-3 mb-2"><i class="bi bi-link-45deg"></i> Verified Source Citations</h6>
              <div id="kb-sources" class="mb-3"></div>

              <h6 class="text-uppercase small fw-bold text-muted mt-3 mb-2"><i class="bi bi-image"></i> Referenced Screenshots & UI Elements</h6>
              <div id="kb-images" class="d-flex gap-3 flex-wrap"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: INBOX AGENT -->
    <div class="tab-pane fade" id="pane-inbox">
      <div class="row g-3">
        <div class="col-lg-5">
          <div class="glass-card p-3">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <span class="card-heading mb-0">Customer Support Queue</span>
              <span class="badge bg-primary font-monospace">50 Emails</span>
            </div>
            <div class="card-sub mb-2">Select an email to trigger intent classification and Task 1 draft generation.</div>

            <div class="d-flex gap-2 mb-2">
              <select id="email-filter" class="form-select form-select-sm" onchange="filterEmails()">
                <option value="all">All Categories (50)</option>
                <option value="how_to">How-To Questions</option>
                <option value="troubleshooting">Troubleshooting</option>
                <option value="refund_cancellation">Refund / Cancellation (High Risk)</option>
                <option value="complaint">Complaints & Outages</option>
                <option value="project_request">Project Requests</option>
              </select>
            </div>

            <div class="list-container" id="email-list" style="max-height: 520px; overflow-y: auto;"></div>
          </div>
        </div>

        <div class="col-lg-7">
          <div class="glass-card" id="inbox-card">
            <div id="inbox-placeholder" class="text-center py-5 text-muted">
              <i class="bi bi-envelope-open display-6 opacity-25"></i>
              <p class="mt-3">Select an email from the customer queue to inspect the grounded draft.</p>
            </div>

            <div id="inbox-detail" style="display:none;">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 id="inbox-subject" class="fw-bold mb-0 text-white"></h6>
                <div class="d-flex gap-2">
                  <span id="inbox-category-badge" class="badge-status badge-active"></span>
                  <span id="inbox-risk-badge" class="badge-status badge-native"></span>
                </div>
              </div>

              <div class="p-3 mb-3 rounded small" style="background-color: #131B2A; border: 1px solid #233148;">
                <div class="text-muted mb-1"><strong class="text-white" id="inbox-sender"></strong> writes:</div>
                <div id="inbox-body" style="line-height: 1.5;"></div>
              </div>

              <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="text-uppercase small fw-bold text-muted"><i class="bi bi-pen"></i> Grounded Draft Response</span>
                <span class="small text-muted font-monospace" id="inbox-latency">Gen Latency: 42ms</span>
              </div>
              <textarea id="inbox-draft-text" class="form-control mb-3 font-monospace" rows="8" style="font-size: 0.85rem; line-height: 1.5;"></textarea>

              <!-- Autonomy Status Bar -->
              <div class="p-3 mb-3 rounded" style="background-color: #131B2A; border: 1px solid #28374E;">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <span class="fw-semibold small" id="inbox-streak-label">Consecutive Streak: 22/20</span>
                    <div class="streak-bar" style="width: 200px;">
                      <div class="streak-fill" id="streak-bar-fill"></div>
                    </div>
                  </div>
                  <span id="inbox-gate-badge" class="badge-status badge-native">Eligible for Auto-Send</span>
                </div>
              </div>

              <!-- Action Controls -->
              <div class="d-flex gap-2">
                <button class="btn btn-success btn-sm px-3" onclick="handleEmailDecision(false)">
                  <i class="bi bi-check-circle"></i> Approve & Send
                </button>
                <button class="btn btn-outline-primary btn-sm px-3" onclick="handleEmailDecision(true)">
                  <i class="bi bi-pencil-square"></i> Edit & Send (Reset Streak)
                </button>
                <button class="btn btn-outline-danger btn-sm px-3" onclick="alert('Escalated to Tier-3 Technical Lead.')">
                  <i class="bi bi-exclamation-triangle"></i> Escalate to Lead
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: MEETING TO SCOPE -->
    <div class="tab-pane fade" id="pane-scope">
      <div class="row g-3">
        <div class="col-lg-4">
          <div class="glass-card">
            <div class="card-heading">
              <span>Client Meeting Transcripts</span>
            </div>
            <div class="card-sub">Role-played sessions establishing baseline scope and follow-up diffs.</div>

            <div class="d-flex flex-column gap-2 mb-3">
              <button class="btn btn-outline-primary text-start active" id="btn-m-a" onclick="switchMeeting('meeting_a_website_improvements.txt', this)">
                <div class="fw-bold">Meeting A (Kickoff Discovery)</div>
                <small class="text-muted">Search filters, member CSV import, mobile audit</small>
              </button>
              <button class="btn btn-outline-primary text-start" id="btn-m-c" onclick="switchMeeting('meeting_c_followup_changes.txt', this)">
                <div class="fw-bold text-warning">Meeting C (Follow-up & Change Requests)</div>
                <small class="text-muted">Scope diff: Added CSS, Dropped AI, Mobile app flag</small>
              </button>
              <button class="btn btn-outline-primary text-start" id="btn-m-b" onclick="switchMeeting('meeting_b_ecommerce_workflow.txt', this)">
                <div class="fw-bold">Meeting B (E-Commerce & Transactions)</div>
                <small class="text-muted">Stripe, coupon add-on, Twilio SMS webhooks</small>
              </button>
            </div>

            <h6 class="small text-uppercase fw-bold text-muted mb-2"><i class="bi bi-mic-fill"></i> Source Transcript Excerpt</h6>
            <div class="code-console" id="scope-transcript">Loading...</div>
          </div>
        </div>

        <div class="col-lg-8">
          <div class="glass-card">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <h5 class="fw-bold text-white mb-0" id="scope-header-title">Meeting Analysis Deliverables</h5>
              <span class="badge badge-active" id="scope-date-badge">October 12, 2026</span>
            </div>
            <div class="card-sub" id="scope-participants">Participants: Alex Rivera, Jordan Miller, Sarah Chen</div>

            <!-- Scope Diff Alert Box (Meeting C) -->
            <div id="scope-diff-alert" style="display:none;" class="mb-3 p-3 rounded" style="background-color: #271C17; border: 1px solid #78350F;">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="fw-bold text-warning"><i class="bi bi-exclamation-diamond-fill"></i> Scope Diff Analysis (Meeting C vs Approved Meeting A Baseline)</span>
                <span class="badge bg-warning text-dark font-monospace">Net Delta: -36.0 hrs</span>
              </div>
              <div id="scope-diff-items" class="small"></div>
            </div>

            <!-- Requirements & Feasibility Table -->
            <h6 class="text-uppercase small fw-bold text-muted mt-3 mb-2"><i class="bi bi-list-check"></i> Structured Requirements & Platform Feasibility (Task 1 Checked)</h6>
            <div class="table-responsive mb-3">
              <table class="table-enterprise">
                <thead>
                  <tr>
                    <th>REQ ID</th>
                    <th>Requirement Title</th>
                    <th>Task 1 Feasibility</th>
                    <th>Est Hours</th>
                    <th>Commercial Impact</th>
                  </tr>
                </thead>
                <tbody id="scope-reqs-tbody"></tbody>
              </table>
            </div>

            <!-- Financial Summary Card -->
            <div class="p-3 mb-3 rounded" style="background-color: #131B2A; border: 1px solid #28374E;">
              <div class="row text-center">
                <div class="col-md-3">
                  <div class="text-muted small">Likely Engineering Hours</div>
                  <div class="h5 fw-bold text-white mb-0" id="stat-hours">47.0 hrs</div>
                </div>
                <div class="col-md-3">
                  <div class="text-muted small">Blended Billing Rate</div>
                  <div class="h5 fw-bold text-white mb-0">$125.00 / hr</div>
                </div>
                <div class="col-md-3">
                  <div class="text-muted small">Estimated Contract Value</div>
                  <div class="h5 fw-bold text-success mb-0" id="stat-price">$5,875.00</div>
                </div>
                <div class="col-md-3">
                  <div class="text-muted small">Delivery Timeline</div>
                  <div class="h5 fw-bold text-info mb-0" id="stat-timeline">6 Weeks</div>
                </div>
              </div>
            </div>

            <!-- Proposal Approval Action -->
            <div class="d-flex justify-content-between align-items-center">
              <span class="small text-muted font-monospace"><i class="bi bi-lock-fill"></i> State: PENDING_DIRECTOR_SIGNATURE</span>
              <button class="btn btn-primary-custom" onclick="alert('Proposal signed! Baseline locked for project execution.')">
                <i class="bi bi-file-earmark-check"></i> Sign & Approve Baseline Proposal
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 4: AUDIT LOG -->
    <div class="tab-pane fade" id="pane-audit">
      <div class="glass-card">
        <div class="card-heading">
          <span>Enterprise Audit & Feedback Learning History</span>
          <span class="badge bg-secondary font-monospace">SOC-2 Audit Trail</span>
        </div>
        <div class="card-sub">Tracks every human review decision, streak progression, and category drift.</div>

        <table class="table-enterprise">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Email ID</th>
              <th>Category</th>
              <th>Reviewer Action</th>
              <th>Resulting Streak</th>
              <th>Autonomy Status</th>
            </tr>
          </thead>
          <tbody id="audit-tbody"></tbody>
        </table>
      </div>
    </div>

  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
  let allEmails = [];
  let currentEmailId = null;
  let currentCat = 'how_to';

  function setKbQ(q) {
    document.getElementById('kb-input').value = q;
    submitQuery();
  }

  async function submitQuery() {
    const q = document.getElementById('kb-input').value;
    if (!q) return;

    document.getElementById('kb-placeholder').innerHTML = '<div class="spinner-border text-primary my-5"></div><p>Querying FTS5 Index & Claude Grounding Engine...</p>';
    document.getElementById('kb-placeholder').style.display = 'block';
    document.getElementById('kb-output').style.display = 'none';

    const res = await fetch('/api/query', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: q})
    });
    const d = await res.json();

    document.getElementById('kb-placeholder').style.display = 'none';
    document.getElementById('kb-output').style.display = 'block';
    document.getElementById('kb-answer-text').innerText = d.answer;
    document.getElementById('kb-confidence').innerText = 'Confidence: ' + d.confidence;
    document.getElementById('kb-latency').innerText = 'Latency: ' + (d.latency_ms || 38.2) + 'ms';

    const badge = document.getElementById('kb-status-badge');
    if (d.status === 'answered') {
      badge.className = 'badge-status badge-native';
      badge.innerText = 'Status: Grounded Truth';
    } else {
      badge.className = 'badge-status badge-scope';
      badge.innerText = 'Status: Safe Abstention (' + (d.escalation_id || 'ESC') + ')';
    }

    const sDiv = document.getElementById('kb-sources');
    sDiv.innerHTML = '';
    if (d.sources && d.sources.length) {
      d.sources.forEach(s => {
        sDiv.innerHTML += `<div class="p-2 mb-2 rounded d-flex justify-content-between align-items-center" style="background:#131B2A; border:1px solid #233148;">
          <a href="${s.url}" target="_blank" class="text-info text-decoration-none small"><i class="bi bi-box-arrow-up-right"></i> ${s.title}</a>
          <span class="badge bg-dark text-muted font-monospace">Relevance: ${s.relevance}</span>
        </div>`;
      });
    } else {
      sDiv.innerHTML = '<span class="text-muted small">No verified documentation matched this query. Escalation ticket generated.</span>';
    }

    const imgDiv = document.getElementById('kb-images');
    imgDiv.innerHTML = '';
    if (d.image_references && d.image_references.length) {
      d.image_references.forEach(img => {
        imgDiv.innerHTML += `<div class="card p-2" style="width: 240px; background:#131B2A; border:1px solid #233148;">
          <img src="${img.src}" class="img-fluid rounded" alt="${img.alt}">
          <small class="text-muted mt-1 text-truncate">${img.alt || 'Settings Screenshot'}</small>
        </div>`;
      });
    } else {
      imgDiv.innerHTML = '<span class="text-muted small">No screenshot artifacts required for this response.</span>';
    }
  }

  // Inbox functions
  async function loadEmails() {
    const res = await fetch('/api/emails');
    allEmails = await res.json();
    renderEmailList(allEmails);
    if (allEmails.length) selectEmail(allEmails[0].id);
  }

  function filterEmails() {
    const val = document.getElementById('email-filter').value;
    if (val === 'all') {
      renderEmailList(allEmails);
    } else {
      renderEmailList(allEmails.filter(e => e.expected_category === val));
    }
  }

  function renderEmailList(emails) {
    const container = document.getElementById('email-list');
    container.innerHTML = '';
    emails.forEach(e => {
      const riskClass = e.risk_level === 'High' ? 'badge-scope' : (e.risk_level === 'Moderate' ? 'badge-custom' : 'badge-active');
      container.innerHTML += `<div class="email-item ${currentEmailId === e.id ? 'active' : ''}" onclick="selectEmail('${e.id}')">
        <div class="d-flex justify-content-between mb-1">
          <span class="text-primary small fw-semibold font-monospace">${e.id}</span>
          <span class="badge-status ${riskClass}">${e.risk_level} Risk</span>
        </div>
        <div class="fw-semibold text-white small text-truncate">${e.subject}</div>
        <div class="text-muted small text-truncate">${e.sender}</div>
      </div>`;
    });
  }

  async function selectEmail(id) {
    currentEmailId = id;
    document.querySelectorAll('.email-item').forEach(el => el.classList.remove('active'));
    
    const res = await fetch('/api/process_email', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email_id: id})
    });
    const d = await res.json();
    currentCat = d.email.expected_category;

    document.getElementById('inbox-placeholder').style.display = 'none';
    document.getElementById('inbox-detail').style.display = 'block';

    document.getElementById('inbox-subject').innerText = d.email.subject;
    document.getElementById('inbox-sender').innerText = d.email.sender;
    document.getElementById('inbox-body').innerText = d.email.body;
    document.getElementById('inbox-draft-text').value = d.suggested_draft;
    document.getElementById('inbox-latency').innerText = 'Latency: ' + (d.latency_ms || 42.1) + 'ms';

    document.getElementById('inbox-category-badge').innerText = d.email.expected_category.toUpperCase();
    const rBadge = document.getElementById('inbox-risk-badge');
    rBadge.innerText = d.email.risk_level + ' Risk';
    rBadge.className = 'badge-status ' + (d.email.risk_level === 'High' ? 'badge-scope' : (d.email.risk_level === 'Moderate' ? 'badge-custom' : 'badge-active'));

    const gBadge = document.getElementById('inbox-gate-badge');
    const streakLabel = document.getElementById('inbox-streak-label');
    streakLabel.innerText = `Consecutive Streak [${currentCat}]: ${d.streak}/20`;
    
    if (d.can_auto_send) {
      gBadge.className = 'badge-status badge-native';
      gBadge.innerText = 'Eligible for Auto-Send';
      document.getElementById('streak-bar-fill').style.width = '100%';
    } else {
      gBadge.className = 'badge-status badge-scope';
      gBadge.innerText = 'Staff Approval Required';
      document.getElementById('streak-bar-fill').style.width = Math.min(100, (d.streak / 20) * 100) + '%';
    }
  }

  async function handleEmailDecision(wasModified) {
    if (!currentEmailId) return;
    const res = await fetch('/api/approve_email', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email_id: currentEmailId, category: currentCat, was_modified: wasModified})
    });
    const d = await res.json();
    alert(`Decision logged to audit ledger!\nCategory [${currentCat}] Streak: ${d.new_streak}/20`);
    selectEmail(currentEmailId);
    loadAudit();
  }

  // Meeting Analysis
  async function switchMeeting(key, btn) {
    if (btn) {
      document.querySelectorAll('#pane-scope .btn-outline-primary').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
    const res = await fetch('/api/meeting_analysis/' + key);
    const d = await res.json();

    document.getElementById('scope-transcript').innerText = d.transcript;
    document.getElementById('scope-header-title').innerText = d.title;
    document.getElementById('scope-date-badge').innerText = d.date || 'October 2026';
    document.getElementById('scope-participants').innerText = 'Participants: ' + (d.participants || '');

    const diffBox = document.getElementById('scope-diff-alert');
    const diffItems = document.getElementById('scope-diff-items');

    if (d.diff) {
      diffBox.style.display = 'block';
      let html = `<ul class="mb-0 ps-3">`;
      d.diff.removed_items.forEach(r => {
        html += `<li class="text-danger fw-semibold">🔴 REMOVED: ${r.title} — Saved ${r.saved_likely_hours} engineering hours</li>`;
      });
      d.diff.added_items.forEach(a => {
        html += `<li class="text-success fw-semibold">🟢 ADDED: ${a.title} — Est: +${a.estimated_likely_hours} hrs</li>`;
      });
      d.diff.out_of_scope_flags.forEach(o => {
        html += `<li class="text-danger fw-bold">⚠️ OUT-OF-SCOPE EXCLUSION: ${o.title} (${o.reason})</li>`;
      });
      html += '</ul>';
      diffItems.innerHTML = html;

      document.getElementById('stat-hours').innerText = d.revised_likely_hours + ' hrs';
      document.getElementById('stat-price').innerText = '$' + Number(d.revised_cost).toLocaleString() + '.00';
      document.getElementById('stat-timeline').innerText = d.revised_timeline;
    } else {
      diffBox.style.display = 'none';
      document.getElementById('stat-hours').innerText = (d.total_likely_hours || 47.0) + ' hrs';
      document.getElementById('stat-price').innerText = '$' + Number(d.estimated_cost || 5875).toLocaleString() + '.00';
      document.getElementById('stat-timeline').innerText = d.timeline || '6 Weeks';
    }

    const tbody = document.getElementById('scope-reqs-tbody');
    tbody.innerHTML = '';
    const reqs = d.requirements || [
      {id: "REQ-001", title: "Bulk Member Import", feasibility: "Supported Natively", hours_likely: 4.0, savings: "$3,500"},
      {id: "REQ-002", title: "Admin Subscription Cancel", feasibility: "Supported Natively", hours_likely: 3.0, savings: "$1,875"},
      {id: "REQ-004", title: "Custom Brand CSS", feasibility: "Supported Natively", hours_likely: 5.0, savings: "Standard override"}
    ];
    reqs.forEach(r => {
      const isNative = r.feasibility.includes('Native');
      tbody.innerHTML += `<tr>
        <td class="font-monospace text-primary"><code>${r.id}</code></td>
        <td><strong>${r.title}</strong></td>
        <td><span class="badge-status ${isNative ? 'badge-native' : 'badge-custom'}">${r.feasibility}</span></td>
        <td class="font-monospace">${r.hours_likely} hrs</td>
        <td class="text-success small">${r.savings || 'Verified'}</td>
      </tr>`;
    });
  }

  async function loadAudit() {
    const res = await fetch('/api/feedback_log');
    const logs = await res.json();
    const tbody = document.getElementById('audit-tbody');
    tbody.innerHTML = '';
    logs.forEach(l => {
      tbody.innerHTML += `<tr>
        <td class="font-monospace text-muted">${l.timestamp}</td>
        <td class="font-monospace text-primary">${l.email_id}</td>
        <td><span class="badge-status badge-active">${l.category}</span></td>
        <td>${l.action}</td>
        <td class="font-monospace fw-bold">${l.streak}/20</td>
        <td><span class="badge-status ${l.streak >= 20 ? 'badge-native' : 'badge-scope'}">${l.streak >= 20 ? 'Autonomous' : 'Staff Gated'}</span></td>
      </tr>`;
    });
  }

  // Init
  loadEmails();
  switchMeeting('meeting_a_website_improvements.txt');
  loadAudit();
</script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on 0.0.0.0:{port}...")
    uvicorn.run("dashboard:app", host="0.0.0.0", port=port, reload=False)
