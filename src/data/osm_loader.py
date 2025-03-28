import osmnx as ox
import yaml
import os
from pathlib import Path
from ..utils.logger import get_logger

logger = get_logger(__name__)

class OSMLoader:
    def __init__(self, config_path='config/cities.yml'):
        ox.config(use_cache=True, log_console=False)
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
    def get_city_network(self, city_name, network_type='drive'):
        """Download road network for a city"""
        try:
            city = self.config['cities'][city_name]
            logger.info(f"Downloading network for {city['name']}")
            
            # Download by bounding box for more reliability
            G = ox.graph_from_bbox(
                north=city['bbox'][0],
                south=city['bbox'][1],
                east=city['bbox'][2],
                west=city['bbox'][3],
                network_type=network_type,
                simplify=True
            )
            return G
        except Exception as e:
            logger.error(f"Error downloading data: {str(e)}")
            return None
            
    def save_network(self, G, city_name):
        """Save network to file"""
        output_dir = Path('data/processed') / city_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ox.save_graphml(G, output_dir / 'road_network.graphml')
        logger.info(f"Saved network to {output_dir}")
        
    def load_network(self, city_name):
        """Load network from file"""
        filepath = Path('data/processed') / city_name / 'road_network.graphml'
        if filepath.exists():
            return ox.load_graphml(filepath)
        return None