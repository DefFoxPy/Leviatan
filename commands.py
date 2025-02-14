from discord.ext import commands
from discord import Embed, Color
from typing import Dict, Optional
from delegation import DelegationSystem
from voting import VotingSystem, ProposalState
from visualization import VoterVisualization, VoteType
from datetime import datetime
import pandas as pd
import json
import discord

delegation_system = DelegationSystem()
voting_system = VotingSystem()

class DelegationCommands(commands.Cog):
    """Comandos para el sistema de delegación de votos"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="delegar")
    async def delegate(self, ctx, to_user: str, points: int, subdelegable: bool = False):
        """Delega puntos a otro usuario
        Uso: !delegar @usuario 500 [True/False]"""
        success = delegation_system.delegate_points(
            str(ctx.author.id), 
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
            
        await ctx.send(embed=embed)

class ProposalCommands(commands.Cog):
    """Comandos para gestionar propuestas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.drafts: Dict[str, Dict] = {}
        
    @commands.command(name="proponer")
    async def start_proposal(self, ctx):
        """Inicia el proceso de crear una propuesta
        Uso: !proponer"""
        embed = Embed(
            title="🗳️ Nueva Propuesta",
            description="Iniciemos el proceso de creación.\nResponde con el título de tu propuesta.",
            color=Color.blue()
        )
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
            
        try:
            title_msg = await self.bot.wait_for('message', timeout=300.0, check=check)
            proposal_id = voting_system.create_proposal(str(ctx.author.id), title_msg.content, 100)
            
            embed = Embed(
                title="✅ Propuesta Creada",
                description=f"ID: {proposal_id}\nTítulo: {title_msg.content}\n\nUsa !articulo {proposal_id} para añadir artículos.",
                color=Color.green()
            )
            await ctx.send(embed=embed)
            
        except TimeoutError:
            await ctx.send("⌛ Tiempo agotado. Intenta crear la propuesta nuevamente.")

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

def setup(bot):
    """Registra los Cogs con el bot"""
    bot.add_cog(DelegationCommands(bot))
    bot.add_cog(ProposalCommands(bot))
    bot.add_cog(InfoCommands(bot))
    bot.add_cog(AdminCommands(bot))
