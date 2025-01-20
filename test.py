import json
import heapq
from math import radians, sin, cos, sqrt, atan2
import folium
from shapely.geometry import Point, Polygon, LineString

class SafeRouteFinder:
    def __init__(self, routing_table, tolerance_meters=75):
        self.routing_table = routing_table
        self.danger_nodes = set()
        self.danger_polygons = []
        self.tolerance_meters = tolerance_meters
        print(f"Initialized with {len(routing_table)} nodes and {tolerance_meters}m tolerance")

    def find_nearest_node(self, coords):
        """Find the nearest node in the routing table to given coordinates"""
        lat, lon = coords
        target = f"{lat},{lon}"
        nearest_node = min(
            self.routing_table.keys(),
            key=lambda node: self.haversine_distance(node, target)
        )
        return nearest_node

    def add_danger_zone(self, coordinates):
        """Add a polygon danger zone"""
        shapely_coords = [(lon, lat) for lat, lon in coordinates]
        polygon = Polygon(shapely_coords)
        self.danger_polygons.append(polygon)
        
        for node in self.routing_table.keys():
            node_lat, node_lon = map(float, node.split(','))
            if polygon.contains(Point(node_lon, node_lat)):
                self.danger_nodes.add(node)
        
        print(f"Added danger zone with {len(coordinates)} vertices")
        return polygon

    def calculate_intersection_length(self, start_point, end_point, danger_zone):
        """Calculate the length of intersection between a road segment and danger zone"""
        start_lat, start_lon = map(float, start_point.split(','))
        end_lat, end_lon = map(float, end_point.split(','))
        road = LineString([(start_lon, start_lat), (end_lon, end_lat)])
        
        if danger_zone.intersects(road):
            intersection = danger_zone.intersection(road)
            if intersection.geom_type == 'LineString':
                return self.haversine_distance(
                    f"{intersection.coords[0][1]},{intersection.coords[0][0]}",
                    f"{intersection.coords[-1][1]},{intersection.coords[-1][0]}"
                ) * 1000  
        return 0

    def is_segment_safe(self, start_point, end_point):
        """Check if a road segment is safe considering tolerance"""
        total_intersection = 0
        for zone in self.danger_polygons:
            intersection_length = self.calculate_intersection_length(start_point, end_point, zone)
            total_intersection += intersection_length
            if total_intersection > self.tolerance_meters:
                return False
        return True

    def find_safe_route(self, start_coords, end_coords):
        """Find a route avoiding danger zones with tolerance"""
        print(f"\nFinding route from {start_coords} to {end_coords}")
        
        start_node = self.find_nearest_node(start_coords)
        end_node = self.find_nearest_node(end_coords)
        
        print(f"Nearest start node: {start_node}")
        print(f"Nearest end node: {end_node}")
        
        distances = {node: float('infinity') for node in self.routing_table.keys()}
        distances[start_node] = 0
        pq = [(0, start_node)]
        previous = {node: None for node in self.routing_table.keys()}
        danger_intersections = {node: 0 for node in self.routing_table.keys()}
        visited = set()
        
        while pq:
            current_distance, current = heapq.heappop(pq)
            
            if current in visited:
                continue
                
            visited.add(current)
            
            if current == end_node:
                break
            
            for neighbor in self.routing_table[current]:
                neighbor_node = neighbor['destination']
                
                intersection_length = 0
                for zone in self.danger_polygons:
                    intersection_length += self.calculate_intersection_length(
                        current, neighbor_node, zone)
                
                if intersection_length > self.tolerance_meters:
                    continue
                    
                distance = current_distance + neighbor['distance']
                new_intersection = danger_intersections[current] + intersection_length
                
                if (distance < distances[neighbor_node] or 
                    (distance == distances[neighbor_node] and 
                     new_intersection < danger_intersections[neighbor_node])):
                    distances[neighbor_node] = distance
                    danger_intersections[neighbor_node] = new_intersection
                    previous[neighbor_node] = current
                    heapq.heappush(pq, (distance, neighbor_node))
        
        if distances[end_node] == float('infinity'):
            raise ValueError("No safe route found")
            
        path = []
        current = end_node
        
        while current is not None:
            path.append(current)
            current = previous[current]
        
        path.reverse()
        
        total_intersection = danger_intersections[end_node]
        print(f"Total intersection with danger zones: {total_intersection:.1f} meters")
        
        return path, distances[end_node]

    @staticmethod
    def haversine_distance(coord1_str, coord2_str):
        """Calculate the distance between two points"""
        def str_to_coord(s):
            return tuple(map(float, s.split(',')))
        
        coord1 = str_to_coord(coord1_str)
        coord2 = str_to_coord(coord2_str)
        
        R = 6371  
        lat1, lon1 = map(radians, coord1)
        lat2, lon2 = map(radians, coord2)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

