"""
Chunking and Indexing Engine for Knowledge Brain.
Parses articles, chunks content with hierarchical headings and images,
and populates a SQLite FTS5 full-text + metadata index.
"""
import os
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

class KnowledgeIndexer:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.articles_dir = self.data_dir / "articles"
        self.db_path = self.data_dir / "knowledge_brain.db"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks_meta (
                    chunk_id TEXT PRIMARY KEY,
                    article_url TEXT,
                    article_title TEXT,
                    heading TEXT,
                    content TEXT,
                    image_refs TEXT,
                    content_hash TEXT
                )
            """)
            # FTS5 full-text index
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    article_title,
                    heading,
                    content,
                    tokenize='porter unicode61'
                )
            """)
            conn.commit()

    def chunk_article(self, article_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = []
        url = article_data.get("url", "")
        title = article_data.get("title", "Untitled")
        sections = article_data.get("sections", [])
        
        chunk_idx = 0
        for sec in sections:
            heading = sec.get("heading", "General")
            content_list = sec.get("content", [])
            images = sec.get("images", [])
            
            if not content_list and not images:
                continue
                
            # If section content is short, keep as 1 chunk. If long, split into paragraphs.
            text_block = " ".join(content_list)
            if len(text_block) < 1500:
                chunk_id = f"{url}#{chunk_idx}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "article_url": url,
                    "article_title": title,
                    "heading": heading,
                    "content": text_block,
                    "image_refs": json.dumps(images),
                    "content_hash": article_data.get("content_hash", "")
                })
                chunk_idx += 1
            else:
                # Group every ~2-3 paragraphs
                group = []
                cur_len = 0
                for p in content_list:
                    group.append(p)
                    cur_len += len(p)
                    if cur_len > 1000:
                        chunk_id = f"{url}#{chunk_idx}"
                        chunks.append({
                            "chunk_id": chunk_id,
                            "article_url": url,
                            "article_title": title,
                            "heading": heading,
                            "content": " ".join(group),
                            "image_refs": json.dumps(images),
                            "content_hash": article_data.get("content_hash", "")
                        })
                        chunk_idx += 1
                        group = []
                        cur_len = 0
                if group:
                    chunk_id = f"{url}#{chunk_idx}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "article_url": url,
                        "article_title": title,
                        "heading": heading,
                        "content": " ".join(group),
                        "image_refs": json.dumps(images),
                        "content_hash": article_data.get("content_hash", "")
                    })
                    chunk_idx += 1
        return chunks

    def index_all_articles(self) -> int:
        if not self.articles_dir.exists():
            return 0
            
        all_chunks = []
        for file in self.articles_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    art = json.load(f)
                    chunks = self.chunk_article(art)
                    all_chunks.extend(chunks)
            except Exception as e:
                print(f"Error parsing {file}: {e}")
                
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Clear existing index for clean rebuild
            cursor.execute("DELETE FROM chunks_meta")
            cursor.execute("DELETE FROM chunks_fts")
            
            for c in all_chunks:
                cursor.execute("""
                    INSERT INTO chunks_meta (chunk_id, article_url, article_title, heading, content, image_refs, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (c["chunk_id"], c["article_url"], c["article_title"], c["heading"], c["content"], c["image_refs"], c["content_hash"]))
                
                cursor.execute("""
                    INSERT INTO chunks_fts (chunk_id, article_title, heading, content)
                    VALUES (?, ?, ?, ?)
                """, (c["chunk_id"], c["article_title"], c["heading"], c["content"]))
            conn.commit()
            
        print(f"Indexed {len(all_chunks)} chunks across {len(list(self.articles_dir.glob('*.json')))} articles into FTS5 database.")
        return len(all_chunks)

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    indexer = KnowledgeIndexer(base)
    count = indexer.index_all_articles()
    print(f"Total chunks indexed: {count}")
