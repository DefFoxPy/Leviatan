import math
from typing import Dict, List, Tuple

def calculate_required_voters(previous_voters: int) -> int:
    """
    Calcula votantes necesarios para una nueva propuesta
    V = V₀ × ln(V₀)/100
    
    Artículo 0: matemáticamente inmutable por ln(0) = -∞
    """
    if previous_voters == 0:
        return float('-inf')  # Inmutabilidad matemática natural
    return int(previous_voters * (math.log(previous_voters) / 100))

def calculate_minimum_participation(previous_voters: int) -> int:
    """
    Calcula participación mínima legítima
    Vm = V₀ × (1 - ln(V₀)/100)
    """
    return int(previous_voters * (1 - math.log(previous_voters) / 100))

def calculate_consensus_metrics(points_for: int, total_points: int, article_id: str = None) -> Dict[str, float]:
    """
    Calcula métricas de consenso usando puntos (1000 puntos = 1 voto)
    Sin epsilon artificial - las matemáticas funcionan naturalmente
    """
    if total_points == 0:
        return {"immediate": 0, "overtime": 0, "uncertainty": 0}
    
    # Convertir puntos a votos para cálculos
    votes_for = points_for / 1000
    total_votes = total_points / 1000
    percentage_yes = (votes_for / total_votes) * 100
    
    try:
        # Cálculos puros sin epsilon
        consensus_immediate = 1 - (math.log10(abs(percentage_yes - 50)) / math.log10(50))
        consensus_overtime = 1 - (math.log(abs(percentage_yes - 50)) / math.log(50))
        
        p_yes = votes_for / total_votes
        p_no = 1 - p_yes
        uncertainty = -(p_yes * math.log2(p_yes) + p_no * math.log2(p_no))
        
        return {
            "immediate": consensus_immediate,
            "overtime": consensus_overtime,
            "uncertainty": uncertainty,
            "votes_for": votes_for,
            "total_votes": total_votes
        }
    except (ValueError, ZeroDivisionError):
        # Los errores matemáticos son features, no bugs
        return {
            "immediate": float('-inf') if article_id == "0" else float('nan'),
            "overtime": float('-inf') if article_id == "0" else float('nan'),
            "uncertainty": float('-inf') if article_id == "0" else float('nan'),
            "votes_for": 0,
            "total_votes": 0
        }

def validate_proposal_requirements(proposal: Dict) -> Tuple[bool, str]:
    """
    Valida requisitos básicos de una propuesta
    
    El Artículo 0 es inmutable:
    - Si la propuesta intenta modificar el Artículo 0, se rechaza automáticamente
    - La inmutabilidad está garantizada matemáticamente por log(0)
    """
    if "0" in proposal.get('articles', {}):
        return False, "El Artículo 0 es inmutable por diseño matemático (log(0) = -∞)"
    
    required_fields = ['owner_id', 'title', 'articles', 'implementation_plan', 'deadline']
    missing_fields = [field for field in required_fields if field not in proposal]
    
    if missing_fields:
        return False, f"Campos faltantes: {', '.join(missing_fields)}"
        
    if not proposal['articles']:
        return False, "La propuesta debe modificar al menos un artículo"
        
    if len(proposal.get('implementation_plan', '')) < 100:
        return False, "El plan de implementación debe ser más detallado"
        
    return True, "Propuesta válida"
