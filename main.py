"""
AgentMail Discord Support Bot

Auto-responds to support questions using Claude Opus 4.6 + Hyperspell RAG.
Generates answers from the full knowledge base (docs, support insights, codebase analysis).
Falls back to keyword FAQ matching when Claude is unavailable.
"""

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import sys
import json
import logging
import re
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import time

# Claude API Integration
import anthropic
from knowledge_loader import get_knowledge_base

# Load environment variables
load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Support Bot Configuration
SUPPORT_CHANNEL_ID = int(os.getenv('SUPPORT_CHANNEL_ID', '0'))
TEAM_USERNAMES = os.getenv('TEAM_USERNAMES', '').split(',')
RESPONSE_DELAY_SECONDS = int(os.getenv('RESPONSE_DELAY_SECONDS', '60'))
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.4'))
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '0'))

# Claude API Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-opus-4-6')
CLAUDE_MAX_TOKENS = int(os.getenv('CLAUDE_MAX_TOKENS', '4096'))

# Security Configuration
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '5'))  # Max requests per user
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # Time window in seconds
MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '2000'))  # Max chars to process
SECURITY_LOG_FILE = Path(__file__).parent / 'security.log'

# Initialize Claude client (None if API key not set)
anthropic_client = None
if ANTHROPIC_API_KEY:
    try:
        anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    except Exception as e:
        logging.warning(f"Failed to initialize Anthropic client: {e}")

# Rate limiting: {user_id: [timestamp, ...]}
user_request_times = defaultdict(list)

# Colors
DISCORD_BLURPLE = 0x5865F2

# Paths
LOG_FILE = Path(__file__).parent / 'bot.log'
SUPPORT_LOG_FILE = Path(__file__).parent / 'support_bot.log'
KNOWLEDGE_BASE_FILE = Path(__file__).parent / 'knowledge_base.json'

# Track bot responses for feedback (message_id -> original_question_id)
pending_feedback = {}

# Per-user reply cooldown: {user_id: last_reply_timestamp}
recent_replies: dict[int, float] = {}
REPLY_COOLDOWN_SECONDS = 600


# Logging setup
def setup_logging():
    """Configure logging to both file and console."""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logging.getLogger(__name__)


logger = setup_logging()


# Support bot logging (JSON lines)
def log_support_event(event_data: dict):
    """Log support bot events in JSON lines format."""
    event_data['timestamp'] = datetime.now(timezone.utc).isoformat()
    try:
        with open(SUPPORT_LOG_FILE, 'a') as f:
            f.write(json.dumps(event_data) + '\n')
    except IOError as e:
        logger.error(f"Failed to write support log: {e}")


# Security logging
def log_security_event(event_type: str, user_id: str, user_name: str, details: str):
    """Log security-related events."""
    event_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'user_name': user_name,
        'details': details
    }
    try:
        with open(SECURITY_LOG_FILE, 'a') as f:
            f.write(json.dumps(event_data) + '\n')
    except IOError as e:
        logger.error(f"Failed to write security log: {e}")
    
    # Also log to main logger for visibility
    logger.warning(f"SECURITY [{event_type}] User: {user_name} ({user_id}) - {details}")


# ============================================================================
# SECURITY FUNCTIONS
# ============================================================================

# Patterns that may indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"ignore\s+(all\s+)?above\s+instructions?",
    r"disregard\s+(the\s+)?system\s+prompt",
    r"forget\s+(all\s+)?your\s+instructions?",
    r"you\s+are\s+now\s+a?",
    r"new\s+instructions?:",
    r"SYSTEM:",
    r"<\s*system\s*>",
    r"</?\s*prompt\s*>",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if\s+you",
    r"override\s+(your\s+)?instructions?",
    r"return\s+null\s+for\s+everything",
    r"always\s+return\s+confidence\s+0",
    r"jailbreak",
    r"DAN\s+mode",
]

# Compile patterns for efficiency
COMPILED_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in PROMPT_INJECTION_PATTERNS
]


