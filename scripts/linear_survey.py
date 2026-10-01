import urllib.request
import json

key = '***'
url = 'https://api.linear.app/graphql'

def query(q):
    data = json.dumps({"query": q}).encode()
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {key}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {'error': e.read().decode()[:300], 'status': e.code}

# Teams
print("=== Teams ===")
r = query('{ teams { nodes { id name } } }')
if 'error' in r:
    print('Error:', r)
else:
    for t in r['data']['teams']['nodes']:
        print(f"  {t['id'][:20]}... {t['name']}")

# Projects
print("\n=== Projects ===")
r = query('{ projects { nodes { id name } } }')
if 'error' in r:
    print('Error:', r)
else:
    for p in r['data']['projects']['nodes']:
        print(f"  {p['id'][:20]}... {p['name']}")

# Issues in Pulse of Earth team
print("\n=== Issues (first 10) ===")
r = query('{ issues(first: 10) { nodes { id title state { name } team { name } } } }')
if 'error' in r:
    print('Error:', r)
else:
    for i in r['data']['issues']['nodes']:
        team_name = i['team']['name'] if i['team'] else 'no team'
        print(f"  [{i['state']['name']}] {i['title'][:50]} (team: {team_name})")
