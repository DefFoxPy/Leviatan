"""
Sistema de Delegación Líquida de Votos
=====================================

Este módulo implementa un sistema de democracia líquida donde:
- Cada votante tiene 1000 puntos base (1 voto completo)
- Los puntos pueden ser delegados parcialmente
- Las delegaciones pueden ser subdelegables o no
- Se mantiene 2 puntos reservado siempre
- Se detectan y resuelven ciclos de delegación

Características principales:
-------------------------
1. Delegación parcial de puntos
2. Subdelegación controlada
3. Detección de ciclos
4. Persistencia de datos
5. Trazabilidad de delegaciones

Clases:
-------
- Voter: Representa un votante con sus delegaciones y puntos
- DelegationSystem: Sistema general de delegación y gestión

Ejemplo de uso:
-------------
```python
system = DelegationSystem()
system.add_voter("voter1")
system.add_voter("voter2")
# Delegar 500 puntos, permitiendo subdelegación
system.delegate_points("voter1", "voter2", 500, subdelegable=True)
```
"""

import json
from datetime import datetime
import os
from typing import Dict, List, Set, Tuple

class Voter:
    """
    Representa un votante en el sistema de delegación líquida.
    
    Atributos:
        voter_id (str): Identificador único del votante
        delegations (Dict): Delegaciones realizadas {delegado: {puntos, subdelegable}}
        received_points (Dict): Puntos recibidos {delegador: {puntos, subdelegable}}
        base_points (int): Puntos base (1000 = 1 voto)
        available_points (int): Puntos disponibles para delegar
        reserved_points (int): Puntos reservados no delegables (siempre 1)
    """
    
    def __init__(self, voter_id: str):
        self.voter_id = voter_id
        self.delegations: Dict[str, Dict] = {}  # {delegate_id: {'points': int, 'subdelegable': bool}}
        self.received_points: Dict[str, Dict] = {}  # {from_voter: {'points': int, 'subdelegable': bool}}
        self.base_points = 1000
        self.RESERVED_POINTS = 2  # Aumentado de 1 a 2 puntos reservados
        self.available_points = self.base_points - self.RESERVED_POINTS
        
    def get_total_voting_power(self) -> Tuple[int, int]:
        subdelegable = sum(d['points'] for d in self.received_points.values() if d['subdelegable'])
        non_subdelegable = sum(d['points'] for d in self.received_points.values() if not d['subdelegable'])
        return (subdelegable, non_subdelegable)

    def get_delegatable_points(self) -> int:
        """Retorna el número de puntos que pueden ser delegados"""
        return self.available_points - self.RESERVED_POINTS

