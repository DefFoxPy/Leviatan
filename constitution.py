"""
Sistema de Gestión Constitucional
================================
Gestiona los artículos de la constitución y sus requisitos de votación.
La constitución mantiene un caché de requisitos para optimizar el rendimiento.

Características:
- Caché de requisitos por artículo
- Historial de votaciones
- Artículo 0 matemáticamente inmutable
- Cálculo dinámico de barreras de votación
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Set
from utility import calculate_required_voters, calculate_minimum_participation
import logging

logger = logging.getLogger(__name__)

class Constitution:
    """Gestiona la constitución y sus reglas"""
    
    def __init__(self):
        self.data_file = "Data/constitution.json"
        self.articles = {}
        self.load_constitution()
        
    def load_constitution(self):
        """Carga la constitución desde el archivo"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.articles = data.get('articles', {})
        except Exception as e:
            logger.error(f"Error cargando constitución: {e}")
            self.articles = {}
            
    def calculate_proposal_requirements(self, article_ids: List[str]) -> Dict:
        """
        Calcula requisitos para una propuesta basado en los artículos afectados
        
        Args:
            article_ids: Lista de IDs de artículos (existentes y nuevos)
            
        Returns:
            Dict con requisitos calculados
        """
        try:
            existing_articles = [aid for aid in article_ids if aid in self.articles]
            new_articles = [aid for aid in article_ids if aid not in self.articles]
            
            # Base de votantes requeridos
            base_required = 100  # Requisito mínimo base
            
            # Multiplicador por artículos existentes
            existing_multiplier = sum(
                self.articles[aid].get('weight', 1) 
                for aid in existing_articles
            )
            
            # Multiplicador por artículos nuevos
            new_multiplier = len(new_articles) * 0.5  # 50% del peso de uno existente
            
            total_required = int(base_required * (existing_multiplier + new_multiplier))
            
            # Artículo que gobierna esta propuesta (el de mayor peso)
            governing_article = max(
                existing_articles,
                key=lambda aid: self.articles[aid].get('weight', 1),
                default=None
            )
            
            return {
                'required_voters': total_required,
                'min_participation': int(total_required * 0.75),  # 75% del requerido
                'governing_article': governing_article,
                'existing_articles': len(existing_articles),
                'new_articles': len(new_articles)
            }
            
        except Exception as e:
            logger.error(f"Error calculando requisitos: {e}")
            return None
            
    def validate_article_id(self, article_id: str) -> bool:
        """Valida si un ID de artículo existe"""
        return article_id in self.articles

    def validate_article_group(self, article_ids: Set[str]) -> bool:
        """Valida si un grupo de artículos puede votarse junto"""
        if not article_ids:
            return False
            
        # Verificar que todos existen
        if not all(self.validate_article_id(aid) for aid in article_ids):
            return False
            
        # Verificar coherencia de requisitos
        reqs = [self.get_article_requirements(aid) for aid in article_ids]
        if not all(reqs):
            return False
            
        # Verificar que los artículos están relacionados
        return self._are_articles_related(article_ids)

    def _are_articles_related(self, article_ids: Set[str]) -> bool:
        """Verifica si los artículos están relacionadamente conectados"""
        # Implementar lógica de relación entre artículos
        # Por ahora retorna True para pruebas
        return True

    def get_group_requirements(self, article_ids: Set[str]) -> Optional[Dict]:
        """Obtiene requisitos combinados para un grupo de artículos"""
        if not self.validate_article_group(article_ids):
            return None
            
        # Usar requisitos del artículo más exigente
        reqs = [self.get_article_requirements(aid) for aid in article_ids]
        return max(reqs, key=lambda r: r['required_voters'])

    def initialize_empty_constitution(self) -> None:
        """Inicializa una constitución con el Artículo 0 inmutable"""
        initial_data = {
            "articles": {
                "0": {
                    "text": "Artículo fundamental del sistema",
                    "version": "1.0.0",
                    "last_modified": datetime.now().isoformat(),
                    "history": [],
                    "cached_requirements": {
                        "required_voters": float('-inf'),
                        "min_participation": 0,
                        "previous_voters": 0,
                        "last_calculation": datetime.now().isoformat()
                    }
                }
            },
            "requirements_cache": {
                "last_calculated": datetime.now().isoformat(),
                "cache_duration_days": 7,
                "by_article": {
                    "0": {
                        "current": {
                            "required_voters": float('-inf'),
                            "min_participation": 0,
                            "previous_voters": 0
                        },
                        "history": []
                    }
                }
            }
        }
        
        self.articles = initial_data['articles']
        self.requirements_cache = initial_data['requirements_cache']
        self.save_data()

    def get_article_requirements(self, article_id: str) -> Dict:
        """Obtiene requisitos cacheados de un artículo"""
        if article_id == "0":
            return {
                "required_voters": float('-inf'),
                "min_participation": 0,
                "previous_voters": 0,
                "immutable": True
            }

        cached = self.articles.get(article_id, {}).get('cached_requirements')
        if not cached:
            return None

        cache_age = datetime.now() - datetime.fromisoformat(cached['last_calculation'])
        if cache_age > self.cache_duration:
            self._recalculate_requirements(article_id)
            cached = self.articles[article_id]['cached_requirements']

        return cached

    def _recalculate_requirements(self, article_id: str) -> None:
        """Recalcula requisitos para un artículo basado en su historia"""
        article = self.articles.get(article_id)
        if not article:
            return

        history = article.get('history', [])
        if not history:
            previous_voters = 0
        else:
            previous_voters = history[-1].get('voters_participated', 0)

        article['cached_requirements'] = {
            'required_voters': calculate_required_voters(previous_voters),
            'min_participation': calculate_minimum_participation(previous_voters),
            'previous_voters': previous_voters,
            'last_calculation': datetime.now().isoformat()
        }

        self.save_data()

    def update_article_history(self, article_id: str, vote_result: Dict) -> None:
        """Actualiza el historial de un artículo después de una votación"""
        if article_id not in self.articles:
            return

        self.articles[article_id]['history'].append({
            'date': datetime.now().isoformat(),
            'voters_participated': vote_result['total_voters'],
            'vote_result': vote_result
        })

        self._recalculate_requirements(article_id)
        self.save_data()

    def save_data(self) -> None:
        """Guarda el estado actual de la constitución"""
        data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0",
                "total_articles": len(self.articles)
            },
            "articles": self.articles,
            "requirements_cache": {
                "last_calculated": datetime.now().isoformat(),
                "cache_duration_days": self.cache_duration.days,
                "by_article": self.requirements_cache['by_article']
            }
        }

        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
