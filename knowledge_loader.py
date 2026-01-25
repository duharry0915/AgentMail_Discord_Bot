"""
Knowledge Loader for AgentMail Support Bot

Loads multi-source knowledge base for Claude API integration:
- FAQs from knowledge_base.json
- Support insights from support_insights.md
- Documentation from knowledge_base/docs/
- Codebase analysis from knowledge_base/codebase/
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Multi-source knowledge base for intelligent FAQ matching.
    
    Loads and manages knowledge from:
    - FAQs (structured JSON)
    - Support insights (community patterns)
    - Documentation (official docs)
    - Codebase analysis (API/MCP/Console)
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the knowledge base.
        
        Args:
            base_path: Base directory containing knowledge files.
                      Defaults to the directory containing this file.
        """
        if base_path is None:
            base_path = Path(__file__).parent
        else:
            base_path = Path(base_path)
        
        self.base_path = base_path
        self.faqs = []
        self.faqs_dict = {}  # For quick lookup by ID
        self.support_insights = ""
        self.docs = {}
        self.codebase = {}
        self._loaded = False
    
    def load_all(self) -> None:
        """Load all knowledge sources."""
        if self._loaded:
            return
        
        self._load_faqs()
        self._load_support_insights()
        self._load_docs()
        self._load_codebase()
        
        self._loaded = True
        logger.info(f"Knowledge base loaded: {len(self.faqs)} FAQs, "
                   f"{len(self.docs)} docs, {len(self.codebase)} codebase files")
    
    def _load_faqs(self) -> None:
        """Load FAQs from knowledge_base.json."""
        faq_path = self.base_path / 'knowledge_base.json'
        if faq_path.exists():
            try:
                with open(faq_path, 'r') as f:
                    data = json.load(f)
                    self.faqs = data.get('faqs', [])
                    self.faqs_dict = {faq['id']: faq for faq in self.faqs}
                    logger.info(f"Loaded {len(self.faqs)} FAQs")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load FAQs: {e}")
    
    def _load_support_insights(self) -> None:
        """Load support insights from support_insights.md."""
        insights_path = self.base_path / 'support_insights.md'
        if insights_path.exists():
            try:
                with open(insights_path, 'r') as f:
                    self.support_insights = f.read()
                    logger.info(f"Loaded support insights ({len(self.support_insights)} chars)")
            except IOError as e:
                logger.error(f"Failed to load support insights: {e}")
    
    def _load_docs(self) -> None:
        """Load documentation from knowledge_base/docs/."""
        docs_path = self.base_path / 'knowledge_base' / 'docs'
        if docs_path.exists():
            for file_path in docs_path.glob('*.mdx'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if content.strip():  # Skip empty files
                            self.docs[file_path.stem] = content
                except IOError as e:
                    logger.warning(f"Failed to load doc {file_path.name}: {e}")
            logger.info(f"Loaded {len(self.docs)} documentation files")
    
    def _load_codebase(self) -> None:
        """Load codebase analysis from knowledge_base/codebase/."""
        codebase_path = self.base_path / 'knowledge_base' / 'codebase'
        if codebase_path.exists():
            for file_path in codebase_path.glob('*.md'):
                try:
                    with open(file_path, 'r') as f:
                        self.codebase[file_path.stem] = f.read()
                except IOError as e:
                    logger.warning(f"Failed to load codebase {file_path.name}: {e}")
            logger.info(f"Loaded {len(self.codebase)} codebase analysis files")
    
    def get_faq_by_id(self, faq_id: str) -> Optional[dict]:
        """Get a specific FAQ by its ID."""
        if not self._loaded:
            self.load_all()
        return self.faqs_dict.get(faq_id)
    
    def get_faqs_summary(self) -> str:
        """
        Get a concise summary of all FAQs for Claude context.
        
        Returns a formatted string with FAQ ID, category, and question patterns.
        """
        if not self._loaded:
            self.load_all()
        
        lines = ["## Available FAQs\n"]
        for faq in self.faqs:
            lines.append(f"### {faq['id']} ({faq.get('category', 'General')})")
            lines.append(f"Keywords: {', '.join(faq.get('keywords', []))}")
            lines.append(f"Answer preview: {faq['answer'][:200]}...")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_context_for_query(self, query: str, max_tokens: int = 4000) -> str:
        """
        Build optimized context for Claude based on the user query.
        
        This method constructs a context string that includes:
        1. All FAQs (always included for matching)
        2. Relevant support insights (key sections)
        3. Related documentation (based on query keywords)
        4. Codebase info (if query mentions API/SDK/code)
        
        Args:
            query: The user's question
            max_tokens: Approximate max tokens for context (1 token ≈ 4 chars)
            
        Returns:
            Optimized context string for Claude
        """
        if not self._loaded:
            self.load_all()
        
        context_parts = []
        query_lower = query.lower()
        
        # 1. Always include FAQs (core knowledge)
        faqs_json = json.dumps(self.faqs, indent=2)
        context_parts.append(f"## FAQ Database\n```json\n{faqs_json}\n```\n")
        
        # 2. Include key support insights (common patterns)
        if self.support_insights:
            # Extract the most relevant sections based on query
            insights_sections = self._extract_relevant_sections(
                self.support_insights, 
                query_lower,
                max_chars=2000
            )
            if insights_sections:
                context_parts.append(f"## Support Insights\n{insights_sections}\n")
        
        # 3. Include relevant documentation
        relevant_docs = self._find_relevant_docs(query_lower)
        if relevant_docs:
            docs_content = "\n\n".join([
                f"### {name}\n{content[:1500]}..." 
                for name, content in relevant_docs[:3]  # Limit to 3 most relevant
            ])
            context_parts.append(f"## Relevant Documentation\n{docs_content}\n")
        
        # 4. Include codebase info if query mentions API/SDK/code
        if any(term in query_lower for term in ['api', 'sdk', 'code', 'endpoint', 'mcp', 'console']):
            codebase_info = self._get_relevant_codebase(query_lower)
            if codebase_info:
                context_parts.append(f"## Codebase Information\n{codebase_info[:2000]}\n")
        
        full_context = "\n".join(context_parts)
        
        # Truncate if needed (rough token estimation)
        max_chars = max_tokens * 4
        if len(full_context) > max_chars:
            full_context = full_context[:max_chars] + "\n[Context truncated for length]"
        
        return full_context
    
    def _extract_relevant_sections(self, content: str, query: str, max_chars: int = 2000) -> str:
        """Extract sections from content that are relevant to the query."""
        # Split into sections by ## headers
        sections = []
        current_section = []
        current_header = ""
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections.append((current_header, '\n'.join(current_section)))
                current_header = line
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append((current_header, '\n'.join(current_section)))
        
        # Score sections by relevance to query
        query_words = set(query.split())
        scored_sections = []
        for header, content in sections:
            score = sum(1 for word in query_words if word in content.lower())
            if score > 0:
                scored_sections.append((score, header, content))
        
        # Sort by score and take top sections within char limit
        scored_sections.sort(reverse=True)
        result = []
        total_chars = 0
        for score, header, content in scored_sections:
            if total_chars + len(content) < max_chars:
                result.append(content)
                total_chars += len(content)
        
        return '\n\n'.join(result)
    
    def _find_relevant_docs(self, query: str) -> list:
        """Find documentation files relevant to the query."""
        relevant = []
        
        # Map keywords to doc files
        keyword_map = {
            'webhook': ['webhooks-overview', 'webhook-setup', 'webhooks-events'],
            'inbox': ['inboxes', 'quickstart'],
            'thread': ['threads', 'messages'],
            'message': ['messages', 'sending-receiving-email'],
            'domain': ['custom-domains', 'managing-domains'],
            'attachment': ['attachments'],
            'label': ['labels'],
            'pod': ['pods'],
            'mcp': ['claude-skill'],
            'draft': ['drafts'],
            'deliverability': ['email-deliverability'],
            'smtp': ['imap-smtp'],
            'imap': ['imap-smtp'],
        }
        
        matching_docs = set()
        for keyword, docs in keyword_map.items():
            if keyword in query:
                matching_docs.update(docs)
        
        for doc_name in matching_docs:
            if doc_name in self.docs:
                relevant.append((doc_name, self.docs[doc_name]))
        
        return relevant
    
    def _get_relevant_codebase(self, query: str) -> str:
        """Get relevant codebase information based on query."""
        parts = []
        
        if 'mcp' in query:
            if 'mcp-analysis' in self.codebase:
                parts.append(self.codebase['mcp-analysis'][:1500])
        
        if any(term in query for term in ['api', 'endpoint', 'sdk']):
            if 'api-analysis' in self.codebase:
                parts.append(self.codebase['api-analysis'][:1500])
        
        # Console UI related queries - check for common UI terms
        console_terms = [
            'console', 'dashboard', 'ui', 'interface', 'button', 'click',
            'where', 'find', 'how do i', 'screen', 'page', 'tab', 'modal',
            'create inbox', 'create webhook', 'add domain', 'api key',
            'metrics', 'pods', 'settings'
        ]
        if any(term in query for term in console_terms):
            if 'console-ui' in self.codebase:
                parts.append(self.codebase['console-ui'][:2000])
            elif 'apps-analysis' in self.codebase:
                parts.append(self.codebase['apps-analysis'][:1500])
        
        return '\n\n'.join(parts)


# Singleton instance for the bot
_knowledge_base_instance = None


def get_knowledge_base() -> KnowledgeBase:
    """Get the singleton knowledge base instance."""
    global _knowledge_base_instance
    if _knowledge_base_instance is None:
        _knowledge_base_instance = KnowledgeBase()
        _knowledge_base_instance.load_all()
    return _knowledge_base_instance