def create_route_map(path, danger_zones, start_name, end_name, start_coords, end_coords):
    """Create an HTML map with the route and danger zones"""
    def str_to_coord(s):
        return tuple(map(float, s.split(',')))
    
    center_lat = (start_coords[0] + end_coords[0]) / 2
    center_lon = (start_coords[1] + end_coords[1]) / 2
    m = folium.Map(location=(center_lat, center_lon), zoom_start=12)
    
    for zone in danger_zones:
        coords = list(zone.exterior.coords)
        coords = [(lat, lon) for lon, lat in coords]
        folium.Polygon(
            locations=coords,
            color='red',
            weight=2,
            fill=True,
            fillColor='red',
            fillOpacity=0.3,
            popup='Danger Zone'
        ).add_to(m)
    
    folium.Marker(
        start_coords,
        popup=f'Start: {start_name}',
        icon=folium.Icon(color='green')
    ).add_to(m)
    
    folium.Marker(
        end_coords,
        popup=f'End: {end_name}',
        icon=folium.Icon(color='red')
    ).add_to(m)
    
    route_coords = [str_to_coord(point) for point in path]
    folium.PolyLine(
        route_coords,
        weight=4,
        color='blue',
        opacity=0.8
    ).add_to(m)
    
    m.save('safe_route.html')

def main():
    locations = {
        "A": (21.179206042997826, 79.05441631195121),
        "B": (21.17764658441052, 79.06716588500915)
    }
    
    print("Loading routing table...")
    with open('routing-table-nagpur.json', 'r') as f:
        routing_table = json.load(f)
    
    route_finder = SafeRouteFinder(routing_table, tolerance_meters=40)
    
    danger_zone = [
        (21.17803196117215, 79.06196963813251),
        (21.178031961172145, 79.06196963813251),
        (21.175329258469443, 79.06196963813251),
        (21.175329258469443, 79.05907141880003),
        (21.178031961172145, 79.05907141880003),
        (21.17803196117215,79.05907141880003),
        (21.18073466387485,79.05907141880003),
        (21.18073466387485,79.06196963813251),
        (21.17803196117215,79.06196963813251)

    ]
    route_finder.add_danger_zone(danger_zone)
    
    print("\nAvailable locations:")
    for i, (name, coords) in enumerate(locations.items(), 1):
        print(f"{i}. {name}")
    
    try:
        start_idx = int(input("\nEnter number for start location: ")) - 1
        end_idx = int(input("\nEnter number for destination location: ")) - 1
        
        locations = list(locations.items())
        start_name, start_coords = locations[start_idx]
        end_name, end_coords = locations[end_idx]
        
        print(f"\nCalculating safe route from {start_name} to {end_name}...")
        path, total_distance = route_finder.find_safe_route(start_coords, end_coords)
        
        print(f"\nSafe route found!")
        print(f"Total distance: {total_distance:.2f} km")
        
        print("\nCreating route map...")
        create_route_map(path, route_finder.danger_polygons, start_name, end_name, 
                        start_coords, end_coords)
        print("Route map saved as 'safe_route.html'")
        
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()