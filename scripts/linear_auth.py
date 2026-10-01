import json
import urllib.request

key = '***'
url = 'https://api.linear.app/graphql'
data = json.dumps({'query': '{ teams { nodes { id name } } }'}).encode()
req = urllib.request.Request(url, data=data, method='POST')
req.add_header('Authorization', key)
req.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req, timeout=30) as resp:
 r = json.loads(resp.read())
 if 'errors' in r:
  print('ERROR:', r['errors'][0]['message'])
 else:
  teams = r['data']['teams']['nodes']
  print(f'OK: {len(teams)} teams')
