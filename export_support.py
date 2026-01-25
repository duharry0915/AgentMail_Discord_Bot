# export_support.py
import discord
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    
    channel = client.get_channel(int(os.getenv('SUPPORT_CHANNEL_ID')))
    print(f'📥 Fetching ALL messages from #{channel.name}...')
    
    messages = []
    async for msg in channel.history(limit=None):  # 获取所有消息
        messages.append({
            'author': str(msg.author),
            'author_id': str(msg.author.id),
            'is_bot': msg.author.bot,
            'content': msg.content,
            'timestamp': str(msg.created_at),
            'id': str(msg.id)
        })
    
    # 按时间排序（oldest first）
    messages.reverse()
    
    # 覆盖旧文件
    with open('support_history.json', 'w', encoding='utf-8') as f:
        json.dump({
            'export_date': str(datetime.now()),
            'message_count': len(messages),
            'messages': messages
        }, f, indent=2, ensure_ascii=False)
    
    print(f'✅ Exported {len(messages)} messages to support_history.json')
    await client.close()

client.run(os.getenv('DISCORD_BOT_TOKEN'))