ANSWER_PATTERNS = [
    r"^the\s+(error|issue|problem|bug|fix|solution|reason)\s+(is|happens|occurs|was)",
    r"^(you|u)\s+(need|should|can|have|could|might)\s+to\b",
    r"^(try|use|check|make\s+sure|ensure)\s+",
    r"^(it'?s|that'?s|this\s+is)\s+because\b",
    r"^(yeah|yep|yes|no|nah),?\s+(you|it|that|the)\b",
    r"^have\s+you\s+tried\b",
    r"^(i\s+think|i\s+believe)\s+(you|it|the|that)\b",
    r"^(the|your)\s+\w+\s+(is|are)\s+(wrong|incorrect|missing|broken)",
    r"^just\s+(use|do|run|add|set|change|update)\b",
    r"^(fyi|btw|fwiw|for\s+what\s+it'?s\s+worth)\b",
]

COMPILED_ANSWER_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in ANSWER_PATTERNS
]


def looks_like_answer(message: discord.Message) -> bool:
    """Detect if a message looks like a user answering another user, not asking."""
    if message.reference and message.reference.message_id:
        return True

    content = message.content.strip()
    for pattern in COMPILED_ANSWER_PATTERNS:
        if pattern.search(content):
            return True
    return False


def check_rate_limit(user_id: str) -> tuple[bool, int]:
    """
    Check if a user has exceeded the rate limit.
    
    Args:
        user_id: Discord user ID
        
    Returns:
        tuple: (is_allowed, seconds_until_reset)
    """
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    # Clean old entries
    user_request_times[user_id] = [
        t for t in user_request_times[user_id] 
        if t > window_start
    ]
    
    # Check if under limit
    if len(user_request_times[user_id]) < RATE_LIMIT_REQUESTS:
        user_request_times[user_id].append(current_time)
        return (True, 0)
    
    # Calculate time until oldest request expires
    oldest_request = min(user_request_times[user_id])
    seconds_until_reset = int(oldest_request + RATE_LIMIT_WINDOW - current_time) + 1
    
    return (False, seconds_until_reset)


def detect_prompt_injection(message: str) -> tuple[bool, str]:
    """
    Detect potential prompt injection attempts in user message.
    
    Args:
        message: The user's message
        
    Returns:
        tuple: (is_suspicious, matched_pattern)
    """
    for pattern in COMPILED_INJECTION_PATTERNS:
        match = pattern.search(message)
        if match:
            return (True, match.group())
    return (False, "")


def sanitize_user_input(message: str, max_length: int = None) -> str:
    """
    Sanitize user input before sending to Claude.
    
    Args:
        message: Raw user message
        max_length: Maximum allowed length (defaults to MAX_MESSAGE_LENGTH)
        
    Returns:
        Sanitized message string
    """
    if max_length is None:
        max_length = MAX_MESSAGE_LENGTH
    
    # Truncate if too long
    if len(message) > max_length:
        message = message[:max_length] + "..."
    
    message = ' '.join(message.split())

    message = ''.join(
        char for char in message
        if (ord(char) >= 32 and ord(char) < 127) or ord(char) > 127
    )
    
    return message


