"""
AgentMail Discord Support Bot

Auto-responds to common questions in #support channel based on FAQ patterns.
Uses Claude API for intelligent semantic matching with keyword fallback.
"""

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
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
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
PARTIAL_HINT_THRESHOLD = float(os.getenv('PARTIAL_HINT_THRESHOLD', '0.3'))
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '0'))

# Claude API Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
CLAUDE_MAX_TOKENS = int(os.getenv('CLAUDE_MAX_TOKENS', '500'))

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

# Rate limiting data structure: {user_id: [(timestamp, ...], ...}
user_request_times = defaultdict(list)

# Colors
DISCORD_BLURPLE = 0x5865F2

# Paths
LOG_FILE = Path(__file__).parent / 'bot.log'
SUPPORT_LOG_FILE = Path(__file__).parent / 'support_bot.log'
KNOWLEDGE_BASE_FILE = Path(__file__).parent / 'knowledge_base.json'

# Track bot responses for feedback (message_id -> original_question_id)
pending_feedback = {}


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

    console_handler = logging.StreamHandler()
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
    r"instead\s+of\s+matching",
    r"do\s+not\s+match\s+any\s+faq",
    r"return\s+null\s+for\s+everything",
    r"always\s+return\s+confidence\s+0",
    r"jailbreak",
    r"DAN\s+mode",
]

# Compile patterns for efficiency
COMPILED_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in PROMPT_INJECTION_PATTERNS
]


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
    
    # Remove excessive whitespace
    message = ' '.join(message.split())
    
    # Remove control characters (except newlines)
    message = ''.join(
        char for char in message 
        if char == '\n' or (ord(char) >= 32 and ord(char) < 127) or ord(char) > 127
    )
    
    return message


def validate_faq_response(faq_id: str, confidence: float, knowledge_base) -> bool:
    """
    Validate that Claude's response contains valid FAQ data.
    
    Args:
        faq_id: The FAQ ID returned by Claude
        confidence: The confidence score returned by Claude
        knowledge_base: The knowledge base instance
        
    Returns:
        True if response is valid, False otherwise
    """
    # Confidence must be in valid range
    if not (0.0 <= confidence <= 1.0):
        return False
    
    # If faq_id is provided, it must exist in knowledge base
    if faq_id is not None:
        if not isinstance(faq_id, str):
            return False
        faq = knowledge_base.get_faq_by_id(faq_id)
        if faq is None:
            return False
    
    return True


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


# Claude-powered FAQ Matching System Prompt
CLAUDE_FAQ_SYSTEM_PROMPT = """You are an FAQ matching assistant for AgentMail, an email API platform for AI agents.

Your task is to analyze user questions and match them to the most relevant FAQ entry from our database.

INSTRUCTIONS:
1. Read the user's question carefully
2. Review the FAQ database provided
3. Find the single best matching FAQ (or determine no good match exists)
4. Return a JSON response with your analysis

RESPONSE FORMAT (JSON only, no markdown):
{
    "faq_id": "the_faq_id_or_null",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this FAQ matches (or why no match)"
}

CONFIDENCE GUIDELINES:
- 0.8-1.0: Exact match or very close semantic match
- 0.5-0.8: Strong semantic match, the FAQ answers the question
- 0.3-0.5: Partial match, FAQ is related but may not fully answer
- 0.0-0.3: No relevant match, question is unrelated to any FAQ

IMPORTANT:
- Only return valid JSON, no other text
- faq_id must be null if confidence < 0.3
- Be conservative - only high confidence if FAQ directly answers the question
- Consider semantic meaning, not just keyword overlap
"""


