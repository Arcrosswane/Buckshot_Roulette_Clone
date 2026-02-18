import urllib.request
import urllib.error
import json

BASE_URL = 'http://127.0.0.1:5000'

def post(endpoint, data=None):
    url = BASE_URL + endpoint
    try:
        req = urllib.request.Request(url, method='POST')
        req.add_header('Content-Type', 'application/json')
        if data:
            jsondata = json.dumps(data).encode('utf-8')
            req.data = jsondata
        
        with urllib.request.urlopen(req) as response:
            print(f"POST {endpoint}: {response.status}")
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"POST {endpoint} FAILED: {e.code} - {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"POST {endpoint} ERROR: {e}")

def get(endpoint):
    url = BASE_URL + endpoint
    try:
        with urllib.request.urlopen(url) as response:
            print(f"GET {endpoint}: {response.status}")
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"GET {endpoint} FAILED: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"GET {endpoint} ERROR: {e}")

# 1. Reset (just in case)
post('/api/reset')

# 2. Join
post('/api/join', {'name': 'DebugP1'})
post('/api/join', {'name': 'DebugP2'})

# 3. Start
post('/api/start')

# 4. Get State (Trigger 500?)
get('/api/state?player=DebugP1')