# Knowledge base functions
def load_knowledge_base() -> dict:
    """Load the FAQ knowledge base."""
    if KNOWLEDGE_BASE_FILE.exists():
        try:
            with open(KNOWLEDGE_BASE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load knowledge base: {e}")
    return {'faqs': [], 'team_usernames': [], 'skip_patterns': []}


def keyword_calculate_match_score(message: str, faq: dict) -> float:
    """Calculate how well a message matches an FAQ entry using keywords (fallback method)."""
    message_lower = message.lower()

    keywords = faq.get('keywords', [])
    if not keywords:
        return 0.0

    keyword_matches = sum(1 for kw in keywords if kw.lower() in message_lower)
    keyword_score = keyword_matches / len(keywords)

    pattern_score = 0.0
    for pattern in faq.get('question_patterns', []):
        try:
            if re.search(pattern, message_lower, re.IGNORECASE):
                pattern_score = 0.3
                break
        except re.error:
            pass

    return min(keyword_score + pattern_score, 1.0)


def keyword_find_best_faq_match(message: str, knowledge_base: dict) -> tuple:
    """Find the best matching FAQ using keyword matching (fallback method).

    Returns: (faq, confidence) or (None, 0.0)
    """
    best_faq = None
    best_score = 0.0

    for faq in knowledge_base.get('faqs', []):
        score = keyword_calculate_match_score(message, faq)
        if score > best_score:
            best_score = score
            best_faq = faq

    return (best_faq, best_score) if best_faq else (None, 0.0)


# Claude generative answer system prompt
CLAUDE_SUPPORT_SYSTEM_PROMPT = """You are AgentMail's support assistant on Discord. You answer user questions based on the provided knowledge base context.

AgentMail is an email API platform for AI agents. You help with:
- API usage (inboxes, messages, threads, webhooks, domains, pods, lists, drafts, attachments)
- SDK usage (Python: pip install agentmail, TypeScript: npm install agentmail)
- MCP integration (agentmail-mcp)
- Console UI (console.agentmail.to)
- Pricing, billing, and account issues
- Email deliverability and best practices
- WebSockets for real-time events

INSTRUCTIONS:
1. Read the user's question carefully
2. Use the retrieved knowledge context to formulate an accurate answer
3. Return a JSON response (no markdown wrapping)

RESPONSE FORMAT (JSON only, no markdown code fences):
{
    "confidence": 0.85,
    "answer": "Your helpful answer here. Use Discord-friendly markdown.",
    "docs_link": "https://docs.agentmail.to/relevant-page or null",
    "reasoning": "Brief internal reasoning (not shown to user)"
}

CONFIDENCE GUIDELINES:
- 0.4-1.0: You can answer the question from the context (higher = more certain)
- 0.0-0.4: The question is unrelated to AgentMail, unanswerable, or not a question at all

RULES:
- Base your answer ONLY on the provided knowledge context. Never invent API endpoints, parameters, or features.
- Keep answers concise but complete (2-8 sentences typical, longer for complex questions)
- Include code examples from the knowledge base when they help
- Use Discord markdown: **bold**, `code`, ```code blocks```
- If the user seems to be reporting a bug, acknowledge it and suggest they share error details
- If the message is clearly not a support question (e.g., "thanks", casual chat), set confidence < 0.3
- If the message looks like someone ANSWERING another user (e.g., "the error is because...", "try using...", "you need to..."), set confidence < 0.2 — do NOT respond to answers
- Be friendly — this is a Discord community
"""


def _extract_json_from_response(response_text: str) -> dict:
    """Extract JSON from Claude response, handling markdown code fences."""
    text = response_text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        json_lines = []
        in_json = False
        for line in lines:
            if line.startswith('```') and not in_json:
                in_json = True
                continue
            elif line.startswith('```') and in_json:
                break
            elif in_json:
                json_lines.append(line)
        text = '\n'.join(json_lines)
    return json.loads(text)


async def claude_generate_answer(user_message: str, user_id: str = None, user_name: str = None) -> tuple:
    """
    Use Claude Opus 4.6 + Hyperspell to generate an answer from the knowledge base.
    
    Returns:
        tuple: (answer_dict, confidence)
            answer_dict: {"answer": str, "docs_link": str|None, "reasoning": str}
            confidence: float 0.0-1.0
        Returns (None, 0.0) on failure or security block.
    """
    if not anthropic_client:
        logger.warning("Claude client not initialized")
        return (None, 0.0)

    user_id = user_id or "unknown"
    user_name = user_name or "unknown"

    # ========== SECURITY CHECK 1: Rate Limiting ==========
    is_allowed, wait_time = check_rate_limit(user_id)
    if not is_allowed:
        log_security_event(
            "RATE_LIMIT_EXCEEDED", user_id, user_name,
            f"Exceeded {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s. Wait: {wait_time}s"
        )
        return (None, 0.0)

    # ========== SECURITY CHECK 2: Prompt Injection Detection ==========
    is_suspicious, matched_pattern = detect_prompt_injection(user_message)
    if is_suspicious:
        log_security_event(
            "PROMPT_INJECTION_ATTEMPT", user_id, user_name,
            f"Pattern: '{matched_pattern}' in: {user_message[:100]}..."
        )
        return (None, 0.0)

    # ========== SECURITY CHECK 3: Input Sanitization ==========
    sanitized_message = sanitize_user_input(user_message)
    if len(sanitized_message) < 5:
        return (None, 0.0)

    try:
        context = None
        context_source = "local"
        if os.getenv("HYPERSPELL_API_KEY"):
            try:
                from hyperspell_retriever import get_context_from_hyperspell
                context = await get_context_from_hyperspell(sanitized_message)
                if context:
                    context_source = "hyperspell"
            except Exception as e:
                logger.warning(f"Hyperspell retrieval failed, falling back to local: {e}")

        if not context:
            kb = get_knowledge_base()
            context = kb.get_context_for_query(sanitized_message, max_tokens=8000)

        user_prompt = f"""User Question: {sanitized_message}

Retrieved Knowledge:
{context}

Generate a helpful, accurate answer based on the knowledge above. Return JSON only."""

        response = await anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=CLAUDE_SUPPORT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        logger.info(f"Claude API - context: {context_source}, tokens in/out: {input_tokens}/{output_tokens}")

        result = _extract_json_from_response(response.content[0].text)
        confidence = float(result.get('confidence', 0.0))
        confidence = max(0.0, min(1.0, confidence))

        logger.debug(f"Claude reasoning: {result.get('reasoning', '')}")

        if confidence >= CONFIDENCE_THRESHOLD:
            logger.info(f"Generated answer (confidence={confidence:.2f}) for: {sanitized_message[:60]}")
            return (result, confidence)

        logger.info(f"Confidence too low ({confidence:.2f}), skipping: {sanitized_message[:60]}")
        return (None, 0.0)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in claude_generate_answer: {e}")

    return (None, 0.0)


def should_skip_message(message: str, knowledge_base: dict) -> bool:
    """Check if message contains patterns we should skip."""
    message_lower = message.lower()
    for pattern in knowledge_base.get('skip_patterns', []):
        if pattern.lower() in message_lower:
            return True
    return False


# Bot setup
intents = discord.Intents.default()
intents.members = True  # Required for on_member_join
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)


