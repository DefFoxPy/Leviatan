"""
Sistema de Votación y Gestión de Propuestas
=========================================

Este módulo implementa un sistema de votación por etapas donde:
- Las propuestas pasan por múltiples estados
- Los votos se realizan usando puntos (1000 = 1 voto)
- Los requisitos se calculan logarítmicamente
- Cada artículo tiene su propio árbol de modificaciones

Estados de una Propuesta:
-----------------------
1. DRAFT: Redacción inicial
2. GATHERING: Recolección de simpatizantes
3. DEBATE: Discusión y modificaciones
4. VOTING: Votación final
5. APPROVED/REJECTED: Resultado
6. PUBLISHED: En vigor
7. ABANDONED: Abandonada por inactividad

Características:
--------------
- Sistema de estados para propuestas
- Cálculo dinámico de requisitos
- Historial de modificaciones
- Validación de participantes
- Gestión de plazos

Ejemplo de uso:
-------------
```python
voting = VotingSystem()
proposal_id = voting.create_proposal("user123", "Nueva Ley", 100)
voting.commit_points(proposal_id, "voter1", 500, support=True)
```
"""

from enum import Enum
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from utility import calculate_required_voters, calculate_minimum_participation, validate_proposal_requirements, MathUtils
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Dict, List, Optional, Set, Tuple
from constitution import Constitution

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProposalState(Enum):
    """
    Estados posibles de una propuesta
    
    Estados:
        DRAFT: En redacción inicial
        GATHERING: Juntando simpatizantes iniciales
        DEBATE: En periodo de debate y modificaciones
        VOTING: En votación final
        APPROVED: Aprobada y pendiente de implementación
        REJECTED: Rechazada
        PUBLISHED: Publicada y en vigor
        ABANDONED: Abandonada por inactividad
        CLEANUP: Estado temporal durante limpieza
    """
    DRAFT = "draft"
    GATHERING = "gathering"
    DEBATE = "debate"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ABANDONED = "abandoned" 
    CLEANUP = "cleanup"

