# Custom Routing System

A Python-based routing system that fetches road network data from OpenStreetMap via the Overpass API, creates a routing table, and implements safe route finding algorithms with danger zone avoidance.

## Features

- Fetches road network data for specific geographic areas using Overpass API
- Converts OpenStreetMap data into a structured routing table
- Implements safe route finding with configurable danger zone avoidance
- Supports visualization of routes and danger zones using Folium
- Calculates distances using the Haversine formula for geographic accuracy

## Project Structure

The project consists of two main Python files:

### main.py
- Fetches road data from OpenStreetMap
- Creates a road network graph using NetworkX
- Generates and saves the routing table
- Functions:
  - `fetch_roads()`: Retrieves road data from Overpass API
  - `create_road_graph()`: Converts OSM data to NetworkX graph
  - `create_routing_table()`: Generates routing table from the graph
  - `save_routing_table()`: Saves the routing table to JSON format

### test.py
- Implements the SafeRouteFinder class for route calculation
- Handles danger zone definition and avoidance
- Creates visual route maps
- Key features:
  - Custom tolerance for danger zone proximity
  - Route visualization with Folium
  - Interactive location selection
  - Distance calculations

## Dependencies

- networkx
- requests
- folium
- shapely
- json
- heapq
- math

## Installation

1. Clone the repository
2. Install required packages:
```bash
pip install networkx requests folium shapely
```

## Usage

1. Generate the routing table:
```bash
python main.py
```

2. Find safe routes:
```bash
python test.py
```

The system will:
- Load the routing table
- Allow you to select start and end locations
- Calculate a safe route avoiding danger zones
- Generate an HTML map showing the route and danger zones

## Configuration

- Danger zones can be defined using coordinate polygons
- Tolerance for danger zone proximity can be adjusted (default: 40 meters)
- Custom locations can be added to the locations dictionary

## Output

- Routing table is saved as 'routing-table-nagpur.json'
- Route visualization is saved as 'safe_route.html'

## Algorithm Details

The routing system uses:
- Haversine formula for distance calculations
- A* pathfinding with danger zone avoidance
- Polygon intersection checking for safety verification
- NetworkX for graph operations

