# test_dashboard_routes.py
"""Quick test to check what routes are available on your main server"""

import requests
import json

def test_dashboard_routes():
    """Test available dashboard routes"""
    base_url = "http://localhost:8000"
    
    routes_to_test = [
        "/",
        "/health", 
        "/dev-dashboard",
        "/dashboard",
        "/api/dashboard-data/test",  # Fixed: add test dashboard ID
        "/ws",
        "/dashboard-ws/test"  # Fixed: add test dashboard ID
    ]
    
    print("🔍 Testing Dashboard Routes")
    print("=" * 40)
    
    for route in routes_to_test:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            status = "✅ Available" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"{route:<20} {status}")
            
            # If it's a dashboard route, show some content info
            if "dashboard" in route and response.status_code == 200:
                content_length = len(response.text)
                print(f"                    Content length: {content_length} chars")
                
        except requests.exceptions.RequestException as e:
            print(f"{route:<20} ❌ Error: {str(e)[:30]}...")
    
    print("\n" + "=" * 40)
    print("🎯 Next Steps:")
    print("If /dev-dashboard shows ❌, we need to add the route to main.py")
    print("If /dev-dashboard shows ✅, you can access it in browser!")

if __name__ == "__main__":
    test_dashboard_routes()
