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
APPLICATION_ID = os.getenv('APPLICATION_ID')

# Valores por defecto si no se encuentran en .env
if not TOKEN or not APPLICATION_ID:
    print("⚠️ Configuración no encontrada en .env")
    TOKEN = "TU_TOKEN_AQUI"  # Reemplaza con tu token
    APPLICATION_ID = "TU_APPLICATION_ID_AQUI"  # Reemplaza con tu application ID
    print("ℹ️ Usando valores por defecto")

class Leviathan(commands.Bot):
    """The immortal artificial sovereign, born from the mathematical void."""
    
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            application_id=int(APPLICATION_ID)
        )
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
        # Initialize extensions
        await self.load_extensions()
        
        # Sincronizar comandos inmediatamente después de cargar extensiones
        print("🔄 Sincronizando comandos...")
        await self.tree.sync()
        print("✅ Comandos sincronizados")
        
    async def load_extensions(self):
        """Load all extensions/cogs"""
        # Asegurarse que el directorio cogs existe
        if not os.path.exists("cogs"):
            os.makedirs("cogs")
            print("📁 Creado directorio cogs")

        extensions = [
            'cogs.basic_commands'
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                print(f"✅ {extension} loaded")
            except Exception as e:
                print(f"❌ Error loading {extension}: {str(e)}")
            
    async def on_ready(self):
        print(f"✨ {self.user} está listo!")
        print(f"🔗 ID de Aplicación: {self.application_id}")

bot = Leviathan()

if __name__ == "__main__":
    try:
        print("\n🚀 Iniciando bot...\n")
        bot.run(TOKEN)
    except Exception as e:
        print(f'❌ Error fatal: {e}')
        print("💡 Tip: ¿Verificaste que el token en .env sea correcto?")