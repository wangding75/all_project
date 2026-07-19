#!/usr/bin/env python3
"""CI/CD Packaging Script: Automates downloading frida-server, extracting, and renaming it for anti-detection."""
from __future__ import annotations

import lzma
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP_DIR = ROOT / "tools" / "setup"

FRIDA_VERSION = "16.7.19"
FRIDA_ARCH = "android-x86_64"  # Default MuMu/Emulator architecture
FRIDA_FILE = f"frida-server-{FRIDA_VERSION}-{FRIDA_ARCH}.xz"
DOWNLOAD_URL = f"https://github.com/frida/frida/releases/download/{FRIDA_VERSION}/{FRIDA_FILE}"

OUT_XZ = SETUP_DIR / FRIDA_FILE
OUT_BIN = SETUP_DIR / "sys_hlpd"  # Renamed for anti-detection


def download_frida() -> None:
    SETUP_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_BIN.is_file():
        print(f"[*] sys_hlpd already exists at {OUT_BIN}. Skipping download.")
        return

    if not OUT_XZ.is_file():
        print(f"[*] Downloading {FRIDA_FILE} from {DOWNLOAD_URL}...")
        try:
            # Download with a custom User-Agent to avoid blocks
            req = urllib.request.Request(
                DOWNLOAD_URL,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req) as response, open(OUT_XZ, "wb") as out_file:
                out_file.write(response.read())
            print("[+] Download complete.")
        except Exception as e:
            print(f"[-] Download failed: {e}")
            print("[-] Please download the file manually and place it in tools/setup/")
            raise

    print(f"[*] Decompressing {FRIDA_FILE} to {OUT_BIN}...")
    try:
        with lzma.open(OUT_XZ) as f_in, open(OUT_BIN, "wb") as f_out:
            f_out.write(f_in.read())
        print(f"[+] Successfully extracted and renamed to {OUT_BIN}")
        
        # Clean up the compressed archive to save space
        if OUT_XZ.is_file():
            OUT_XZ.unlink()
            print("[*] Cleaned up temporary archive.")
    except Exception as e:
        print(f"[-] Decompression failed: {e}")
        raise


def main() -> None:
    print("=== Start Packaging / CI-CD Build Task ===")
    try:
        download_frida()
        print("=== Packaging Task Finished Successfully ===")
    except Exception as e:
        print(f"=== Packaging Task Failed: {e} ===")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
