"""
AgentMail Discord Support Bot

Auto-responds to common questions in #support channel based on FAQ patterns.
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

# Load environment variables
load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Support Bot Configuration
SUPPORT_CHANNEL_ID = int(os.getenv('SUPPORT_CHANNEL_ID', '0'))
TEAM_USERNAMES = os.getenv('TEAM_USERNAMES', '').split(',')
RESPONSE_DELAY_SECONDS = int(os.getenv('RESPONSE_DELAY_SECONDS', '300'))
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
PARTIAL_HINT_THRESHOLD = float(os.getenv('PARTIAL_HINT_THRESHOLD', '0.3'))
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '0'))

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


def calculate_match_score(message: str, faq: dict) -> float:
    """Calculate how well a message matches an FAQ entry."""
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


def find_best_faq_match(message: str, knowledge_base: dict) -> tuple:
    """Find the best matching FAQ for a message.

    Returns: (faq, confidence) or (None, 0.0)
    """
    best_faq = None
    best_score = 0.0

    for faq in knowledge_base.get('faqs', []):
        score = calculate_match_score(message, faq)
        if score > best_score:
            best_score = score
            best_faq = faq

    return (best_faq, best_score) if best_faq else (None, 0.0)


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

    faq, confidence = find_best_faq_match(message.content, knowledge_base)

    if not faq:
        logger.debug(f"No FAQ match for: {message.content[:50]}...")
        return

    logger.info(f"FAQ match: {faq['id']} (confidence: {confidence:.2f}) for: {message.content[:50]}...")

    # High confidence - wait and send full response
    if confidence >= CONFIDENCE_THRESHOLD:
        logger.info(f"Waiting {RESPONSE_DELAY_SECONDS}s before responding...")
        await asyncio.sleep(RESPONSE_DELAY_SECONDS)

        if await check_team_responded(message.channel, message):
            logger.info("Team already responded, skipping auto-response")
            log_support_event({
                'user': message.author.name,
                'user_id': str(message.author.id),
                'question': message.content[:200],
                'matched_faq_id': faq['id'],
                'confidence': round(confidence, 2),
                'action': 'team_first',
                'user_feedback': None,
                'escalated': False
            })
            return

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
    faq, confidence = find_best_faq_match(question, knowledge_base)

    if faq:
        action = "auto_respond" if confidence >= CONFIDENCE_THRESHOLD else \
                 "partial_hint" if confidence >= PARTIAL_HINT_THRESHOLD else "ignore"
        logger.info(f"[TEST] Match: {faq['id']} ({faq.get('category', 'N/A')}) | Confidence: {confidence:.2f} | Action: {action}")
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
