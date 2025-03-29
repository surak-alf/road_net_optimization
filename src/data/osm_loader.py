import osmnx as ox
import yaml
import os
from pathlib import Path
from ..utils.logger import get_logger
import time

logger = get_logger(__name__)

class OSMLoader:
    def __init__(self, config_path='config/cities.yml'):
        ox.settings.log_console = False
        ox.settings.use_cache = True
        ox.settings.cache_folder = Path('data/raw/osmnx_cache')
        ox.settings.timeout = 600
        
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
    def get_city_network(self, city_name, network_type='drive', retries=3):
        """Download road network with retry logic"""
        city = self.config['cities'][city_name]
        logger.info(f"Attempting to download network for {city['name']}")
        
        # Try multiple servers
        servers = [
            "https://overpass-api.de/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
        ]
        
        for attempt in range(retries):
            for server in servers:
                try:
                    ox.settings.overpass_endpoint = server
                    logger.info(f"Attempt {attempt+1} using {server}")
                    
                    # Try smaller area if first attempt fails
                    if attempt > 0:
                        bbox = self._get_smaller_bbox(city['bbox'], attempt)
                    else:
                        bbox = city['bbox']
                    
                    G = ox.graph_from_bbox(
                        north=bbox[0],
                        south=bbox[1],
                        east=bbox[2],
                        west=bbox[3],
                        network_type=network_type,
                        simplify=True,
                        retain_all=False
                    )
                    
                    logger.info("Download successful!")
                    return G
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
                    time.sleep(5)  # Wait before retrying
        
        logger.error("All download attempts failed")
        return None
        
    def _get_smaller_bbox(self, original_bbox, attempt):
        """Reduce bbox size with each attempt"""
        lat_range = original_bbox[0] - original_bbox[1]
        lon_range = original_bbox[2] - original_bbox[3]
        
        reduction = 0.5 ** (attempt + 1)  # Halve the area each time
        
        new_north = original_bbox[0] - (lat_range * reduction / 2)
        new_south = original_bbox[1] + (lat_range * reduction / 2)
        new_east = original_bbox[2] - (lon_range * reduction / 2)
        new_west = original_bbox[3] + (lon_range * reduction / 2)
        
        return [new_north, new_south, new_east, new_west]
        
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