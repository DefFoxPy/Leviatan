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
    def __init__(self):
        self.data_file = "Data/constitution.json"
        self.articles: Dict = {}
        self.requirements_cache: Dict = {}
        self.cache_duration = timedelta(days=7)
        self.load_data()

    def load_data(self) -> None:
        """Carga la constitución y su caché de requisitos"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.articles = data['articles']
                self.requirements_cache = data.get('requirements_cache', {
                    "last_calculated": datetime.now().isoformat(),
                    "by_article": {}
                })
        except FileNotFoundError:
            self.initialize_empty_constitution()

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

    def calculate_proposal_requirements(self, article_ids: List[str]) -> Dict:
        """Calcula requisitos para una propuesta basado en sus artículos"""
        if "0" in article_ids:
            return {
                "required_voters": float('-inf'),
                "min_participation": 0,
                "governing_article": "0",
                "total_articles": len(article_ids),
                "immutable": True
            }

        requirements = []
        for article_id in article_ids:
            req = self.get_article_requirements(article_id)
            if req:
                requirements.append({**req, "article_id": article_id})

        if not requirements:
            return None

        # El artículo que requiere más votantes gobierna la propuesta
        governing_req = max(requirements, key=lambda x: x['required_voters'])

        return {
            "required_voters": governing_req['required_voters'],
            "min_participation": governing_req['min_participation'],
            "governing_article": governing_req['article_id'],
            "total_articles": len(article_ids)
        }

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