class Proposal:
    """
    Representa una propuesta de modificación de artículos
    
    Atributos:
        owner_id (str): ID del creador de la propuesta
        title (str): Título descriptivo
        state (ProposalState): Estado actual
        articles (Dict): Artículos a modificar
        supporters (Dict[str, int]): Votos a favor {voter_id: points}
        opponents (Dict[str, int]): Votos en contra {voter_id: points}
        modifications (List[Dict]): Historial de cambios
        required_voters (int): Votantes necesarios calculados
        deadline (datetime): Fecha límite
        implementation_date (datetime): Fecha de implementación
        last_activity (datetime): Marca de última actividad
        abandon_threshold (timedelta): Umbral de tiempo para considerar abandono
    """
    
    def __init__(self, owner_id: str, title: str):
        self.owner_id = owner_id
        self.title = title
        self.state = ProposalState.DRAFT
        self.articles: Dict[str, Dict] = {}
        self.supporters: Dict[str, int] = {}  # voter_id: points
        self.opponents: Dict[str, int] = {}   # voter_id: points
        self.modifications: List[Dict] = []    # Historial de cambios
        self.required_voters = 0
        self.deadline = None
        self.implementation_date = None
        self.last_activity = datetime.now()
        self.abandon_threshold = timedelta(days=30)  # 30 días sin actividad = abandonada
        self.state_lock = asyncio.Lock()
        self.cleanup_lock = asyncio.Lock()
        self.min_activity_threshold = 5  # Mínimo de participantes para no abandonar
        self.max_inactivity_period = timedelta(days=30)
        self.creation_date = datetime.now()
        self.last_state_change = datetime.now()
        self.article_requirements: Dict[str, Dict] = {}  # {article_id: {'previous_voters': int, 'required_voters': int}}
        self.constitution = Constitution()
        self.affected_articles: Dict[str, Dict] = {}  # Artículos afectados y sus cambios
        self.governing_article: str = None  # Artículo que determina los requisitos
        self.existing_articles: Dict[str, Dict] = {}  # Modificaciones a artículos existentes
        self.new_articles: Dict[str, Dict] = {}       # Nuevos artículos propuestos
        self.required_existing_articles = 1  # Mínimo de artículos existentes a modificar
        self.article_votes: Dict[str, Dict[str, int]] = {}  # {article_id: {voter_id: points}}
        self.article_requirements: Dict[str, Dict] = {}      # {article_id: requirements}
        self.article_groups: List[Set[str]] = []            # Grupos de artículos relacionados
        
    def add_article_modification(self, article_id: str, changes: Dict, is_new: bool = False) -> bool:
        """
        Añade o modifica un artículo en la propuesta
        
        Args:
            article_id: Identificador del artículo
            changes: Diccionario con los cambios
            is_new: True si es un artículo nuevo, False si es modificación
        """
        if self.state != ProposalState.DEBATE:
            return False

        article_data = {
            "current_version": changes.get("new_text", ""),
            "previous_version": changes.get("old_text", "") if not is_new else None,
            "justification": changes.get("justification", ""),
            "last_modified": datetime.now().isoformat(),
            "modified_by": changes.get("author_id"),
            "is_new": is_new
        }

        if is_new:
            self.new_articles[article_id] = article_data
        else:
            self.existing_articles[article_id] = article_data

        return True

    def add_article_group(self, articles: Set[str]) -> bool:
        """Añade un grupo de artículos relacionados"""
        if not all(art_id in self.get_all_articles() for art_id in articles):
            return False
        
        self.article_groups.append(articles)
        return True

    def get_group_requirements(self, group: Set[str]) -> Dict:
        """Obtiene requisitos para un grupo basado en el artículo más exigente"""
        if not group:
            return None
            
        reqs = [
            self.article_requirements.get(art_id, {'required_voters': 0})
            for art_id in group
        ]
        
        return max(reqs, key=lambda r: r['required_voters'])

    def validate_group_vote(self, group: Set[str], points: int) -> bool:
        """Valida si un voto cumple los requisitos del grupo"""
        req = self.get_group_requirements(group)
        if not req:
            return False
            
        return points >= req['required_voters']

    def validate_requirements(self) -> bool:
        """
        Valida que la propuesta cumpla con los requisitos mínimos
        """
        # Debe tener al menos un artículo existente modificado
        if len(self.existing_articles) < self.required_existing_articles:
            return False
            
        # Si hay nuevos artículos, validar que tengan contenido
        for article in self.new_articles.values():
            if not article["current_version"].strip():
                return False
                
        return True

    def get_all_articles(self) -> Dict[str, Dict]:
        """
        Retorna todos los artículos (existentes y nuevos)
        """
        return {
            **self.existing_articles,
            **self.new_articles
        }
        
    async def change_state(self, new_state: ProposalState) -> bool:
        """Cambia estado de forma thread-safe"""
        async with self.state_lock:
            if self._is_valid_state_transition(new_state):
                self.state = new_state
                self.last_state_change = datetime.now()
                return True
            return False
            
    def _is_valid_state_transition(self, new_state: ProposalState) -> bool:
        """Valida transiciones de estado permitidas"""
        valid_transitions = {
            ProposalState.DRAFT: [ProposalState.GATHERING, ProposalState.ABANDONED],
            ProposalState.GATHERING: [ProposalState.DEBATE, ProposalState.ABANDONED],
            ProposalState.DEBATE: [ProposalState.VOTING, ProposalState.ABANDONED],
            ProposalState.VOTING: [ProposalState.APPROVED, ProposalState.REJECTED, ProposalState.ABANDONED],
            ProposalState.CLEANUP: [ProposalState.ABANDONED]
        }
        return new_state in valid_transitions.get(self.state, [])

    def calculate_requirements(self, article_ids: List[str]):
        """
        Obtiene requisitos pre-calculados de la constitución
        """
        requirements = self.constitution.calculate_proposal_requirements(article_ids)
        if requirements:
            self.required_voters = requirements['required_voters']
            self.min_participation = requirements['min_participation']
            self.governing_article = requirements['governing_article']
            return True
        return False

    def update_activity(self):
        """Actualiza la marca de última actividad"""
        self.last_activity = datetime.now()

    def is_abandoned(self) -> bool:
        """
        Verifica si la propuesta está abandonada basado en:
        - Tiempo desde última actividad
        - Estado actual
        - Número de simpatizantes
        """
        if self.state in [ProposalState.APPROVED, ProposalState.REJECTED, 
                         ProposalState.PUBLISHED, ProposalState.ABANDONED]:
            return False
            
        time_inactive = datetime.now() - self.last_activity
        return time_inactive > self.abandon_threshold

    async def set_affected_articles(self, articles: Dict[str, Dict]) -> bool:
        """
        Configura los artículos afectados y calcula requisitos
        basados en la constitución
        """
        try:
            for article_id, changes in articles.items():
                requirements = self.constitution
                # Aquí iría la lógica para calcular los requisitos basados en la constitución
                self.affected_articles[article_id] = changes
            return True
        except Exception as e:
            logger.error(f"Error configurando artículos afectados: {e}")
            return False

