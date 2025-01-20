import requests
import json
import networkx as nx
from collections import defaultdict
from math import radians, sin, cos, sqrt, atan2

def coord_to_string(coord):
    """Convert coordinate tuple to string"""
    return f"{coord[0]},{coord[1]}"

def string_to_coord(s):
    """Convert string back to coordinate tuple"""
    lat, lon = map(float, s.split(','))
    return (lat, lon)

def fetch_delhi_roads():
    """
    Fetch road data from Overpass API for Delhi
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json][timeout:60];
    // Define the bounding box for Nagpur city
    (
    way["highway"](21.0110,78.0062,21.2156,79.2296);
    );
    out body;
    >;
    out skel qt;
    """
    
    response = requests.post(overpass_url, data=overpass_query)
    return response.json()

def calculate_distance(point1, point2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371 

    lat1, lon1 = point1
    lat2, lon2 = point2
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def create_road_graph(data):
    """
    Create a NetworkX graph from OSM data
    """
    G = nx.Graph()

    nodes = {}
    for element in data['elements']:
        if element['type'] == 'node':
            nodes[element['id']] = (element['lat'], element['lon'])

    for element in data['elements']:
        if element['type'] == 'way' and 'tags' in element and 'highway' in element['tags']:
            road_type = element['tags']['highway']
            road_name = element['tags'].get('name', 'unnamed')
            oneway = element['tags'].get('oneway', 'no') == 'yes'
            
            for i in range(len(element['nodes']) - 1):
                node1_id = element['nodes'][i]
                node2_id = element['nodes'][i + 1]
                
                if node1_id in nodes and node2_id in nodes:
                    point1 = nodes[node1_id]
                    point2 = nodes[node2_id]
                    
                    distance = calculate_distance(point1, point2)
                    
                    G.add_edge(
                        point1, 
                        point2, 
                        distance=distance,
                        road_type=road_type,
                        name=road_name,
                        oneway=oneway
                    )
    
    return G

def create_routing_table(G):
    """
    Create routing table from road network graph
    """
    routing_table = defaultdict(list)
    
    for node in G.nodes():
        node_str = coord_to_string(node)
        for neighbor in G.neighbors(node):
            edge_data = G.get_edge_data(node, neighbor)
            
            entry = {
                'destination': coord_to_string(neighbor),
                'next_hop': coord_to_string(neighbor),
                'distance': edge_data['distance'],
                'road_type': edge_data['road_type'],
                'road_name': edge_data['name'],
                'oneway': edge_data['oneway']
            }
            
            routing_table[node_str].append(entry)
    
    return dict(routing_table)

def save_routing_table(routing_table, filename):
    """Save routing table with proper serialization"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(routing_table, f, ensure_ascii=False, indent=2)

def main():
    try:
        print("Fetching road data...")
        data = fetch_delhi_roads()
        
        print("Creating road network graph...")
        G = create_road_graph(data)
        
        print("Generating routing table...")
        routing_table = create_routing_table(G)
        
        print("Saving routing table...")
        save_routing_table(routing_table, 'routing-table-nagpur.json')
        
        print("\nStatistics:")
        print(f"Number of nodes: {len(routing_table)}")
        total_routes = sum(len(routes) for routes in routing_table.values())
        print(f"Total routes: {total_routes}")
        print(f"Average routes per node: {total_routes/len(routing_table):.2f}")
        print("\nRouting table saved to delhi_routing_table.json")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()