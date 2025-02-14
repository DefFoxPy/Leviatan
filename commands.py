import discord
from discord import app_commands
from discord.ext import commands
from discord import Embed, Color
from typing import Dict, Optional
from delegation import DelegationSystem
from voting import VotingSystem, ProposalState
from visualization import VoterVisualization, VoteType
from datetime import datetime
import pandas as pd
import json

delegation_system = DelegationSystem()
voting_system = VotingSystem()

# Agregar descripción de comandos slash
help_descriptions = {
    "delegar": "Delega puntos de votación a otro usuario",
    "revocar": "Revoca la delegación a un usuario y recupera tus puntos",
    "proponer": "Inicia el proceso de crear una nueva propuesta",
    "articulo": "Añade un artículo a una propuesta existente",
    "requisitos": "Muestra los requisitos de votación para un artículo",
    "perfil": "Muestra tu perfil de votante y estadísticas",
    "arbol": "Visualiza tu árbol de delegación o tubérculo",
    "analisis": "Analiza el estado del sistema (Admin)",
    "exportar": "Exporta datos del sistema para análisis (Admin)",
    "simulacion": "Ejecuta simulaciones del sistema (Admin)",
    "modificar": "Propone una modificación a un artículo",
    "votar_mod": "Vota en una modificación propuesta",
    "delegar_debate": "Delega puntos durante el debate",
    "comprometer": "Compromete más puntos al debate"
}

