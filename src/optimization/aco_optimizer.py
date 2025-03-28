import numpy as np
import networkx as nx
from tqdm import tqdm
from collections import defaultdict
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ACOOptimizer:
    def __init__(self, graph, params):
        self.graph = graph
        self.params = params
        self.pheromones = self._init_pheromones()
        
    def _init_pheromones(self):
        """Initialize pheromone matrix"""
        pheromones = defaultdict(dict)
        for u, v, data in self.graph.edges(data=True):
            pheromones[u][v] = self.params['initial_pheromone']
            pheromones[v][u] = self.params['initial_pheromone']
        return pheromones
        
    def optimize(self, stops, max_routes=5):
        """Optimize routes between given stops"""
        if len(stops) < 2:
            logger.error("Need at least 2 stops for optimization")
            return []
            
        best_routes = []
        stats = {'iterations': [], 'best_cost': []}
        
        for iteration in tqdm(range(self.params['iterations']), desc="ACO Optimization"):
            routes = []
            for _ in range(self.params['ants']):
                route = self._construct_route(stops)
                if route:
                    routes.append(route)
            
            if routes:
                self._update_pheromones(routes)
                self._evaporate_pheromones()
                
                current_best = min(routes, key=lambda x: x['cost'])
                best_routes.append(current_best)
                
                stats['iterations'].append(iteration)
                stats['best_cost'].append(current_best['cost'])
                
        # Return top N unique routes
        unique_routes = []
        seen = set()
        
        for route in sorted(best_routes, key=lambda x: x['cost']):
            path_str = str(route['path'])
            if path_str not in seen and len(unique_routes) < max_routes:
                seen.add(path_str)
                unique_routes.append(route)
                
        logger.info(f"Found {len(unique_routes)} optimized routes")
        return unique_routes, stats
        
    def _construct_route(self, stops):
        """Construct a route using ACO"""
        from random import choices
        
        remaining = set(stops)
        current = stops[0]
        remaining.remove(current)
        path = []
        
        while remaining:
            # Get possible next stops
            candidates = list(remaining)
            
            # Calculate probabilities
            probabilities = []
            total = 0.0
            
            for node in candidates:
                try:
                    # Find shortest path between current and candidate
                    path_nodes = nx.shortest_path(
                        self.graph, current, node, weight='weight')
                    
                    # Calculate pheromone and heuristic for the path
                    pheromone = 1.0
                    heuristic = 0.0
                    
                    for i in range(len(path_nodes)-1):
                        u, v = path_nodes[i], path_nodes[i+1]
                        pheromone *= self.pheromones[u].get(v, 1e-10)
                        heuristic += 1 / self.graph[u][v]['weight']
                    
                    value = (pheromone ** self.params['alpha']) * (heuristic ** self.params['beta'])
                    probabilities.append(value)
                    total += value
                except nx.NetworkXNoPath:
                    probabilities.append(0)
                    
            if total <= 0:
                break
                
            # Normalize probabilities
            probabilities = [p/total for p in probabilities]
            
            # Select next stop
            next_node = choices(candidates, weights=probabilities, k=1)[0]
            
            # Get the actual path taken
            try:
                path_nodes = nx.shortest_path(self.graph, current, next_node, weight='weight')
                for i in range(len(path_nodes)-1):
                    path.append((path_nodes[i], path_nodes[i+1]))
            except nx.NetworkXNoPath:
                break
                
            current = next_node
            remaining.remove(current)
            
        if not path:
            return None
            
        # Calculate total cost
        cost = sum(self.graph[u][v]['weight'] for u, v in path)
        
        return {'path': path, 'cost': cost, 'nodes': list(set([u for u, _ in path] + [path[-1][1]]))}
        
    def _update_pheromones(self, routes):
        """Update pheromones based on ant solutions"""
        for route in routes:
            delta = self.params['q'] / route['cost']
            for u, v in route['path']:
                self.pheromones[u][v] += delta
                self.pheromones[v][u] += delta
                
    def _evaporate_pheromones(self):
        """Evaporate pheromones"""
        for u in self.pheromones:
            for v in self.pheromones[u]:
                self.pheromones[u][v] *= (1 - self.params['evaporation'])