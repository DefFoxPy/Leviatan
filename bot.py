import discord
from discord.ext import commands
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

# Bot setup with command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    startup_animation()
    print(f'''
╔══════════════════════════════════════╗
║     🎮 Tamagotchi Demócrata 0.0     ║
║      ¡Tu democracia virtual! 🗳️      ║
╚══════════════════════════════════════╝
    
🟢 Bot conectado como: {bot.user}
📊 Presente en {len(bot.guilds)} servidores
🔧 Prefix: !

¡Escribe !ayuda para ver los comandos disponibles!
    ''')
    try:
        setup(bot)
        print('✨ ¡Comandos cargados exitosamente! ✨')
    except Exception as e:
        print(f'❌ Error cargando comandos: {e}')

if __name__ == "__main__":
    try:
        print("\n🚀 Iniciando bot...\n")
        bot.run(TOKEN)
    except Exception as e:
        print(f'❌ Error fatal: {e}')
        print("💡 Tip: ¿Verificaste que el token en .env sea correcto?")