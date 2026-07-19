"""Scrape possible MuMu Windows installer URLs from official pages."""
from __future__ import annotations

import re
import urllib.request

PAGES = [
    "https://mumu.163.com/download/",
    "https://mumu.163.com/",
    "https://www.mumuplayer.com/download/",
]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", "replace")


def main() -> None:
    for page in PAGES:
        print("===", page)
        try:
            html = fetch(page)
        except Exception as e:
            print("fetch fail", e)
            continue
        urls = set(re.findall(r"https?://[^\s\"'<>]+", html))
        for u in sorted(urls):
            low = u.lower()
            if any(k in low for k in (".exe", "download", "mumu", "install", "setup")):
                if any(x in low for x in (".png", ".jpg", ".css", ".js", ".svg", "font")):
                    continue
                print(u)


if __name__ == "__main__":
    main()
