from __future__ import annotations

import re
import urllib.request

SCRIPTS = [
    "https://mumu.163.com/res/cms/res/page.CMKbWR5T.js",
    "https://mumu.163.com/res/cms/res/CommonJs.astro_astro_type_script_index_0_lang.DVyn8tgw.js",
    "https://mumu.163.com/res/cms/res/HomeJs.astro_astro_type_script_index_0_lang.BfBxF1VF.js",
]


def main() -> None:
    for url in SCRIPTS:
        print("===", url)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            js = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            print("fail", e)
            continue
        print("len", len(js))
        urls = re.findall(r"https?://[^\s\"'<>]{8,400}", js)
        for u in urls:
            low = u.lower()
            if any(k in low for k in ("exe", "download", "install", "gdl", "fp.ps", "mumu-apk", "setup")):
                print(u)
        # chinese download keywords
        for kw in ("下载", "download", "windows", "Jdownload", "channel"):
            if kw in js:
                print("has", kw)


if __name__ == "__main__":
    main()
