import os
import json
import urllib.request

key = os.environ.get('LINEAR_API_KEY', '')
if not key or key == '***' or len(key) < 10:
    print("LINEAR_API_KEY not available")
    exit(0)

url = 'https://api.linear.app/graphql'


def query(q, variables=None):
    payload = {"query": q}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {key}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if 'errors' in result:
                raise Exception(result['errors'][0]['message'])
            return result['data']
    except urllib.error.HTTPError as e:
        raise Exception(f'HTTP {e.code}: {e.read().decode()[:200]}')


# Step 1 - Find team
print("Step 1: Finding team...")
teams = query('{ teams { nodes { id name } } }')['teams']['nodes']
team_id = None
for t in teams:
    if 'pulse' in t['name'].lower() or 'terra' in t['name'].lower():
        team_id = t['id']
        print(f"  Found: {t['name']}")
        break

if not team_id:
    print("  Team not found:")
    for t in teams:
        print(f"    {t['name']}")
    exit(1)

# Step 2 - Create project
print("\nStep 2: Creating project...")
create_q = """
mutation($teamId: String!, $name: String!) {
    projectCreate(input: { teamIds: [$teamId], name: $name }) {
        success
        project { id name }
    }
}
"""
try:
    result = query(create_q, {'teamId': team_id, 'name': 'Pulse of Earth Roadmap'})
    if result['projectCreate']['success']:
        proj_id = result['projectCreate']['project']['id']
        print(f"  Created: {result['projectCreate']['project']['name']} ({proj_id})")
    else:
        print("  Failed to create project")
        exit(1)
except Exception as e:
    print(f"  Error: {e}")
    exit(1)

# Step 3 - List issues
print("\nStep 3: Existing issues...")
issues = query('{ issues(first: 50) { nodes { id title state { name } } } }')['issues']['nodes']
print(f"  Found {len(issues)} issues")
for i in issues[:5]:
    print(f"    [{i['state']['name']}] {i['title'][:50]}")

# Step 4 - Create labels
print("\nStep 4: Creating labels...")
labels = ['discovery', 'architecture', 'backend', 'frontend', 'devops', 'security', 'testing', 'documentation']
for label_name in labels:
    label_q = """
    mutation($name: String!, $teamId: String!) {
        labelCreate(input: { name: $name, teamId: $teamId }) { success }
    }
    """
    try:
        r = query(label_q, {'name': label_name, 'teamId': team_id})
        if r.get('labelCreate', {}).get('success', False):
            print(f"  OK: {label_name}")
        else:
            print(f"  Exists: {label_name}")
    except Exception:
        print(f"  Exists: {label_name}")

# Result
print("\n=== RESULT ===")
print(f"Project ID: {proj_id}")
print(f"Team ID: {team_id}")
