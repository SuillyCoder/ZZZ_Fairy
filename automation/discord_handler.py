import os, asyncio, sys, discord

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DISCORD_TOKEN, DISCORD_SERVER_ID

MESSAGES_PER_CHANNEL = 3 #Checks the top 3 messages per channel

intents = discord.Intents.default() #Extracts the intent
intents.message_content = True

#Asynchronous function to fetch recent messages
async def fetch_recent_messages() -> list[dict]:
    results = [] #Results in an empty array
    client = discord.Client(intents = intents)

    @client.event
    async def on_ready():
        try: 
            guild = client.get_guild(DISCORD_SERVER_ID)
            if guild is None: #No server of such detected
                try: 
                    guild = await client.fetch_guild(DISCORD_SERVER_ID)
                except discord.NotFound: #Flag an exception if discord client is not found
                    print(f"[Discord]: Server ID {DISCORD_SERVER_ID} not found — is the bot actually in it?")
                    return
                except discord.Forbidden:
                    print(f"[Discord]: No access to server ID {DISCORD_SERVER_ID}.")
                    return
            channels = guild.text_channels if hasattr(guild, "text_channels") else [] #Extract all the text channels present within the server
            if not channels:
                print(f"[Discord]: No text channels found in server '{guild.name}'.")
            
            for channel in channels:
                try:
                    messages = []
                    async for msg in channel.history(limit=MESSAGES_PER_CHANNEL):
                        if msg.author.bot:
                            continue  # Skip messages from other bots
                        messages.append({
                            "channel_name": channel.name,
                            "author": msg.author.display_name,
                            "content": msg.content if msg.content else "[attachment or embed]",
                        })
                    messages.reverse()  # history() is newest-first; flip to chronological order
                    results.extend(messages)
 
                except discord.Forbidden:
                    # No permission to read this specific channel — skip silently
                    print(f"[Discord]: No permission for #{channel.name} — skipping.")
                    continue
                except discord.HTTPException as e:
                    print(f"[Discord]: Could not read #{channel.name}: {e} — skipping.")
                    continue
 
        finally:
            await client.close()  # Always disconnect, even if something above failed
 
    await client.start(DISCORD_TOKEN)
    return results
            
def get_recent_discord_messages() -> str:
    if not DISCORD_TOKEN:
        return "Discord isn't set up yet, Master. Add your bot token to the .env file."
 
    if not DISCORD_SERVER_ID:
        return "No Discord server is configured, Master. Add the server ID to the .env file."
 
    try:
        messages = asyncio.run(fetch_recent_messages())
    except discord.LoginFailure:
        print("[Discord Error]: Invalid bot token.")
        return "My Discord bot token seems invalid, Master. Check your .env file."
    except Exception as e:
        print(f"[Discord Error]: {e}")
        return "I ran into a problem connecting to Discord, Master."
 
    if not messages:
        return "No recent messages anywhere in the server, Master."
 
    # ── Group by channel for a clean, organized spoken summary ──
    by_channel: dict[str, list[dict]] = {}
    for m in messages:
        by_channel.setdefault(m["channel_name"], []).append(m)
 
    spoken_parts = []
    for channel_name, msgs in by_channel.items():
        count = len(msgs)
        if count == 1:
            m = msgs[0]
            spoken_parts.append(f"In {channel_name}, {m['author']} said: {m['content']}")
        else:
            snippet = ". ".join(f"{m['author']} said: {m['content']}" for m in msgs)
            spoken_parts.append(f"In {channel_name}, {count} recent messages: {snippet}")
 
    return " ... ".join(spoken_parts)