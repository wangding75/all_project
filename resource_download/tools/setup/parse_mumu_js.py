from __future__ import annotations

import re
import urllib.request

url = "https://www.mumuplayer.com/res/cms/res/page.C95ZQHmb.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
js = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
print("len", len(js))
for m in re.findall(r"https?://[^\"'\s]{10,300}", js):
    low = m.lower()
    if any(k in low for k in ("exe", "download", "mumu", "install", "fp.ps", "gdl", "setup")):
        print(m)
for token in ("downloadUrl", "download_url", ".exe", "Jdownload", "windows"):
    print("token", token, js.find(token))
# dump interesting chunks
for token in ("http", "download", "exe"):
    i = 0
    count = 0
    while count < 5:
        j = js.find(token, i)
        if j < 0:
            break
        print("---", token, j, js[j : j + 180].replace("\n", " "))
        i = j + len(token)
        count += 1
