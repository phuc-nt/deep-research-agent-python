import requests
import json
import time
from pprint import pprint

BASE_URL = "http://localhost:8000/api/v1"

def test_create_research():
    """Test create research endpoint"""
    url = f"{BASE_URL}/research"
    data = {
        "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
        "topic": "Trí tuệ nhân tạo trong giáo dục",
        "scope": "Tổng quan và ứng dụng thực tế",
        "target_audience": "Giáo viên và nhà quản lý giáo dục"
    }
    
    print(f"Creating research task with data: {json.dumps(data, indent=2, ensure_ascii=False)}")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Research task created successfully with ID: {result['id']}")
        print(f"Status: {result['status']}")
        return result['id']
    else:
        print(f"Error creating research task: {response.status_code}")
        print(response.text)
        return None

def test_get_research(research_id):
    """Test get research endpoint"""
    url = f"{BASE_URL}/research/{research_id}"
    
    print(f"Getting research task with ID: {research_id}")
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Research task retrieved successfully")
        print(f"Status: {result['status']}")
        return result
    else:
        print(f"Error getting research task: {response.status_code}")
        print(response.text)
        return None

def test_get_research_status(research_id):
    """Test get research status endpoint"""
    url = f"{BASE_URL}/research/{research_id}/status"
    
    print(f"Getting status for research task with ID: {research_id}")
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result}")
        return result
    else:
        print(f"Error getting research status: {response.status_code}")
        print(response.text)
        return None

def test_get_research_outline(research_id):
    """Test get research outline endpoint"""
    url = f"{BASE_URL}/research/{research_id}/outline"
    
    print(f"Getting outline for research task with ID: {research_id}")
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        if result:
            print(f"Outline retrieved successfully")
            print(f"Number of sections: {len(result['sections'])}")
            for i, section in enumerate(result['sections']):
                print(f"  Section {i+1}: {section['title']}")
        else:
            print("Outline not available yet")
        return result
    else:
        print(f"Error getting research outline: {response.status_code}")
        print(response.text)
        return None

def monitor_research_progress(research_id, max_attempts=10, delay=5):
    """Monitor research progress until completion or max attempts reached"""
    print(f"Monitoring research progress for task ID: {research_id}")
    
    for attempt in range(max_attempts):
        print(f"\nAttempt {attempt + 1}/{max_attempts}")
        
        # Get current status
        status = test_get_research_status(research_id)
        
        if status == "completed":
            print("Research completed!")
            result = test_get_research(research_id)
            print("\nFinal result:")
            pprint(result)
            return result
        elif status == "failed":
            print("Research failed!")
            result = test_get_research(research_id)
            print("\nError details:")
            pprint(result.get("error"))
            return result
        
        # Get outline if available
        if status in ["outlining", "researching", "editing"]:
            outline = test_get_research_outline(research_id)
        
        # Wait before next attempt
        if attempt < max_attempts - 1:
            print(f"Waiting {delay} seconds before next check...")
            time.sleep(delay)
    
    print("Maximum monitoring attempts reached")
    return test_get_research(research_id)

if __name__ == "__main__":
    # Create a new research task
    research_id = test_create_research()
    
    if research_id:
        # Monitor progress
        monitor_research_progress(research_id, max_attempts=20, delay=3) 