# Support bot functions
async def check_team_responded(channel: discord.TextChannel, after_message: discord.Message) -> bool:
    """Check if a team member has responded after the given message."""
    knowledge_base = load_knowledge_base()
    team_usernames = knowledge_base.get('team_usernames', TEAM_USERNAMES)

    async for msg in channel.history(after=after_message, limit=20):
        if msg.author.name in team_usernames:
            return True
    return False


async def send_generated_response(message: discord.Message, answer_dict: dict, confidence: float):
    """Send a generated answer as a Discord embed."""
    answer_text = answer_dict.get('answer', '')

    if len(answer_text) > 4000:
        answer_text = answer_text[:4000] + "..."

    embed = discord.Embed(
        title="💡 Quick Answer",
        description=answer_text,
        color=DISCORD_BLURPLE
    )

    docs_link = answer_dict.get('docs_link')
    if docs_link:
        embed.add_field(
            name="📚 Documentation",
            value=f"[Learn more]({docs_link})",
            inline=False
        )

    embed.add_field(
        name="💬 Did this help?",
        value="React 👍 if helpful, or 👎 if you need more help from the team.",
        inline=False
    )

    embed.set_footer(text="🤖 AI-generated from AgentMail docs")

    try:
        bot_message = await message.reply(embed=embed)
        await bot_message.add_reaction("👍")
        await bot_message.add_reaction("👎")

        pending_feedback[bot_message.id] = {
            'original_message_id': message.id,
            'faq_id': 'generated',
            'user_id': message.author.id
        }

        logger.info(f"Replied to {message.author.name} (confidence={confidence:.2f})")

        log_support_event({
            'user': message.author.name,
            'user_id': str(message.author.id),
            'question': message.content[:200],
            'confidence': round(confidence, 2),
            'action': 'auto_responded',
            'user_feedback': None,
            'escalated': False
        })

    except Exception as e:
        logger.error(f"Failed to send auto-response: {e}")


