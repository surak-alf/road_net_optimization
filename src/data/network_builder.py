import osmnx as ox
import networkx as nx
import pandas as pd
from tqdm import tqdm
from ..utils.logger import get_logger

logger = get_logger(__name__)

class RoadNetworkBuilder:
    def __init__(self, graph):
        self.graph = graph
        self.nodes, self.edges = ox.graph_to_gdfs(graph)
        self._add_default_speeds()
        
    def _add_default_speeds(self):
        """Add default speeds based on road types"""
        for u, v, data in self.graph.edges(data=True):
            if 'maxspeed' not in data:
                road_type = data.get('highway', 'residential')
                if isinstance(road_type, list):
                    road_type = road_type[0]
                
                # Get default speed from config
                if hasattr(self, 'default_speeds'):
                    data['maxspeed'] = self.default_speeds.get(road_type, 25)
                else:
                    data['maxspeed'] = 25
                    
    def add_transport_stops(self, stops_gdf):
        """Integrate transport stops into the network"""
        if stops_gdf is None or stops_gdf.empty:
            logger.warning("No stops provided")
            return
            
        # Snap stops to nearest network nodes
        self.stops = ox.distance.nearest_nodes(
            self.graph, 
            stops_gdf.geometry.x.values,
            stops_gdf.geometry.y.values
        )
        logger.info(f"Added {len(self.stops)} transport stops")
        
    def calculate_edge_weights(self):
        """Compute weights considering multiple factors"""
        # Calculate travel times
        self.graph = ox.speed.add_edge_speeds(self.graph)
        self.graph = ox.speed.add_edge_travel_times(self.graph)
        
        # Enhance with custom weights
        for u, v, data in tqdm(self.graph.edges(data=True), desc="Calculating weights"):
            # Base weight (travel time in seconds)
            weight = data['travel_time']
            
            # Adjust for road type
            road_type = data.get('highway', 'unclassified')
            if isinstance(road_type, list):
                road_type = road_type[0]
                
            if road_type in ['motorway', 'trunk']:
                weight *= 0.9  # Prefer highways
            elif road_type in ['residential', 'service']:
                weight *= 1.2  # Avoid small roads
                
            # Adjust for lanes
            lanes = data.get('lanes', 1)
            if isinstance(lanes, list):
                lanes = int(lanes[0])
            try:
                lanes = int(lanes)
                weight *= (4 / max(1, lanes))
            except (ValueError, TypeError):
                pass
                
            data['weight'] = weight
            
        logger.info("Edge weights calculated")
        
    def get_network_stats(self):
        """Return network statistics"""
        stats = {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges),
            'avg_degree': sum(dict(self.graph.degree()).values()) / len(self.graph.nodes),
            'road_types': pd.Series(
                [data.get('highway', 'unknown') for _, _, data in self.graph.edges(data=True)]
            ).value_counts().to_dict()
        }
        return stats