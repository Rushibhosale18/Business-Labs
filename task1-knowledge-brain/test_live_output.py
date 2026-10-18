"""
Live demonstration script for Task 1: Knowledge Brain.
Tests a supported product question and an unsupported question (abstention/escalation).
"""
import sys
import json
from pathlib import Path

# Set path
base_dir = Path(__file__).resolve().parent
sys.path.append(str(base_dir))

from app.rag_service import RAGService

def main():
    rag = RAGService(base_dir)
    
    print("\n=======================================================")
    print("TEST 1: Supported Product Question (Cancel Payment Subscriptions)")
    print("=======================================================")
    q1 = "How do I cancel a member payment subscription or recurring order?"
    res1 = rag.answer_query(q1)
    print(json.dumps(res1, indent=2))
    
    print("\n=======================================================")
    print("TEST 2: Supported Question (Mandatory Fields for Member Import)")
    print("=======================================================")
    q2 = "What are the mandatory fields required when importing members via CSV?"
    res2 = rag.answer_query(q2)
    print(json.dumps(res2, indent=2))

    print("\n=======================================================")
    print("TEST 3: Unsupported Question (Safe Abstention & Escalation)")
    print("=======================================================")
    q3 = "Can Brilliant Directories automatically dispatch drone couriers for physical product delivery?"
    res3 = rag.answer_query(q3)
    print(json.dumps(res3, indent=2))

if __name__ == "__main__":
    main()
