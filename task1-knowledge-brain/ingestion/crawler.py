"""
Resumable, polite sitemap crawler for Brilliant Directories Solution Center.
Tracks manifest state, handles rate limiting, retries, and extracts structured article knowledge.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from task1_knowledge_brain.ingestion.parser import parse_article_html
except ImportError:
    try:
        from ingestion.parser import parse_article_html
    except ImportError:
        import sys
        sys.path.append(str(Path(__file__).resolve().parent))
        from parser import parse_article_html

DEFAULT_SITEMAP = "https://support.brilliantdirectories.com/support/sitemap.xml"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AITechConsultant-Bot/1.0"

class KnowledgeCrawler:
    def __init__(self, base_dir: Path, sitemap_url: str = DEFAULT_SITEMAP):
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.articles_dir = self.data_dir / "articles"
        self.manifest_file = self.data_dir / "ingestion_manifest.json"
        self.sitemap_url = sitemap_url
        
        # Ensure directories exist
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "last_crawled": None,
            "total_urls_discovered": 0,
            "articles": {}  # url -> {lastmod, content_hash, title, status, last_fetched, file}
        }

    def _save_manifest(self):
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2)

    def fetch_sitemap_urls(self) -> List[Dict[str, str]]:
        req = urllib.request.Request(self.sitemap_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            
        root = ET.fromstring(content)
        urls = []
        for child in root:
            loc = child.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            lastmod = child.find("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
            if loc is not None and loc.text:
                url_str = loc.text.strip()
                # Focus on solutions/articles for direct knowledge
                if "/solutions/articles/" in url_str:
                    urls.append({
                        "url": url_str,
                        "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else ""
                    })
        self.manifest["total_urls_discovered"] = len(urls)
        self._save_manifest()
        return urls

    def fetch_page(self, url: str, max_retries: int = 3, delay: float = 0.3) -> Optional[str]:
        headers = {"User-Agent": USER_AGENT}
        for attempt in range(max_retries):
            try:
                time.sleep(delay)
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    if resp.status == 200:
                        return resp.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as e:
                if e.code in [429, 500, 502, 503, 504]:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"Permanent HTTP error {e.code} for {url}")
                    return None
            except Exception as e:
                time.sleep(1)
                continue
        return None

    def crawl(self, limit: int = 20, force_refresh: bool = False) -> Dict[str, Any]:
        urls = self.fetch_sitemap_urls()
        print(f"Found {len(urls)} solution articles in sitemap. Processing batch of up to {limit}...")
        
        stats = {"total_considered": 0, "ingested": 0, "unchanged": 0, "failed": 0}
        
        for item in urls:
            if stats["ingested"] + stats["unchanged"] >= limit:
                break
                
            url = item["url"]
            lastmod = item["lastmod"]
            stats["total_considered"] += 1
            
            existing = self.manifest["articles"].get(url)
            if existing and not force_refresh:
                # Check if lastmod is identical and file exists
                art_file = self.articles_dir / existing.get("file", "")
                if art_file.exists() and existing.get("lastmod") == lastmod and lastmod != "":
                    stats["unchanged"] += 1
                    continue
                    
            # Fetch and parse
            html = self.fetch_page(url)
            if not html:
                stats["failed"] += 1
                self.manifest["articles"][url] = {
                    "status": "failed",
                    "lastmod": lastmod,
                    "last_attempt": time.time()
                }
                continue
                
            parsed = parse_article_html(html, url)
            
            # Create a safe filename
            url_slug = url.rstrip("/").split("/")[-1]
            filename = f"{url_slug}.json"
            file_path = self.articles_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2)
                
            self.manifest["articles"][url] = {
                "title": parsed["title"],
                "lastmod": lastmod,
                "content_hash": parsed["content_hash"],
                "status": "ingested",
                "file": filename,
                "sections_count": len(parsed["sections"]),
                "images_count": len(parsed["images"]),
                "last_fetched": time.time()
            }
            stats["ingested"] += 1
            print(f"[{stats['ingested']}/{limit}] Ingested: {parsed['title'][:50]} ({len(parsed['images'])} images)")
            
        self.manifest["last_crawled"] = time.time()
        self._save_manifest()
        return stats

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    crawler = KnowledgeCrawler(base_dir=base)
    results = crawler.crawl(limit=15)
    print("Crawl results:", results)
