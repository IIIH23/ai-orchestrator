import json
import urllib.request
import os

token = os.environ['CF_API_TOKEN']
zone_id = os.environ['CF_ZONE_ID']

print('=== Verifying CF API Token ===')
url = 'https://api.cloudflare.com/client/v4/user/tokens/verify'
req = urllib.request.Request(url)
req.add_header('Authorization', 'Bearer ' + token)
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        r = json.loads(resp.read())
        print('Token status:', r.get('result', {}).get('status'))
        print('Success:', r.get('success'))
        if not r.get('success'):
            print('Errors:', json.dumps(r.get('errors', []), ensure_ascii=False)[:400])
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()[:300]}')

print()
print('=== Listing zones ===')
url = 'https://api.cloudflare.com/client/v4/zones'
req = urllib.request.Request(url)
req.add_header('Authorization', 'Bearer ' + token)
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        r = json.loads(resp.read())
        print('Success:', r.get('success'))
        zones = r.get('result', [])
        print(f'Found {len(zones)} zones')
        for z in zones[:10]:
            print(f'  {z["name"]} (id={z["id"]}, status={z["status"]})')
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()[:300]}')