class DelegationCommands(commands.Cog):
    """Comandos para el sistema de delegación de votos"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(
        name="delegar",
        description=help_descriptions["delegar"]
    )
    @app_commands.describe(
        to_user="Usuario al que quieres delegar",
        points="Cantidad de puntos a delegar",
        subdelegable="Permitir que el usuario pueda subdelegar estos puntos"
    )
    async def delegate_slash(self, interaction: discord.Interaction, to_user: str, points: int, subdelegable: bool = False):
        """Delega puntos a otro usuario
        Uso: !delegar @usuario 500 [True/False]"""
        success = delegation_system.delegate_points(
            str(interaction.user.id), 
            to_user.strip('<@!>'), 
            points, 
            subdelegable
        )
        
        if success:
            embed = Embed(
                title="✅ Delegación Exitosa",
                description=f"Has delegado {points} puntos a {to_user}",
                color=Color.green()
            )
        else:
            embed = Embed(
                title="❌ Error en Delegación",
                description="No tienes suficientes puntos o el usuario no existe",
                color=Color.red()
            )
            
        await interaction.response.send_message(embed=embed)

    @commands.command(name='revocar')
    async def revoke(ctx, target: discord.Member):
        """Revoca la delegación a un usuario y recupera todos los puntos subdelegados"""
        success, points = delegation_system.revoke_delegation(
            str(ctx.author.id), 
            str(target.id)
        )
        
        if success:
            embed = discord.Embed(
                title="Delegación Revocada",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Puntos Recuperados", 
                value=f"Has recuperado {points} puntos en total (incluyendo subdelegaciones)"
            )
        else:
            embed = discord.Embed(
                title="Error",
                description="No tienes una delegación activa con este usuario.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

class ProposalCommands(commands.Cog):
    """Comandos para gestionar propuestas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.drafts: Dict[str, Dict] = {}
        
    @app_commands.command(
        name="proponer",
        description=help_descriptions["proponer"]
    )
    async def start_proposal_slash(self, interaction: discord.Interaction):
        """Inicia el proceso de crear una propuesta
        Uso: !proponer"""
        embed = Embed(
            title="🗳️ Nueva Propuesta",
            description="Iniciemos el proceso de creación.\nResponde con el título de tu propuesta.",
            color=Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
            
        try:
            title_msg = await self.bot.wait_for('message', timeout=300.0, check=check)
            proposal_id = voting_system.create_proposal(str(interaction.user.id), title_msg.content, 100)
            
            embed = Embed(
                title="✅ Propuesta Creada",
                description=f"ID: {proposal_id}\nTítulo: {title_msg.content}\n\nUsa !articulo {proposal_id} para añadir artículos.",
                color=Color.green()
            )
            await interaction.followup.send(embed=embed)
            
        except TimeoutError:
            await interaction.followup.send("⌛ Tiempo agotado. Intenta crear la propuesta nuevamente.")

    @app_commands.command(
        name="requisitos",
        description=help_descriptions["requisitos"]
    )
    @app_commands.describe(
        article_id="ID del artículo"
    )
    async def requisitos_slash(self, interaction: discord.Interaction, article_id: int):
        """Muestra requisitos de votación para un artículo"""
        reqs = self.voting.calculate_requirements(article_id)
        if not reqs:
            await interaction.response.send_message("❌ Artículo no encontrado")
            return

        metadata = self.voting.get_article_metadata(article_id)
        
        embed = discord.Embed(title=f"Requisitos para Artículo {article_id}")
        
        if article_id == 0:
            embed.description = "⚠️ Este artículo es matemáticamente inmutable (ln(0) = -∞)"
            embed.color = discord.Color.red()
        else:
            embed.add_field(
                name="Votos Necesarios",
                value=f"{reqs['required_votes']:.2f}",
                inline=True
            )
            embed.add_field(
                name="Participación Mínima",
                value=f"{reqs['min_participation']:.2f}",
                inline=True
            )
            embed.add_field(
                name="Base",
                value=str(reqs['base']),
                inline=True
            )
            embed.add_field(
                name="Última Modificación",
                value=metadata['last_modification'],
                inline=False
            )
            embed.color = discord.Color.blue()
            
        await interaction.response.send_message(embed=embed)

class InfoCommands(commands.Cog):
    """Comandos de información y ayuda"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="perfil")
    async def show_profile(self, ctx):
        """Muestra tu perfil de votante
        Uso: !perfil"""
        voter = delegation_system.voters.get(str(ctx.author.id))
        if not voter:
            await ctx.send("❌ No estás registrado como votante.")
            return
            
        subdelegable, no_subdelegable = voter.get_total_voting_power()
        embed = Embed(
            title=f"Perfil de {ctx.author.name}",
            color=Color.blue()
        )
        embed.add_field(
            name="🎯 Puntos Base",
            value=str(voter.base_points),
            inline=True
        )
        embed.add_field(
            name="📊 Puntos Disponibles",
            value=str(voter.available_points),
            inline=True
        )
        embed.add_field(
            name="🔄 Puntos Subdelegables",
            value=str(subdelegable),
            inline=True
        )
        
        # Mostrar delegaciones si existen
        if voter.delegations:
            delegations_text = "\n".join(
                f"→ <@{delegate_id}>: {details['points']} pts ({'↪️' if details['subdelegable'] else '🔒'})"
                for delegate_id, details in voter.delegations.items()
            )
            embed.add_field(
                name="📤 Delegaciones Realizadas",
                value=delegations_text,
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.command(name="arbol")
    async def show_tree(self, ctx):
        """Muestra tu árbol de delegación o tubérculo
        Uso: !arbol"""
        voter = delegation_system.voters.get(str(ctx.author.id))
        if not voter:
            await ctx.send("❌ No estás registrado como votante.")
            return

        viz = VoterVisualization(str(ctx.author.id))
        # Configurar visualización basada en el estado del votante
        if voter.delegations:
            viz.vote_type = VoteType.TREE
            viz.delegations_tree = voter.delegations
        else:
            viz.vote_type = VoteType.TUBER
            viz.direct_votes = voter.received_points
            viz.tuber_size = len(viz.direct_votes)

        tree_viz = viz.generate_tree_visualization()
        embed = Embed(
            title=f"🌳 Árbol de Delegación de {ctx.author.name}",
            description=f"```\n{tree_viz}\n```",
            color=Color.green()
        )
        
        consensus = viz.get_consensus_visualization(
            sum(v['points'] for v in voter.delegations.values()),
            voter.base_points
        )
        
        embed.add_field(
            name="📊 Métricas de Consenso",
            value=(
                f"Inmediato: {consensus['immediate'].value[0]}\n"
                f"Largo plazo: {consensus['longterm'].value[0]}\n"
                f"Incertidumbre: {consensus['uncertainty'].value[0]}"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

class AdminCommands(commands.Cog):
    """Comandos administrativos para análisis de datos"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="analisis")
    @commands.has_role("Admin")
    async def analyze_system(self, ctx, tipo: str = "general"):
        """Analiza el estado del sistema
        Uso: !analisis [general|delegacion|votacion|actividad]"""
        
        if tipo == "general":
            stats = {
                "Total Votantes": len(delegation_system.voters),
                "Propuestas Activas": len([p for p in voting_system.proposals.values() if p.state == ProposalState.ACTIVE]),
                "Delegaciones Totales": sum(len(v.delegations) for v in delegation_system.voters.values()),
                "Puntos en Circulación": sum(v.base_points for v in delegation_system.voters.values())
            }
            
            embed = Embed(title="📊 Estadísticas Generales", color=Color.blue())
            for key, value in stats.items():
                embed.add_field(name=key, value=str(value), inline=True)
                
        elif tipo == "delegacion":
            # Análisis de red de delegación
            delegacion_stats = {
                "Delegadores Activos": len([v for v in delegation_system.voters.values() if v.delegations]),
                "Delegación Promedio": sum(len(v.delegations) for v in delegation_system.voters.values()) / len(delegation_system.voters) if delegation_system.voters else 0,
                "Mayor Delegador": max((len(v.delegations), k) for k, v in delegation_system.voters.items())[1] if delegation_system.voters else "Ninguno",
                "Ciclos Detectados": len(delegation_system.detect_cycles())
            }
            
            embed = Embed(title="🔄 Análisis de Delegaciones", color=Color.gold())
            for key, value in delegacion_stats.items():
                embed.add_field(name=key, value=str(value), inline=True)
                
        elif tipo == "votacion":
            # Análisis de votaciones
            votacion_stats = {
                "Participación Promedio": voting_system.get_average_participation(),
                "Consenso Promedio": voting_system.get_average_consensus(),
                "Propuestas Exitosas": len([p for p in voting_system.proposals.values() if p.state == ProposalState.PASSED]),
                "Propuestas Fallidas": len([p for p in voting_system.proposals.values() if p.state == ProposalState.FAILED])
            }
            
            embed = Embed(title="🗳️ Análisis de Votaciones", color=Color.purple())
            for key, value in votacion_stats.items():
                embed.add_field(name=key, value=f"{value:.2f}%" if isinstance(value, float) else str(value), inline=True)
                
        elif tipo == "actividad":
            # Análisis de actividad temporal
            activity_stats = voting_system.get_activity_metrics()
            
            embed = Embed(title="📈 Análisis de Actividad", color=Color.green())
            embed.add_field(name="Horas Más Activas", value="\n".join(f"{h}:00 - {activity}%" for h, activity in activity_stats["peak_hours"]), inline=False)
            embed.add_field(name="Días Más Activos", value="\n".join(f"{d} - {activity}%" for d, activity in activity_stats["active_days"]), inline=False)
            
        else:
            embed = Embed(title="❌ Error", description="Tipo de análisis no válido", color=Color.red())
        
        await ctx.send(embed=embed)
    
    @commands.command(name="exportar")
    @commands.has_role("Admin")
    async def export_data(self, ctx, formato: str = "json"):
        """Exporta datos del sistema para análisis externo
        Uso: !exportar [json|csv]"""
        
        if formato not in ["json", "csv"]:
            await ctx.send("❌ Formato no válido. Usa json o csv.")
            return
            
        # Preparar datos
        export_data = {
            "delegations": delegation_system.export_data(),
            "proposals": voting_system.export_data(),
            "activity": voting_system.get_activity_metrics()
        }
        
        # Guardar archivo
        filename = f"analysis_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{formato}"
        filepath = f"Data/Exports/{filename}"
        
        if formato == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
        else:  # csv
            # Convertir a formato tabular
            df = pd.DataFrame(export_data)
            df.to_csv(filepath, index=False)
            
        # Enviar archivo
        await ctx.send(
            "📊 Datos exportados",
            file=discord.File(filepath, filename=filename)
        )

    @commands.command(name="simulacion")
    @commands.has_role("Admin")
    async def run_simulation(self, ctx, escenario: str, n_iteraciones: int = 1000):
        """Ejecuta simulación del sistema
        Uso: !simulacion [centralizado|distribuido|aleatorio] [iteraciones]"""
        
        embed = Embed(title="🔬 Simulación Iniciada", color=Color.blue())
        status_msg = await ctx.send(embed=embed)
        
        # Ejecutar simulación
        resultados = await self.bot.loop.run_in_executor(
            None,
            delegation_system.simulate_scenario,
            escenario,
            n_iteraciones
        )
        
        # Mostrar resultados
        embed = Embed(title="🔬 Resultados de Simulación", color=Color.green())
        embed.add_field(name="Escenario", value=escenario, inline=False)
        embed.add_field(name="Iteraciones", value=str(n_iteraciones), inline=False)
        
        for metrica, valor in resultados.items():
            embed.add_field(name=metrica, value=f"{valor:.2f}", inline=True)
            
        await status_msg.edit(embed=embed)

class DebateCommands(commands.Cog):
    """Comandos para la fase de debate"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="modificar")
    async def propose_modification(self, ctx, proposal_id: str, article_id: str):
        """Propone una modificación a un artículo
        Uso: !modificar ID_PROPUESTA ID_ARTICULO"""
        embed = Embed(
            title="📝 Nueva Modificación",
            description="Responde con los cambios propuestos y su justificación.",
            color=Color.blue()
        )
        await ctx.send(embed=embed)
        
        try:
            msg = await self.bot.wait_for(
                'message',
                timeout=300.0,
                check=lambda m: m.author == ctx.author
            )
            
            changes = {
                'new_text': msg.content,
                'justification': 'Pendiente de justificación'
            }
            
            mod_id = await voting_system.debate_system.propose_modification(
                proposal_id,
                article_id,
                str(ctx.author.id),
                changes
            )
            
            if mod_id:
                embed = Embed(
                    title="✅ Modificación Propuesta",
                    description=f"ID: {mod_id}\nUsa !votar_mod {proposal_id} {mod_id} para votar",
                    color=Color.green()
                )
            else:
                embed = Embed(
                    title="❌ Error",
                    description="No se pudo proponer la modificación",
                    color=Color.red()
                )
                
            await ctx.send(embed=embed)
            
        except TimeoutError:
            await ctx.send("⌛ Tiempo agotado")
            
    @commands.command(name="votar_mod")
    async def vote_modification(self, ctx, proposal_id: str, mod_id: str, points: int):
        """Vota en una modificación propuesta
        Uso: !votar_mod ID_PROPUESTA ID_MOD PUNTOS"""
        success = await voting_system.debate_system.vote_modification(
            proposal_id,
            mod_id,
            str(ctx.author.id),
            points
        )
        
        if success:
            embed = Embed(
                title="✅ Voto Registrado",
                description=f"Has votado con {points} puntos",
                color=Color.green()
            )
        else:
            embed = Embed(
                title="❌ Error",
                description="No se pudo registrar el voto",
                color=Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.command(name="delegar_debate")
    async def delegate_debate_points(self, ctx, proposal_id: str, mod_id: str, 
                                   to_user: str, points: int):
        """Delega puntos durante el debate
        Uso: !delegar_debate ID_PROPUESTA ID_MOD @usuario PUNTOS"""
        
        success = await voting_system.debate_system.delegate_debate_points(
            proposal_id,
            mod_id,
            str(ctx.author.id),
            to_user.strip('<@!>'),
            points
        )
        
        if success:
            embed = Embed(
                title="✅ Delegación en Debate",
                description=f"Has delegado {points} puntos a {to_user} para esta modificación",
                color=Color.green()
            )
        else:
            embed = Embed(
                title="❌ Error",
                description="No tienes suficientes puntos comprometidos o la modificación no existe",
                color=Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.command(name="comprometer")
    async def commit_to_debate(self, ctx, proposal_id: str, points: int):
        """Compromete más puntos al debate
        Uso: !comprometer ID_PROPUESTA PUNTOS"""
        
        success = await voting_system.debate_system.add_committed_points(
            proposal_id,
            str(ctx.author.id),
            points
        )
        
        if success:
            embed = Embed(
                title="✅ Puntos Comprometidos",
                description=f"Has comprometido {points} puntos adicionales al debate",
                color=Color.green()
            )
        else:
            embed = Embed(
                title="❌ Error",
                description="No se pudieron comprometer los puntos",
                color=Color.red()
            )
            
        await ctx.send(embed=embed)

@app_commands.command(name="help")
async def help_command(interaction: discord.Interaction):
    """Muestra ayuda sobre los comandos disponibles"""
    embed = discord.Embed(
        title="📚 Ayuda - Comandos Disponibles",
        color=discord.Color.blue()
    )
    
    categories = {
        "Delegación": ["delegar", "revocar"],
        "Propuestas": ["proponer", "articulo", "requisitos"],
        "Información": ["perfil", "arbol"],
        "Admin": ["analisis", "exportar", "simulacion"],
        "Debate": ["modificar", "votar_mod", "delegar_debate", "comprometer"]
    }
    
    for category, cmds in categories.items():
        commands_text = "\n".join(
            f"/{cmd} - {help_descriptions[cmd]}"
            for cmd in cmds
        )
        embed.add_field(
            name=f"🔹 {category}",
            value=commands_text,
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    """Registra los Cogs con el bot"""
    bot.add_cog(DelegationCommands(bot))
    bot.add_cog(ProposalCommands(bot))
    bot.add_cog(InfoCommands(bot))
    bot.add_cog(AdminCommands(bot))
    bot.add_cog(DebateCommands(bot))
    bot.tree.add_command(help_command)
