# AgentMail Discord Bot

Discord support bot for the AgentMail community. Uses Claude Opus 4.6 + Hyperspell RAG to generate answers from the full knowledge base.

## Features

- **Generative AI Support**: Claude reads retrieved docs/FAQs and generates accurate answers in #support
- **Hyperspell RAG**: Semantic search over 100+ knowledge base documents for context retrieval
- **Keyword Fallback**: Falls back to keyword-based FAQ matching when Claude is unavailable
- **Welcome Messages**: Sends a welcome embed with quick-start links when new members join
- **Security**: Rate limiting, prompt injection detection, input sanitization

## Quick Start

```bash
cp .env.example .env   # fill in your tokens
pip install -r requirements.txt
make ingest            # one-time: populate Hyperspell vault
make run               # start the bot
```

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Bot entry point — Discord events, Claude API, response logic |
| `knowledge_loader.py` | Loads FAQs, docs, codebase analysis into structured context |
| `hyperspell_retriever.py` | Async Hyperspell client for semantic retrieval |
| `ingest_hyperspell.py` | One-time script to ingest knowledge base into Hyperspell |
| `export_support.py` | Export Discord support messages to JSON |
| `faq_analyzer.py` | Analyze support history for FAQ patterns |
| `knowledge_base.json` | Structured FAQ database (43 entries) |
| `knowledge_base/` | Docs (pages/), codebase analysis, support insights |
| `Makefile` | Convenience targets: `run`, `ingest`, `export`, `install` |

## How It Works

1. User asks a question in #support
2. Security checks run (rate limit, injection detection, sanitization)
3. Hyperspell retrieves relevant context from the knowledge vault
4. Claude generates an answer grounded in the retrieved context
5. If confidence >= 0.4, waits for team response window, then sends answer
6. User reacts thumbs-up/down; thumbs-down escalates to team
7. 10-minute per-user cooldown prevents duplicate replies

## Environment Variables

See `.env.example` for all options. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Discord bot token |
| `SUPPORT_CHANNEL_ID` | Yes | Channel ID for support questions |
| `WELCOME_CHANNEL_ID` | No | Channel ID for welcome messages |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `HYPERSPELL_API_KEY` | No | Hyperspell API key for RAG retrieval |

## Deployment

Uses `Procfile` for platforms like Railway:

```
worker: python main.py
```