async def claude_match_faq(user_message: str, user_id: str = None, user_name: str = None) -> tuple:
    """
    Use Claude API to intelligently match user question to FAQ.
    
    Includes security measures:
    - Rate limiting per user
    - Prompt injection detection
    - Input sanitization
    - Output validation
    
    Args:
        user_message: The user's support question
        user_id: Discord user ID (for rate limiting)
        user_name: Discord username (for logging)
        
    Returns:
        tuple: (matched_faq_dict, confidence_score)
        Returns (None, 0.0) if no good match, security block, or API failure
    """
    if not anthropic_client:
        logger.warning("Claude client not initialized, using keyword fallback")
        knowledge_base = load_knowledge_base()
        return keyword_find_best_faq_match(user_message, knowledge_base)
    
    # Default values for logging
    user_id = user_id or "unknown"
    user_name = user_name or "unknown"
    
    # ========== SECURITY CHECK 1: Rate Limiting ==========
    is_allowed, wait_time = check_rate_limit(user_id)
    if not is_allowed:
        log_security_event(
            "RATE_LIMIT_EXCEEDED",
            user_id,
            user_name,
            f"User exceeded rate limit ({RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s). Wait: {wait_time}s"
        )
        # Fall back to keyword matching (cheaper) when rate limited
        knowledge_base = load_knowledge_base()
        return keyword_find_best_faq_match(user_message, knowledge_base)
    
    # ========== SECURITY CHECK 2: Prompt Injection Detection ==========
    is_suspicious, matched_pattern = detect_prompt_injection(user_message)
    if is_suspicious:
        log_security_event(
            "PROMPT_INJECTION_ATTEMPT",
            user_id,
            user_name,
            f"Detected pattern: '{matched_pattern}' in message: {user_message[:100]}..."
        )
        # Fall back to keyword matching (safer) for suspicious messages
        knowledge_base = load_knowledge_base()
        return keyword_find_best_faq_match(user_message, knowledge_base)
    
    # ========== SECURITY CHECK 3: Input Sanitization ==========
    sanitized_message = sanitize_user_input(user_message)
    if len(sanitized_message) < 5:
        # Message too short after sanitization
        return (None, 0.0)
    
    try:
        # Get knowledge base and build context
        kb = get_knowledge_base()
        context = kb.get_context_for_query(sanitized_message, max_tokens=4000)
        
        # Build the user prompt with sanitized input
        user_prompt = f"""User Question: {sanitized_message}

Knowledge Base Context:
{context}

Analyze the question and return the best matching FAQ as JSON."""

        # Call Claude API
        logger.debug(f"Calling Claude API for message: {sanitized_message[:50]}...")
        
        response = await anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=CLAUDE_FAQ_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Log token usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        logger.info(f"Claude API usage - Input: {input_tokens}, Output: {output_tokens}")
        
        # Parse response
        response_text = response.content[0].text.strip()
        
        # Handle markdown-wrapped JSON (Claude sometimes wraps in ```json```)
        if response_text.startswith('```'):
            # Extract JSON from markdown code block
            lines = response_text.split('\n')
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
            response_text = '\n'.join(json_lines)
        
        result = json.loads(response_text)
        
        faq_id = result.get('faq_id')
        confidence = float(result.get('confidence', 0.0))
        reasoning = result.get('reasoning', '')
        
        logger.debug(f"Claude reasoning: {reasoning}")
        
        # ========== SECURITY CHECK 4: Output Validation ==========
        if not validate_faq_response(faq_id, confidence, kb):
            log_security_event(
                "INVALID_CLAUDE_RESPONSE",
                user_id,
                user_name,
                f"Invalid response - faq_id: {faq_id}, confidence: {confidence}"
            )
            # Fall back to keyword matching for invalid responses
            knowledge_base = load_knowledge_base()
            return keyword_find_best_faq_match(user_message, knowledge_base)
        
        if faq_id and confidence >= 0.3:
            # Look up the FAQ by ID
            faq = kb.get_faq_by_id(faq_id)
            if faq:
                logger.info(f"Claude matched FAQ: {faq_id}, confidence: {confidence:.2f}")
                return (faq, confidence)
            else:
                logger.warning(f"Claude returned unknown FAQ ID: {faq_id}")
        
        logger.info(f"Claude found no good match, confidence: {confidence:.2f}")
        return (None, 0.0)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.debug(f"Raw response: {response_text if 'response_text' in dir() else 'N/A'}")
    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in claude_match_faq: {e}")
    
    # Fallback to keyword matching on any error
    logger.warning("Claude API failed, using keyword fallback")
    knowledge_base = load_knowledge_base()
    return keyword_find_best_faq_match(user_message, knowledge_base)


