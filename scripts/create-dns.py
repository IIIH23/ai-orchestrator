import json, urllib.request, os

token = os.environ['CF_API_TOKEN']
zone_id = os.environ['CF_ZONE_ID']

url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
data = json.dumps({
    "type": "A",
    "name": os.environ['DNS_RECORD_NAME'],
    "content": os.environ['STAGING_HOST'],
    "ttl": 300,
    "proxied": False,
}).encode()

req = urllib.request.Request(url, data=data, method='POST')
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        r = json.loads(resp.read())
        print('Success:', r.get('success'))
        for rec in r.get('result', []):
            print(f'  {rec["name"]} -> {rec["content"]}')
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()[:500]}')
