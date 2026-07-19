from __future__ import annotations

import re
import urllib.request

CANDIDATES = [
    "https://mumu.163.com/download/windows/",
    "https://mumu.163.com/api/v2/download?os=windows",
    "https://a.163.com/mumu",
    "https://adl.netease.com/d/g/mumu",
    "https://x19.gdl.netease.com/MuMuInstaller.exe",
    "https://mumu.nie.netease.com/download/windows",
]


def main() -> None:
    for u in CANDIDATES:
        try:
            req = urllib.request.Request(
                u,
                method="HEAD",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                print("OK", u, r.status, r.geturl())
                print(" ", r.headers.get("Content-Type"), r.headers.get("Content-Length"))
        except Exception as e:
            print("FAIL", u, type(e).__name__, e)

    # parse homepage scripts for api
    html = urllib.request.urlopen(
        urllib.request.Request("https://mumu.163.com/", headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30,
    ).read().decode("utf-8", "replace")
    for s in re.findall(r'src="([^"]+\.js)"', html):
        if s.startswith("//"):
            s = "https:" + s
        elif s.startswith("/"):
            s = "https://mumu.163.com" + s
        print("script", s)


if __name__ == "__main__":
    main()
