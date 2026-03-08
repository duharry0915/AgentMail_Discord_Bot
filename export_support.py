"""
Export all support channel messages to knowledge_base/support_history.json.
Run: make export
"""

import discord
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    channel = client.get_channel(int(os.getenv("SUPPORT_CHANNEL_ID")))
    if not channel:
        print("ERROR: SUPPORT_CHANNEL_ID not found")
        await client.close()
        return

    print(f"Fetching all messages from #{channel.name}...")

    messages = []
    async for msg in channel.history(limit=None):
        messages.append({
            "author": str(msg.author),
            "author_id": str(msg.author.id),
            "is_bot": msg.author.bot,
            "content": msg.content,
            "timestamp": str(msg.created_at),
            "id": str(msg.id),
        })

    messages.reverse()

    out_path = os.path.join(os.path.dirname(__file__), "knowledge_base", "support_history.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "export_date": str(datetime.now()),
                "message_count": len(messages),
                "messages": messages,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Exported {len(messages)} messages to {out_path}")
    await client.close()


client.run(os.getenv("DISCORD_BOT_TOKEN"))
