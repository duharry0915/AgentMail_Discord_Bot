#!/usr/bin/env python3
"""
Ingest AgentMail knowledge base into Hyperspell vault.
Run once after setup: python ingest_hyperspell.py

Sources (all under knowledge_base/):
- FAQs from knowledge_base.json (project root or knowledge_base/)
- support_insights.md
- pages/**/*.mdx (docs)
- codebase/*.md (API, MCP, SDK, CLI, Console analysis)
"""

import os
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

KB_DIR = Path(__file__).parent / "knowledge_base"


def main():
    api_key = os.getenv("HYPERSPELL_API_KEY")
    user_id = os.getenv("HYPERSPELL_USER_ID", "agentmail-support")
    if not api_key:
        print("ERROR: HYPERSPELL_API_KEY not set in .env")
        sys.exit(1)

    try:
        from hyperspell import Hyperspell
    except ImportError:
        print("ERROR: hyperspell not installed. Run: pip install hyperspell")
        sys.exit(1)

    client = Hyperspell(api_key=api_key, user_id=user_id)
    base = Path(__file__).parent
    items = []

    # 1. FAQs from knowledge_base.json (root or knowledge_base/)
    for faq_path in [base / "knowledge_base.json", KB_DIR / "knowledge_base.json"]:
        if faq_path.exists():
            data = json.loads(faq_path.read_text())
            for faq in data.get("faqs", []):
                text = (
                    f"FAQ [{faq['id']}] {faq.get('category', '')}\n"
                    f"Keywords: {', '.join(faq.get('keywords', []))}\n"
                    f"Q patterns: {faq.get('question_patterns', [])}\n"
                    f"A: {faq['answer']}"
                )
                if faq.get("docs_link"):
                    text += f"\nDocs: {faq['docs_link']}"
                items.append({
                    "text": text,
                    "title": f"faq-{faq['id']}",
                    "metadata": {"collection": "agentmail", "type": "faq"},
                })
            print(f"Loaded {len(data.get('faqs', []))} FAQs")
            break

    # 2. Support insights from knowledge_base/support_insights.md
    insights_path = KB_DIR / "support_insights.md"
    if insights_path.exists():
        content = insights_path.read_text()
        if content.strip():
            items.append({
                "text": content,
                "title": "support_insights",
                "metadata": {"collection": "agentmail", "type": "insights"},
            })
            print("Loaded support_insights.md")

    # 3. Docs from knowledge_base/pages/**/*.mdx (recursive)
    pages_path = KB_DIR / "pages"
    if pages_path.exists():
        doc_files = list(pages_path.rglob("*.mdx"))
        for f in doc_files:
            try:
                content = f.read_text()
                if content.strip():
                    # Use path relative to pages for title (e.g. core-concepts-inboxes)
                    rel = f.relative_to(pages_path)
                    title_slug = str(rel.with_suffix("")).replace("/", "-").replace("\\", "-")
                    items.append({
                        "text": content,
                        "title": f"doc-{title_slug}",
                        "metadata": {"collection": "agentmail", "type": "doc"},
                    })
            except Exception as e:
                print(f"  Skip {f}: {e}")
        print(f"Loaded {len(doc_files)} doc files from pages/")

    # 4. Codebase from knowledge_base/codebase/*.md
    codebase_path = KB_DIR / "codebase"
    if codebase_path.exists():
        codebase_files = list(codebase_path.glob("*.md"))
        for f in codebase_files:
            try:
                content = f.read_text()
                if content.strip():
                    items.append({
                        "text": content,
                        "title": f"codebase-{f.stem}",
                        "metadata": {"collection": "agentmail", "type": "codebase"},
                    })
            except Exception as e:
                print(f"  Skip {f}: {e}")
        print(f"Loaded {len(codebase_files)} codebase files")

    if not items:
        print("No items to ingest.")
        sys.exit(0)

    # Bulk add (100 per batch)
    total = 0
    for i in range(0, len(items), 100):
        batch = items[i : i + 100]
        result = client.memories.add_bulk(items=batch)
        total += result.count
        print(f"  Added batch {i // 100 + 1}: {result.count} items")
        for item in result.items:
            if getattr(item, "status", None) and getattr(item, "status", "") != "success":
                print(f"    Warning: {item.resource_id} - {item.status}")

    print(f"\nDone. Total ingested: {total} items into Hyperspell vault.")


if __name__ == "__main__":
    main()
