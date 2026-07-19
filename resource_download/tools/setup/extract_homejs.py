from __future__ import annotations

import re
import urllib.request

url = "https://mumu.163.com/res/cms/res/HomeJs.astro_astro_type_script_index_0_lang.BfBxF1VF.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
js = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
Path = __import__("pathlib").Path
Path("tools/setup/HomeJs.js").write_text(js, encoding="utf-8")
print("saved HomeJs.js len", len(js))
for m in re.finditer(r".{0,80}(download|exe|gdl|fp\.ps|install|windows).{0,120}", js, re.I):
    print(m.group(0).replace("\n", " ")[:220])
    print("---")