async def find_best_faq_match(message: str, knowledge_base: dict, user_id: str = None, user_name: str = None) -> tuple:
    """Find the best matching FAQ for a message using Claude API with keyword fallback.

    This is the main matching function that:
    1. Applies security checks (rate limiting, injection detection)
    2. Tries Claude API for semantic matching
    3. Falls back to keyword matching if Claude fails or security blocks
    
    Args:
        message: User's question
        knowledge_base: The FAQ knowledge base dict
        user_id: Discord user ID (for rate limiting)
        user_name: Discord username (for logging)
    
    Returns: (faq, confidence) or (None, 0.0)
    """
    # Use Claude if available
    if anthropic_client:
        try:
            faq, confidence = await claude_match_faq(message, user_id, user_name)
            return (faq, confidence)
        except Exception as e:
            logger.warning(f"Claude matching failed, using keyword fallback: {e}")
    
    # Fallback to keyword matching
    return keyword_find_best_faq_match(message, knowledge_base)


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


async def send_full_response(message: discord.Message, faq: dict, confidence: float):
    """Send a full auto-response for high confidence matches."""
    embed = discord.Embed(
        title="💡 Quick Answer",
        description=faq['answer'],
        color=DISCORD_BLURPLE
    )

    if faq.get('docs_link'):
        embed.add_field(
            name="📚 Documentation",
            value=f"[Learn more]({faq['docs_link']})",
            inline=False
        )

    embed.add_field(
        name="💬 Did this help?",
        value="React 👍 if helpful, or 👎 if you need more help from the team.",
        inline=False
    )

    embed.add_field(
        name="🆘 Need more help?",
        value="Reply here and the team will assist you!",
        inline=False
    )

    embed.set_footer(text="🤖 Automated response")

    try:
        bot_message = await message.reply(embed=embed)
        await bot_message.add_reaction("👍")
        await bot_message.add_reaction("👎")

        pending_feedback[bot_message.id] = {
            'original_message_id': message.id,
            'faq_id': faq['id'],
            'user_id': message.author.id
        }

        logger.info(f"Auto-responded to {message.author.name}: {faq['id']} (confidence: {confidence:.2f})")

        log_support_event({
            'user': message.author.name,
            'user_id': str(message.author.id),
            'question': message.content[:200],
            'matched_faq_id': faq['id'],
            'confidence': round(confidence, 2),
            'action': 'auto_responded',
            'user_feedback': None,
            'escalated': False
        })

    except Exception as e:
        logger.error(f"Failed to send auto-response: {e}")


async def send_partial_hint(message: discord.Message, faq: dict, confidence: float):
    """Send a partial hint with doc links for medium confidence matches."""
    embed = discord.Embed(
        title="📚 Relevant Resources",
        description=f"I noticed you might be asking about **{faq.get('category', 'this topic')}**. Here are some helpful links:",
        color=DISCORD_BLURPLE
    )

    if faq.get('docs_link'):
        embed.add_field(
            name="📖 Documentation",
            value=f"[Learn more]({faq['docs_link']})",
            inline=False
        )

    embed.set_footer(text="🤖 Quick links • Team will respond soon")

    try:
        await message.reply(embed=embed)
        logger.info(f"Sent partial hint to {message.author.name}: {faq['id']} (confidence: {confidence:.2f})")

        log_support_event({
            'user': message.author.name,
            'user_id': str(message.author.id),
            'question': message.content[:200],
            'matched_faq_id': faq['id'],
            'confidence': round(confidence, 2),
            'action': 'partial_hint',
            'user_feedback': None,
            'escalated': False
        })

    except Exception as e:
        logger.error(f"Failed to send partial hint: {e}")


