"""
FastAPI Server for Knowledge Brain (Task 1).
Provides REST endpoints for querying, ingestion monitoring, and human escalations.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import time

try:
    from app.rag_service import RAGService
    from ingestion.crawler import KnowledgeCrawler
    from retrieval.indexer import KnowledgeIndexer
except ImportError:
    from task1_knowledge_brain.app.rag_service import RAGService
    from task1_knowledge_brain.ingestion.crawler import KnowledgeCrawler
    from task1_knowledge_brain.retrieval.indexer import KnowledgeIndexer

app = FastAPI(
    title="Knowledge Brain API",
    description="Single Source of Truth Knowledge Service for AI Tech Consultant",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent
rag_service = RAGService(BASE_DIR)
crawler = KnowledgeCrawler(BASE_DIR)
indexer = KnowledgeIndexer(BASE_DIR)

class QueryRequest(BaseModel):
    question: str = Field(..., example="How do I connect my Stripe payment gateway?")
    top_k: int = Field(default=4, ge=1, le=10)

class SourceItem(BaseModel):
    title: str
    url: str
    relevance: float

class ImageRef(BaseModel):
    src: str
    alt: Optional[str] = ""
    context: Optional[str] = ""
    section: Optional[str] = ""

class QueryResponse(BaseModel):
    answer: str
    status: str
    sources: List[SourceItem]
    image_references: List[ImageRef]
    confidence: float
    needs_human: bool
    escalation_id: Optional[str] = None

class EscalationResolveRequest(BaseModel):
    human_answer: str
    reviewer: str = "Expert Reviewer"

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Knowledge Brain API",
        "version": "1.0.0"
    }

@app.post("/query", response_model=QueryResponse)
def query_knowledge(req: QueryRequest):
    result = rag_service.answer_query(req.question, top_k=req.top_k)
    return result

@app.post("/ingestion/run")
def trigger_ingestion(background_tasks: BackgroundTasks, limit: int = 20):
    def run_crawl_and_index():
        crawler.crawl(limit=limit)
        indexer.index_all_articles()
        
    background_tasks.add_task(run_crawl_and_index)
    return {"message": f"Ingestion job triggered for up to {limit} articles in background."}

@app.get("/ingestion/status")
def get_ingestion_status():
    manifest = crawler._load_manifest()
    total_indexed = 0
    try:
        import sqlite3
        with sqlite3.connect(indexer.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT count(*) FROM chunks_meta")
            total_indexed = c.fetchone()[0]
    except Exception:
        pass
        
    return {
        "total_urls_discovered": manifest.get("total_urls_discovered", 0),
        "total_crawled_articles": len(manifest.get("articles", {})),
        "total_indexed_chunks": total_indexed,
        "last_crawled": manifest.get("last_crawled")
    }

@app.get("/escalations")
def list_escalations():
    return rag_service._load_escalations()

@app.post("/escalations/{esc_id}/resolve")
def resolve_escalation(esc_id: str, req: EscalationResolveRequest):
    escalations = rag_service._load_escalations()
    found = False
    for esc in escalations:
        if esc["id"] == esc_id:
            esc["status"] = "resolved"
            esc["human_answer"] = req.human_answer
            esc["resolved_by"] = req.reviewer
            esc["resolved_at"] = time.time()
            found = True
            break
            
    if not found:
        raise HTTPException(status_code=404, detail="Escalation ID not found")
        
    rag_service._save_escalations(escalations)
    return {"status": "success", "message": f"Escalation {esc_id} resolved."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
