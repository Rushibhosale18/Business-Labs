"""
Search engine for Knowledge Brain.
Executes BM25 / FTS5 ranking with image context retrieval and score calibration.
"""
import re
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

class KnowledgeSearcher:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _sanitize_query(self, query: str) -> str:
        # Keep alphanumeric and spaces; replace punctuation with space for FTS5
        words = re.findall(r'\b[a-zA-Z0-9_-]+\b', query)
        if not words:
            return ""
        # Match words with prefix wildcard for flexible retrieval
        return " OR ".join([f'"{w}"*' for w in words if len(w) > 2])

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        if not self.db_path.exists():
            return []
            
        sanitized = self._sanitize_query(query)
        if not sanitized:
            return []
            
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # FTS5 bm25 ranking query
            sql = """
                SELECT f.chunk_id, bm25(chunks_fts) as rank, m.article_url, m.article_title, m.heading, m.content, m.image_refs
                FROM chunks_fts f
                JOIN chunks_meta m ON f.chunk_id = m.chunk_id
                WHERE chunks_fts MATCH ?
                ORDER BY rank ASC
                LIMIT ?
            """
            try:
                cursor.execute(sql, (sanitized, top_k))
                rows = cursor.fetchall()
                for row in rows:
                    chunk_id, rank, url, title, heading, content, img_refs_str = row
                    images = []
                    if img_refs_str:
                        try:
                            images = json.loads(img_refs_str)
                        except Exception:
                            pass
                            
                    # Normalize bm25 rank (bm25 is negative in sqlite, lower is better)
                    normalized_relevance = max(0.0, min(1.0, 1.0 / (1.0 + abs(rank) * 0.1)))
                    
                    results.append({
                        "chunk_id": chunk_id,
                        "title": title,
                        "url": url,
                        "heading": heading,
                        "content": content,
                        "relevance": round(normalized_relevance, 3),
                        "images": images
                    })
            except sqlite3.OperationalError as e:
                print(f"FTS5 Query error for '{query}': {e}")
                
        return results

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    db = base / "data" / "knowledge_brain.db"
    searcher = KnowledgeSearcher(db)
    res = searcher.search("stripe payment gateway")
    print("Found:", len(res))
    for r in res:
        print(f"- {r['title']} [{r['relevance']}]: {r['heading']}")
