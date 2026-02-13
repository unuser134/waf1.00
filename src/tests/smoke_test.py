import requests

ENDPOINTS = [
    ('health', 'http://localhost:8080/api/health'),
    ('logs', 'http://localhost:8080/api/logs?limit=5'),
    ('rules_reload', 'http://localhost:8080/api/rules/reload')
]

results = []
for name, url in ENDPOINTS:
    try:
        if name == 'rules_reload':
            r = requests.post(url, timeout=5)
        else:
            r = requests.get(url, timeout=5)
        try:
            payload = r.json()
        except Exception:
            payload = r.text[:200]
        results.append((name, r.status_code, payload))
    except Exception as e:
        results.append((name, 'ERROR', str(e)))

for name, status, payload in results:
    print(f"{name}: {status} -> {payload}")

# exit code 0 if all endpoints returned 2xx
if all(isinstance(s, int) and 200 <= s < 300 for _, s, _ in results):
    print('\nSMOKE TEST: OK')
else:
    print('\nSMOKE TEST: FAIL')
    raise SystemExit(1)
