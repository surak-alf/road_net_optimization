import folium
import osmnx as ox
import branca.colormap as cm
from ..utils.logger import get_logger

logger = get_logger(__name__)

class MapVisualizer:
    def __init__(self, graph):
        self.graph = graph
        self.nodes, self.edges = ox.graph_to_gdfs(graph)
        self.colormap = cm.LinearColormap(
            ['green', 'yellow', 'red'],
            vmin=0,
            vmax=100
        )
        
    def plot_route(self, route, filepath='route.html'):
        """Visualize optimized route on interactive map"""
        if not route or not route['path']:
            logger.error("No valid route provided")
            return None
            
        # Get center of the route
        route_nodes = list(set([u for u, _ in route['path']] + [route['path'][-1][1]]))
        avg_lat = self.nodes.loc[route_nodes].y.mean()
        avg_lon = self.nodes.loc[route_nodes].x.mean()
        
        # Create map
        route_map = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=13,
            tiles='cartodbpositron'
        )
        
        # Add route
        route_coords = []
        for u, v in route['path']:
            u_data = self.nodes.loc[u]
            v_data = self.nodes.loc[v]
            route_coords.append([u_data.y, u_data.x])
            route_coords.append([v_data.y, v_data.x])
            
        folium.PolyLine(
            route_coords,
            color='#0066cc',
            weight=5,
            opacity=0.7
        ).add_to(route_map)
        
        # Add stops
        for node in route['nodes']:
            node_data = self.nodes.loc[node]
            folium.CircleMarker(
                location=[node_data.y, node_data.x],
                radius=8,
                color='#cc0000',
                fill=True,
                fill_color='#ffffff',
                fill_opacity=1,
                popup=f"Stop: {node}"
            ).add_to(route_map)
            
        # Save to file
        route_map.save(filepath)
        logger.info(f"Saved route visualization to {filepath}")
        return route_map
        
    def plot_network(self, filepath='network.html'):
        """Visualize entire road network"""
        # Create map centered on the network
        avg_lat = self.nodes.y.mean()
        avg_lon = self.nodes.x.mean()
        
        network_map = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=12,
            tiles='cartodbpositron'
        )
        
        # Sample edges for visualization (full network may be too dense)
        edges_sample = self.edges.sample(min(1000, len(self.edges)))
        
        for _, edge in edges_sample.iterrows():
            folium.PolyLine(
                [ [edge['geometry'].coords[0][1], edge['geometry'].coords[0][0]],
                  [edge['geometry'].coords[-1][1], edge['geometry'].coords[-1][0]] ],
                color='#666666',
                weight=1,
                opacity=0.5
            ).add_to(network_map)
            
        network_map.save(filepath)
        logger.info(f"Saved network visualization to {filepath}")
        return network_map