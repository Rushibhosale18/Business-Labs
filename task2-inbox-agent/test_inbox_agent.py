"""
Task 2: Inbox Agent Live Output Generator.
Simulates incoming customer emails, calls Task 1 Knowledge Brain for grounded truth,
generates policy-compliant structured drafts, and tracks human review & autonomy.
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Ensure task1 is importable
base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir / "task1-knowledge-brain"))

from app.rag_service import RAGService

class InboxAgent:
    def __init__(self, task1_dir: Path):
        self.rag = RAGService(task1_dir)
        self.consecutive_approvals = {
            "how_to": 19,  # Simulating 19 previous successful consecutive approvals!
            "troubleshooting": 8,
            "refund": 0
        }

    def classify_email(self, email_body: str) -> Dict[str, str]:
        body_lower = email_body.lower()
        if "cancel" in body_lower or "refund" in body_lower:
            if "policy" in body_lower or "money back" in body_lower:
                return {"category": "refund", "risk": "High", "urgency": "High"}
            return {"category": "how_to", "risk": "Low", "urgency": "Medium"}
        elif "import" in body_lower or "csv" in body_lower:
            return {"category": "how_to", "risk": "Low", "urgency": "Medium"}
        elif "broken" in body_lower or "error" in body_lower or "fail" in body_lower:
            return {"category": "troubleshooting", "risk": "Medium", "urgency": "High"}
        else:
            return {"category": "general", "risk": "Low", "urgency": "Low"}

    def process_email(self, sender: str, subject: str, body: str) -> Dict[str, Any]:
        classification = self.classify_email(body)
        cat = classification["category"]
        risk = classification["risk"]
        
        # 1. Call Task 1 Knowledge Brain
        kb_response = self.rag.answer_query(body)
        
        # 2. Formulate grounded response draft
        sources = kb_response.get("sources", [])
        source_links = "\n".join([f"- {s['title']}: {s['url']}" for s in sources])
        
        if kb_response["status"] == "answered":
            draft_text = f"Hello {sender.split('@')[0].capitalize()},\n\nThank you for reaching out to support.\n\n"
            draft_text += f"{kb_response['answer']}\n\n"
            if sources:
                draft_text += f"For full visual guides and step-by-step instructions, please see our documentation:\n{source_links}\n\n"
            draft_text += "Best regards,\nCustomer Support Team"
            needs_expert = False
        else:
            draft_text = f"Hello {sender.split('@')[0].capitalize()},\n\nThank you for reaching out. We are researching this with our senior technical specialists and will follow up shortly."
            needs_expert = True

        # 3. Autonomy rule calculation (20-consecutive rule)
        current_streak = self.consecutive_approvals.get(cat, 0)
        # Note: Financial/Refund emails are permanently gated
        can_auto_send = (current_streak >= 20) and (risk != "High") and not needs_expert

        return {
            "email_id": "EML-LIVE-001",
            "sender": sender,
            "subject": subject,
            "classification": classification,
            "retrieved_knowledge": {
                "status": kb_response["status"],
                "sources": sources,
                "confidence": kb_response.get("confidence", 0.0)
            },
            "generated_draft": draft_text,
            "review_controls": {
                "requires_human_approval": not can_auto_send,
                "reason_for_gate": "Autonomous approval unlocked" if can_auto_send else ("Risk level High" if risk == "High" else f"Consecutive streak ({current_streak}/20)"),
                "consecutive_unmodified_streak": current_streak,
                "autonomy_eligible": can_auto_send
            }
        }

if __name__ == "__main__":
    agent = InboxAgent(base_dir / "task1-knowledge-brain")
    
    print("\n=======================================================")
    print("TASK 2: INBOX AGENT PROCESSED EMAIL OUTPUT")
    print("=======================================================")
    test_email = {
        "sender": "sarah.connor@clientwebsite.com",
        "subject": "Question regarding cancelling member recurring orders",
        "body": "Hi team, how can an administrator cancel a member's payment subscription in the dashboard?"
    }
    output = agent.process_email(test_email["sender"], test_email["subject"], test_email["body"])
    print(json.dumps(output, indent=2))
