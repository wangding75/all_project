from __future__ import annotations

import urllib.request

URLS = [
    "http://mumu-apk.fp.ps.netease.com/file/6a3e2dc0365cdef1ab1bcdebZQKc43iw07",
    "http://mumu-apk.fp.ps.netease.com/file/6a3e2dcb0a9eb5f0f9f59743TKXIzYYz07",
    "http://mumu-apk.fp.ps.netease.com/file/6a45f45b365b24696a9a7114645l9NzK07",
    "http://mumu-apk.fp.ps.netease.com/file/6a4602e455e787bdf2d74cc9Jx4Udb8H07",
    "http://mumu-apk.fp.ps.netease.com/file/6a461090562356a632a1114cxA4yJyrQ07",
]


def main() -> None:
    for u in URLS:
        try:
            req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                print(u)
                print(" ", r.status, r.headers.get("Content-Type"), r.headers.get("Content-Length"))
                print(" ", r.headers.get("Content-Disposition"))
        except Exception as e:
            print(u, "ERR", e)


if __name__ == "__main__":
    main()
