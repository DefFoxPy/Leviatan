from typing import Dict, Set, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class DebateState(Enum):
    DISCUSSION = "discussion"  # Discusión general
    VOTING = "voting"         # Votando una modificación
    REVIEWING = "reviewing"   # Revisando resultados

class ArticleModification:
    def __init__(self, article_id: str, author_id: str, changes: Dict):
        self.article_id = article_id
        self.author_id = author_id
        self.changes = changes
        self.created_at = datetime.now()
        self.votes: Dict[str, int] = {}  # voter_id: points
        self.state = DebateState.DISCUSSION
        self.voting_deadline: Optional[datetime] = None
        self.required_points = 100  # Puntos base requeridos
        self.comments: List[Dict] = []
        
    def add_vote(self, voter_id: str, points: int) -> bool:
        """Añade voto a la modificación"""
        if self.state != DebateState.VOTING:
            return False
            
        self.votes[voter_id] = points
        return True
        
    def calculate_result(self) -> Dict:
        """Calcula resultado de la votación"""
        total_points = sum(self.votes.values())
        return {
            'passed': total_points >= self.required_points,
            'total_points': total_points,
            'total_voters': len(self.votes),
            'created_at': self.created_at.isoformat()
        }

class DebateSystem:
    """Sistema de debate para propuestas"""
    
    def __init__(self):
        self.modifications: Dict[str, Dict[str, ArticleModification]] = {}  # proposal_id -> {mod_id: modification}
        self.proposal_articles: Dict[str, Set[str]] = {}  # proposal_id -> {article_ids}
        self.locks: Dict[str, asyncio.Lock] = {}
        
    async def initialize_debate(self, proposal_id: str, article_ids: Set[str]) -> bool:
        """Inicializa sistema de debate para una propuesta"""
        if proposal_id in self.modifications:
            return False
            
        self.locks[proposal_id] = asyncio.Lock()
        self.modifications[proposal_id] = {}
        self.proposal_articles[proposal_id] = article_ids
        return True
        
    async def propose_modification(self, proposal_id: str, article_id: str, author_id: str, changes: Dict) -> Optional[str]:
        """Propone una modificación a un artículo"""
        if not self._validate_article_access(proposal_id, article_id):
            return None
            
        async with self.locks[proposal_id]:
            mod_id = f"mod_{len(self.modifications[proposal_id]) + 1}"
            modification = ArticleModification(article_id, author_id, changes)
            self.modifications[proposal_id][mod_id] = modification
            return mod_id
            
    async def start_modification_vote(self, proposal_id: str, mod_id: str, duration: timedelta = timedelta(hours=24)) -> bool:
        """Inicia votación para una modificación"""
        if not self._validate_modification(proposal_id, mod_id):
            return False
            
        modification = self.modifications[proposal_id][mod_id]
        modification.state = DebateState.VOTING
        modification.voting_deadline = datetime.now() + duration
        return True
        
    async def vote_modification(self, proposal_id: str, mod_id: str, voter_id: str, points: int) -> bool:
        """Vota en una modificación propuesta"""
        if not self._validate_modification(proposal_id, mod_id):
            return False
            
        modification = self.modifications[proposal_id][mod_id]
        if modification.state != DebateState.VOTING:
            return False
            
        if datetime.now() > modification.voting_deadline:
            return False
            
        return modification.add_vote(voter_id, points)
        
    async def get_modification_result(self, proposal_id: str, mod_id: str) -> Optional[Dict]:
        """Obtiene resultado de una modificación"""
        if not self._validate_modification(proposal_id, mod_id):
            return None
            
        modification = self.modifications[proposal_id][mod_id]
        return modification.calculate_result()
        
    def _validate_article_access(self, proposal_id: str, article_id: str) -> bool:
        """Valida si un artículo pertenece a la propuesta"""
        return (proposal_id in self.proposal_articles and
                article_id in self.proposal_articles[proposal_id])
                
    def _validate_modification(self, proposal_id: str, mod_id: str) -> bool:
        """Valida si una modificación existe"""
        return (proposal_id in self.modifications and
                mod_id in self.modifications[proposal_id])
                
    def get_article_modifications(self, proposal_id: str, article_id: str) -> List[Dict]:
        """Obtiene historial de modificaciones de un artículo"""
        if not self._validate_article_access(proposal_id, article_id):
            return []
            
        modifications = []
        for mod_id, mod in self.modifications[proposal_id].items():
            if mod.article_id == article_id:
                modifications.append({
                    'id': mod_id,
                    'author_id': mod.author_id,
                    'changes': mod.changes,
                    'state': mod.state.value,
                    'votes': len(mod.votes),
                    'created_at': mod.created_at.isoformat()
                })
                
        return modifications

    async def add_comment(self, proposal_id: str, mod_id: str, author_id: str, content: str) -> bool:
        """Añade un comentario a una modificación"""
        if not self._validate_modification(proposal_id, mod_id):
            return False
            
        modification = self.modifications[proposal_id][mod_id]
        modification.comments.append({
            'author_id': author_id,
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        return True
