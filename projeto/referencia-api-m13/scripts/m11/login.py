import json
import ssl
import sys
import urllib.error
import urllib.request

n = int(sys.argv[2])
url = sys.argv[1]
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
codes = []
for _ in range(n):
    req = urllib.request.Request(
        url,
        data=json.dumps({"username": "x", "password": "errada"}).encode(),
        headers={"Content-Type": "application/json", "Host": "localhost"},
    )
    try:
        urllib.request.urlopen(req, context=ctx)
    except urllib.error.HTTPError as e:
        codes.append(e.code)
print(codes)
