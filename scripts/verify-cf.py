import json
import urllib.request
import os

token = os.environ['CF_API_TOKEN']

# First: verify token
url = 'https://api.cloudflare.com/client/v4/user/tokens/verify'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        r = json.loads(resp.read())
        print('Token status:', r.get('result', {}).get('status'))
        print('Success:', r.get('success'))
        if not r.get('success'):
            print('Errors:', json.dumps(r.get('errors', []), indent=2, ensure_ascii=False))
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()[:500]}')

print()

# List zones
print('=== Available zones ===')
url = 'https://api.cloudflare.com/client/v4/zones'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        r = json.loads(resp.read())
        print(f'Success: {r.get("success")}')
        for zone in r.get('result', []):
            print(f"  {zone['name']} (id={zone['id']}, status={zone['status']})")
        if not r.get('result'):
            print('No zones found. Token may not have Zone.Read permission.')
            if not r.get('success'):
                print('Errors:', json.dumps(r.get('errors', []), indent=2, ensure_ascii=False)[:300])
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()[:500]}')