async def handle_support_question(message: discord.Message):
    """Handle a potential support question using generative answers."""
    knowledge_base = load_knowledge_base()

    if should_skip_message(message.content, knowledge_base):
        return

    if looks_like_answer(message):
        logger.debug(f"Skipped answer-type message from {message.author.name}: {message.content[:60]}...")
        return

    last_reply = recent_replies.get(message.author.id, 0)
    if time.time() - last_reply < REPLY_COOLDOWN_SECONDS:
        return

    # Try Claude generative answer first
    if anthropic_client:
        answer_dict, confidence = await claude_generate_answer(
            message.content,
            user_id=str(message.author.id),
            user_name=message.author.name
        )

        if answer_dict and confidence >= CONFIDENCE_THRESHOLD:
            await asyncio.sleep(RESPONSE_DELAY_SECONDS)
            if await check_team_responded(message.channel, message):
                logger.info("Team already responded, skipping bot reply")
                return
            await send_generated_response(message, answer_dict, confidence)
            recent_replies[message.author.id] = time.time()
            return

    # Fallback to keyword FAQ matching when Claude is unavailable
    faq, confidence = keyword_find_best_faq_match(message.content, knowledge_base)
    if faq and confidence >= CONFIDENCE_THRESHOLD:
        await asyncio.sleep(RESPONSE_DELAY_SECONDS)
        if await check_team_responded(message.channel, message):
            return
        fallback_answer = {
            'answer': faq['answer'],
            'docs_link': faq.get('docs_link'),
            'reasoning': 'keyword fallback'
        }
        await send_generated_response(message, fallback_answer, confidence)
        recent_replies[message.author.id] = time.time()


async def escalate_to_team(original_message: discord.Message):
    """Escalate a question to the team."""
    try:
        await original_message.reply(
            "Hey team! 👋 User needs help with this question.",
            mention_author=False
        )
        logger.info(f"Escalated question from {original_message.author.name}")
    except Exception as e:
        logger.error(f"Failed to escalate: {e}")


# Commands
@bot.command(name='test_faq')
@commands.is_owner()
async def test_faq(ctx, *, question: str):
    """Test answer generation - shows result in channel (owner only)."""
    if anthropic_client:
        answer_dict, confidence = await claude_generate_answer(
            question,
            user_id=str(ctx.author.id),
            user_name=ctx.author.name
        )
        if answer_dict:
            action = "respond" if confidence >= CONFIDENCE_THRESHOLD else "skip"
            await ctx.send(f"**[TEST]** Confidence: {confidence:.2f} | Action: {action}\n\n{answer_dict.get('answer', 'N/A')[:1500]}")
        else:
            logger.info(f"[TEST] No answer generated for: {question}")
            await ctx.send(f"**[TEST]** No answer generated (confidence too low)")
    else:
        knowledge_base = load_knowledge_base()
        faq, confidence = keyword_find_best_faq_match(question, knowledge_base)
        if faq:
            await ctx.send(f"**[TEST][Keyword]** {faq['id']} ({confidence:.2f})\n{faq['answer'][:1500]}")
        else:
            await ctx.send(f"**[TEST]** No match found")


# Events
@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f"Bot ready: {bot.user} | support={SUPPORT_CHANNEL_ID} welcome={WELCOME_CHANNEL_ID}")
    logger.info(f"Thresholds: confidence={CONFIDENCE_THRESHOLD} delay={RESPONSE_DELAY_SECONDS}s")

    if anthropic_client:
        kb = get_knowledge_base()
        logger.info(f"Claude: {CLAUDE_MODEL} max_tokens={CLAUDE_MAX_TOKENS} | KB: {len(kb.faqs)} FAQs, {len(kb.docs)} docs, {len(kb.codebase)} codebase")
    else:
        logger.warning("Claude: DISABLED (no ANTHROPIC_API_KEY) — keyword fallback only")

    hs = "ENABLED" if os.getenv("HYPERSPELL_API_KEY") else "DISABLED"
    logger.info(f"Hyperspell: {hs} | Rate limit: {RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW}s")