class VotingSystem:
    """
    Sistema de gestión de votaciones y propuestas
    
    Responsabilidades:
    1. Crear y gestionar propuestas
    2. Validar modificaciones
    3. Gestionar votos y puntos
    4. Controlar estados de propuestas
    
    Notas:
    - Cada votante debe comprometer sus puntos
    - Las propuestas tienen requisitos dinámicos
    - Los artículos tienen su propio árbol de cambios
    """
    
    def __init__(self):
        self.proposals: Dict[str, Proposal] = {}
        self.current_votes: Dict[str, Dict[str, int]] = {}  # proposal_id -> {voter_id: points}
        self.cleanup_interval = timedelta(days=1)  # Revisar propuestas abandonadas diariamente
        self.last_cleanup = datetime.now()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.proposal_locks: Dict[str, asyncio.Lock] = {}
        self.data_file = "Data/proposals.json"
        self.constitution = Constitution()
        self.math = MathUtils()
        
    async def create_proposal(self, owner_id: str, title: str, existing_articles: Dict[str, Dict], new_articles: Dict[str, Dict] = None) -> Tuple[str, bool]:
        """
        Crea una nueva propuesta
        
        Args:
            owner_id: ID del creador
            title: Título de la propuesta
            existing_articles: Artículos existentes a modificar
            new_articles: Nuevos artículos a crear (opcional)
        """
        if not owner_id or not title or not existing_articles:
            raise ValueError("Owner_id, título y al menos un artículo existente son requeridos")
            
        if not self._validate_owner(owner_id):
            return None, False

        proposal_id = f"prop_{len(self.proposals) + 1}"
        self.proposal_locks[proposal_id] = asyncio.Lock()
        
        proposal = Proposal(owner_id, title)
        try:
            # Procesar artículos existentes
            for art_id, changes in existing_articles.items():
                proposal.add_article_modification(art_id, changes, is_new=False)
                
            # Procesar nuevos artículos si existen
            if new_articles:
                for art_id, changes in new_articles.items():
                    proposal.add_article_modification(art_id, changes, is_new=True)
            
            # Validar requisitos mínimos
            if not proposal.validate_requirements():
                return None, False
                
            # Calcular requisitos basados en todos los artículos
            article_ids = list(proposal.get_all_articles().keys())
            proposal.calculate_requirements(article_ids)
            
            self.proposals[proposal_id] = proposal
            await self._save_data()
            return proposal_id, True
            
        except Exception as e:
            logger.error(f"Error creando propuesta: {e}")
            return None, False
        
    def add_modification(self, proposal_id: str, article_id: str, changes: Dict, voter_id: str) -> bool:
        """
        Añade modificación a un artículo
        
        Args:
            proposal_id: ID de la propuesta
            article_id: ID del artículo
            changes: Cambios propuestos
            voter_id: ID del votante que propone
            
        Returns:
            bool: True si se aceptó la modificación
            
        Validaciones:
        - El votante debe ser simpatizante o dueño
        - La propuesta debe estar en DEBATE
        """
        if proposal_id not in self.proposals:
            return False
            
        proposal = self.proposals[proposal_id]
        if proposal.state == ProposalState.ABANDONED:
            return False
            
        if voter_id not in proposal.supporters and voter_id != proposal.owner_id:
            return False
            
        success = proposal.add_article_modification(article_id, changes)
        if success:
            proposal.update_activity()
            self.check_abandoned_proposals()
        return success
        
    async def commit_points(self, proposal_id: str, voter_id: str, article_group: Set[str], points: int, support: bool) -> bool:
        """
        Compromete puntos para un grupo de artículos
        
        Args:
            proposal_id: ID de la propuesta
            voter_id: ID del votante
            article_group: Conjunto de IDs de artículos
            points: Puntos a comprometer
            support: True si es a favor
        """
        if proposal_id not in self.proposals:
            return False
            
        async with self.proposal_locks[proposal_id]:
            proposal = self.proposals[proposal_id]
            
            if not proposal.validate_group_vote(article_group, points):
                return False
                
            try:
                # Distribuir puntos entre artículos
                points_per_article = points // len(article_group)
                remainder = points % len(article_group)
                
                for i, article_id in enumerate(article_group):
                    art_points = points_per_article + (1 if i < remainder else 0)
                    
                    if support:
                        proposal.article_votes.setdefault(article_id, {})
                        proposal.article_votes[article_id][voter_id] = art_points
                    else:
                        proposal.article_votes.setdefault(article_id, {})
                        proposal.article_votes[article_id][voter_id] = -art_points
                
                proposal.update_activity()
                await self._save_data()
                return True
                
            except Exception as e:
                logger.error(f"Error en commit_points: {e}")
                return False

    def can_close_proposal(self, proposal_id: str) -> bool:
        """
        Verifica si una propuesta puede cerrarse
        
        Args:
            proposal_id: ID de la propuesta
            
        Returns:
            bool: True si cumple requisitos de cierre
            
        Verifica:
        - Suficientes votos
        - Plazo cumplido
        - Estado correcto
        """
        if proposal_id not in self.proposals:
            return False
            
        proposal = self.proposals[proposal_id]
        total_support = sum(proposal.supporters.values())
        return total_support >= proposal.required_voters

    async def check_abandoned_proposals(self):
        """Verificación thread-safe de propuestas abandonadas"""
        if datetime.now() - self.last_cleanup < self.cleanup_interval:
            return

        async with asyncio.Lock():
            try:
                for proposal_id, proposal in self.proposals.items():
                    if await self._should_abandon_proposal(proposal):
                        await self._abandon_proposal(proposal_id)
                self.last_cleanup = datetime.now()
                await self._save_data()
            except Exception as e:
                logger.error(f"Error en cleanup: {e}")

    async def _abandon_proposal(self, proposal_id: str):
        """Limpieza completa de una propuesta abandonada"""
        async with self.proposal_locks[proposal_id]:
            proposal = self.proposals[proposal_id]
            await proposal.change_state(ProposalState.CLEANUP)
            
            # Liberar recursos
            self._release_committed_points(proposal_id)
            self._clean_proposal_data(proposal_id)
            
            await proposal.change_state(ProposalState.ABANDONED)
            logger.info(f"Propuesta {proposal_id} abandonada y limpiada")

    async def can_close_proposal(self, proposal_id: str) -> bool:
        """Verificación completa para cerrar propuesta"""
        if proposal_id not in self.proposals:
            return False
            
        async with self.proposal_locks[proposal_id]:
            proposal = self.proposals[proposal_id]
            
            if proposal.state != ProposalState.VOTING:
                return False
                
            if datetime.now() < proposal.deadline:
                return False
                
            total_support = sum(proposal.supporters.values())
            total_votes = total_support + sum(proposal.opponents.values())
            
            return (total_support >= proposal.required_voters and
                    total_votes >= proposal.min_participation)

    async def _save_data(self):
        """Guarda estado del sistema de forma thread-safe"""
        async with asyncio.Lock():
            try:
                data = self._serialize_proposals()
                await self.executor.submit(self._write_data_to_file, data)
            except Exception as e:
                logger.error(f"Error guardando datos: {e}")
                raise

    def _serialize_proposals(self) -> Dict:
        """Serializa propuestas para persistencia"""
        return {
            "proposals": {
                pid: {
                    "owner_id": p.owner_id,
                    "title": p.title,
                    "state": p.state.value,
                    "articles": p.articles,
                    "supporters": p.supporters,
                    "opponents": p.opponents,
                    "created_at": p.creation_date.isoformat(),
                    "last_activity": p.last_activity.isoformat(),
                    "deadline": p.deadline.isoformat() if p.deadline else None
                } for pid, p in self.proposals.items()
            },
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }

    def load_data(self) -> None:
        """Carga datos persistentes"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self._deserialize_proposals(data)
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            raise

    def _calculate_article_results(self, proposal_id: str) -> Dict[str, Dict]:
        """Calcula resultados por artículo"""
        proposal = self.proposals[proposal_id]
        results = {}
        
        for article_id, votes in proposal.article_votes.items():
            support = sum(p for p in votes.values() if p > 0)
            oppose = abs(sum(p for p in votes.values() if p < 0))
            total = support + oppose
            
            results[article_id] = {
                'support': support,
                'oppose': oppose,
                'total': total,
                'passed': support > oppose and support >= proposal.article_requirements[article_id]['required_voters']
            }
            
        return results

    def get_article_metadata(self, article_id: int) -> Dict:
        """Obtiene metadatos del artículo incluyendo base y votos previos"""
        article = self.constitution.get_article(article_id)
        if not article:
            return None
        
        return {
            'base': article.get('base', 1),  # Art 0: base 0, Art 1: base 1, otros: base 1
            'previous_votes': self.vote_history.get(article_id, 0),
            'last_modification': article.get('votacion_anterior', {}).get('fecha', 'N/A')
        }

    def calculate_requirements(self, article_id: int) -> Dict[str, float]:
        """Calcula requisitos basados en metadatos del artículo"""
        metadata = self.get_article_metadata(article_id)
        if not metadata:
            return None

        # Si es Artículo 0, es imposible
        if article_id == 0:
            return {
                'required_votes': float('inf'),
                'min_participation': float('inf'),
                'base': 0
            }

        # Para otros artículos, usar ln(previous_votes)
        return {
            'required_votes': self.math.calculate_proposal_requirement(metadata['previous_votes']),
            'min_participation': self.math.calculate_legitimate_participation(metadata['previous_votes']),
            'base': metadata['base']
        }
