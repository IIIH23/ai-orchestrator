import json
import urllib.request

key = '***'
url = 'https://api.linear.app/graphql'


def query(q, variables=None):
    payload = {"query": q}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', key)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if 'errors' in result:
                return result
            return result.get('data')
    except urllib.error.HTTPError as e:
        return {'error': e.read().decode()[:300], 'status': e.code}


print("=== Raw Authorization header ===")
r = query('{ teams { nodes { id name } } }')
if isinstance(r, dict) and 'error' in r:
    print(f"FAIL: {r}")
elif isinstance(r, dict) and 'errors' in r:
    print(f"GraphQL Error: {r['errors'][0]['message']}")
else:
    print(f"OK: {len(r.get('teams',{}).get('nodes',[]))} teams")
    for t in r.get('teams',{}).get('nodes',[]):
        print(f"  {t['id'][:20]}... {t['name']}")