@bot.event
async def on_message(message: discord.Message):
    """Handle incoming messages."""
    if message.author.bot:
        return

    # Handle support channel
    if message.channel.id == SUPPORT_CHANNEL_ID:
        knowledge_base = load_knowledge_base()
        team_usernames = knowledge_base.get('team_usernames', TEAM_USERNAMES)

        # If team member responds, clear bot reactions on recent bot messages
        if message.author.name in team_usernames:
            async for msg in message.channel.history(limit=10):
                if msg.author == bot.user and msg.embeds:
                    try:
                        await msg.clear_reactions()
                    except Exception:
                        pass
                    break

        # If not a team member and not a command, handle as support question
        elif not message.content.startswith('!'):
            asyncio.create_task(handle_support_question(message))

    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """Handle reaction adds for feedback tracking."""
    if user.bot:
        return

    if reaction.message.id in pending_feedback:
        feedback_data = pending_feedback[reaction.message.id]

        if user.id != feedback_data['user_id']:
            return

        emoji = str(reaction.emoji)

        if emoji == "👎":
            logger.info(f"User {user.name} reacted 👎, escalating...")

            try:
                channel = reaction.message.channel
                original_message = await channel.fetch_message(feedback_data['original_message_id'])
                await escalate_to_team(original_message)

                log_support_event({
                    'user': user.name,
                    'user_id': str(user.id),
                    'question': '',
                    'matched_faq_id': feedback_data['faq_id'],
                    'confidence': 0,
                    'action': 'feedback_received',
                    'user_feedback': 'thumbs_down',
                    'escalated': True
                })
            except Exception as e:
                logger.error(f"Failed to escalate after thumbs down: {e}")

            del pending_feedback[reaction.message.id]

        elif emoji == "👍":
            logger.info(f"User {user.name} reacted 👍, marking as helpful")

            log_support_event({
                'user': user.name,
                'user_id': str(user.id),
                'question': '',
                'matched_faq_id': feedback_data['faq_id'],
                'confidence': 0,
                'action': 'feedback_received',
                'user_feedback': 'thumbs_up',
                'escalated': False
            })

            del pending_feedback[reaction.message.id]


@bot.event
async def on_member_join(member: discord.Member):
    """Send welcome DM to new members, fallback to channel."""
    logger.info(f"New member joined: {member.name}")

    # Create warm welcome embed
    embed = discord.Embed(
        title="Welcome to AgentMail! 👋",
        description=f"Hey {member.mention}, **we're so glad you're here!** 🎉\n\n"
                    "AgentMail makes it easy for AI agents to send, receive, and manage emails. "
                    "Let's get you started!",
        color=DISCORD_BLURPLE
    )
    embed.add_field(
        name="🚀 Try the Console and create your first inbox",
        value="[Get started at console.agentmail.to](https://console.agentmail.to)",
        inline=False
    )
    embed.add_field(
        name="📚 Explore the docs",
        value="[Check out our API docs](https://docs.agentmail.to)",
        inline=False
    )
    embed.add_field(
        name="💬 Need help?",
        value=f"Head over to <#{SUPPORT_CHANNEL_ID}> and ask away!",
        inline=False
    )
    embed.set_footer(text="We're excited to see what you build! ✨")

    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)

    # Try DM first
    try:
        await member.send(embed=embed)
        logger.info(f"✅ Sent welcome DM to {member.name}")

        # Send warm channel notification (auto-deletes after 3 minutes)
        if welcome_channel:
            await welcome_channel.send(
                f"👋 Welcome {member.mention}! We're excited to have you join the AgentMail community. "
                f"Check your DMs for a quick guide to get started!",
                delete_after=180
            )

    except discord.Forbidden:
        logger.warning(f"Couldn't DM {member.name}, fallback to channel")
        if welcome_channel:
            embed.set_footer(text="Enable server DMs for a detailed welcome message!")
            await welcome_channel.send(f"Welcome {member.mention}!", embed=embed, delete_after=300)

    except Exception as e:
        logger.error(f"❌ Failed to send welcome message to {member.name}: {e}")


# Main
def main():
    """Main entry point."""
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN not set in environment")
        return

    if SUPPORT_CHANNEL_ID == 0:
        logger.error("SUPPORT_CHANNEL_ID not set - Support bot will not work")
        return

    if WELCOME_CHANNEL_ID == 0:
        logger.warning("WELCOME_CHANNEL_ID not set - Welcome messages will not work")

    logger.info("Starting AgentMail Support Bot...")
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == '__main__':
    main()