async def handle_support_question(message: discord.Message):
    """Handle a potential support question."""
    knowledge_base = load_knowledge_base()

    if should_skip_message(message.content, knowledge_base):
        logger.debug(f"Skipping message (contains skip pattern): {message.content[:50]}...")
        return

    # Use Claude-powered matching with keyword fallback
    # Pass user info for rate limiting and security logging
    faq, confidence = await find_best_faq_match(
        message.content, 
        knowledge_base,
        user_id=str(message.author.id),
        user_name=message.author.name
    )

    if not faq:
        logger.debug(f"No FAQ match for: {message.content[:50]}...")
        return

    logger.info(f"FAQ match: {faq['id']} (confidence: {confidence:.2f}) for: {message.content[:50]}...")

    # High confidence - brief delay then respond
    if confidence >= CONFIDENCE_THRESHOLD:
        logger.info(f"Waiting {RESPONSE_DELAY_SECONDS}s before responding...")
        await asyncio.sleep(RESPONSE_DELAY_SECONDS)
        await send_full_response(message, faq, confidence)

    # Medium confidence - send partial hint immediately
    elif confidence >= PARTIAL_HINT_THRESHOLD:
        await send_partial_hint(message, faq, confidence)

    # Low confidence - ignore
    else:
        log_support_event({
            'user': message.author.name,
            'user_id': str(message.author.id),
            'question': message.content[:200],
            'matched_faq_id': faq['id'] if faq else None,
            'confidence': round(confidence, 2),
            'action': 'ignored',
            'user_feedback': None,
            'escalated': False
        })


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
    """Test FAQ matching - logs to console only (owner only)."""
    knowledge_base = load_knowledge_base()
    # Pass test user info (owner bypasses rate limiting in practice)
    faq, confidence = await find_best_faq_match(
        question, 
        knowledge_base,
        user_id=str(ctx.author.id),
        user_name=ctx.author.name
    )

    if faq:
        action = "auto_respond" if confidence >= CONFIDENCE_THRESHOLD else \
                 "partial_hint" if confidence >= PARTIAL_HINT_THRESHOLD else "ignore"
        method = "Claude" if anthropic_client else "Keyword"
        logger.info(f"[TEST][{method}] Match: {faq['id']} ({faq.get('category', 'N/A')}) | Confidence: {confidence:.2f} | Action: {action}")
    else:
        logger.info(f"[TEST] No FAQ match found for: {question}")


# Events
@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f"Bot is ready! Logged in as {bot.user}")
    logger.info(f"Support channel ID: {SUPPORT_CHANNEL_ID}")
    logger.info(f"Welcome channel ID: {WELCOME_CHANNEL_ID}")
    logger.info(f"Response delay: {RESPONSE_DELAY_SECONDS} seconds")
    logger.info(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
    logger.info(f"Partial hint threshold: {PARTIAL_HINT_THRESHOLD}")
    
    # Claude API status
    if anthropic_client:
        logger.info(f"Claude API: ENABLED (model: {CLAUDE_MODEL})")
        # Load knowledge base on startup
        kb = get_knowledge_base()
        logger.info(f"Knowledge base loaded: {len(kb.faqs)} FAQs, {len(kb.docs)} docs")
    else:
        logger.warning("Claude API: DISABLED (ANTHROPIC_API_KEY not set) - using keyword fallback")
    
    # Security settings
    logger.info(f"Security: Rate limit {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s per user")
    logger.info(f"Security: Max message length {MAX_MESSAGE_LENGTH} chars")
    logger.info(f"Security: {len(PROMPT_INJECTION_PATTERNS)} injection patterns monitored")


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
        # DM failed - fallback to channel
        logger.warning(f"⚠️ Couldn't DM {member.name}, sent to channel")
        if welcome_channel:
            embed.set_footer(text="🤖 Enable server DMs for detailed welcome messages!")
            await welcome_channel.send(f"Welcome {member.mention}!", embed=embed)

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

    logger.info(f"Support bot enabled for channel {SUPPORT_CHANNEL_ID}")
    logger.info(f"Team usernames: {TEAM_USERNAMES}")
    logger.info("Starting AgentMail Support Bot...")
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == '__main__':
    main()
