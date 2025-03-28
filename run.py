import yaml
from src.data.osm_loader import OSMLoader
from src.data.network_builder import RoadNetworkBuilder
from src.optimization.aco_optimizer import ACOOptimizer
from src.visualization.map_plotter import MapVisualizer

def main():
    # Load configuration
    with open('config/params.yml') as f:
        params = yaml.safe_load(f)
    
    # 1. Load and prepare road network
    loader = OSMLoader()
    city = 'seattle'  # Change to your target city
    
    print(f"\nLoading road network for {city}...")
    G = loader.get_city_network(city)
    if G is None:
        print("Failed to load network")
        return
        
    # 2. Build and enhance network
    print("\nBuilding transport network...")
    builder = RoadNetworkBuilder(G)
    builder.calculate_edge_weights()
    
    # 3. Select stops (in practice, load from GTFS or other source)
    print("\nSelecting transport stops...")
    important_nodes = list(G.nodes)[:10]  # First 10 nodes as example stops
    
    # 4. Run optimization
    print("\nRunning route optimization...")
    optimizer = ACOOptimizer(builder.graph, params['aco'])
    routes, stats = optimizer.optimize(important_nodes)
    
    if not routes:
        print("No routes generated")
        return
        
    # 5. Visualize results
    print("\nVisualizing results...")
    visualizer = MapVisualizer(builder.graph)
    
    # Visualize best route
    visualizer.plot_route(routes[0], 'data/outputs/best_route.html')
    
    # Visualize network
    visualizer.plot_network('data/outputs/road_network.html')
    
    print("\nOptimization complete!")
    print(f"Best route cost: {routes[0]['cost']:.2f}")
    print(f"Visualizations saved to data/outputs/")

if __name__ == '__main__':
    main()