class DelegationSystem:
    """
    Sistema de gestión de delegaciones líquidas.
    
    Responsabilidades:
    1. Gestionar votantes y sus delegaciones
    2. Detectar y resolver ciclos de delegación
    3. Mantener persistencia de datos
    4. Validar operaciones de delegación
    
    Propiedades importantes:
    - Cada votante mantiene 1 punto reservado
    - Los ciclos se resuelven devolviendo puntos al origen
    - Las subdelegaciones son controladas por el delegador original
    """

    def __init__(self):
        self.voters: Dict[str, Voter] = {}
        self.data_file = "Data/delegations.json"
        self.load_data()
        self.debug_mode = True  # Para loggear detección de bucles

    def load_data(self) -> None:
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for voter_id, voter_data in data['voters']['nodes'].items():
                        voter = Voter(voter_id)
                        voter.delegations = voter_data['delegations']
                        voter.received_points = voter_data['received_points']
                        voter.base_points = voter_data['base_points']
                        voter.available_points = voter_data['available_points']
                        self.voters[voter_id] = voter
        except Exception as e:
            self.initialize_empty_data()

    def save_data(self) -> None:
        data = {
            "voters": {
                "voter_metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_voters": len(self.voters)
                },
                "nodes": {
                    voter_id: {
                        "delegations": voter.delegations,
                        "received_points": voter.received_points,
                        "base_points": voter.base_points,
                        "available_points": voter.available_points
                    } for voter_id, voter in self.voters.items()
                }
            }
        }
        
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def initialize_empty_data(self) -> None:
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump({"voters": {"voter_metadata": {"total_voters": 0}, "nodes": {}}}, f)

    def add_voter(self, voter_id: str) -> bool:
        if voter_id not in self.voters:
            self.voters[voter_id] = Voter(voter_id)
            self.save_data()
            return True
        return False

    def detect_cycles(self, start_voter: str) -> List[List[str]]:
        """
        Detecta ciclos en el grafo de delegación usando DFS.
        
        Args:
            start_voter (str): ID del votante desde donde empezar la búsqueda
            
        Returns:
            List[List[str]]: Lista de ciclos encontrados, cada uno como lista de IDs
        
        Ejemplo de ciclo: ["A", "B", "C", "A"] donde cada votante delegó al siguiente
        """
        def find_cycles_dfs(current: str, path: List[str], cycles: List[List[str]]):
            if current in path:
                cycle_start = path.index(current)
                cycles.append(path[cycle_start:])
                return
                
            path.append(current)
            if current in self.voters:
                for delegate in self.voters[current].delegations:
                    find_cycles_dfs(delegate, path.copy(), cycles)
        
        cycles = []
        find_cycles_dfs(start_voter, [], cycles)
        return cycles

    def clean_delegation_cycle(self, cycle: List[str]) -> None:
        """
        Limpia un ciclo de delegación devolviendo los puntos al origen.
        
        Proceso:
        1. Identifica el origen del ciclo
        2. Encuentra la menor cantidad de puntos en el ciclo
        3. Devuelve esos puntos al origen
        4. Mantiene el resto de delegaciones intactas
        
        Args:
            cycle (List[str]): Lista de IDs de votantes que forman el ciclo
        """
        if not cycle:
            return
            
        # Encontrar el origen del ciclo (primer votante)
        origin_voter = cycle[0]
        if origin_voter not in self.voters:
            return
            
        # Rastrear puntos a través del ciclo
        current = origin_voter
        points_in_cycle = float('inf')
        cycle_delegations = []
        
        # Encontrar la menor cantidad de puntos en el ciclo
        for i in range(len(cycle)):
            from_voter = cycle[i]
            to_voter = cycle[(i + 1) % len(cycle)]
            
            if from_voter in self.voters and to_voter in self.voters:
                delegator = self.voters[from_voter]
                if to_voter in delegator.delegations:
                    points = delegator.delegations[to_voter]['points']
                    points_in_cycle = min(points_in_cycle, points)
                    cycle_delegations.append((from_voter, to_voter, points))

        if points_in_cycle == float('inf'):
            return

        # Devolver los puntos al origen
        for from_voter, to_voter, points in cycle_delegations:
            delegator = self.voters[from_voter]
            receiver = self.voters[to_voter]
            
            # Reducir la delegación por la cantidad mínima del ciclo
            delegator.delegations[to_voter]['points'] -= points_in_cycle
            receiver.received_points[from_voter]['points'] -= points_in_cycle
            
            # Limpiar la delegación si llega a 0
            if delegator.delegations[to_voter]['points'] <= 0:
                del delegator.delegations[to_voter]
                del receiver.received_points[from_voter]
            
            # Si es el origen, recupera sus puntos
            if from_voter == origin_voter:
                delegator.available_points += points_in_cycle
                
            if self.debug_mode:
                print(f"Ciclo detectado: {points_in_cycle} puntos regresan a {origin_voter}")
                print(f"Reduciendo delegación {from_voter} -> {to_voter}")

        self.save_data()

    def delegate_points(self, from_voter: str, to_voter: str, points: int, subdelegable: bool = False) -> bool:
        """
        Delega puntos de un votante a otro.
        
        Args:
            from_voter (str): ID del delegador
            to_voter (str): ID del delegado
            points (int): Cantidad de puntos a delegar (1-999)
            subdelegable (bool): Si los puntos pueden ser subdelegados
            
        Returns:
            bool: True si la delegación fue exitosa
            
        Notas:
        - Verifica que se mantenga 1 punto reservado
        - Detecta y resuelve ciclos automáticamente
        - Actualiza la persistencia de datos
        """
        if from_voter not in self.voters or to_voter not in self.voters:
            return False
            
        delegator = self.voters[from_voter]
        delegatable_points = delegator.get_delegatable_points()
        
        if points > delegatable_points or points <= 0:
            return False
            
        # Realizar la delegación
        if to_voter not in delegator.delegations:
            delegator.delegations[to_voter] = {'points': 0, 'subdelegable': subdelegable}
        
        delegator.delegations[to_voter]['points'] += points
        delegator.available_points -= points
        
        receiver = self.voters[to_voter]
        if from_voter not in receiver.received_points:
            receiver.received_points[from_voter] = {'points': 0, 'subdelegable': subdelegable}
            
        receiver.received_points[from_voter]['points'] += points
        
        # Detectar y limpiar ciclos después de la delegación
        cycles = self.detect_cycles(from_voter)
        if cycles and self.debug_mode:
            print(f"Ciclos detectados: {cycles}")
        
        for cycle in cycles:
            self.clean_delegation_cycle(cycle)
            
        self.save_data()
        return True

    def get_delegation_chain(self, voter_id: str) -> List[Tuple[str, int]]:
        """
        Obtiene la cadena completa de delegaciones de un votante.
        
        Args:
            voter_id (str): ID del votante
            
        Returns:
            List[Tuple[str, int]]: Lista de (delegado, puntos) en orden de delegación
        """
        chain = []
        visited = set()
        
        def build_chain(current: str):
            if current in visited:
                return
            visited.add(current)
            
            if current in self.voters:
                voter = self.voters[current]
                for delegate, details in voter.delegations.items():
                    chain.append((delegate, details['points']))
                    build_chain(delegate)
        
        build_chain(voter_id)
        return chain

    def get_subdelegable_points_by_source(self, voter_id: str) -> Dict[str, int]:
        """
        Retorna un diccionario con los puntos subdelegables disponibles por cada fuente
        """
        if voter_id not in self.voters:
            return {}
            
        voter = self.voters[voter_id]
        return {
            from_voter: details['points'] 
            for from_voter, details in voter.received_points.items() 
            if details['subdelegable']
        }

    def subdelegate_points(self, from_voter: str, to_voter: str, points: int) -> bool:
        """
        Subdelega puntos recibidos que fueron marcados como subdelegables.
        
        Args:
            from_voter (str): ID del subdelegador
            to_voter (str): ID del nuevo delegado
            points (int): Cantidad de puntos a subdelegar
            
        Returns:
            bool: True si la subdelegación fue exitosa
            
        Verifica:
        1. Que los puntos sean originalmente subdelegables
        2. Que no excedan los puntos subdelegables disponibles
        3. Que se mantenga el punto reservado
        """
        if from_voter not in self.voters or to_voter not in self.voters:
            return False
            
        delegator = self.voters[from_voter]
        delegatable_points = min(
            sum(
                details['points'] 
                for details in delegator.received_points.values() 
                if details['subdelegable']
            ),
            delegator.get_delegatable_points()
        )
        
        if points > delegatable_points or points <= 0:
            return False
            
        # Los puntos subdelegados no pueden ser subdelegados nuevamente
        return self.delegate_points(from_voter, to_voter, points, subdelegable=False)

    def revoke_delegation(self, from_voter: str, to_voter: str) -> bool:
        if from_voter not in self.voters or to_voter not in self.voters:
            return False
            
        delegator = self.voters[from_voter]
        receiver = self.voters[to_voter]
        
        if to_voter not in delegator.delegations:
            return False
            
        points = delegator.delegations[to_voter]['points']
        delegator.available_points += points
        del delegator.delegations[to_voter]
        del receiver.received_points[from_voter]
        
        self.save_data()
        return True

    def get_all_descendants(self, voter_id: str, visited: Set[str] = None) -> Set[str]:
        if visited is None:
            visited = set()
        
        if voter_id not in self.voters or voter_id in visited:
            return visited
        
        visited.add(voter_id)
        for delegate in self.voters[voter_id].delegations:
            self.get_all_descendants(delegate, visited)
        
        return visited

    def get_total_delegated_points(self, user_id: str, visited=None) -> int:
        """Recursively calculate total points under a user's control"""
        if visited is None:
            visited = set()
        
        if user_id in visited:
            return 0  # Prevent cycles
            
        visited.add(user_id)
        total = 0
        
        # Get direct delegations to this user
        delegations = self.get_delegations_to(user_id)
        for delegation in delegations:
            total += delegation.points
            # Add subdelegated points
            total += self.get_total_delegated_points(delegation.from_id, visited)
            
        return total

    def revoke_delegation(self, from_id: str, to_id: str) -> tuple[bool, int]:
        """
        Revokes delegation and returns all points from subdelegations
        Returns: (success, total_points_recovered)
        """
        # Get points before breaking the delegation chain
        points_to_recover = self.get_total_delegated_points(to_id)
        
        # Remove the direct delegation
        if not self._remove_delegation(from_id, to_id):
            return False, 0
            
        # Reset all subdelegations recursively
        self._reset_subdelegations(to_id)
        
        # Return points to original delegator
        self.voters[from_id].available_points += points_to_recover
        
        return True, points_to_recover
        
    def _reset_subdelegations(self, user_id: str, visited=None):
        """Recursively reset all subdelegations"""
        if visited is None:
            visited = set()
            
        if user_id in visited:
            return
            
        visited.add(user_id)
        
        # Get all subdelegations
        delegations = self.get_delegations_from(user_id)
        for delegation in delegations:
            # Reset subdelegations first
            self._reset_subdelegations(delegation.to_id, visited)
            # Remove this delegation
            self._remove_delegation(user_id, delegation.to_id)