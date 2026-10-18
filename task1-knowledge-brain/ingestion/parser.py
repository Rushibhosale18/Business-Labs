"""
Article parser for Brilliant Directories Solution Center.
Extracts title, structured content, breadcrumbs, headings, tables, and image references with surrounding context.
"""
from bs4 import BeautifulSoup
import re
import hashlib
from typing import Dict, List, Any, Optional

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Normalize whitespace and non-breaking spaces
    text = text.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def parse_article_html(html_content: str, url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 1. Extract title
    title = ""
    title_tag = soup.find("h1") or soup.find("title")
    if title_tag:
        title = clean_text(title_tag.get_text())
        
    # 2. Main content container detection
    # Freshdesk uses <article class="article-body">
    article_container = (
        soup.find("article", class_=lambda c: c and "article-body" in c)
        or soup.find("article")
        or soup.find("div", class_=lambda c: c and "article-body" in c)
        or soup.find("main")
        or soup.body
    )
    
    if not article_container:
        return {
            "url": url,
            "title": title or "Brilliant Directories Article",
            "sections": [],
            "full_text": "",
            "images": [],
            "content_hash": ""
        }

    # Extract all relevant structural elements in order
    sections = []
    current_section = {"heading": "Overview", "content": [], "images": []}
    article_images = []
    
    elements = article_container.find_all(["h1", "h2", "h3", "h4", "p", "li", "ol", "ul", "img"])
    for elem in elements:
        if elem.name in ["h1", "h2", "h3", "h4"]:
            h_text = clean_text(elem.get_text())
            if h_text and h_text != title:
                if current_section["content"] or current_section["images"]:
                    sections.append(current_section)
                current_section = {"heading": h_text, "content": [], "images": []}
        elif elem.name in ["p", "li"]:
            p_text = clean_text(elem.get_text())
            # Skip noise like "Was this article helpful?" or "Link: ..."
            if p_text and len(p_text) > 15 and not p_text.startswith("Was this article") and not p_text.startswith("Link:"):
                current_section["content"].append(p_text)
        elif elem.name == "img":
            src = elem.get("src", "")
            alt = elem.get("alt", "")
            if src and not src.endswith(".svg") and "icon" not in src.lower():
                parent_text = clean_text(elem.parent.get_text()) if elem.parent else ""
                img_data = {
                    "src": src,
                    "alt": alt,
                    "context": parent_text[:250],
                    "section": current_section["heading"]
                }
                current_section["images"].append(img_data)
                article_images.append(img_data)

    if current_section["content"] or current_section["images"]:
        sections.append(current_section)

    full_body = "\n\n".join([
        f"### {sec['heading']}\n" + "\n".join(sec['content'])
        for sec in sections if sec['content']
    ])
    
    content_hash = hashlib.sha256(full_body.encode('utf-8')).hexdigest()
    
    return {
        "url": url,
        "title": title or "Brilliant Directories Article",
        "sections": sections,
        "full_text": full_body,
        "images": article_images,
        "content_hash": content_hash
    }
