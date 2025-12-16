# export_support.py
import discord
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    channel = client.get_channel(int(os.getenv('SUPPORT_CHANNEL_ID')))
    
    messages = []
    async for msg in channel.history(limit=500):
        messages.append({
            'author': str(msg.author),
            'content': msg.content,
            'timestamp': str(msg.created_at),
            'id': str(msg.id)
        })
    
    with open('support_history.json', 'w') as f:
        json.dump(messages, f, indent=2)
    
    print(f'✅ Exported {len(messages)} messages')
    await client.close()

client.run(os.getenv('DISCORD_BOT_TOKEN'))