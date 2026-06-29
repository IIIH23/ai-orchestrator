import urllib.request, json

pat = '***'
url = 'https://api.github.com/repos/IIIH23/earth-pulse-poc/actions/workflows/linear-sync.yml/dispatches'
data = json.dumps({"ref": "master"}).encode()
req = urllib.request.Request(url, data=data, method='POST')
req.add_header('Authorization', f'Bearer {pat}')
req.add_header('Accept', 'application/vnd.github+json')
req.add_header('X-GitHub-Api-Version', '2022-11-28')

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print('Status:', resp.status)
        if resp.status == 204:
  SUCCESS: Linear Sync workflow triggered!')
     se:
      print('Response:', resp.read().decode()[:200])
except urllib.error.HTTPError as e:
    print(f'Error: HTTP {e.code}')
    print(e.read().decode()[:300])
