"""
FAQ Analyzer for AgentMail Discord Support Bot

Analyzes support_history.json to identify FAQ patterns and help build/update knowledge_base.json.

Usage:
    python faq_analyzer.py

Output:
    - Top keywords in questions
    - Question-answer pairs
    - Suggested FAQ patterns
"""

import json
import re
from collections import Counter
from pathlib import Path

# Configuration
SUPPORT_HISTORY_FILE = Path(__file__).parent / 'support_history.json'
KNOWLEDGE_BASE_FILE = Path(__file__).parent / 'knowledge_base.json'

# Team members (their messages are answers)
TEAM_USERNAMES = ['haakam21', 'mablanc', 'simplehacker1313', 'mikesteroonie', 'harryduu_61189']

# Skip patterns (messages we don't want to learn from)
SKIP_PATTERNS = ['dm you', 'dmed you', 'will look', 'looking into', 'looking now']


def load_support_history() -> list:
    """Load support history from JSON file."""
    if not SUPPORT_HISTORY_FILE.exists():
        print(f"Error: {SUPPORT_HISTORY_FILE} not found")
        return []

    with open(SUPPORT_HISTORY_FILE, 'r') as f:
        return json.load(f)


def is_team_member(author: str) -> bool:
    """Check if author is a team member."""
    return author in TEAM_USERNAMES


def should_skip(content: str) -> bool:
    """Check if message should be skipped."""
    content_lower = content.lower()
    return any(pattern in content_lower for pattern in SKIP_PATTERNS)


def extract_question_answer_pairs(messages: list) -> list:
    """Extract question-answer pairs from message history.

    A pair is: non-team message followed by team response.
    """
    pairs = []

    # Messages are in reverse chronological order, so reverse them
    messages_chrono = list(reversed(messages))

    for i, msg in enumerate(messages_chrono):
        # Skip if team member or empty
        if is_team_member(msg['author']) or not msg['content'].strip():
            continue

        # Look for team response after this message
        for j in range(i + 1, min(i + 5, len(messages_chrono))):
            response = messages_chrono[j]
            if is_team_member(response['author']) and response['content'].strip():
                # Skip if response contains skip patterns
                if should_skip(response['content']):
                    continue

                pairs.append({
                    'question': msg['content'],
                    'question_author': msg['author'],
                    'answer': response['content'],
                    'answer_author': response['author']
                })
                break

    return pairs


def extract_keywords(text: str) -> list:
    """Extract meaningful keywords from text."""
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    # Split and lowercase
    words = text.lower().split()

    # Filter stopwords and short words
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                 'should', 'may', 'might', 'must', 'shall', 'can', 'to', 'of', 'in',
                 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                 'during', 'before', 'after', 'above', 'below', 'between', 'under',
                 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
                 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
                 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'as',
                 'until', 'while', 'this', 'that', 'these', 'those', 'am', 'it', 'its',
                 'my', 'your', 'his', 'her', 'our', 'their', 'what', 'which', 'who',
                 'whom', 'any', 'both', 'im', 'ive', 'dont', 'cant', 'wont', 'isnt',
                 'hi', 'hey', 'hello', 'thanks', 'thank', 'please', 'yes', 'no', 'ok',
                 'okay', 'sure', 'got', 'get', 'getting', 'try', 'trying', 'tried',
                 'using', 'use', 'used', 'want', 'wanted', 'wanting', 'need', 'needed'}

    return [w for w in words if len(w) > 2 and w not in stopwords]


def analyze_questions(pairs: list) -> dict:
    """Analyze questions to find common patterns."""
    all_keywords = []
    question_types = Counter()

    for pair in pairs:
        keywords = extract_keywords(pair['question'])
        all_keywords.extend(keywords)

        # Categorize question types
        q_lower = pair['question'].lower()
        if 'domain' in q_lower:
            if 'pending' in q_lower or 'verify' in q_lower or 'stuck' in q_lower:
                question_types['domain_verification'] += 1
            else:
                question_types['domain_general'] += 1
        elif '404' in q_lower or 'not found' in q_lower:
            question_types['api_error_404'] += 1
        elif 'webhook' in q_lower:
            question_types['webhook'] += 1
        elif 'upgrade' in q_lower or 'paid' in q_lower or 'plan' in q_lower or 'pricing' in q_lower:
            question_types['billing'] += 1
        elif 'free' in q_lower and ('tier' in q_lower or 'plan' in q_lower):
            question_types['free_tier'] += 1
        elif 'profile' in q_lower or 'picture' in q_lower or 'image' in q_lower:
            question_types['profile_picture'] += 1
        elif 'auto' in q_lower and 'reply' in q_lower:
            question_types['auto_reply'] += 1
        elif 'gmail' in q_lower or 'google' in q_lower:
            question_types['gmail_integration'] += 1
        elif 'reply' in q_lower and ('wrong' in q_lower or 'myself' in q_lower):
            question_types['reply_issue'] += 1
        elif 'attachment' in q_lower or 'download' in q_lower:
            question_types['attachment'] += 1
        else:
            question_types['other'] += 1

    return {
        'top_keywords': Counter(all_keywords).most_common(50),
        'question_types': question_types.most_common(20)
    }


def print_sample_pairs(pairs: list, n: int = 10):
    """Print sample question-answer pairs."""
    print("\n" + "="*80)
    print("SAMPLE QUESTION-ANSWER PAIRS")
    print("="*80)

    for i, pair in enumerate(pairs[:n]):
        print(f"\n--- Pair {i+1} ---")
        print(f"Q ({pair['question_author']}): {pair['question'][:200]}...")
        print(f"A ({pair['answer_author']}): {pair['answer'][:200]}...")


def main():
    print("Loading support history...")
    messages = load_support_history()
    print(f"Loaded {len(messages)} messages")

    print("\nExtracting question-answer pairs...")
    pairs = extract_question_answer_pairs(messages)
    print(f"Found {len(pairs)} question-answer pairs")

    print("\nAnalyzing questions...")
    analysis = analyze_questions(pairs)

    print("\n" + "="*80)
    print("TOP 30 KEYWORDS IN QUESTIONS")
    print("="*80)
    for keyword, count in analysis['top_keywords'][:30]:
        print(f"  {keyword}: {count}")

    print("\n" + "="*80)
    print("QUESTION TYPES")
    print("="*80)
    for qtype, count in analysis['question_types']:
        print(f"  {qtype}: {count}")

    print_sample_pairs(pairs, n=15)

    # Check if knowledge base exists
    if KNOWLEDGE_BASE_FILE.exists():
        print("\n" + "="*80)
        print("KNOWLEDGE BASE STATUS")
        print("="*80)
        with open(KNOWLEDGE_BASE_FILE, 'r') as f:
            kb = json.load(f)
        print(f"  FAQs defined: {len(kb.get('faqs', []))}")
        for faq in kb.get('faqs', []):
            print(f"    - {faq['id']}: {faq.get('category', 'N/A')}")

    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print("""
Based on the analysis, consider adding/updating these FAQ categories:

1. Domain verification issues (pending, stuck, DNS)
2. 404 API errors (common cause: free tier limitations)
3. Webhook configuration
4. Billing/upgrade questions
5. Profile picture/avatar setup
6. Auto-reply implementation
7. Gmail/Google Workspace integration
8. Reply going to wrong recipient
9. Attachment download issues

Run the bot with DEBUG logging to see which questions are being matched
and adjust the knowledge_base.json accordingly.
""")


if __name__ == '__main__':
    main()
