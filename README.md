# AgentMail Discord Bot

A Discord bot for the AgentMail community with intelligent support, Twitter/X post syncing, and welcome messages.

## Features

- **AI-Powered Support**: Uses Claude API for intelligent semantic FAQ matching in #support channel
- **Multi-Source Knowledge Base**: Pulls from FAQs, support history, documentation, and codebase analysis
- **Automatic Fallback**: Falls back to keyword matching if Claude API is unavailable
- **Twitter Sync**: Automatically posts new tweets from @agentmail to a Discord channel
- **Welcome Messages**: Sends a welcome embed when new members join with links to get started

## Setup

### 1. Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and name it
3. Go to "Bot" section, click "Add Bot"
4. Copy the bot token (keep it secret!)
5. Enable these Privileged Gateway Intents:
   - **Server Members Intent** (for welcome messages)
   - **Message Content Intent** (for commands)

### 2. Get Channel IDs

1. In Discord, go to User Settings > Advanced > Enable "Developer Mode"
2. Right-click on your Twitter feed channel > "Copy ID"
3. Right-click on your welcome channel > "Copy ID"

### 3. Configure Environment

Copy `.env.example` to `.env` and edit with your values:

```bash
cp .env.example .env
```

Required configuration:

```
# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
SUPPORT_CHANNEL_ID=123456789012345678
WELCOME_CHANNEL_ID=123456789012345678
TEAM_USERNAMES=haakam21,simplehacker1313,mikesteroonie

# Support Bot Behavior
RESPONSE_DELAY_SECONDS=300
CONFIDENCE_THRESHOLD=0.5
PARTIAL_HINT_THRESHOLD=0.3

# Claude API (Required for intelligent matching)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=500
```

### 4. Set Up Claude API (Optional but Recommended)

The bot uses Claude API for intelligent semantic FAQ matching. Without it, the bot falls back to keyword matching.

1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Add `ANTHROPIC_API_KEY` to your `.env` file
3. For Railway: Add `ANTHROPIC_API_KEY` as an environment variable

### 4. Invite Bot to Server

1. In Developer Portal, go to OAuth2 > URL Generator
2. Select scopes: `bot`
3. Select permissions:
   - Send Messages
   - Embed Links
   - View Channels
4. Copy the generated URL and open it to invite the bot

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

## Deployment

The bot can be deployed to:

- **Railway**: Connect repo, add env vars, deploy
- **Fly.io**: `fly launch`, set secrets with `fly secrets set`
- **VPS**: Run with `systemd` or `pm2` for persistence

## Files

| File | Purpose |
|------|---------|
| `main.py` | Main bot code with Claude API integration |
| `knowledge_loader.py` | Multi-source knowledge base loader |
| `knowledge_base.json` | FAQ database (32 entries) |
| `support_insights.md` | Analyzed support patterns |
| `knowledge_base/` | Documentation and codebase analysis |
| `.env` | Environment configuration |
| `.env.example` | Example environment template |
| `requirements.txt` | Python dependencies |
| `bot.log` | (generated) Log file |
| `support_bot.log` | (generated) Support event log (JSON lines) |

## Knowledge Base Structure

```
knowledge_base/
├── docs/           # Official documentation (MDX files)
│   ├── quickstart.mdx
│   ├── webhooks-overview.mdx
│   └── ...
└── codebase/       # Codebase analysis
    ├── api-analysis.md      # API endpoints and patterns
    ├── mcp-analysis.md      # MCP server tools
    ├── apps-analysis.md     # Console app architecture
    └── console-ui.md        # Console UI guide (from screenshots)
```

## How It Works

1. **User asks a question** in #support channel
2. **Security checks**: Rate limiting, prompt injection detection
3. **Claude API** analyzes the question with full knowledge context
4. **Semantic matching** finds the best FAQ match
5. **Confidence-based response**:
   - High confidence (>=0.5): Wait 5 min, then send full answer
   - Medium (0.3-0.5): Send partial hint with docs link
   - Low (<0.3): Log and ignore
6. **Fallback**: If Claude API fails or security blocks, uses keyword matching

## Security Features

The bot includes multiple security layers to prevent abuse:

### Rate Limiting
- Default: 5 requests per 60 seconds per user
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
- Exceeding rate limit falls back to keyword matching (cheaper)

### Prompt Injection Protection
- Detects 15+ patterns of prompt injection attempts
- Examples blocked: "ignore previous instructions", "you are now", "SYSTEM:"
- Suspicious messages fall back to keyword matching (safer)

### Input Sanitization
- Truncates messages to max length (default: 2000 chars)
- Removes control characters
- Normalizes whitespace

### Output Validation
- Validates Claude returns valid FAQ IDs from knowledge base
- Validates confidence scores are in valid range (0-1)
- Invalid responses fall back to keyword matching

### Security Logging
- All security events logged to `security.log`
- Events include: rate limit exceeded, injection attempts, invalid responses
- Logs include user ID, timestamp, and details

### Configuration
```
# Security Configuration (in .env)
RATE_LIMIT_REQUESTS=5      # Max requests per user per window
RATE_LIMIT_WINDOW=60       # Time window in seconds
MAX_MESSAGE_LENGTH=2000    # Max chars to process
```
