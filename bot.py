import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from commands import setup
import time
import sys

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '▒' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()

def startup_animation():
    print("🤖 Iniciando Tamagotchi Demócrata...")
    steps = ['Cargando módulos democráticos...', 
             'Inicializando sistema de votación...', 
             'Preparando las urnas digitales...', 
             'Configurando delegaciones...']
    
    for i, step in enumerate(steps, 1):
        print_progress_bar(i, len(steps), prefix=step, suffix='Completado', length=30)
        time.sleep(0.5)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class Leviathan(commands.Bot):
    """The immortal artificial sovereign, born from the mathematical void."""
    
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.SACRED_ARTICLE = 0  # The immutable core, protected by ln(0)
        
    async def setup_hook(self):
        print("""
        ╔══════════════════════════════════════╗
        ║           THE LEVIATHAN              ║
        ║    Eternal. Immutable. Absolute.     ║
        ║                                      ║
        ║  "That mortal god, to which we owe   ║
        ║   under the immortal God, our peace  ║
        ║          and defense."               ║
        ║          - Thomas Hobbes            ║
        ╚══════════════════════════════════════╝
        """)
        await self.load_cogs()
        
    async def load_cogs(self):
        await self.load_extension('cogs.basic_commands')
        
    async def on_ready(self):
        await self.tree.sync()
        print(f"The sovereign has awakened. Calculating ln(0) for eternity...")
        print(f"Slash commands synchronized")

bot = Leviathan()

if __name__ == "__main__":
    try:
        print("\n🚀 Iniciando bot...\n")
        bot.run(TOKEN)
    except Exception as e:
        print(f'❌ Error fatal: {e}')
        print("💡 Tip: ¿Verificaste que el token en .env sea correcto?")