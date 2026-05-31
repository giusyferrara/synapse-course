"""
London Transport API Integration
==================================
Official Transport for London (TfL) API integration for teaching Python

This module provides:
1. Real-time London transport data (Tube, Bus, DLR, Trams)
2. Educational scaffolding for API learning
3. Database storage for analytics
4. Mock data for offline learning

Official TfL API: https://api.tfl.gov.uk/
Documentation: https://api.tfl.gov.uk/swagger/ui/index.html
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class LondonTransportTracker:
    """
    Transport for London (TfL) API Integration
    
    Teaches students:
    - Making HTTP requests to official UK government APIs
    - Parsing JSON responses
    - Error handling
    - Real-time data processing
    - Working with location data
    """
    
    def __init__(self, app_key: Optional[str] = None, use_mock: bool = False):
        """
        Initialize TfL tracker
        
        Args:
            app_key: TfL API key (free from api-portal.tfl.gov.uk)
            use_mock: Use mock data for offline learning
        """
        self.app_key = app_key
        self.use_mock = use_mock
        self.base_url = "https://api.tfl.gov.uk"
        
    def get_tube_lines(self) -> Dict[str, Any]:
        """
        Get all London Underground lines
        
        Educational value:
        - First API call lesson
        - Understanding JSON responses
        - Error handling basics
        
        Returns:
            Dictionary with tube lines information
        """
        if self.use_mock:
            return self._mock_tube_lines()
            
        try:
            url = f"{self.base_url}/Line/Mode/tube"
            params = {}
            if self.app_key:
                params['app_key'] = self.app_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            lines = response.json()
            
            return {
                'success': True,
                'lines': lines,
                'count': len(lines),
                'explanation': "Successfully retrieved London Underground lines!"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'explanation': "Failed to connect to TfL API. Check your internet connection.",
                'learning_tip': "This is a common error when working with APIs. Always handle network errors!"
            }
    
    def get_bus_routes(self) -> Dict[str, Any]:
        """
        Get London bus routes
        
        Educational value:
        - Working with multiple transport modes
        - Filtering data
        - Understanding API endpoints
        
        Returns:
            Dictionary with bus routes information
        """
        if self.use_mock:
            return self._mock_bus_routes()
            
        try:
            url = f"{self.base_url}/Line/Mode/bus"
            params = {}
            if self.app_key:
                params['app_key'] = self.app_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            routes = response.json()
            
            return {
                'success': True,
                'routes': routes[:50],  # Limit to first 50 for learning
                'count': len(routes),
                'explanation': f"Found {len(routes)} London bus routes!"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_stop_arrivals(self, stop_id: str) -> Dict[str, Any]:
        """
        Get real-time arrivals at a stop
        
        Educational value:
        - Working with real-time data
        - Parsing timestamps
        - Sorting and filtering results
        
        Args:
            stop_id: TfL stop point ID (e.g., "940GZZLUKSX" for King's Cross)
            
        Returns:
            Dictionary with arrival predictions
        """
        if self.use_mock:
            return self._mock_arrivals(stop_id)
            
        try:
            url = f"{self.base_url}/StopPoint/{stop_id}/Arrivals"
            params = {}
            if self.app_key:
                params['app_key'] = self.app_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            arrivals = response.json()
            
            # Sort by time to station
            arrivals.sort(key=lambda x: x.get('timeToStation', 999999))
            
            # Format for students
            formatted_arrivals = []
            for arrival in arrivals[:10]:  # First 10 arrivals
                formatted_arrivals.append({
                    'line': arrival.get('lineName'),
                    'destination': arrival.get('destinationName'),
                    'platform': arrival.get('platformName'),
                    'time_to_station': arrival.get('timeToStation', 0) // 60,  # Convert to minutes
                    'expected_arrival': arrival.get('expectedArrival'),
                    'current_location': arrival.get('currentLocation')
                })
            
            return {
                'success': True,
                'stop_id': stop_id,
                'arrivals': formatted_arrivals,
                'count': len(formatted_arrivals),
                'timestamp': datetime.now().isoformat(),
                'explanation': f"Found {len(formatted_arrivals)} upcoming arrivals"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stop_id': stop_id
            }
    
    def search_stops(self, query: str) -> Dict[str, Any]:
        """
        Search for stops by name
        
        Educational value:
        - Query parameters
        - Searching and filtering
        - Working with location data
        
        Args:
            query: Search term (e.g., "Oxford Circus", "King's Cross")
            
        Returns:
            Dictionary with matching stops
        """
        if self.use_mock:
            return self._mock_search_stops(query)
            
        try:
            url = f"{self.base_url}/StopPoint/Search"
            params = {
                'query': query,
                'modes': 'tube,bus'
            }
            if self.app_key:
                params['app_key'] = self.app_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            matches = data.get('matches', [])
            
            formatted_stops = []
            for match in matches[:10]:  # Limit to 10 results
                formatted_stops.append({
                    'id': match.get('id'),
                    'name': match.get('name'),
                    'modes': match.get('modes', []),
                    'zone': match.get('zone'),
                    'lat': match.get('lat'),
                    'lon': match.get('lon')
                })
            
            return {
                'success': True,
                'query': query,
                'stops': formatted_stops,
                'count': len(formatted_stops),
                'explanation': f"Found {len(formatted_stops)} stops matching '{query}'"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    # ===== MOCK DATA FOR OFFLINE LEARNING =====
    
    def _mock_tube_lines(self) -> Dict[str, Any]:
        """Mock tube line data"""
        return {
            'success': True,
            'lines': [
                {'id': 'bakerloo', 'name': 'Bakerloo', 'modeName': 'tube'},
                {'id': 'central', 'name': 'Central', 'modeName': 'tube'},
                {'id': 'circle', 'name': 'Circle', 'modeName': 'tube'},
                {'id': 'district', 'name': 'District', 'modeName': 'tube'},
                {'id': 'northern', 'name': 'Northern', 'modeName': 'tube'},
                {'id': 'piccadilly', 'name': 'Piccadilly', 'modeName': 'tube'},
                {'id': 'victoria', 'name': 'Victoria', 'modeName': 'tube'},
            ],
            'count': 7,
            'explanation': "Mock data: Sample London Underground lines",
            'mock': True
        }
    
    def _mock_bus_routes(self) -> Dict[str, Any]:
        """Mock bus route data"""
        return {
            'success': True,
            'routes': [
                {'id': 'route-1', 'name': '1', 'modeName': 'bus'},
                {'id': 'route-24', 'name': '24', 'modeName': 'bus'},
                {'id': 'route-N1', 'name': 'N1', 'modeName': 'bus'},
            ],
            'count': 3,
            'explanation': "Mock data: Sample London bus routes",
            'mock': True
        }
    
    def _mock_arrivals(self, stop_id: str) -> Dict[str, Any]:
        """Mock arrival data"""
        now = datetime.now()
        
        arrivals = [
            {
                'line': 'Northern',
                'destination': 'Edgware',
                'platform': 'Northbound',
                'time_to_station': 2,
                'expected_arrival': (now + timedelta(minutes=2)).isoformat(),
                'current_location': 'At Platform'
            },
            {
                'line': 'Northern',
                'destination': 'Morden',
                'platform': 'Southbound',
                'time_to_station': 5,
                'expected_arrival': (now + timedelta(minutes=5)).isoformat(),
                'current_location': 'Approaching'
            }
        ]
        
        return {
            'success': True,
            'stop_id': stop_id,
            'arrivals': arrivals,
            'count': len(arrivals),
            'timestamp': now.isoformat(),
            'explanation': "Mock data: Sample arrivals",
            'mock': True
        }
    
    def _mock_search_stops(self, query: str) -> Dict[str, Any]:
        """Mock stop search data"""
        stops = {
            'kings cross': [
                {
                    'id': '940GZZLUKSX',
                    'name': "King's Cross St. Pancras Underground Station",
                    'modes': ['tube'],
                    'zone': '1',
                    'lat': 51.5308,
                    'lon': -0.1238
                }
            ],
            'oxford': [
                {
                    'id': '940GZZLUOXC',
                    'name': 'Oxford Circus Underground Station',
                    'modes': ['tube'],
                    'zone': '1',
                    'lat': 51.5152,
                    'lon': -0.1415
                }
            ]
        }
        
        # Find matching stops
        query_lower = query.lower()
        matching_stops = []
        for key, stop_list in stops.items():
            if key in query_lower:
                matching_stops.extend(stop_list)
        
        if not matching_stops:
            matching_stops = list(stops.values())[0]  # Default to first
        
        return {
            'success': True,
            'query': query,
            'stops': matching_stops,
            'count': len(matching_stops),
            'explanation': f"Mock data: Sample stops for '{query}'",
            'mock': True
        }
    
    # ===== EDUCATIONAL HELPERS =====
    
    def generate_tutorial(self, lesson_level: int = 1) -> Dict[str, Any]:
        """
        Generate step-by-step tutorial
        
        Args:
            lesson_level: 1=basics, 2=intermediate, 3=advanced
            
        Returns:
            Tutorial content
        """
        tutorials = {
            1: {
                'title': '🚇 Lesson 1: Your First TfL API Call',
                'objective': 'Learn to fetch data from Transport for London API',
                'concepts': ['HTTP requests', 'JSON parsing', 'Error handling'],
                'code_example': '''
# Step 1: Import the requests library
import requests

# Step 2: Define the TfL API endpoint
url = "https://api.tfl.gov.uk/Line/Mode/tube"

# Step 3: Make the request
response = requests.get(url)

# Step 4: Parse the JSON response
lines = response.json()

# Step 5: Display the lines
for line in lines:
    print(f"Line: {line['name']}")
''',
                'exercises': [
                    'Modify the code to print line IDs',
                    'Count how many tube lines exist',
                    'Add error handling with try/except'
                ]
            },
            2: {
                'title': '🚇 Lesson 2: Search for Stops',
                'objective': 'Learn to use query parameters and search',
                'concepts': ['Query parameters', 'Searching', 'Filtering results'],
                'code_example': '''
# Search for stops by name
query = "Oxford Circus"

url = "https://api.tfl.gov.uk/StopPoint/Search"
params = {
    'query': query,
    'modes': 'tube,bus'
}

response = requests.get(url, params=params)
data = response.json()

stops = data['matches']
for stop in stops[:5]:  # First 5 results
    print(f"{stop['name']} - {stop['modes']}")
''',
                'exercises': [
                    'Search for stops near your location',
                    'Filter results by mode (tube only)',
                    'Create a function to find nearest stop'
                ]
            },
            3: {
                'title': '🚇 Lesson 3: Real-Time Arrivals',
                'objective': 'Work with live arrival predictions',
                'concepts': ['Real-time data', 'Timestamps', 'Data sorting'],
                'code_example': '''
from datetime import datetime

def get_next_trains(stop_id):
    """Get upcoming train arrivals"""
    url = f"https://api.tfl.gov.uk/StopPoint/{stop_id}/Arrivals"
    
    response = requests.get(url)
    arrivals = response.json()
    
    # Sort by time to station
    arrivals.sort(key=lambda x: x['timeToStation'])
    
    for arrival in arrivals[:5]:
        line = arrival['lineName']
        dest = arrival['destinationName']
        mins = arrival['timeToStation'] // 60
        print(f"{line} to {dest}: {mins} minutes")

# Try it at King's Cross
get_next_trains("940GZZLUKSX")
''',
                'exercises': [
                    'Filter by specific line',
                    'Show only northbound trains',
                    'Create alerts for trains arriving soon'
                ]
            }
        }
        
        return tutorials.get(lesson_level, tutorials[1])
    
    def create_practice_exercise(self, difficulty: str = 'beginner') -> Dict[str, Any]:
        """
        Create coding exercises
        
        Args:
            difficulty: 'beginner', 'intermediate', 'advanced'
            
        Returns:
            Exercise description and tests
        """
        exercises = {
            'beginner': {
                'title': 'Exercise: List All Tube Lines',
                'description': 'Create a function that fetches and displays all tube lines',
                'starter_code': '''
def list_tube_lines():
    """
    Fetch all London Underground lines
    
    Expected output:
    Bakerloo
    Central
    Circle
    ...
    """
    # YOUR CODE HERE
    pass

# Test your function
list_tube_lines()
''',
                'hints': [
                    'Use requests.get() with TfL API',
                    'Parse the JSON response',
                    'Loop through the lines list'
                ]
            },
            'intermediate': {
                'title': 'Exercise: Find Nearest Station',
                'description': 'Given coordinates, find the nearest tube station',
                'starter_code': '''
import math

def distance(lat1, lon1, lat2, lon2):
    """Calculate approximate distance"""
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)

def find_nearest_station(my_lat, my_lon):
    """
    Find nearest tube station to coordinates
    
    Args:
        my_lat: Your latitude
        my_lon: Your longitude
    
    Returns:
        Nearest station information
    """
    # YOUR CODE HERE
    pass

# Test (coordinates near London Eye)
nearest = find_nearest_station(51.5033, -0.1195)
print(f"Nearest station: {nearest}")
''',
                'hints': [
                    'Search for nearby stops',
                    'Calculate distance to each',
                    'Find minimum distance'
                ]
            }
        }
        
        return exercises.get(difficulty, exercises['beginner'])


# ===== MCP INTEGRATION =====

async def extend_tutor_with_london_tools(tutor_instance):
    """
    Extend tutor with London Transport tools
    
    Usage:
        tutor = EnhancedSecurityTutor()
        await extend_tutor_with_london_tools(tutor)
    """
    london_tracker = LondonTransportTracker(use_mock=True)  # Start with mock
    
    async def tool_london_tube_lines(args):
        """Get London Underground lines"""
        return london_tracker.get_tube_lines()
    
    async def tool_london_bus_routes(args):
        """Get London bus routes"""
        return london_tracker.get_bus_routes()
    
    async def tool_london_arrivals(args):
        """Get arrivals at a stop"""
        stop_id = args.get('stop_id', '940GZZLUKSX')  # Default: King's Cross
        return london_tracker.get_stop_arrivals(stop_id)
    
    async def tool_london_search(args):
        """Search for stops"""
        query = args.get('query', 'Oxford Circus')
        return london_tracker.search_stops(query)
    
    async def tool_london_tutorial(args):
        """Get London Transport tutorial"""
        lesson = args.get('lesson', 1)
        return london_tracker.generate_tutorial(lesson)
    
    async def tool_london_exercise(args):
        """Get practice exercise"""
        difficulty = args.get('difficulty', 'beginner')
        return london_tracker.create_practice_exercise(difficulty)
    
    # Attach to tutor
    tutor_instance.tool_london_tube_lines = tool_london_tube_lines
    tutor_instance.tool_london_bus_routes = tool_london_bus_routes
    tutor_instance.tool_london_arrivals = tool_london_arrivals
    tutor_instance.tool_london_search = tool_london_search
    tutor_instance.tool_london_tutorial = tool_london_tutorial
    tutor_instance.tool_london_exercise = tool_london_exercise
    
    # Store tracker instance
    tutor_instance.london_tracker = london_tracker
    
    print("✅ London Transport tools integrated!")
    print("   🚇 Real TfL API integration")
    print("   📚 6 new tools available")
    
    return tutor_instance
