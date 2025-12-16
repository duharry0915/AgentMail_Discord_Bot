# AgentMail Discord Bot

A Discord bot for the AgentMail community with Twitter/X post syncing and welcome messages.

## Features

- **Twitter Sync**: Automatically posts new tweets from @agentmail to a Discord channel (configurable interval)
- **Manual Trigger**: Admin command `!check_tweets` to manually check for new tweets
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

Edit `.env` with your values:

```
DISCORD_BOT_TOKEN=your_bot_token_here
TWITTER_CHANNEL_ID=123456789012345678
WELCOME_CHANNEL_ID=123456789012345678
TWITTER_CHECK_HOURS=24
TWITTER_RSS_USERNAME=agentmail
LOG_LEVEL=INFO
```

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
| `main.py` | Main bot code |
| `.env` | Environment configuration |
| `requirements.txt` | Python dependencies |
| `tweets_cache.json` | (generated) Tracks last posted tweet |
| `bot.log` | (generated) Log file |
