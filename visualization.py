from typing import Dict, List, Tuple
from enum import Enum
import math

class VoteType(Enum):
    TREE = "tree"       # Delegador activo
    TUBER = "tuber"     # Votante directo
    HYBRID = "hybrid"   # Mixto

class FruitStatus(Enum):
    GREEN = "🟢"    # A favor
    RED = "🔴"      # En contra
    YELLOW = "🟡"   # Dividido
    GREY = "⚪"     # Sin votar
    BLUE = "🫐"     # Nueva propuesta

class TuberType(Enum):
    POTATO = "🥔"     # Votos directos varios
    CARROT = "🥕"     # Delegación total recibida
    RADISH = "🌱"     # Pocas delegaciones
    CASSAVA = "🌿"    # Muchas delegaciones

class ConsensusLevel(Enum):
    WAR = ("🔴", "Guerra total", 1.0)
    DEBATE = ("🟠", "En debate", 0.75)
    PROGRESS = ("🟡", "Avanzando", 0.5)
    SETTLED = ("🟢", "Casi resuelto", 0.25)
    DONE = ("🔵", "Consenso", 0.0)

class VoterVisualization:
    def __init__(self, voter_id: str):
        self.voter_id = voter_id
        self.vote_type = VoteType.HYBRID
        self.delegations_tree: Dict = {}
        self.direct_votes: Dict = {}
        self.fruits: List[Dict] = []
        self.tuber_size = 0
        self.influence_level = 0

    def calculate_fruit_status(self, proposal_votes: Dict) -> FruitStatus:
        """Calcula el estado del fruto basado en votos"""
        total_for = sum(v for v in proposal_votes.values() if v > 0)
        total_against = abs(sum(v for v in proposal_votes.values() if v < 0))
        
        if not total_for and not total_against:
            return FruitStatus.GREY
        
        ratio = total_for / (total_for + total_against)
        if ratio > 0.6:
            return FruitStatus.GREEN
        elif ratio < 0.4:
            return FruitStatus.RED
        return FruitStatus.YELLOW

    def get_tuber_type(self) -> TuberType:
        """Determina el tipo de tubérculo basado en patrones de voto"""
        if len(self.direct_votes) > len(self.delegations_tree):
            if self.influence_level > 0.8:
                return TuberType.POTATO
            return TuberType.RADISH
        elif len(self.delegations_tree) == 1 and next(iter(self.delegations_tree.values()))['points'] >= 900:
            return TuberType.CARROT
        return TuberType.CASSAVA

    def get_consensus_visualization(self, votes_for: int, total_votes: int) -> Dict[str, ConsensusLevel]:
        """
        Calcula los tres tipos de consenso:
        - Inmediato (log10) - Percepción rápida
        - A largo plazo (ln) - Cambio de opinión
        - Incertidumbre (Shannon) - Confiabilidad
        """
        if total_votes == 0:
            return {
                "immediate": ConsensusLevel.GREY,
                "longterm": ConsensusLevel.GREY,
                "uncertainty": ConsensusLevel.GREY
            }

        percentage = (votes_for / total_votes) * 100
        deviation = abs(percentage - 50)

        # Consenso inmediato (log10)
        immediate = 1 - (math.log10(deviation + 1) / math.log10(50))
        
        # Consenso a largo plazo (ln)
        longterm = 1 - (math.log(deviation + 1) / math.log(50))
        
        # Incertidumbre (Shannon)
        p_yes = votes_for / total_votes
        p_no = 1 - p_yes
        uncertainty = -(p_yes * math.log2(p_yes + 0.0001) + p_no * math.log2(p_no + 0.0001))

        def get_level(value: float) -> ConsensusLevel:
            if value > 0.8: return ConsensusLevel.WAR
            elif value > 0.6: return ConsensusLevel.DEBATE
            elif value > 0.4: return ConsensusLevel.PROGRESS
            elif value > 0.2: return ConsensusLevel.SETTLED
            return ConsensusLevel.DONE

        return {
            "immediate": get_level(immediate),
            "longterm": get_level(longterm),
            "uncertainty": get_level(uncertainty)
        }

    def generate_tree_visualization(self) -> str:
        """Genera una representación visual del árbol de delegación"""
        if self.vote_type == VoteType.TUBER:
            tuber = self.get_tuber_type()
            size = "🥔" * (min(self.tuber_size, 5))
            return f"{tuber.value} {size}"
        
        tree = "🌳\n"
        for branch, details in self.delegations_tree.items():
            thickness = "═" * (details['points'] // 100)
            tree += f"├{thickness}> {branch} ({details['points']}pts)\n"
        
        for fruit in self.fruits:
            tree += f"{fruit['status'].value} {fruit['proposal_id']}\n"
        
        return tree
