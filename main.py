import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')

class Leviatan(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!l",
            intents=discord.Intents.all()
        )
    
    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Loaded extension: {filename}')
                except Exception as e:
                    print(f'Failed to load extension {filename}: {e}')
        
        try:
            await self.tree.sync()
            print("Comandos slash sincronizados")
        except Exception as e:
            print(f"Error al sincronizar comandos: {e}")

    async def on_ready(self):
        print(f'Bot conectado como {self.user}')
        print('------')

async def main():
    bot = Leviatan()
    try:
        await bot.start(TOKEN)
    except discord.errors.LoginFailure:
        print("Error: Token inválido. Por favor verifica tu token.")
    except Exception as e:
        print(f"Error al iniciar el bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
